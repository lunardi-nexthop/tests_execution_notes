# 🚀 START HERE - Warm Reboot Layer 2 Test Plan

## Welcome!

This directory contains a comprehensive test plan for validating Layer 2 functionality during SONiC warm-reboot/warm-boot operations.

---

## 📚 Documentation Files (Read in Order)

### 1️⃣ **INDEX.md** ← Read First
Quick navigation guide showing all files and their purposes.

### 2️⃣ **WARM_REBOOT_LAYER2_TESTING_README.md** ← Main Entry Point
- Overview of the entire test plan
- Quick start guide
- Success criteria
- Troubleshooting tips

### 3️⃣ **warm_reboot_layer2_test_summary.md** ← Quick Reference
- Test tree structure
- Priority matrix (P0/P1/P2)
- Execution time estimates
- Quick commands

### 4️⃣ **warm_reboot_layer2_test_plan.md** ← Detailed Test Procedures
- All 20 test cases with step-by-step procedures
- Pre-conditions and expected results
- Validation commands
- Automation recommendations

---

## 🎯 What's Covered?

### Layer 2 Components (6 total)
- ✅ **vlanmgrd** - VLAN management
- ✅ **fdbsyncd** - FDB synchronization
- ✅ **teamsyncd** - LAG/PortChannel sync
- ✅ **teammgrd** - LAG/PortChannel management
- ✅ **portsyncd** - Port synchronization
- ✅ **intfmgrd** - Interface management

### Test Categories (20 tests total)
1. VLAN Tests (3)
2. FDB Tests (3)
3. LAG/PortChannel Tests (4)
4. Port Synchronization Tests (2)
5. Interface Management Tests (1)
6. Integration Tests (3)
7. Negative Tests (4)
8. Reconciliation Tests (3)

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Enable warm restart
config warm_restart enable system
config warm_restart enable swss
config warm_restart enable teamd

# 2. Verify it's enabled
redis-cli -n 6 keys "WARM_RESTART_TABLE|*"

# 3. Setup test environment (example)
config vlan add 100
config vlan member add 100 Ethernet0 -u

# 4. Execute warm reboot
warm-reboot

# 5. Monitor reconciliation (in another terminal)
watch -n 1 'redis-cli -n 6 keys "WARM_RESTART_TABLE|*" | xargs -I {} redis-cli -n 6 hget {} state'

# 6. Verify after reboot
show vlan brief
show interfaces portchannel
show mac
```

---

## ✅ Success Criteria

- ✓ Zero configuration loss
- ✓ < 1% packet loss during warm reboot
- ✓ < 5 minutes reconciliation time
- ✓ > 95% FDB entries preserved
- ✓ No LACP re-negotiation

---

## ⏱️ Time Estimates

- **Quick smoke test**: 30 minutes
- **Basic tests**: 2 hours
- **Full test suite**: 6 hours (sequential) or 3-4 hours (parallel)

---

## 🔗 Next Steps

1. **New to warm reboot testing?**
   → Start with `WARM_REBOOT_LAYER2_TESTING_README.md`

2. **Need quick reference?**
   → Check `warm_reboot_layer2_test_summary.md`

3. **Ready to execute tests?**
   → Use `warm_reboot_layer2_test_plan.md`

4. **Looking for specific info?**
   → See `INDEX.md` for navigation

---

## 📞 Support

For questions or issues:
- Review the troubleshooting section in the main test plan
- Check component logs: `sudo tail -f /var/log/syslog | grep <component>`
- Verify database state: `redis-cli -n 6 hgetall "WARM_RESTART_TABLE|<component>"`

---

**Happy Testing! 🧪**

*Version 1.0 | Created: 2026-02-04 | Status: Ready for Review*
