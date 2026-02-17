# Warm Restart vs Warm Reboot in SONiC

This document explains the differences between **warm restart** and **warm reboot** in SONiC.

## Overview

SONiC provides two mechanisms for minimizing traffic disruption during system/service updates:

| Feature | Warm Reboot | Warm Restart |
|---------|-------------|--------------|
| **Scope** | Entire system | Individual container/service |
| **Kernel reboot** | Yes | No |
| **Command** | `sudo warm-reboot` | `config warm_restart enable <service>` |

---

## Warm Reboot (System-level)

A **warm reboot** is a **system-wide operation** that restarts the entire SONiC switch (including the Linux kernel) while maintaining data plane forwarding.

### Characteristics

- **Scope**: Entire system - reboots the Linux kernel and all containers
- **Command**: `sudo warm-reboot`
- **Goal**: Upgrade the entire SONiC image with minimal traffic disruption
- **Data Plane**: Traffic continues forwarding during reboot (no packet loss for existing flows)
- **Control Plane**: Temporarily down during reboot
- **ASIC State**: Preserved - SDK/SAI maintains hardware state across reboot
- **Typical Duration**: ~90-120 seconds
- **Use Cases**: 
  - OS/image upgrades
  - Kernel updates
  - Full system restarts

### How It Works

1. System saves state to persistent storage
2. Kernel reboots using kexec (fast kernel reload)
3. ASIC/SDK preserves hardware forwarding state
4. After reboot, services restore state and reconcile with hardware
5. Control plane re-establishes sessions (BGP GR, LACP, etc.)

---

## Warm Restart (Container/Service-level)

A **warm restart** is a **per-service/container operation** that restarts individual Docker containers or services without rebooting the system.

### Characteristics

- **Scope**: Individual containers/services (bgp, swss, syncd, teamd)
- **Command**: `config warm_restart enable <service>` then restart the service
- **Goal**: Restart a specific service without affecting others
- **Data Plane**: Traffic continues forwarding
- **Control Plane**: Only the specific service is affected
- **ASIC State**: Preserved for the restarting component
- **Typical Duration**: ~30-60 seconds
- **Use Cases**:
  - Service upgrades
  - Bug fixes in specific containers
  - Configuration changes requiring service restart

### Supported Services

The following services support warm restart:

| Service | Description |
|---------|-------------|
| `bgp` | BGP routing (FRR) - uses BGP Graceful Restart |
| `swss` | Switch State Service |
| `syncd` | SAI/ASIC synchronization daemon |
| `teamd` | LAG/Port-channel management |
| `system` | Enable warm restart for all services |

### Configuration

```bash
# Enable warm restart for BGP
config warm_restart enable bgp

# Check warm restart status
show warm_restart config

# Disable warm restart for BGP
config warm_restart disable bgp
```

### State Storage

Warm restart settings are stored in `STATE_DB` under `WARM_RESTART_ENABLE_TABLE`:

```
WARM_RESTART_ENABLE_TABLE|bgp
    "enable" "true"
```

> **Note**: STATE_DB is not persistent across reboots. Settings are lost after a system reboot unless explicitly re-applied.

---

## Comparison Table

| Aspect | Warm Reboot | Warm Restart |
|--------|-------------|--------------|
| **Scope** | Entire system | Single container |
| **Kernel reboot** | Yes | No |
| **All services down** | Yes (temporarily) | No |
| **Use case** | Image upgrade | Service upgrade |
| **Downtime** | Longer (~90-120s) | Shorter (~30-60s) |
| **State storage** | Persistent | STATE_DB (non-persistent) |
| **Traffic impact** | Minimal (existing flows) | Minimal (service-specific) |

---

## Related: PR #3040 (NOS-4039)

PR #3040 implements **enabling warm restart for BGP by default**.

### Problem
- Warm restart is not enabled by default for any service
- The setting is stored in `STATE_DB`, which is lost after reboot
- Users had to manually re-enable warm restart after every reboot

### Solution
Introduces a **post-boot hook** mechanism:

1. Creates `/etc/config-setup/config-post-boot-hooks.d/` directory
2. Adds `config-warm-restart-defaults` script that runs after boot
3. Automatically executes `config warm_restart enable bgp`

### Files Changed
- `files/build_templates/sonic_debian_extension.j2` - Installs the hook
- `files/image_config/config-setup/config-setup` - Adds post-boot hook execution
- `files/image_config/config-setup/config-warm-restart-defaults` - The hook script

---

## References

- [SONiC Warmboot Documentation](https://github.com/sonic-net/SONiC/blob/master/doc/warm-reboot/SONiC_Warmboot.md)
- [SWSS Warm Restart](https://github.com/sonic-net/SONiC/blob/master/doc/warm-reboot/swss_warm_restart.md)
- [System Warmboot](https://github.com/sonic-net/SONiC/blob/master/doc/warm-reboot/system-warmboot.md)
