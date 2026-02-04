# Warm Reboot Layer 2 Testing Documentation

## 📋 Overview

This documentation package provides a comprehensive test plan for validating Layer 2 functionality during SONiC warm-reboot/warm-boot operations. The test plan focuses on ensuring that Layer 2 services (VLANs, FDB, LAG/PortChannels) maintain state and recover properly during warm restart.

## 📁 Documentation Files

### 1. **warm_reboot_layer2_test_plan.md** (Main Document)
The comprehensive test plan containing:
- Detailed test procedures for all 20 test cases
- Pre-conditions and expected results for each test
- Validation commands and success criteria
- Test automation recommendations
- Troubleshooting guide and references

**Use this for**: Detailed test execution and implementation

### 2. **warm_reboot_layer2_test_summary.md** (Quick Reference)
A condensed summary including:
- Test categories overview with tree structure
- Quick start commands
- Test priority matrix
- Estimated execution times
- Key validation points

**Use this for**: Quick reference and test planning

## 🎯 Scope

### Components Covered
Based on WARM_RESTART_TABLE entries (excluding vxlanmgrd as "not priority"):

| Component | Purpose | Test Count |
|-----------|---------|------------|
| **vlanmgrd** | VLAN management | 3 tests |
| **fdbsyncd** | FDB synchronization | 3 tests |
| **teamsyncd** | LAG/PortChannel sync | 4 tests |
| **teammgrd** | LAG/PortChannel management | 4 tests |
| **portsyncd** | Port synchronization | 2 tests |
| **intfmgrd** | Interface management | 1 test |

### Test Categories (20 Total Tests)

1. **VLAN Tests** (3 tests) - Configuration, state, and tagging mode persistence
2. **FDB Tests** (3 tests) - MAC learning, static entries, and aging behavior
3. **LAG/PortChannel Tests** (4 tests) - Configuration, LACP, member links, min-links
4. **Port Tests** (2 tests) - Port state and configuration preservation
5. **Interface Tests** (1 test) - Interface configuration persistence
6. **Integration Tests** (3 tests) - Multi-component scenarios and data plane validation
7. **Negative Tests** (4 tests) - Failure scenarios and edge cases
8. **Verification Tests** (3 tests) - Reconciliation tracking and database consistency

## 🚀 Quick Start

### Step 1: Enable Warm Restart
```bash
config warm_restart enable system
config warm_restart enable swss
config warm_restart enable teamd
```

### Step 2: Verify Configuration
```bash
redis-cli -n 6 keys "WARM_RESTART_TABLE|*"
redis-cli -n 6 hgetall "WARM_RESTART_ENABLE_TABLE|system"
```

### Step 3: Setup Test Environment
```bash
# Create test VLANs
config vlan add 100
config vlan add 200
config vlan member add 100 Ethernet0 -u

# Create test PortChannels
config portchannel add PortChannel0001
config portchannel member add PortChannel0001 Ethernet8
```

### Step 4: Execute Warm Reboot
```bash
warm-reboot
```

### Step 5: Monitor Reconciliation
```bash
# Watch component states
watch -n 1 'redis-cli -n 6 keys "WARM_RESTART_TABLE|*" | xargs -I {} redis-cli -n 6 hget {} state'
```

### Step 6: Verify Results
```bash
show vlan brief
show interfaces portchannel
show mac
```

## 📊 Success Criteria

### Critical Metrics
- ✅ **Zero Configuration Loss**: All Layer 2 configurations preserved
- ✅ **Minimal Traffic Loss**: < 1% packet loss during warm reboot
- ✅ **Fast Reconciliation**: All components reconcile within 5 minutes
- ✅ **FDB Preservation**: > 95% of FDB entries preserved
- ✅ **No LACP Re-negotiation**: LACP state maintained

### Component-Specific Targets
| Component | Reconciliation Time | State |
|-----------|-------------------|-------|
| vlanmgrd | < 30 seconds | reconciled |
| fdbsyncd | < 60 seconds | reconciled |
| teamsyncd | < 45 seconds | reconciled |
| teammgrd | < 45 seconds | reconciled |
| portsyncd | < 30 seconds | reconciled |
| intfmgrd | < 30 seconds | reconciled |

## 🔍 Key Validation Points

### Database Tables to Monitor

**CONFIG_DB (DB 4)** - Configuration persistence
```bash
redis-cli -n 4 keys "VLAN|*"
redis-cli -n 4 keys "VLAN_MEMBER|*"
redis-cli -n 4 keys "PORTCHANNEL|*"
redis-cli -n 4 keys "PORTCHANNEL_MEMBER|*"
```

**STATE_DB (DB 6)** - Warm restart state
```bash
redis-cli -n 6 keys "WARM_RESTART_TABLE|*"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|vlanmgrd"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|fdbsyncd"
```

**APPL_DB (DB 0)** - Application state
```bash
redis-cli -n 0 keys "LAG_TABLE*"
redis-cli -n 0 keys "FDB_TABLE*"
```

**ASIC_DB (DB 1)** - Hardware state
```bash
redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_FDB_ENTRY:*"
```

## ⏱️ Estimated Execution Time

- **Basic Tests (Categories 1-5)**: ~2 hours
- **Integration Tests (Category 6)**: ~1.5 hours
- **Negative Tests (Category 7)**: ~2 hours
- **Verification Tests (Category 8)**: ~30 minutes
- **Total Sequential**: ~6 hours
- **With Parallelization**: ~3-4 hours

## 🧪 Test Automation

### Recommended Framework
```python
import pytest
from swsscommon import swsscommon

class TestWarmRebootLayer2:
    def test_vlan_persistence(self, dvs):
        # Test implementation
        pass
```

### Tools Required
- **pytest**: Test framework
- **swsscommon**: SONiC database interaction
- **scapy**: Traffic generation
- **redis-py**: Database access

## 📈 Test Priority

| Priority | Description | Test Count |
|----------|-------------|------------|
| **P0** | Must pass for release | 8 tests |
| **P1** | Should pass for release | 9 tests |
| **P2** | Nice to have | 3 tests |

## 🔧 Troubleshooting

### Component Not Reconciling
1. Check logs: `sudo tail -f /var/log/syslog | grep <component>`
2. Verify restore_count: `redis-cli -n 6 hget "WARM_RESTART_TABLE|<component>" restore_count`
3. Check component status: `docker ps | grep <component>`

### FDB Entries Lost
1. Check fdbsyncd logs
2. Verify ASIC_DB state
3. Check MAC aging configuration

### LACP Re-negotiation
1. Check teamd logs
2. Verify LACP PDU exchange
3. Check teamsyncd/teammgrd reconciliation

## 📚 References

- **SONiC Warm Reboot Design**: [SONiC GitHub Wiki](https://github.com/sonic-net/SONiC/wiki)
- **WARM_RESTART_TABLE Schema**: `src/sonic-yang-models/yang-models/sonic-warm-restart.yang`
- **Reconciliation Script**: `files/image_config/warmboot-finalizer/finalize-warmboot.sh`

## 📝 Document Information

- **Version**: 1.0
- **Last Updated**: 2026-02-04
- **Status**: Ready for Review
- **Target**: Layer 2 Warm Reboot Testing

---

**For detailed test procedures**: See `warm_reboot_layer2_test_plan.md`  
**For quick reference**: See `warm_reboot_layer2_test_summary.md`

