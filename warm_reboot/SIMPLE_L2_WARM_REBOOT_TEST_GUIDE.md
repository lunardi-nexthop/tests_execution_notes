# Simple L2 Warm Reboot Test Guide
## Test Scenario: 2 Ports in VLAN - Maintain L2 Traffic Without Loss

---

## 📋 Test Objective

**Goal**: Verify that when 2 ports belong to a VLAN, L2 traffic continues without loss after warm-reboot when the system comes back up.

This corresponds to **TC-WARM-001** (VLAN Configuration Persistence) and **TC-WARM-052** (Layer 2 Forwarding During Warm Reboot) from the test plan.

---

## ⚠️ IMPORTANT: Pre-Flight Check Required

**Before running this test**, you MUST verify and enable required warm restart components.

👉 **See**: `WARM_RESTART_PREFLIGHT_CHECKLIST.md` for detailed instructions.

**Quick Check**:
```bash
# On DUT - verify warm restart state
show warm_restart state

# CRITICAL: Ensure fdbsyncd is NOT disabled
# If it shows "disabled", run:
config warm_restart enable fdbsyncd
```

---

## 🔍 Assessment Based on sonic-mgmt Repository

### Key Files Found:

1. **Warm Reboot Infrastructure**:
   - `tests/common/reboot.py` - Core reboot functions
   - `tests/platform_tests/test_advanced_reboot.py` - Advanced reboot tests including warm-reboot
   - `tests/arp/test_wr_arp.py` - Warm reboot ARP test (VLAN-related)

2. **VLAN Test Infrastructure**:
   - `tests/vlan/test_vlan.py` - VLAN forwarding tests
   - `tests/vlan/test_vlan_ping.py` - VLAN ping tests
   - `tests/common/helpers/sad_path.py` - VLAN member down scenarios during warm-reboot

3. **Reboot Configuration** (from `tests/common/reboot.py`):
```python
REBOOT_TYPE_WARM: {
    "command": "warm-reboot",
    "timeout": 300,
    "wait": 90,
    "warmboot_finalizer_timeout": 180,
    "cause": "warm-reboot",
    "test_reboot_cause_only": False
}
```

4. **How Warm Reboot Tests Actually Work**:
   - Tests use `warm-reboot` command directly (NOT `config warm_restart enable system`)
   - The `warm-reboot` script handles enabling warm restart internally
   - Tests check `WARM_RESTART_ENABLE_TABLE|system` in STATE_DB to verify warm restart state

---

## 🚀 Commands to Run Simple Warm Reboot Test

### Option 1: Using Existing Test Framework (Recommended)

#### A. Run Warm Reboot ARP Test (Tests VLAN + Warm Reboot)
```bash
cd /home/lunardi/workspace/private-sonic-mgmt/tests

# Run warm reboot ARP test - tests VLAN member ports during warm-reboot
./run_tests.sh -d <dut_name> -n <testbed_name> -u -c arp/test_wr_arp.py

# Or using pytest directly:
pytest arp/test_wr_arp.py \
    --inventory ../ansible/<inventory_file> \
    --host-pattern <dut_hostname> \
    --testbed_file <testbed_yaml> \
    --log-cli-level info
```

**What this test does**:
- Continuously sends ARP requests to VLAN member ports
- Initiates warm-reboot using `warm-reboot` command
- Expects to receive ARP replies throughout
- Fails if no replies for >25 seconds on any VLAN member port

#### B. Run Advanced Warm Reboot Test
```bash
# Run warm reboot test with traffic validation
./run_tests.sh -d <dut_name> -n <testbed_name> -u \
    -c platform_tests/test_advanced_reboot.py::test_warm_reboot
```

#### C. Run VLAN Tests After Warm Reboot
```bash
# First do warm reboot, then run VLAN tests
./run_tests.sh -d <dut_name> -n <testbed_name> -u \
    -c vlan/test_vlan.py
```

---

### Option 2: Manual Test Procedure

#### Step 1: Pre-Flight Check - Verify Warm Restart State
```bash
# SSH to DUT
ssh admin@<dut_ip>

# Check current warm restart state
show warm_restart state

# Expected output should show these components ENABLED (not "disabled"):
# - vlanmgrd     ✅ (Critical for VLAN config persistence)
# - fdbsyncd     ✅ (Critical for MAC address learning)
# - portsyncd    ✅ (Important for port state)
# - orchagent    ✅ (Critical for orchestration)
# - syncd        ✅ (Critical for ASIC sync)
```

#### Step 2: Enable Required Components (If Disabled)
```bash
# CRITICAL: Enable fdbsyncd if it shows "disabled"
# (Required for MAC address table persistence during warm-reboot)
config warm_restart enable fdbsyncd

# RECOMMENDED: Enable intfmgrd if it shows "disabled"
# (Helps preserve interface configuration)
config warm_restart enable intfmgrd

# Verify changes took effect
show warm_restart state

# Should now show:
# fdbsyncd     0  (no "disabled" - means enabled)
# intfmgrd     0  (no "disabled" - means enabled)
```

**Note**: Based on analysis of sonic-mgmt test code:
- The `warm-reboot` command handles system-level warm restart internally
- You do NOT need to run `config warm_restart enable system`
- Component-level warm restart (fdbsyncd, intfmgrd, etc.) must be enabled separately

#### Step 3: VLAN Setup
```bash
# Create test VLAN (if not exists)
config vlan add 100

# Add 2 ports to VLAN as untagged members
config vlan member add 100 Ethernet0 -u
config vlan member add 100 Ethernet4 -u

# Verify VLAN configuration
show vlan brief
redis-cli -n 4 keys "VLAN|*"
redis-cli -n 4 keys "VLAN_MEMBER|*"
```

#### Step 4: Start Traffic Generator
```bash
# On PTF host or traffic generator
# Generate continuous L2 traffic between the 2 ports
# Example using scapy or iperf with L2 mode

# Simple ping test (from one port to another via VLAN)
# This should be done from connected devices or PTF
```

#### Step 5: Monitor Traffic (Before Reboot)
```bash
# On DUT - monitor interface counters
show interfaces counters
watch -n 1 'show interfaces counters | grep -E "Ethernet0|Ethernet4"'

# Check FDB entries
show mac
```

#### Step 6: Initiate Warm Reboot
```bash
# On DUT
warm-reboot

# The system will reboot while maintaining data plane
# The warm-reboot script handles enabling system-level warm restart
```

#### Step 7: Monitor During Reboot (From Another Terminal)
```bash
# Monitor reconciliation status
watch -n 1 'redis-cli -n 6 keys "WARM_RESTART_TABLE|*" | xargs -I {} redis-cli -n 6 hget {} state'

# Expected states: initialized → restored → reconciled
```

#### Step 8: Post-Reboot Verification
```bash
# After system comes back up

# 1. Verify VLAN configuration preserved
show vlan brief
redis-cli -n 4 hgetall "VLAN|Vlan100"
redis-cli -n 4 hgetall "VLAN_MEMBER|Vlan100|Ethernet0"
redis-cli -n 4 hgetall "VLAN_MEMBER|Vlan100|Ethernet4"

# 2. Verify vlanmgrd reconciled
redis-cli -n 6 hget "WARM_RESTART_TABLE|vlanmgrd" state
# Should return: reconciled

# 3. Verify fdbsyncd reconciled (CRITICAL for L2)
redis-cli -n 6 hget "WARM_RESTART_TABLE|fdbsyncd" state
# Should return: reconciled

# 4. Check FDB entries preserved
show mac
# Compare with pre-reboot MAC table

# 5. Verify traffic continuity
show interfaces counters
# Check for packet loss

# 6. Verify warm reboot cause
show reboot-cause
# Should show: warm-reboot

# 7. Check all component reconciliation
show warm_restart state
# All enabled components should show restore_count > 0
```

---

## 📊 Success Criteria

### Must Pass (P0):
- ✅ VLAN 100 exists after reboot
- ✅ Both ports (Ethernet0, Ethernet4) are members of VLAN 100
- ✅ Port tagging mode preserved (untagged)
- ✅ vlanmgrd state = "reconciled"
- ✅ fdbsyncd state = "reconciled"
- ✅ **Packet loss < 1%** during warm reboot
- ✅ Traffic resumes immediately after reboot
- ✅ FDB entries preserved (>95%)

### Should Pass (P1):
- ✅ Reconciliation time < 5 minutes
- ✅ No errors in syslog related to VLAN or FDB
- ✅ Interface states preserved
- ✅ All L2 components show restore_count incremented

---

## 🔧 Detailed Test Commands

### Using pytest with Custom Parameters
```bash
cd /home/lunardi/workspace/private-sonic-mgmt/tests

# Run with specific testbed
pytest arp/test_wr_arp.py::test_wr_arp \
    --inventory ../ansible/veos_vtb \
    --host-pattern <dut_hostname> \
    --testbed <testbed_name> \
    --testbed_file ../ansible/testbed.yaml \
    --log-cli-level debug \
    --disable_loganalyzer \
    --skip_sanity

# Run with traffic duration
pytest arp/test_wr_arp.py::test_wr_arp_advance \
    --inventory ../ansible/veos_vtb \
    --host-pattern <dut_hostname> \
    --testbed <testbed_name> \
    --testbed_file ../ansible/testbed.yaml \
    --test_duration 300 \
    --log-cli-level info
```

### Using run_tests.sh Script
```bash
cd /home/lunardi/workspace/private-sonic-mgmt/tests

# Basic warm reboot test
./run_tests.sh \
    -d <dut_name> \
    -n <testbed_name> \
    -u \
    -c arp/test_wr_arp.py

# With specific test case filter
./run_tests.sh \
    -d <dut_name> \
    -n <testbed_name> \
    -u \
    -c arp/test_wr_arp.py \
    -C "test_wr_arp"

# Run multiple related tests
./run_tests.sh \
    -d <dut_name> \
    -n <testbed_name> \
    -u \
    -c "arp/test_wr_arp.py vlan/test_vlan.py"
```

---

## 📝 Test Execution Checklist

### Pre-Test:
- [ ] Testbed is accessible
- [ ] DUT is in healthy state
- [ ] **Warm restart state verified** (see WARM_RESTART_PREFLIGHT_CHECKLIST.md)
- [ ] **fdbsyncd warm restart enabled** (CRITICAL)
- [ ] VLAN configuration is clean
- [ ] Traffic generator is ready

### During Test:
- [ ] Traffic is flowing before reboot
- [ ] Warm-reboot command executed
- [ ] Monitor reconciliation states
- [ ] Capture packet loss metrics

### Post-Test:
- [ ] VLAN configuration verified
- [ ] FDB entries verified
- [ ] Traffic resumed
- [ ] Packet loss calculated
- [ ] Logs collected
- [ ] Test results documented

---

## 🛠️ Troubleshooting

### If VLAN Configuration Lost:
```bash
# Check CONFIG_DB
redis-cli -n 4 keys "VLAN*"

# Check vlanmgrd logs
docker exec swss tail -100 /var/log/syslog | grep vlanmgrd

# Check reconciliation state
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|vlanmgrd"

# Check if vlanmgrd warm restart is enabled
show warm_restart state | grep vlanmgrd
```

### If FDB Entries Lost (MAC Addresses):
```bash
# Check fdbsyncd state
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|fdbsyncd"

# Check if fdbsyncd warm restart is enabled
show warm_restart state | grep fdbsyncd
# If it shows "disabled", this is the problem!

# Enable it for next test
config warm_restart enable fdbsyncd

# Check FDB in ASIC_DB
redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_FDB_ENTRY*"
```

### If Traffic Loss Exceeds Threshold:
```bash
# Check interface status
show interfaces status

# Check FDB
show mac

# Check for errors
show logging | grep -i error

# Verify warm restart was actually performed
show reboot-cause

# Check which components failed reconciliation
show warm_restart state
```

### If Reconciliation Stuck:
```bash
# Check all component states
redis-cli -n 6 keys "WARM_RESTART_TABLE|*" | \
    xargs -I {} sh -c 'echo {} && redis-cli -n 6 hgetall {}'

# Check warmboot finalizer
systemctl status warmboot-finalizer

# Check logs
journalctl -u warmboot-finalizer -n 100

# Check specific component logs
docker exec swss tail -200 /var/log/syslog | grep -E "vlanmgrd|fdbsyncd|orchagent"
```

---

## 📚 Related Test Cases

From the test plan:
- **TC-WARM-001**: VLAN Configuration Persistence
- **TC-WARM-002**: VLAN Interface State Preservation
- **TC-WARM-003**: VLAN Member Port Tagging Mode
- **TC-WARM-010**: MAC Address Learning Persistence (requires fdbsyncd)
- **TC-WARM-052**: Layer 2 Forwarding During Warm Reboot

---

## 🔗 References

- **Pre-Flight Checklist**: `WARM_RESTART_PREFLIGHT_CHECKLIST.md` ⭐ **START HERE**
- Test Plan: `TEST_CASES_TABLE.md`
- Detailed Test Plan: `warm_reboot_layer2_test_plan.md`
- sonic-mgmt repo: `/home/lunardi/workspace/private-sonic-mgmt`
- Reboot module: `tests/common/reboot.py`
- VLAN tests: `tests/vlan/test_vlan.py`
- Warm reboot ARP test: `tests/arp/test_wr_arp.py`
- PTF warm reboot test: `ansible/roles/test/files/ptftests/py3/wr_arp.py`

---

## 📌 Key Learnings from Code Analysis

1. **The `warm-reboot` command is self-contained**:
   - You don't need to run `config warm_restart enable system`
   - The `warm-reboot` script handles system-level warm restart

2. **Component-level warm restart must be enabled separately**:
   - `config warm_restart enable fdbsyncd` - **CRITICAL for L2**
   - `config warm_restart enable intfmgrd` - Recommended
   - These are NOT enabled by `warm-reboot` command

3. **Test verification**:
   - Tests check `WARM_RESTART_ENABLE_TABLE|system` in STATE_DB
   - Tests verify component reconciliation states
   - Tests measure actual packet loss during reboot

---

**Version**: 2.0  
**Created**: 2026-02-05  
**Updated**: 2026-02-05  
**Status**: Ready for Execution  
**Based on**: Actual sonic-mgmt code analysis + system state verification
