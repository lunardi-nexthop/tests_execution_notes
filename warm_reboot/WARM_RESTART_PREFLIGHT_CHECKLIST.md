# Warm Restart Pre-Flight Checklist
## Verify System State Before Running Warm-Reboot Tests

---

## 🎯 Purpose

This checklist ensures your SONiC system is properly configured for warm-reboot testing, specifically for Layer 2 (VLAN) tests.

---

## 📋 Pre-Flight Checklist

### Step 1: Check Current Warm Restart State

```bash
# On DUT
show warm_restart state
```

### Step 2: Analyze Output - Layer 2 Components

Based on your system output, verify these critical components:

| Component | Current State | Required for L2 Test | Action Needed |
|-----------|---------------|---------------------|---------------|
| **vlanmgrd** | ✅ enabled (restore_count: 0) | ✅ **CRITICAL** | None - already enabled |
| **fdbsyncd** | ❌ **disabled** | ✅ **CRITICAL** | **MUST ENABLE** |
| **portsyncd** | ✅ enabled (restore_count: 0) | ✅ Important | None - already enabled |
| **orchagent** | ✅ enabled (restore_count: 0) | ✅ **CRITICAL** | None - already enabled |
| **syncd** | ✅ enabled (restore_count: 0) | ✅ **CRITICAL** | None - already enabled |
| **teamsyncd** | ✅ enabled (restore_count: 0) | ⚠️ If using LAG/PortChannel | None - already enabled |
| **teammgrd** | ✅ enabled (restore_count: 0) | ⚠️ If using LAG/PortChannel | None - already enabled |
| **intfmgrd** | ❌ **disabled** | ⚠️ Recommended | Recommended to enable |
| **neighsyncd** | ✅ enabled (restore_count: 0) | ⚠️ For ARP/ND | None - already enabled |
| **tunnelmgrd** | ✅ enabled (restore_count: 0) | ❌ Not needed for basic L2 | None |
| **bgp** | ❌ disabled | ❌ Not needed for L2 | None - L3 only |
| **vrfmgrd** | ❌ disabled | ❌ Not needed for L2 | None - L3 only |

---

## 🔧 Required Actions

### ✅ Action 1: Enable fdbsyncd (CRITICAL)

**Why**: FDB (Forwarding Database) stores MAC address learning table. Without warm restart enabled, MAC addresses will be lost during reboot, causing traffic disruption.

```bash
# Enable fdbsyncd warm restart
config warm_restart enable fdbsyncd

# Verify
show warm_restart state | grep fdbsyncd
# Should show: fdbsyncd    0  (no "disabled")
```

### ✅ Action 2: Enable intfmgrd (RECOMMENDED)

**Why**: Interface manager preserves interface configuration (IP addresses, admin state, etc.)

```bash
# Enable intfmgrd warm restart
config warm_restart enable intfmgrd

# Verify
show warm_restart state | grep intfmgrd
# Should show: intfmgrd    0  (no "disabled")
```

---

## 📊 Component Explanations

### Critical Components (Must Be Enabled):

1. **vlanmgrd** - VLAN Manager
   - Manages VLAN configuration
   - Preserves VLAN membership during warm-reboot
   - **Status on your system**: ✅ Already enabled

2. **fdbsyncd** - FDB Synchronization Daemon
   - Synchronizes MAC address learning table
   - Preserves learned MAC addresses during warm-reboot
   - **Status on your system**: ❌ **DISABLED - MUST ENABLE**

3. **orchagent** - Orchestration Agent
   - Central orchestration engine in SWSS
   - Coordinates all other components
   - **Status on your system**: ✅ Already enabled

4. **syncd** - Synchronization Daemon
   - Synchronizes state with ASIC (hardware)
   - Critical for data plane continuity
   - **Status on your system**: ✅ Already enabled

5. **portsyncd** - Port Synchronization Daemon
   - Synchronizes port state and configuration
   - Preserves port admin/oper state
   - **Status on your system**: ✅ Already enabled

### Important Components (Should Be Enabled):

6. **intfmgrd** - Interface Manager
   - Manages interface configuration
   - Preserves IP addresses and interface settings
   - **Status on your system**: ❌ **DISABLED - RECOMMENDED TO ENABLE**

7. **teamsyncd** - Team Synchronization Daemon
   - Synchronizes LAG/PortChannel state
   - Only needed if using PortChannels
   - **Status on your system**: ✅ Already enabled

8. **teammgrd** - Team Manager
   - Manages LAG/PortChannel configuration
   - Only needed if using PortChannels
   - **Status on your system**: ✅ Already enabled

### Optional Components (Not Required for Basic L2):

9. **neighsyncd** - Neighbor Synchronization Daemon
   - Synchronizes ARP/ND entries
   - Useful for ARP tests
   - **Status on your system**: ✅ Already enabled

10. **bgp** - BGP Daemon
    - Layer 3 routing protocol
    - Not needed for Layer 2 tests
    - **Status on your system**: ❌ Disabled (OK for L2)

11. **vrfmgrd** - VRF Manager
    - Virtual Routing and Forwarding
    - Not needed for Layer 2 tests
    - **Status on your system**: ❌ Disabled (OK for L2)

---

## ✅ Final Verification

After enabling required components, run:

```bash
# Check all warm restart states
show warm_restart state

# Expected output for L2 test readiness:
# name             restore_count  state
# -------------  ---------------  --------
# vlanmgrd                    0           ✅
# fdbsyncd                    0           ✅ (should NOT show "disabled")
# portsyncd                   0           ✅
# orchagent                   0           ✅
# syncd                       0           ✅
# intfmgrd                    0           ✅ (should NOT show "disabled")
# teamsyncd                   0           ✅
# teammgrd                    0           ✅
```

---

## 🚀 Ready to Test?

Once all critical components show as enabled (no "disabled" status), you're ready to proceed with:

1. **Automated Test**: `./run_tests.sh -d <dut_name> -n <testbed_name> -u -c arp/test_wr_arp.py`
2. **Manual Test**: Follow the procedure in `SIMPLE_L2_WARM_REBOOT_TEST_GUIDE.md`

---

## 🔍 Troubleshooting

### If a component won't enable:

```bash
# Check if the service is running
docker ps | grep swss

# Check service logs
docker exec swss tail -100 /var/log/syslog | grep <component_name>

# Restart SWSS container (last resort)
sudo systemctl restart swss
```

### If warm restart state shows unexpected values:

```bash
# Check STATE_DB directly
redis-cli -n 6 keys "WARM_RESTART_TABLE|*"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|fdbsyncd"

# Check ENABLE table
redis-cli -n 6 keys "WARM_RESTART_ENABLE_TABLE|*"
redis-cli -n 6 hgetall "WARM_RESTART_ENABLE_TABLE|fdbsyncd"
```

---

## 📚 References

- Main Test Plan: `TEST_CASES_TABLE.md`
- Simple L2 Test Guide: `SIMPLE_L2_WARM_REBOOT_TEST_GUIDE.md`
- Detailed Test Plan: `warm_reboot_layer2_test_plan.md`

---

**Version**: 1.0  
**Created**: 2026-02-05  
**Status**: Ready for Use  
**Based on**: Actual system state from `show warm_restart state`
