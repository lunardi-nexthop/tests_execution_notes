# Warm Reboot Layer 2 Test Plan - Index

## 📂 File Structure

```
warm_reboot/
├── INDEX.md (this file)
├── WARM_REBOOT_LAYER2_TESTING_README.md
├── warm_reboot_layer2_test_plan.md
└── warm_reboot_layer2_test_summary.md
```

## 📖 Reading Guide

### Start Here: README
**File**: `WARM_REBOOT_LAYER2_TESTING_README.md`

This is your main entry point. It provides:
- Overview of the entire test plan
- Quick start guide
- Success criteria
- Troubleshooting tips

**Read this first** to understand the scope and get started quickly.

---

### Detailed Test Plan
**File**: `warm_reboot_layer2_test_plan.md` (789 lines)

The comprehensive test plan with all 20 test cases organized into 8 categories:

#### Test Categories:
1. **VLAN Tests (vlanmgrd)** - 3 tests
2. **FDB Tests (fdbsyncd)** - 3 tests
3. **LAG/PortChannel Tests (teamsyncd, teammgrd)** - 4 tests
4. **Port Synchronization Tests (portsyncd)** - 2 tests
5. **Interface Management Tests (intfmgrd)** - 1 test
6. **Integration Tests (Multi-Component)** - 3 tests
7. **Negative Tests** - 4 tests
8. **Reconciliation and State Verification Tests** - 3 tests

**Use this for**: Detailed test execution, step-by-step procedures, validation commands

---

### Quick Reference Summary
**File**: `warm_reboot_layer2_test_summary.md`

A condensed version with:
- Test tree structure visualization
- Component matrix
- Test priority matrix (P0/P1/P2)
- Quick start commands
- Execution time estimates

**Use this for**: Quick lookups, test planning, time estimation

---

## 🎯 Components Tested

Based on WARM_RESTART_TABLE entries (excluding vxlanmgrd):

| Component | Purpose | Tests |
|-----------|---------|-------|
| vlanmgrd | VLAN management | 3 |
| fdbsyncd | FDB synchronization | 3 |
| teamsyncd | LAG/PortChannel sync | 4 |
| teammgrd | LAG/PortChannel management | 4 |
| portsyncd | Port synchronization | 2 |
| intfmgrd | Interface management | 1 |

**Total**: 20 test cases

---

## 🚀 Quick Start

1. **Read the README** (`WARM_REBOOT_LAYER2_TESTING_README.md`)
2. **Review the Summary** (`warm_reboot_layer2_test_summary.md`) for test overview
3. **Execute Tests** using the detailed plan (`warm_reboot_layer2_test_plan.md`)

### Essential Commands

```bash
# Enable warm restart
config warm_restart enable system
config warm_restart enable swss
config warm_restart enable teamd

# Verify configuration
redis-cli -n 6 keys "WARM_RESTART_TABLE|*"

# Execute warm reboot
warm-reboot

# Monitor reconciliation
watch -n 1 'redis-cli -n 6 keys "WARM_RESTART_TABLE|*" | xargs -I {} redis-cli -n 6 hget {} state'
```

---

## 📊 Test Execution Timeline

- **Basic Tests (1-5)**: ~2 hours
- **Integration Tests (6)**: ~1.5 hours
- **Negative Tests (7)**: ~2 hours
- **Verification Tests (8)**: ~30 minutes
- **Total Sequential**: ~6 hours
- **With Parallelization**: ~3-4 hours

---

## ✅ Success Criteria Summary

- Zero configuration loss
- < 1% packet loss during warm reboot
- < 5 minutes reconciliation time
- > 95% FDB entries preserved
- No LACP re-negotiation

---

## 📝 Document Versions

- **Version**: 1.0
- **Created**: 2026-02-04
- **Status**: Ready for Review
- **Target**: Layer 2 Warm Reboot Testing

---

## 🔗 Navigation

- **[README](WARM_REBOOT_LAYER2_TESTING_README.md)** - Start here
- **[Test Plan](warm_reboot_layer2_test_plan.md)** - Detailed procedures
- **[Summary](warm_reboot_layer2_test_summary.md)** - Quick reference

---

**Happy Testing! 🧪**
