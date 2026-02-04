# Warm Reboot/Warm Boot Test Plan - Layer 2 Tests

## Overview
This test plan covers Layer 2 functionality validation during and after warm-reboot/warm-boot operations in SONiC. The focus is on ensuring that Layer 2 services (VLANs, FDB, LAG/PortChannels) maintain state and recover properly during warm restart.

## Scope
This test plan focuses on the following Layer 2 components and their associated WARM_RESTART_TABLE entries:
- **vlanmgrd** - VLAN management daemon
- **fdbsyncd** - FDB (Forwarding Database) synchronization daemon  
- **teamsyncd** - Team/LAG synchronization daemon
- **teammgrd** - Team/LAG management daemon
- **portsyncd** - Port synchronization daemon
- **intfmgrd** - Interface management daemon

## Test Environment Setup

### Prerequisites
- SONiC device with warm-reboot capability
- Traffic generator or test endpoints for data plane validation
- Access to redis-cli for database verification
- Multiple VLANs configured
- Multiple PortChannels/LAGs configured
- Active MAC learning and FDB entries

### Warm Restart Configuration
```bash
# Enable warm restart for Layer 2 components
config warm_restart enable system
config warm_restart enable swss
config warm_restart enable teamd

# Verify warm restart is enabled
redis-cli -n 6 hgetall "WARM_RESTART_ENABLE_TABLE|system"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|vlanmgrd"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|fdbsyncd"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|teamsyncd"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|teammgrd"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|portsyncd"
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|intfmgrd"
```

## Test Categories

### 1. VLAN Tests (vlanmgrd)

#### Test 1.1: VLAN Configuration Persistence
**Objective**: Verify VLAN configurations are preserved during warm reboot

**Pre-conditions**:
- Create multiple VLANs (e.g., Vlan100, Vlan200, Vlan300)
- Configure VLAN members (tagged and untagged)
- Verify VLANs are operational

**Test Steps**:
1. Record VLAN configuration from CONFIG_DB
   ```bash
   redis-cli -n 4 keys "VLAN|*"
   redis-cli -n 4 keys "VLAN_MEMBER|*"
   ```
2. Initiate warm reboot
   ```bash
   warm-reboot
   ```
3. After reboot, verify VLAN configuration matches pre-reboot state
4. Check WARM_RESTART_TABLE|vlanmgrd state transitions

**Expected Results**:
- All VLANs present in CONFIG_DB before reboot exist after reboot
- VLAN members (tagged/untagged) are preserved
- vlanmgrd reconciles successfully (state: "reconciled")
- No data plane traffic loss during reboot

**Validation Commands**:
```bash
redis-cli -n 4 hgetall "VLAN|Vlan100"
redis-cli -n 4 hgetall "VLAN_MEMBER|Vlan100|Ethernet0"
redis-cli -n 6 hget "WARM_RESTART_TABLE|vlanmgrd" state
show vlan brief
```

#### Test 1.2: VLAN Interface State Preservation
**Objective**: Verify VLAN interface admin/oper states are maintained

**Pre-conditions**:
- VLANs with different admin states (up/down)
- VLAN interfaces with IP addresses configured

**Test Steps**:
1. Record VLAN interface states (admin_status, oper_status)
2. Perform warm reboot
3. Verify interface states match pre-reboot configuration

**Expected Results**:
- VLAN interface admin states preserved
- VLAN interface operational states recover correctly
- IP addresses on VLAN interfaces remain configured

#### Test 1.3: VLAN Member Port Tagging Mode
**Objective**: Verify VLAN member tagging modes (tagged/untagged) are preserved

**Pre-conditions**:
- VLANs with both tagged and untagged member ports
- Active traffic on VLAN member ports

**Test Steps**:
1. Document tagging mode for each VLAN member
2. Send tagged and untagged traffic
3. Perform warm reboot
4. Verify tagging modes and traffic forwarding

**Expected Results**:
- Tagging modes preserved for all VLAN members
- Tagged traffic continues to flow correctly
- Untagged traffic continues to flow correctly

### 2. FDB Tests (fdbsyncd)

#### Test 2.1: MAC Address Learning Persistence
**Objective**: Verify learned MAC addresses are preserved during warm reboot

**Pre-conditions**:
- Active traffic generating MAC learning
- Multiple MAC addresses learned on different VLANs
- FDB entries populated in ASIC_DB

**Test Steps**:
1. Generate traffic to learn MAC addresses
2. Record FDB entries from ASIC_DB and STATE_DB
   ```bash
   redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_FDB_ENTRY:*"
   show mac
   ```
3. Perform warm reboot
4. Verify MAC addresses are preserved after reboot

**Expected Results**:
- Learned MAC addresses preserved in FDB
- fdbsyncd reconciles successfully
- No MAC re-learning required for existing entries
- Continuous traffic forwarding based on existing FDB

**Validation Commands**:
```bash
redis-cli -n 6 hget "WARM_RESTART_TABLE|fdbsyncd" state
show mac
redis-cli -n 0 keys "FDB_TABLE:*"
```

#### Test 2.2: Static MAC Entries Preservation
**Objective**: Verify statically configured MAC entries are preserved

**Pre-conditions**:
- Static MAC entries configured
- Mix of static and dynamic MAC entries

**Test Steps**:
1. Configure static MAC entries
2. Record static MAC configuration
3. Perform warm reboot
4. Verify static MAC entries remain configured

**Expected Results**:
- All static MAC entries preserved
- Static MAC entries not aged out
- Static MAC entries take precedence over dynamic learning

#### Test 2.3: FDB Aging During Warm Reboot
**Objective**: Verify FDB aging behavior during warm reboot

**Pre-conditions**:
- MAC addresses with different aging timers
- FDB aging configured

**Test Steps**:
1. Learn MAC addresses at different times
2. Note aging timers for each MAC entry
3. Perform warm reboot
4. Verify aging timers are handled correctly

**Expected Results**:
- MAC aging suspended during warm reboot
- MAC entries not aged out during reboot process
- Aging resumes after warm reboot completion

### 3. LAG/PortChannel Tests (teamsyncd, teammgrd)

#### Test 3.1: PortChannel Configuration Persistence
**Objective**: Verify PortChannel configurations are preserved during warm reboot

**Pre-conditions**:
- Multiple PortChannels configured (e.g., PortChannel0001, PortChannel0002)
- PortChannel members configured
- LACP operational on PortChannels

**Test Steps**:
1. Record PortChannel configuration
   ```bash
   redis-cli -n 4 keys "PORTCHANNEL|*"
   redis-cli -n 4 keys "PORTCHANNEL_MEMBER|*"
   show interfaces portchannel
   ```
2. Verify LACP state for all PortChannels
3. Perform warm reboot
4. Verify PortChannel configuration and state after reboot

**Expected Results**:
- All PortChannels preserved with correct configuration
- PortChannel members remain associated
- teamsyncd and teammgrd reconcile successfully
- LACP state maintained (no re-negotiation)

**Validation Commands**:
```bash
redis-cli -n 6 hget "WARM_RESTART_TABLE|teamsyncd" state
redis-cli -n 6 hget "WARM_RESTART_TABLE|teammgrd" state
show interfaces portchannel
teamshow
```

#### Test 3.2: LACP State Preservation
**Objective**: Verify LACP protocol state is maintained during warm reboot

**Pre-conditions**:
- PortChannels with LACP enabled
- Active LACP sessions with peer devices
- Traffic flowing through PortChannels

**Test Steps**:
1. Verify LACP is in COLLECTING_DISTRIBUTING state
2. Record LACP partner information
3. Perform warm reboot
4. Verify LACP state is maintained without re-negotiation

**Expected Results**:
- LACP sessions remain active
- No LACP PDU exchange during warm reboot
- Partner information preserved
- No traffic disruption on PortChannels

#### Test 3.3: PortChannel Member Link Failure During Warm Reboot
**Objective**: Verify handling of member link failure during warm reboot

**Pre-conditions**:
- PortChannel with multiple members
- Active traffic on PortChannel

**Test Steps**:
1. Initiate warm reboot
2. During reboot, simulate member link failure
3. Verify PortChannel remains operational with remaining members
4. Verify warm reboot completes successfully

**Expected Results**:
- PortChannel remains operational with active members
- Failed member detected and removed from PortChannel
- Warm reboot completes successfully
- Traffic redistributed to active members

#### Test 3.4: PortChannel Min-Links Configuration
**Objective**: Verify min-links configuration is honored during warm reboot

**Pre-conditions**:
- PortChannel with min-links configured
- Number of active members >= min-links

**Test Steps**:
1. Configure PortChannel with min-links
2. Verify PortChannel is operational
3. Perform warm reboot
4. Verify min-links configuration preserved

**Expected Results**:
- Min-links configuration preserved
- PortChannel operational state based on min-links
- Configuration in CONFIG_DB matches pre-reboot state

### 4. Port Synchronization Tests (portsyncd)

#### Test 4.1: Port State Preservation
**Objective**: Verify port admin and operational states are preserved

**Pre-conditions**:
- Ports with different admin states (up/down)
- Mix of active and inactive ports

**Test Steps**:
1. Record port states (admin_status, oper_status)
   ```bash
   show interfaces status
   redis-cli -n 4 keys "PORT|*"
   ```
2. Perform warm reboot
3. Verify port states match pre-reboot configuration

**Expected Results**:
- Port admin states preserved
- Port operational states recover correctly
- portsyncd reconciles successfully

**Validation Commands**:
```bash
redis-cli -n 6 hget "WARM_RESTART_TABLE|portsyncd" state
show interfaces status
```

#### Test 4.2: Port Configuration Preservation
**Objective**: Verify port configurations (speed, MTU, etc.) are preserved

**Pre-conditions**:
- Ports with various configurations (speed, MTU, FEC, etc.)

**Test Steps**:
1. Record port configurations
2. Perform warm reboot
3. Verify all port configurations preserved

**Expected Results**:
- Port speed settings preserved
- MTU settings preserved
- FEC settings preserved
- All port attributes match pre-reboot state

### 5. Interface Management Tests (intfmgrd)

#### Test 5.1: Interface Configuration Persistence
**Objective**: Verify interface configurations are preserved during warm reboot

**Pre-conditions**:
- Various interface types configured (physical, VLAN, PortChannel)
- Interface attributes configured

**Test Steps**:
1. Record interface configurations
2. Perform warm reboot
3. Verify interface configurations preserved

**Expected Results**:
- All interface configurations preserved
- intfmgrd reconciles successfully
- Interface states match pre-reboot configuration

**Validation Commands**:
```bash
redis-cli -n 6 hget "WARM_RESTART_TABLE|intfmgrd" state
show interfaces status
```

### 6. Integration Tests (Multi-Component)

#### Test 6.1: VLAN with PortChannel Members
**Objective**: Verify VLANs with PortChannel members work correctly during warm reboot

**Pre-conditions**:
- VLANs configured with PortChannel members
- Traffic flowing through VLAN on PortChannel
- MAC addresses learned on PortChannel VLAN members

**Test Steps**:
1. Configure VLAN with PortChannel as member
2. Generate traffic and verify MAC learning
3. Perform warm reboot
4. Verify VLAN, PortChannel, and FDB all preserved

**Expected Results**:
- VLAN configuration preserved
- PortChannel membership in VLAN preserved
- MAC addresses learned on PortChannel preserved
- Traffic continues to flow without interruption
- All related daemons (vlanmgrd, teamsyncd, fdbsyncd) reconcile successfully

#### Test 6.2: Multiple VLANs with Overlapping PortChannel Members
**Objective**: Verify complex VLAN/PortChannel configurations during warm reboot

**Pre-conditions**:
- Multiple VLANs configured
- PortChannels as members of multiple VLANs (trunk mode)
- Active traffic on all VLANs

**Test Steps**:
1. Configure multiple VLANs with same PortChannel as tagged member
2. Generate traffic on all VLANs
3. Perform warm reboot
4. Verify all VLAN/PortChannel associations preserved

**Expected Results**:
- All VLAN configurations preserved
- PortChannel trunk membership preserved
- Traffic segregation maintained across VLANs
- No cross-VLAN traffic leakage

#### Test 6.3: Layer 2 Forwarding During Warm Reboot
**Objective**: Verify continuous Layer 2 forwarding during warm reboot

**Pre-conditions**:
- Active bidirectional traffic between endpoints
- Traffic flowing through VLANs and PortChannels
- Established FDB entries

**Test Steps**:
1. Start continuous traffic between endpoints
2. Monitor packet loss and latency
3. Initiate warm reboot
4. Continue monitoring during and after reboot

**Expected Results**:
- Minimal packet loss (within acceptable threshold)
- Traffic forwarding continues during reboot
- FDB entries used for forwarding without re-learning
- Latency spike within acceptable limits

**Metrics to Collect**:
- Packet loss percentage
- Maximum latency spike
- Traffic throughput before/during/after reboot
- Time to full reconciliation

### 7. Negative Tests

#### Test 7.1: Warm Reboot with Component Failure
**Objective**: Verify system behavior when a Layer 2 component fails to reconcile

**Pre-conditions**:
- Warm reboot enabled
- All Layer 2 components operational

**Test Steps**:
1. Initiate warm reboot
2. Simulate failure of one component (e.g., vlanmgrd)
3. Monitor system behavior and recovery

**Expected Results**:
- System detects component failure
- Appropriate error logging
- System attempts recovery or falls back to cold reboot
- No system hang or crash

#### Test 7.2: Configuration Change During Warm Reboot
**Objective**: Verify handling of configuration changes during warm reboot

**Pre-conditions**:
- Warm reboot in progress

**Test Steps**:
1. Initiate warm reboot
2. Attempt to modify VLAN/PortChannel configuration during reboot
3. Verify configuration change handling

**Expected Results**:
- Configuration changes blocked during warm reboot
- Appropriate error message displayed
- System state remains consistent
- Warm reboot completes successfully

#### Test 7.3: Warm Reboot Timeout
**Objective**: Verify system behavior when warm reboot exceeds timeout

**Pre-conditions**:
- Warm reboot timeout configured
- Component reconciliation delayed

**Test Steps**:
1. Configure short warm reboot timeout
2. Initiate warm reboot
3. Monitor timeout handling

**Expected Results**:
- System detects timeout condition
- Appropriate logging and alerts
- System takes corrective action (e.g., fallback to cold reboot)
- No data corruption

#### Test 7.4: Repeated Warm Reboots
**Objective**: Verify system stability with multiple consecutive warm reboots

**Pre-conditions**:
- System in stable state

**Test Steps**:
1. Perform warm reboot
2. Wait for full reconciliation
3. Immediately perform another warm reboot
4. Repeat 5-10 times

**Expected Results**:
- All warm reboots complete successfully
- No degradation in performance
- No memory leaks or resource exhaustion
- Configuration remains consistent

### 8. Reconciliation and State Verification Tests

#### Test 8.1: Component Reconciliation State Tracking
**Objective**: Verify all Layer 2 components transition through correct states

**Pre-conditions**:
- Warm reboot enabled for all Layer 2 components

**Test Steps**:
1. Monitor WARM_RESTART_TABLE for each component
2. Initiate warm reboot
3. Track state transitions for each component

**Expected Results**:
- All components transition: initialized → reconciled
- State transitions occur within expected timeframes
- No components stuck in intermediate states

**Validation Commands**:
```bash
# Monitor state transitions
watch -n 1 'redis-cli -n 6 hget "WARM_RESTART_TABLE|vlanmgrd" state'
watch -n 1 'redis-cli -n 6 hget "WARM_RESTART_TABLE|fdbsyncd" state'
watch -n 1 'redis-cli -n 6 hget "WARM_RESTART_TABLE|teamsyncd" state'
watch -n 1 'redis-cli -n 6 hget "WARM_RESTART_TABLE|teammgrd" state'
watch -n 1 'redis-cli -n 6 hget "WARM_RESTART_TABLE|portsyncd" state'
watch -n 1 'redis-cli -n 6 hget "WARM_RESTART_TABLE|intfmgrd" state'
```

#### Test 8.2: Database Consistency Verification
**Objective**: Verify database consistency across CONFIG_DB, APPL_DB, ASIC_DB, STATE_DB

**Pre-conditions**:
- Layer 2 configuration active

**Test Steps**:
1. Record database state before warm reboot
2. Perform warm reboot
3. Compare database state after reboot

**Expected Results**:
- CONFIG_DB unchanged
- APPL_DB restored correctly
- ASIC_DB reflects hardware state
- STATE_DB updated with current operational state
- No orphaned entries in any database

#### Test 8.3: Restore Count Verification
**Objective**: Verify restore_count is properly maintained for each component

**Pre-conditions**:
- Fresh system state

**Test Steps**:
1. Check initial restore_count for each component
2. Perform warm reboot
3. Verify restore_count incremented

**Expected Results**:
- restore_count incremented by 1 for each component
- restore_count persists across reboots

**Validation Commands**:
```bash
redis-cli -n 6 hget "WARM_RESTART_TABLE|vlanmgrd" restore_count
redis-cli -n 6 hget "WARM_RESTART_TABLE|fdbsyncd" restore_count
redis-cli -n 6 hget "WARM_RESTART_TABLE|teamsyncd" restore_count
redis-cli -n 6 hget "WARM_RESTART_TABLE|teammgrd" restore_count
redis-cli -n 6 hget "WARM_RESTART_TABLE|portsyncd" restore_count
redis-cli -n 6 hget "WARM_RESTART_TABLE|intfmgrd" restore_count
```

## Test Execution Guidelines

### Test Sequence
1. Execute basic functionality tests first (Tests 1.x, 2.x, 3.x, 4.x, 5.x)
2. Execute integration tests (Tests 6.x)
3. Execute negative tests (Tests 7.x)
4. Execute reconciliation tests (Tests 8.x)

### Test Environment Requirements
- **Hardware**: Physical SONiC device or virtual switch (VS)
- **Traffic Generator**: Ixia, Spirent, or software-based (iperf, scapy)
- **Monitoring Tools**:
  - redis-cli for database inspection
  - tcpdump for packet capture
  - syslog monitoring
  - Performance monitoring tools

### Pre-Test Checklist
- [ ] Verify warm-reboot capability is supported on platform
- [ ] Enable warm restart for all required components
- [ ] Configure baseline Layer 2 setup (VLANs, PortChannels, etc.)
- [ ] Verify all components are in healthy state
- [ ] Clear any previous warm reboot state
- [ ] Set up traffic generators and monitoring

### Post-Test Verification
After each test, verify:
- [ ] All Layer 2 components reconciled successfully
- [ ] No error messages in syslog
- [ ] Database consistency maintained
- [ ] Traffic forwarding operational
- [ ] No memory leaks or resource issues

### Data Collection
For each test, collect:
- Pre-reboot configuration snapshots
- Database dumps (CONFIG_DB, APPL_DB, ASIC_DB, STATE_DB)
- Syslog entries during reboot
- Traffic statistics (packet loss, latency, throughput)
- Component state transitions
- Timing metrics (reboot duration, reconciliation time)

## Success Criteria

### Overall Success Criteria
- **Zero Configuration Loss**: All Layer 2 configurations preserved
- **Minimal Traffic Loss**: < 1% packet loss during warm reboot
- **Fast Reconciliation**: All components reconcile within 5 minutes
- **State Consistency**: All databases consistent after reboot
- **No Service Disruption**: Existing connections maintained

### Component-Specific Success Criteria

#### vlanmgrd
- All VLAN configurations preserved
- VLAN member associations intact
- State: "reconciled" within 30 seconds

#### fdbsyncd
- > 95% of FDB entries preserved
- No unnecessary MAC re-learning
- State: "reconciled" within 60 seconds

#### teamsyncd / teammgrd
- All PortChannel configurations preserved
- LACP state maintained (no re-negotiation)
- PortChannel member associations intact
- State: "reconciled" within 45 seconds

#### portsyncd
- All port configurations preserved
- Port states match pre-reboot configuration
- State: "reconciled" within 30 seconds

#### intfmgrd
- All interface configurations preserved
- Interface states correct
- State: "reconciled" within 30 seconds

### Performance Metrics
- **Reboot Time**: < 90 seconds total
- **Reconciliation Time**: < 5 minutes for all components
- **Packet Loss**: < 1% during reboot
- **Latency Spike**: < 100ms maximum
- **Throughput**: Returns to 100% within 10 seconds post-reboot

## Test Automation Recommendations

### Pytest Framework Structure
```python
# Example test structure
import pytest
from swsscommon import swsscommon

class TestWarmRebootLayer2:

    @pytest.fixture(scope="class")
    def setup_vlan_config(self, dvs):
        """Setup VLAN configuration for tests"""
        # Create VLANs
        # Add VLAN members
        # Verify configuration
        yield
        # Cleanup

    def test_vlan_persistence(self, dvs, setup_vlan_config):
        """Test 1.1: VLAN Configuration Persistence"""
        # Get pre-reboot state
        # Perform warm reboot
        # Verify post-reboot state
        pass

    def test_fdb_persistence(self, dvs):
        """Test 2.1: MAC Address Learning Persistence"""
        # Generate traffic for MAC learning
        # Record FDB entries
        # Perform warm reboot
        # Verify FDB preserved
        pass

    def test_portchannel_persistence(self, dvs):
        """Test 3.1: PortChannel Configuration Persistence"""
        # Setup PortChannels
        # Perform warm reboot
        # Verify PortChannel state
        pass
```

### Automation Tools
- **pytest**: Test framework
- **swsscommon**: SONiC database interaction
- **scapy**: Traffic generation and capture
- **paramiko**: SSH automation for device control
- **redis-py**: Direct Redis database access

## Appendix

### A. Useful Commands Reference

#### Database Inspection
```bash
# View all WARM_RESTART_TABLE entries
redis-cli -n 6 keys "WARM_RESTART_TABLE|*"

# Check specific component state
redis-cli -n 6 hgetall "WARM_RESTART_TABLE|vlanmgrd"

# View VLAN configuration
redis-cli -n 4 keys "VLAN|*"
redis-cli -n 4 keys "VLAN_MEMBER|*"

# View PortChannel configuration
redis-cli -n 4 keys "PORTCHANNEL|*"
redis-cli -n 4 keys "PORTCHANNEL_MEMBER|*"

# View FDB entries
redis-cli -n 0 keys "FDB_TABLE:*"
redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_FDB_ENTRY:*"
```

#### Show Commands
```bash
show vlan brief
show vlan config
show mac
show interfaces portchannel
show interfaces status
teamshow
```

#### Warm Reboot Commands
```bash
# Enable warm restart
config warm_restart enable system
config warm_restart enable swss
config warm_restart enable teamd

# Disable warm restart
config warm_restart disable system

# Initiate warm reboot
warm-reboot

# Check warm reboot status
show warm_restart config
show warm_restart state
```

### B. Troubleshooting Guide

#### Component Not Reconciling
1. Check component logs: `sudo tail -f /var/log/syslog | grep <component>`
2. Verify restore_count exists: `redis-cli -n 6 hget "WARM_RESTART_TABLE|<component>" restore_count`
3. Check component is running: `docker ps | grep <component>`
4. Verify database connectivity

#### FDB Entries Lost
1. Check fdbsyncd logs
2. Verify ASIC_DB state
3. Check if MAC aging occurred
4. Verify VLAN configuration preserved

#### PortChannel LACP Re-negotiation
1. Check teamd logs
2. Verify LACP PDU exchange
3. Check partner system behavior
4. Verify teamsyncd/teammgrd reconciliation

### C. Known Limitations
- Warm reboot may not be supported on all platforms
- Some ASIC-specific features may require cold reboot
- Maximum FDB size may impact reconciliation time
- Complex configurations may extend reconciliation time

### D. References
- SONiC Warm Reboot Design: [SONiC GitHub Wiki]
- WARM_RESTART_TABLE Schema: `src/sonic-yang-models/yang-models/sonic-warm-restart.yang`
- Component Reconciliation: `files/image_config/warmboot-finalizer/finalize-warmboot.sh`

---

**Document Version**: 1.0
**Last Updated**: 2026-02-04
**Author**: SONiC Test Team
**Status**: Draft


