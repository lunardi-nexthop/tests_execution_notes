# Warm Reboot Layer 2 Test Cases - Detailed Table

## Complete Test Case Table

| Test ID | Category | Test Area | Test Name | Objective | Pre-Condition | Test Steps | Expected Result | Pass/Fail |
|---------|----------|-----------|-----------|-----------|---------------|------------|-----------------|-----------|
| **1.1** | VLAN Tests | vlanmgrd | VLAN Configuration Persistence | Verify VLAN configurations are preserved during warm reboot | Create multiple VLANs (Vlan100, Vlan200, Vlan300); Configure VLAN members (tagged/untagged); Verify VLANs operational | 1. Record VLAN config from CONFIG_DB<br>2. Initiate warm-reboot<br>3. Verify VLAN config matches pre-reboot<br>4. Check vlanmgrd state transitions | All VLANs in CONFIG_DB preserved; VLAN members preserved; vlanmgrd reconciled; No traffic loss | |
| **1.2** | VLAN Tests | vlanmgrd | VLAN Interface State Preservation | Verify VLAN interface admin/oper states are maintained | VLANs with different admin states (up/down); VLAN interfaces with IP addresses | 1. Record VLAN interface states<br>2. Perform warm reboot<br>3. Verify states match pre-reboot | VLAN interface admin states preserved; Oper states recover correctly; IP addresses remain configured | |
| **1.3** | VLAN Tests | vlanmgrd | VLAN Member Port Tagging Mode | Verify VLAN member tagging modes (tagged/untagged) are preserved | VLANs with mixed tagged/untagged members; Traffic flowing through VLAN | 1. Record tagging mode for each member<br>2. Perform warm reboot<br>3. Verify tagging modes preserved<br>4. Test traffic forwarding | All tagging modes preserved; Traffic forwarding works correctly; No packet loss | |
| **2.1** | FDB Tests | fdbsyncd | MAC Address Learning Persistence | Verify learned MAC addresses are preserved during warm reboot | Active traffic generating MAC learning; Multiple MAC addresses in FDB; FDB entries in ASIC_DB | 1. Record learned MAC addresses<br>2. Count FDB entries<br>3. Perform warm reboot<br>4. Verify MAC addresses preserved | >95% of MAC addresses preserved; fdbsyncd reconciled; MAC-to-port mappings correct | |
| **2.2** | FDB Tests | fdbsyncd | Static MAC Entries Preservation | Verify statically configured MAC entries are preserved | Static MAC entries configured; Entries present in CONFIG_DB and ASIC_DB | 1. Record static MAC entries<br>2. Perform warm reboot<br>3. Verify all static entries preserved | 100% static MAC entries preserved; Entries in CONFIG_DB and ASIC_DB match; No re-learning required | |
| **2.3** | FDB Tests | fdbsyncd | FDB Aging During Warm Reboot | Verify FDB aging behavior during warm reboot | FDB aging timer configured; Mix of old and new MAC entries | 1. Record MAC entry timestamps<br>2. Perform warm reboot<br>3. Verify aging continues correctly<br>4. Check no premature aging | Aging timer preserved; No premature expiration; Aged entries removed correctly post-reboot | |
| **3.1** | LAG Tests | teamsyncd, teammgrd | PortChannel Configuration Persistence | Verify PortChannel configurations are preserved during warm reboot | Multiple PortChannels configured; Members assigned; PortChannels operational | 1. Record PortChannel configs<br>2. Perform warm reboot<br>3. Verify configs preserved<br>4. Check teamsyncd/teammgrd states | All PortChannel configs preserved; Member assignments intact; teamsyncd/teammgrd reconciled | |
| **3.2** | LAG Tests | teamsyncd, teammgrd | LACP State Preservation | Verify LACP protocol state is maintained during warm reboot | LACP-enabled PortChannels; Active LACP sessions; Traffic flowing | 1. Record LACP states (actor/partner)<br>2. Perform warm reboot<br>3. Verify no LACP re-negotiation<br>4. Check traffic continuity | No LACP re-negotiation; LACP states preserved; Traffic continues without interruption; <1% packet loss | |
| **3.3** | LAG Tests | teamsyncd, teammgrd | PortChannel Member Link Failure During Warm Reboot | Verify handling of member link failure during warm reboot | PortChannel with multiple members; Active traffic; One member link down during reboot | 1. Bring down one member link<br>2. Perform warm reboot<br>3. Verify PortChannel remains up<br>4. Check traffic redistribution | PortChannel stays operational; Traffic redistributed to active members; Failed member state preserved | |
| **3.4** | LAG Tests | teamsyncd, teammgrd | PortChannel Min-Links Configuration | Verify min-links configuration is honored during warm reboot | PortChannel with min-links configured; Sufficient active members | 1. Record min-links setting<br>2. Perform warm reboot<br>3. Verify min-links enforced<br>4. Test with member count at threshold | Min-links configuration preserved; PortChannel state correct based on active members; Threshold enforced | |
| **4.1** | Port Tests | portsyncd | Port State Preservation | Verify port admin and operational states are preserved | Ports in various states (up/down/disabled); Port configurations applied | 1. Record all port admin/oper states<br>2. Perform warm reboot<br>3. Verify states match pre-reboot | All port admin states preserved; Oper states recover correctly; portsyncd reconciled | |
| **4.2** | Port Tests | portsyncd | Port Configuration Preservation | Verify port configurations (speed, MTU, etc.) are preserved | Ports with various configs (speed, MTU, FEC); Non-default settings applied | 1. Record port configurations<br>2. Perform warm reboot<br>3. Verify all configs preserved | Speed settings preserved; MTU preserved; FEC settings preserved; All configs match pre-reboot | |
| **5.1** | Interface Tests | intfmgrd | Interface Configuration Persistence | Verify interface configurations are preserved during warm reboot | Interfaces with IP addresses; Various interface types configured | 1. Record interface configs<br>2. Perform warm reboot<br>3. Verify configs preserved<br>4. Check intfmgrd state | All interface configs preserved; IP addresses intact; intfmgrd reconciled | |
| **6.1** | Integration Tests | vlanmgrd, teamsyncd, fdbsyncd | VLAN with PortChannel Members | Verify VLANs with PortChannel members work correctly during warm reboot | VLAN with PortChannel as member; Active traffic; MAC learning on PortChannel | 1. Setup VLAN with PortChannel member<br>2. Generate traffic<br>3. Perform warm reboot<br>4. Verify VLAN, PortChannel, FDB | VLAN config preserved; PortChannel membership intact; MAC addresses preserved; Traffic continues | |
| **6.2** | Integration Tests | vlanmgrd, teamsyncd | Multiple VLANs with Overlapping PortChannel Members | Verify complex VLAN/PortChannel configurations during warm reboot | Multiple VLANs; PortChannels as members in multiple VLANs; Tagged traffic | 1. Setup complex topology<br>2. Generate tagged traffic<br>3. Perform warm reboot<br>4. Verify all configs | All VLAN configs preserved; PortChannel memberships intact; Tagged traffic forwarding correct | |
| **6.3** | Integration Tests | All L2 components | Layer 2 Forwarding During Warm Reboot | Verify continuous Layer 2 forwarding during warm reboot | Full L2 topology; Active traffic flows; All components operational | 1. Start continuous traffic<br>2. Monitor packet loss<br>3. Perform warm reboot<br>4. Measure traffic disruption | <1% packet loss; Traffic resumes quickly; All L2 functions operational; <5 min reconciliation | |
| **7.1** | Negative Tests | All L2 components | Warm Reboot with Component Failure | Verify system behavior when a Layer 2 component fails to reconcile | Warm restart enabled; Simulate component failure scenario | 1. Inject failure in component<br>2. Perform warm reboot<br>3. Monitor system behavior<br>4. Check error handling | System detects failure; Appropriate error logged; Other components continue; Graceful degradation | |
| **7.2** | Negative Tests | All L2 components | Configuration Change During Warm Reboot | Verify handling of configuration changes during warm reboot | Warm restart enabled; Config change attempted during reboot | 1. Initiate warm reboot<br>2. Attempt config change mid-reboot<br>3. Verify system behavior<br>4. Check final state | Config change rejected or queued; System remains stable; No corruption; Clear error message | |
| **7.3** | Negative Tests | All L2 components | Warm Reboot Timeout | Verify system behavior when warm reboot exceeds timeout | Warm restart with timeout configured; Simulate slow reconciliation | 1. Configure short timeout<br>2. Simulate slow component<br>3. Perform warm reboot<br>4. Verify timeout handling | Timeout detected; Appropriate action taken; System recovers; Error logged | |
| **7.4** | Negative Tests | All L2 components | Repeated Warm Reboots | Verify system stability with multiple consecutive warm reboots | Warm restart enabled; Full L2 configuration | 1. Perform warm reboot<br>2. Wait for reconciliation<br>3. Repeat 5 times<br>4. Verify stability | All reboots successful; No degradation; Configs preserved each time; restore_count increments | |
| **8.1** | Verification Tests | All L2 components | Component Reconciliation State Tracking | Verify all Layer 2 components transition through correct states | Warm restart enabled; All L2 components configured | 1. Monitor WARM_RESTART_TABLE<br>2. Perform warm reboot<br>3. Track state transitions<br>4. Verify all reach "reconciled" | All components: initialized→restored→reconciled; Correct timestamps; No stuck states | |
| **8.2** | Verification Tests | All L2 components | Database Consistency Verification | Verify database consistency across CONFIG_DB, APPL_DB, ASIC_DB, STATE_DB | Full L2 configuration; All databases populated | 1. Record all DB states pre-reboot<br>2. Perform warm reboot<br>3. Compare all DBs post-reboot<br>4. Verify consistency | CONFIG_DB unchanged; APPL_DB matches CONFIG_DB; ASIC_DB matches APPL_DB; STATE_DB correct | |
| **8.3** | Verification Tests | All L2 components | Restore Count Verification | Verify restore_count is properly maintained for each component | Warm restart enabled; Initial restore_count recorded | 1. Record restore_count for all components<br>2. Perform warm reboot<br>3. Verify restore_count incremented<br>4. Check consistency | restore_count incremented by 1; All components updated; Timestamps updated | |

---

## Test Summary Statistics

| Metric | Count/Value |
|--------|-------------|
| **Total Test Cases** | 23 |
| **VLAN Tests** | 3 |
| **FDB Tests** | 3 |
| **LAG Tests** | 4 |
| **Port Tests** | 2 |
| **Interface Tests** | 1 |
| **Integration Tests** | 3 |
| **Negative Tests** | 4 |
| **Verification Tests** | 3 |

---

## Test Execution Checklist

### Priority P0 - Must Pass (8 tests)
- [ ] Test 1.1 - VLAN Configuration Persistence
- [ ] Test 2.1 - MAC Address Learning Persistence
- [ ] Test 3.1 - PortChannel Configuration Persistence
- [ ] Test 3.2 - LACP State Preservation
- [ ] Test 6.1 - VLAN with PortChannel Members
- [ ] Test 6.3 - Layer 2 Forwarding During Warm Reboot
- [ ] Test 8.1 - Component Reconciliation State Tracking
- [ ] Test 8.2 - Database Consistency Verification

### Priority P1 - Should Pass (9 tests)
- [ ] Test 1.2 - VLAN Interface State Preservation
- [ ] Test 1.3 - VLAN Member Port Tagging Mode
- [ ] Test 2.2 - Static MAC Entries Preservation
- [ ] Test 3.3 - PortChannel Member Link Failure During Warm Reboot
- [ ] Test 4.1 - Port State Preservation
- [ ] Test 4.2 - Port Configuration Preservation
- [ ] Test 6.2 - Multiple VLANs with Overlapping PortChannel Members
- [ ] Test 7.1 - Warm Reboot with Component Failure
- [ ] Test 7.4 - Repeated Warm Reboots
- [ ] Test 8.3 - Restore Count Verification

### Priority P2 - Nice to Have (6 tests)
- [ ] Test 2.3 - FDB Aging During Warm Reboot
- [ ] Test 3.4 - PortChannel Min-Links Configuration
- [ ] Test 5.1 - Interface Configuration Persistence
- [ ] Test 7.2 - Configuration Change During Warm Reboot
- [ ] Test 7.3 - Warm Reboot Timeout

---

## Components Coverage Matrix

| Component | Test IDs | Total Tests |
|-----------|----------|-------------|
| vlanmgrd | 1.1, 1.2, 1.3, 6.1, 6.2 | 5 |
| fdbsyncd | 2.1, 2.2, 2.3, 6.1 | 4 |
| teamsyncd | 3.1, 3.2, 3.3, 3.4, 6.1, 6.2 | 6 |
| teammgrd | 3.1, 3.2, 3.3, 3.4, 6.1, 6.2 | 6 |
| portsyncd | 4.1, 4.2 | 2 |
| intfmgrd | 5.1 | 1 |
| All L2 | 6.3, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3 | 8 |

---

## Execution Time Estimates

| Category | Estimated Time |
|----------|----------------|
| VLAN Tests (3) | 20 minutes |
| FDB Tests (3) | 30 minutes |
| LAG Tests (4) | 55 minutes |
| Port Tests (2) | 10 minutes |
| Interface Tests (1) | 5 minutes |
| Integration Tests (3) | 75 minutes |
| Negative Tests (4) | 100 minutes |
| Verification Tests (3) | 30 minutes |
| **Total Sequential** | **~6 hours** |
| **Estimated Parallel** | **~3-4 hours** |

---

**Version**: 1.0  
**Created**: 2026-02-04  
**Status**: Ready for Execution  
**Format**: Detailed test case table with Pass/Fail tracking
