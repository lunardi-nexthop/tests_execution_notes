# Warm Reboot Layer 2 Test Cases - Tabulated Summary

## Complete Test Case Table

| Test ID | Test Name | Category | Component(s) | Objective | Priority | Complexity | Duration |
|---------|-----------|----------|--------------|-----------|----------|------------|----------|
| **1.1** | VLAN Configuration Persistence | VLAN Tests | vlanmgrd | Verify VLAN configurations are preserved during warm reboot | P0 | Low | 5 min |
| **1.2** | VLAN Interface State Preservation | VLAN Tests | vlanmgrd | Verify VLAN interface admin/oper states are maintained | P1 | Low | 5 min |
| **1.3** | VLAN Member Port Tagging Mode | VLAN Tests | vlanmgrd | Verify VLAN member tagging modes (tagged/untagged) are preserved | P1 | Medium | 10 min |
| **2.1** | MAC Address Learning Persistence | FDB Tests | fdbsyncd | Verify learned MAC addresses are preserved during warm reboot | P0 | Medium | 10 min |
| **2.2** | Static MAC Entries Preservation | FDB Tests | fdbsyncd | Verify statically configured MAC entries are preserved | P1 | Low | 5 min |
| **2.3** | FDB Aging During Warm Reboot | FDB Tests | fdbsyncd | Verify FDB aging behavior during warm reboot | P2 | Medium | 15 min |
| **3.1** | PortChannel Configuration Persistence | LAG Tests | teamsyncd, teammgrd | Verify PortChannel configurations are preserved during warm reboot | P0 | Medium | 10 min |
| **3.2** | LACP State Preservation | LAG Tests | teamsyncd, teammgrd | Verify LACP protocol state is maintained during warm reboot | P0 | High | 15 min |
| **3.3** | PortChannel Member Link Failure During Warm Reboot | LAG Tests | teamsyncd, teammgrd | Verify handling of member link failure during warm reboot | P1 | High | 20 min |
| **3.4** | PortChannel Min-Links Configuration | LAG Tests | teamsyncd, teammgrd | Verify min-links configuration is honored during warm reboot | P2 | Medium | 10 min |
| **4.1** | Port State Preservation | Port Tests | portsyncd | Verify port admin and operational states are preserved | P1 | Low | 5 min |
| **4.2** | Port Configuration Preservation | Port Tests | portsyncd | Verify port configurations (speed, MTU, etc.) are preserved | P1 | Low | 5 min |
| **5.1** | Interface Configuration Persistence | Interface Tests | intfmgrd | Verify interface configurations are preserved during warm reboot | P2 | Low | 5 min |
| **6.1** | VLAN with PortChannel Members | Integration Tests | vlanmgrd, teamsyncd, fdbsyncd | Verify VLANs with PortChannel members work correctly during warm reboot | P0 | High | 20 min |
| **6.2** | Multiple VLANs with Overlapping PortChannel Members | Integration Tests | vlanmgrd, teamsyncd | Verify complex VLAN/PortChannel configurations during warm reboot | P1 | High | 25 min |
| **6.3** | Layer 2 Forwarding During Warm Reboot | Integration Tests | All L2 components | Verify continuous Layer 2 forwarding during warm reboot | P0 | High | 30 min |
| **7.1** | Warm Reboot with Component Failure | Negative Tests | All L2 components | Verify system behavior when a Layer 2 component fails to reconcile | P1 | High | 15 min |
| **7.2** | Configuration Change During Warm Reboot | Negative Tests | All L2 components | Verify handling of configuration changes during warm reboot | P2 | Medium | 10 min |
| **7.3** | Warm Reboot Timeout | Negative Tests | All L2 components | Verify system behavior when warm reboot exceeds timeout | P2 | Medium | 15 min |
| **7.4** | Repeated Warm Reboots | Negative Tests | All L2 components | Verify system stability with multiple consecutive warm reboots | P1 | Medium | 60 min |
| **8.1** | Component Reconciliation State Tracking | Verification Tests | All L2 components | Verify all Layer 2 components transition through correct states | P0 | Medium | 10 min |
| **8.2** | Database Consistency Verification | Verification Tests | All L2 components | Verify database consistency across CONFIG_DB, APPL_DB, ASIC_DB, STATE_DB | P0 | High | 15 min |
| **8.3** | Restore Count Verification | Verification Tests | All L2 components | Verify restore_count is properly maintained for each component | P1 | Low | 5 min |

---

## Test Summary Statistics

| Metric | Count/Value |
|--------|-------------|
| **Total Test Cases** | 23 |
| **P0 (Must Pass)** | 8 |
| **P1 (Should Pass)** | 9 |
| **P2 (Nice to Have)** | 6 |
| **Low Complexity** | 9 |
| **Medium Complexity** | 8 |
| **High Complexity** | 6 |
| **Total Sequential Time** | ~6 hours |
| **Estimated Parallel Time** | ~3-4 hours |

---

## Test Cases by Category

### Category 1: VLAN Tests (3 tests)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 1.1 | VLAN Configuration Persistence | P0 | 5 min |
| 1.2 | VLAN Interface State Preservation | P1 | 5 min |
| 1.3 | VLAN Member Port Tagging Mode | P1 | 10 min |

### Category 2: FDB Tests (3 tests)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 2.1 | MAC Address Learning Persistence | P0 | 10 min |
| 2.2 | Static MAC Entries Preservation | P1 | 5 min |
| 2.3 | FDB Aging During Warm Reboot | P2 | 15 min |

### Category 3: LAG/PortChannel Tests (4 tests)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 3.1 | PortChannel Configuration Persistence | P0 | 10 min |
| 3.2 | LACP State Preservation | P0 | 15 min |
| 3.3 | PortChannel Member Link Failure During Warm Reboot | P1 | 20 min |
| 3.4 | PortChannel Min-Links Configuration | P2 | 10 min |

### Category 4: Port Synchronization Tests (2 tests)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 4.1 | Port State Preservation | P1 | 5 min |
| 4.2 | Port Configuration Preservation | P1 | 5 min |

### Category 5: Interface Management Tests (1 test)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 5.1 | Interface Configuration Persistence | P2 | 5 min |

### Category 6: Integration Tests (3 tests)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 6.1 | VLAN with PortChannel Members | P0 | 20 min |
| 6.2 | Multiple VLANs with Overlapping PortChannel Members | P1 | 25 min |
| 6.3 | Layer 2 Forwarding During Warm Reboot | P0 | 30 min |

### Category 7: Negative Tests (4 tests)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 7.1 | Warm Reboot with Component Failure | P1 | 15 min |
| 7.2 | Configuration Change During Warm Reboot | P2 | 10 min |
| 7.3 | Warm Reboot Timeout | P2 | 15 min |
| 7.4 | Repeated Warm Reboots | P1 | 60 min |

### Category 8: Reconciliation and State Verification Tests (3 tests)
| Test ID | Test Name | Priority | Duration |
|---------|-----------|----------|----------|
| 8.1 | Component Reconciliation State Tracking | P0 | 10 min |
| 8.2 | Database Consistency Verification | P0 | 15 min |
| 8.3 | Restore Count Verification | P1 | 5 min |

---

## Test Cases by Component

### vlanmgrd (VLAN Management)
| Test ID | Test Name | Priority |
|---------|-----------|----------|
| 1.1 | VLAN Configuration Persistence | P0 |
| 1.2 | VLAN Interface State Preservation | P1 |
| 1.3 | VLAN Member Port Tagging Mode | P1 |
| 6.1 | VLAN with PortChannel Members | P0 |
| 6.2 | Multiple VLANs with Overlapping PortChannel Members | P1 |

### fdbsyncd (FDB Synchronization)
| Test ID | Test Name | Priority |
|---------|-----------|----------|
| 2.1 | MAC Address Learning Persistence | P0 |
| 2.2 | Static MAC Entries Preservation | P1 |
| 2.3 | FDB Aging During Warm Reboot | P2 |
| 6.1 | VLAN with PortChannel Members | P0 |

### teamsyncd & teammgrd (LAG/PortChannel)
| Test ID | Test Name | Priority |
|---------|-----------|----------|
| 3.1 | PortChannel Configuration Persistence | P0 |
| 3.2 | LACP State Preservation | P0 |
| 3.3 | PortChannel Member Link Failure During Warm Reboot | P1 |
| 3.4 | PortChannel Min-Links Configuration | P2 |
| 6.1 | VLAN with PortChannel Members | P0 |
| 6.2 | Multiple VLANs with Overlapping PortChannel Members | P1 |

### portsyncd (Port Synchronization)
| Test ID | Test Name | Priority |
|---------|-----------|----------|
| 4.1 | Port State Preservation | P1 |
| 4.2 | Port Configuration Preservation | P1 |

### intfmgrd (Interface Management)
| Test ID | Test Name | Priority |
|---------|-----------|----------|
| 5.1 | Interface Configuration Persistence | P2 |

---

## Test Cases by Priority

### P0 - Must Pass for Release (8 tests)
| Test ID | Test Name | Category | Duration |
|---------|-----------|----------|----------|
| 1.1 | VLAN Configuration Persistence | VLAN Tests | 5 min |
| 2.1 | MAC Address Learning Persistence | FDB Tests | 10 min |
| 3.1 | PortChannel Configuration Persistence | LAG Tests | 10 min |
| 3.2 | LACP State Preservation | LAG Tests | 15 min |
| 6.1 | VLAN with PortChannel Members | Integration Tests | 20 min |
| 6.3 | Layer 2 Forwarding During Warm Reboot | Integration Tests | 30 min |
| 8.1 | Component Reconciliation State Tracking | Verification Tests | 10 min |
| 8.2 | Database Consistency Verification | Verification Tests | 15 min |
| **Total P0 Duration** | | | **~2 hours** |

### P1 - Should Pass for Release (9 tests)
| Test ID | Test Name | Category | Duration |
|---------|-----------|----------|----------|
| 1.2 | VLAN Interface State Preservation | VLAN Tests | 5 min |
| 1.3 | VLAN Member Port Tagging Mode | VLAN Tests | 10 min |
| 2.2 | Static MAC Entries Preservation | FDB Tests | 5 min |
| 3.3 | PortChannel Member Link Failure During Warm Reboot | LAG Tests | 20 min |
| 4.1 | Port State Preservation | Port Tests | 5 min |
| 4.2 | Port Configuration Preservation | Port Tests | 5 min |
| 6.2 | Multiple VLANs with Overlapping PortChannel Members | Integration Tests | 25 min |
| 7.1 | Warm Reboot with Component Failure | Negative Tests | 15 min |
| 7.4 | Repeated Warm Reboots | Negative Tests | 60 min |
| 8.3 | Restore Count Verification | Verification Tests | 5 min |
| **Total P1 Duration** | | | **~2.5 hours** |

### P2 - Nice to Have (6 tests)
| Test ID | Test Name | Category | Duration |
|---------|-----------|----------|----------|
| 2.3 | FDB Aging During Warm Reboot | FDB Tests | 15 min |
| 3.4 | PortChannel Min-Links Configuration | LAG Tests | 10 min |
| 5.1 | Interface Configuration Persistence | Interface Tests | 5 min |
| 7.2 | Configuration Change During Warm Reboot | Negative Tests | 10 min |
| 7.3 | Warm Reboot Timeout | Negative Tests | 15 min |
| **Total P2 Duration** | | | **~1 hour** |

---

**Total Test Cases**: 23  
**Total Estimated Time**: ~6 hours (sequential) | ~3-4 hours (parallel)

**Version**: 1.0  
**Created**: 2026-02-04  
**Status**: Ready for Execution
