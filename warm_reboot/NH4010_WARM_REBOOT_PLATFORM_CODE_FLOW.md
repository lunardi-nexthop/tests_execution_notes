# NH-4010 Platform Warm-Reboot Code Execution Flow

## Overview

This document explains which platform-specific code gets executed when `warm-reboot` is run on the NH-4010 (Nexthop 4010) platform.

---

## Platform Information

- **Platform**: NH-4010 (Nexthop 4010)
- **ASIC**: Broadcom (Tomahawk5 - BCM78900)
- **Platform Directory**: `device/nexthop/x86_64-nexthop_4010-r0/`
- **Platform Modules**: `platform/broadcom/sonic-platform-modules-nexthop/nh-4010/`

---

## Key Finding: NH-4010 Does NOT Have Platform-Specific Warm-Reboot Plugin

**Checked Location**: `device/nexthop/x86_64-nexthop_4010-r0/warm-reboot_plugin`

**Result**: ❌ File does not exist

**Implication**: NH-4010 uses the **generic SONiC warm-reboot flow** without platform-specific customizations during the warm-reboot command execution.

**Comparison with Other Platforms:**
- ✅ Celestica platforms have `warm-reboot_plugin` that sets LEDs to BMC control
- ✅ Supermicro platforms have `warm-reboot_plugin` that calls `sysledctl.py reboot`
- ❌ NH-4010 relies on generic Broadcom ASIC warm-reboot behavior

---

## Warm-Reboot Execution Flow

### 1. User Executes `warm-reboot` Command

```bash
warm-reboot -v
```

- **Script Location**: `/usr/local/bin/warm-reboot` (from sonic-utilities)
- **What it does**:
  - Checks if any warm restart is already in progress
  - Sets `WARM_RESTART_ENABLE_TABLE|system` to "true" in STATE_DB
  - Calls platform-specific warm-reboot plugin (if exists) ← **NH-4010: SKIPPED**
  - Initiates kexec-based warm reboot

### 2. SWSS Service Warm-Boot Detection

**File**: `files/scripts/swss.sh`

**Function**: `check_warm_boot()` (lines 50-59)

```bash
SYSTEM_WARM_START=`$SONIC_DB_CLI STATE_DB hget "WARM_RESTART_ENABLE_TABLE|system" enable`
SERVICE_WARM_START=`$SONIC_DB_CLI STATE_DB hget "WARM_RESTART_ENABLE_TABLE|${SERVICE}" enable`
if [[ x"$SYSTEM_WARM_START" == x"true" ]] || [[ x"$SERVICE_WARM_START" == x"true" ]]; then
    WARM_BOOT="true"
fi
```

**Result**: SWSS enters warm-boot mode and preserves state

### 3. NH-4010 Platform-Specific: Kexec vs Power Cycle

**File**: `platform/broadcom/sonic-platform-modules-nexthop/nh-4010/utils/system_powercycle`

**Key Code**:

```python
#!/usr/bin/env python3
import sys

# Check if this is a kexec reboot (warm reboot)
if len(sys.argv) > 1 and sys.argv[1] == "kexec":
    # Don't powercycle on kexec/warm reboot
    sys.exit(0)

# For cold reboot, write to FPGA power cycle registers
# ... (power cycle code writes 0xdeadbeef to FPGA)
```

**What this means**:
- **Warm Reboot**: systemd calls `system_powercycle kexec` → script exits → kexec kernel transition
- **Cold Reboot**: systemd calls `system_powercycle reboot` → writes to FPGA → hardware power cycle

### 4. System Comes Back Up

**File**: `files/image_config/config-setup/config-setup`

```bash
SYSTEM_WARM_START=`sonic-db-cli STATE_DB hget "WARM_RESTART_ENABLE_TABLE|system" enable`
if [[ x"$SYSTEM_WARM_START" == x"true" ]]; then
    WARM_BOOT="true"
fi
```

**Result**: System detects warm-boot mode, services start without flushing databases

### 5. Component Reconciliation

**File**: `files/image_config/warmboot-finalizer/finalize-warmboot.sh`

**Critical L2 Components**:
```bash
declare -A RECONCILE_COMPONENTS=( \
    ["swss"]="orchagent neighsyncd" \
    ["bgp"]="bgp" \
)
```

**For L2 Testing**:
- **orchagent**: Reconciles VLAN, FDB, port, LAG state
- **neighsyncd**: Reconciles neighbor (ARP) state

**Reconciliation Wait** (up to 5 minutes):
```bash
for i in `seq 60`; do
    list=`check_list ${list}`
    if [[ -z "${list}" ]]; then
        break
    fi
    sleep 5
done
```

### 6. Warm-Boot Finalization

```bash
function finalize_warm_boot()
{
    debug "Finalizing warmboot..."
    sudo config warm_restart disable  # Clears WARM_RESTART_ENABLE_TABLE|system
}
```

---

## NH-4010 Platform-Specific Files

### ✅ Files That Exist:

1. **`device/nexthop/x86_64-nexthop_4010-r0/platform.json`**
   - Platform configuration (ports, thermals, PSUs)

2. **`device/nexthop/x86_64-nexthop_4010-r0/platform_asic`**
   - Contains: `broadcom`

3. **`platform/broadcom/sonic-platform-modules-nexthop/nh-4010/utils/system_powercycle`**
   - **Critical for warm-reboot**: Skips power cycle when "kexec" argument is passed

4. **`platform/broadcom/sonic-platform-modules-nexthop/nh-4010/utils/asic_init.sh`**
   - ASIC initialization script

### ❌ Files That DO NOT Exist:

1. **`warm-reboot_plugin`** - NH-4010 does not have platform-specific warm-reboot customizations
2. **`fast-reboot_plugin`** - NH-4010 does not have platform-specific fast-reboot customizations

---

## Summary: NH-4010 Warm-Reboot Flow

1. ✅ User runs `warm-reboot -v`
2. ✅ Generic SONiC warm-reboot script sets `WARM_RESTART_ENABLE_TABLE|system` = "true"
3. ❌ **NO platform-specific plugin is called** (NH-4010 doesn't have one)
4. ✅ Kexec-based kernel transition initiated
5. ✅ `system_powercycle` detects "kexec" argument and **skips power cycle**
6. ✅ System comes up, detects warm-boot mode
7. ✅ SWSS and other services start in warm-boot mode (preserve state)
8. ✅ Components reconcile (orchagent, neighsyncd, etc.)
9. ✅ Finalizer waits for reconciliation (up to 5 minutes)
10. ✅ `config warm_restart disable` clears warm-boot flags
11. ✅ System returns to normal operation

**Key Difference from Cold Reboot:**
- **Cold Reboot**: `system_powercycle` writes `0xdeadbeef` to FPGA registers → hardware power cycle
- **Warm Reboot**: `system_powercycle` detects "kexec" → exits without power cycle → kexec kernel transition

---

## Diagram

See the Mermaid diagram "NH-4010 Warm-Reboot Execution Flow" for a visual representation of this flow.


