# Simple L2 Warm Reboot Test Guide
## Test Scenario: 2 Ports in VLAN - Maintain L2 Traffic Without Loss

---

## 📋 Test Objective

**Goal**: Verify that when 2 ports belong to a VLAN, L2 traffic continues without loss after warm-reboot when the system comes back up.

This corresponds to **TC-WARM-001** (VLAN Configuration Persistence) and **TC-WARM-052** (Layer 2 Forwarding During Warm Reboot) from the test plan.

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
- Initiates warm-reboot
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

#### Step 1: Pre-Test Setup
```bash
# SSH to DUT
ssh admin@<dut_ip>

# Enable warm restart
config warm_restart enable system
config warm_restart enable swss
config warm_restart enable teamd

# Verify warm restart is enabled
redis-cli -n 6 hget "WARM_RESTART_ENABLE_TABLE|system" enable
# Should return: true

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

#### Step 2: Start Traffic Generator
```bash
# On PTF host or traffic generator
# Generate continuous L2 traffic between the 2 ports
# Example using scapy or iperf with L2 mode

# Simple ping test (from one port to another via VLAN)
# This should be done from connected devices or PTF
```

#### Step 3: Monitor Traffic (Before Reboot)
```bash
# On DUT - monitor interface counters
show interfaces counters
watch -n 1 'show interfaces counters | grep -E "Ethernet0|Ethernet4"'

# Check FDB entries
show mac
```

#### Step 4: Initiate Warm Reboot
```bash
# On DUT
warm-reboot

# The system will reboot while maintaining data plane
```

#### Step 5: Monitor During Reboot (From Another Terminal)
```bash
# Monitor reconciliation status
watch -n 1 'redis-cli -n 6 keys "WARM_RESTART_TABLE|*" | xargs -I {} redis-cli -n 6 hget {} state'

# Expected states: initialized → restored → reconciled
```

#### Step 6: Post-Reboot Verification
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

# 3. Check FDB entries preserved
show mac
# Compare with pre-reboot MAC table

# 4. Verify traffic continuity
show interfaces counters
# Check for packet loss

# 5. Verify warm reboot cause
show reboot-cause
# Should show: warm-reboot
```

---

## 📊 Success Criteria

### Must Pass (P0):
- ✅ VLAN 100 exists after reboot
- ✅ Both ports (Ethernet0, Ethernet4) are members of VLAN 100
- ✅ Port tagging mode preserved (untagged)
- ✅ vlanmgrd state = "reconciled"
- ✅ **Packet loss < 1%** during warm reboot
- ✅ Traffic resumes immediately after reboot
- ✅ FDB entries preserved (>95%)

### Should Pass (P1):
- ✅ Reconciliation time < 5 minutes
- ✅ No errors in syslog related to VLAN
- ✅ Interface states preserved

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
- [ ] VLAN configuration is clean
- [ ] Traffic generator is ready
- [ ] Warm restart is enabled

### During Test:
- [ ] Traffic is flowing before reboot
- [ ] Warm-reboot command executed
- [ ] Monitor reconciliation states
- [ ] Capture packet loss metrics

### Post-Test:
- [ ] VLAN configuration verified
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
```

---

## 📚 Related Test Cases

From the test plan:
- **TC-WARM-001**: VLAN Configuration Persistence
- **TC-WARM-002**: VLAN Interface State Preservation
- **TC-WARM-003**: VLAN Member Port Tagging Mode
- **TC-WARM-010**: MAC Address Learning Persistence
- **TC-WARM-052**: Layer 2 Forwarding During Warm Reboot

---

## 🔗 References

- Test Plan: `~/workspace/tests_execution_notes/warm_reboot/TEST_CASES_TABLE.md`
- sonic-mgmt repo: `/home/lunardi/workspace/private-sonic-mgmt`
- Reboot module: `tests/common/reboot.py`
- VLAN tests: `tests/vlan/test_vlan.py`
- Warm reboot ARP test: `tests/arp/test_wr_arp.py`

---

**Version**: 1.0  
**Created**: 2026-02-05  
**Status**: Ready for Execution
