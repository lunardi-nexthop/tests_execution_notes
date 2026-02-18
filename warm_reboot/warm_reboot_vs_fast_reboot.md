# Warm Reboot vs Fast Reboot in SONiC

## Overview

Both **Warm Reboot** and **Fast Reboot** are system-level reboot mechanisms in SONiC that use `kexec` to quickly reload the kernel without going through BIOS/UEFI. However, they differ significantly in their approach to preserving control plane state.

| Aspect | Fast Reboot | Warm Reboot |
|--------|-------------|-------------|
| **Primary Goal** | Quick reboot with minimal data plane disruption | Zero-impact reboot preserving control plane state |
| **Data Plane Impact** | ~25-30 seconds disruption | No packet loss for existing flows |
| **Control Plane Impact** | ≤90 seconds (BGP sessions drop) | Preserved via Graceful Restart |
| **ASIC State** | Reset then restored from saved state | Preserved in hardware |
| **BGP Handling** | Uses BGP GR (helper mode on peers) | Full BGP Graceful Restart |
| **syncd Start Flag** | `-t fast` | `-t warm` |

---

## Fast Reboot

### Definition
Fast Reboot (also known as Fast-Reload) enables a switch to reboot quickly with **minimum disruption to the data plane** while accepting that **control plane sessions will be reset**.

### Key Characteristics

| Property | Details |
|----------|---------|
| **Command** | `sudo fast-reboot` |
| **Data Plane Disruption** | ≤25 seconds |
| **Control Plane Disruption** | ≤90 seconds |
| **LACP Mode Requirement** | SLOW mode required for all LAG interfaces |
| **Boot Type Flag** | `SONIC_BOOT_TYPE=fast` in `/proc/cmdline` |
| **STATE_DB Flag** | `FAST_RESTART_ENABLE_TABLE|system` = `true` |

### How Fast Reboot Works

1. **Dump FDB and ARP entries** from SONiC tables to disk (preserved across reboot)
2. **Stop BGP daemon** in BGP Graceful Restart mode (peers preserve routes for 120s)
3. **Stop LAG daemon** - sends last LACP protocol update (90s window)
4. **Stop Docker service** - prevents filesystem corruption
5. **Stop ASIC drivers** if necessary
6. **Execute kexec** - load new kernel and start it
7. **syncd starts** with `-t fast` flag (fast mode initialization)
8. **swss restores** FDB and ARP entries from saved files:
   - `/fdb.json` → FDB table
   - `/arp.json` → ARP table  
   - `/default_routes.json` → Default routes
   - `/media_config.json` → Media configuration
9. **LAG daemon restores** LAG interfaces
10. **BGP daemon re-establishes** sessions with neighbors

### teamd Signal Handling
During fast reboot, teamd processes receive **SIGUSR2** signal:
```bash
# From teamd.sh
docker exec -i ${SERVICE}$DEV pkill -USR2 -f ${TEAMD_CMD}
```
This allows teamd to send **last LACP frames** before shutdown.

---

## Warm Reboot

### Definition
Warm Reboot enables a switch to reboot the entire system (including kernel) while **maintaining data plane forwarding** and **preserving control plane state** through graceful restart mechanisms.

### Key Characteristics

| Property | Details |
|----------|---------|
| **Command** | `sudo warm-reboot` |
| **Data Plane Disruption** | Zero packet loss for existing flows |
| **Control Plane Disruption** | Temporarily down, uses Graceful Restart |
| **ASIC State** | Preserved in hardware |
| **Boot Type Flag** | `SONIC_BOOT_TYPE=warm` in `/proc/cmdline` |
| **STATE_DB Flag** | `WARM_RESTART_ENABLE_TABLE|<service>` = `true` |

### How Warm Reboot Works

1. **Pre-shutdown preparation** - Notify all services of impending warm restart
2. **BGP sends Graceful Restart** notification to peers (forwarding state preserved)
3. **teamd sends SIGUSR1** - prepares LAG for warm restart (preserves state)
4. **syncd pre-shutdown** - ASIC state preserved in hardware
5. **Execute kexec** - load new kernel
6. **syncd starts** with `-t warm` flag (warm mode initialization)
7. **Reconciliation phase** - Compare restored state with ASIC state
8. **Control Plane Assistant** maintains forwarding during control plane downtime
9. **Services reconcile** and resume normal operation

### teamd Signal Handling
During warm reboot, teamd processes receive **SIGUSR1** signal:
```bash
# From teamd.sh
docker exec -i ${SERVICE}$DEV pkill -USR1 -f ${TEAMD_CMD}
```
This **prepares teamd for warm-reboot** while preserving LAG state.

---

## Detailed Comparison

### Control Plane Behavior

| Aspect | Fast Reboot | Warm Reboot |
|--------|-------------|-------------|
| **BGP Sessions** | Drop and re-establish | Preserved via GR |
| **BGP Routes** | Peers hold stale routes (120s GR timer) | Full state preserved |
| **LACP/LAG** | Send last frame, then timeout | State preserved |
| **ARP/NDP** | Saved to disk, restored after boot | Preserved in ASIC |

### Data Plane Behavior

| Aspect | Fast Reboot | Warm Reboot |
|--------|-------------|-------------|
| **Existing Flows** | Brief disruption (~25s) | No disruption |
| **FDB Table** | Saved to /fdb.json, restored | Preserved in ASIC |
| **ASIC Programming** | Reset then reprogrammed | State maintained |
| **Traffic Forwarding** | Uses stale FIB during reboot | Continues uninterrupted |

### syncd Initialization

```bash
# From syncd_init_common.sh
function set_start_type()
{
    if [ x"$WARM_BOOT" == x"true" ]; then
        CMD_ARGS+=" -t warm"      # Warm reboot mode
    elif [ x"$FAST_REBOOT" == x"yes" ]; then
        CMD_ARGS+=" -t fast"      # Fast reboot mode
    elif [ x"$FASTFAST_REBOOT" == x"yes" ]; then
        CMD_ARGS+=" -t fastfast"  # Fast-fast reboot mode
    fi
}
```

### Boot Type Detection

```bash
# From syncd_common.sh - getBootType()
case "$(cat /proc/cmdline)" in
    *SONIC_BOOT_TYPE=warm*)
        TYPE='warm'
        ;;
    *SONIC_BOOT_TYPE=fast*|*fast-reboot*)
        SYSTEM_FAST_REBOOT=$(sonic-db-cli STATE_DB hget "FAST_RESTART_ENABLE_TABLE|system" enable)
        if [[ x"${SYSTEM_FAST_REBOOT}" == x"true" ]]; then
            TYPE='fast'
        else
            TYPE='cold'
        fi
        ;;
    *)
        TYPE='cold'
esac
```

---

## swss Behavior

### Fast Reboot - State Restoration
During fast reboot, swss restores saved state from JSON files:

```bash
# From swssconfig.sh
function fast_reboot {
    case "$(cat /proc/cmdline)" in
        *fast-reboot*)
            if [[ -f /fdb.json ]]; then
                swssconfig /fdb.json
                mv -f /fdb.json /fdb.json.1
            fi
            if [[ -f /arp.json ]]; then
                swssconfig /arp.json
                mv -f /arp.json /arp.json.1
            fi
            if [[ -f /default_routes.json ]]; then
                swssconfig /default_routes.json
            fi
            if [[ -f /media_config.json ]]; then
                swssconfig /media_config.json
            fi
            ;;
    esac
}
```

### Warm Reboot - Reconciliation
During warm reboot, swss performs **reconciliation** to compare expected state with ASIC state and resolve any differences.

---

## Finalization

Both reboot types have a finalization phase after services are restored:

```bash
# From finalize-warmboot.sh
function finalize_fast_reboot() {
    debug "Finalizing fast-reboot..."
    finalize_common
    sonic-db-cli STATE_DB hset "FAST_RESTART_ENABLE_TABLE|system" "enable" "false"
    sonic-db-cli CONFIG_DB DEL "WARM_RESTART|teamd"
}

function finalize_warm_boot() {
    debug "Finalizing warmboot..."
    finalize_common
    sudo config warm_restart disable
}
```

---

## When to Use Each

### Use Fast Reboot When:
- Quick system upgrade is needed
- Some control plane disruption is acceptable
- Data plane disruption of ~25-30 seconds is tolerable
- You need faster reboot time than warm reboot

### Use Warm Reboot When:
- Zero packet loss is required for existing flows
- Control plane sessions must be preserved
- Mission-critical services cannot tolerate BGP session flaps
- Performing in-service software upgrade (ISSU)

---

## Requirements Comparison

| Requirement | Fast Reboot | Warm Reboot |
|-------------|-------------|-------------|
| **LACP Mode** | SLOW mode required | SLOW mode required |
| **BGP GR Support** | Required on peers | Required on local and peers |
| **SAI/SDK Support** | Fast restart mode | Warm restart mode |
| **Control Plane Assistant** | Not used | Used to maintain forwarding |
| **Pre-shutdown Phase** | Simple state dump | Full service preparation |

---

## Related Reboot Types

| Reboot Type | Description |
|-------------|-------------|
| **cold reboot** | Full system restart through BIOS |
| **fast-reboot** | Quick kexec-based reboot, control plane reset |
| **warm-reboot** | kexec-based reboot with full state preservation |
| **fastfast-reboot** | Faster variant for specific use cases |
| **express-reboot** | Even faster reboot for supported platforms |

---

## References

- [SONiC Fast Reboot Wiki](https://github.com/sonic-net/SONiC/wiki/Fast-Reboot)
- [SONiC Warm Reboot Design](https://github.com/sonic-net/SONiC/blob/master/doc/warm-reboot/SONiC_Warmboot.md)
- [System Warmboot HLD](https://github.com/sonic-net/SONiC/blob/master/doc/warm-reboot/system-warmboot.md)
