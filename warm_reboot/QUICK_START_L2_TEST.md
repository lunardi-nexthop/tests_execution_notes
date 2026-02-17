# Quick Start: L2 Warm Reboot Test
## 2 Ports in VLAN - Zero Traffic Loss

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Check Your System (30 seconds)
```bash
# On DUT
show warm_restart state | grep -E "vlanmgrd|fdbsyncd|portsyncd|orchagent|syncd"
```

**Expected**:
- ✅ vlanmgrd: enabled (no "disabled")
- ❌ fdbsyncd: **disabled** ← **MUST FIX**
- ✅ portsyncd: enabled
- ✅ orchagent: enabled
- ✅ syncd: enabled

### Step 2: Enable FDB Warm Restart (30 seconds)
```bash
# CRITICAL: Enable fdbsyncd
config warm_restart enable fdbsyncd

# RECOMMENDED: Enable intfmgrd
config warm_restart enable intfmgrd

# Verify
show warm_restart state | grep -E "fdbsyncd|intfmgrd"
# Should NOT show "disabled"
```

### Step 3: Run the Test (2-5 minutes)
```bash
# Option A: Automated test (recommended)
cd /home/lunardi/workspace/private-sonic-mgmt/tests
./run_tests.sh -d <dut_name> -n <testbed_name> -u -c arp/test_wr_arp.py

# Option B: Manual test
# 1. Setup VLAN with 2 ports
config vlan add 100
config vlan member add 100 Ethernet0 -u
config vlan member add 100 Ethernet4 -u

# 2. Start traffic between ports

# 3. Execute warm reboot
warm-reboot

# 4. Verify after reboot
show vlan brief
show mac
show warm_restart state
```

---

## ✅ Success Criteria

- ✅ Packet loss < 1%
- ✅ VLAN config preserved
- ✅ MAC addresses preserved (>95%)
- ✅ vlanmgrd state = "reconciled"
- ✅ fdbsyncd state = "reconciled"

---

## 📚 Detailed Documentation

1. **WARM_RESTART_PREFLIGHT_CHECKLIST.md** - Component explanations
2. **SIMPLE_L2_WARM_REBOOT_TEST_GUIDE.md** - Full test procedure
3. **TEST_CASES_TABLE.md** - All 23 test cases

---

## 🚨 Common Issues

### Issue: FDB entries lost after reboot
**Cause**: fdbsyncd warm restart was disabled  
**Fix**: `config warm_restart enable fdbsyncd`

### Issue: VLAN config lost
**Cause**: vlanmgrd warm restart was disabled  
**Fix**: Should already be enabled on your system

### Issue: High packet loss
**Cause**: Multiple components not enabled for warm restart  
**Fix**: See WARM_RESTART_PREFLIGHT_CHECKLIST.md

---

**Version**: 1.0  
**Created**: 2026-02-05
