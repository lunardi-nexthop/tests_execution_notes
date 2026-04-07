# BGP Usage Examples with VRF Sub-Interfaces

## Overview

This document provides practical examples of using the VRF sub-interface configuration script for BGP peering scenarios. BGP commonly uses /31 point-to-point networks (RFC 3021) for efficient IP address utilization.

## Scenario 1: Single BGP Peer with VRF

Configure a single sub-interface for BGP peering with a customer in a dedicated VRF.

### Configuration

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.0/31 \
  --ipv6-address 2001:db8::0/127 \
  --vrf-name Customer1 \
  --print-cli
```

### Result

- **Local Router**: `10.0.0.0/31` and `2001:db8::0/127`
- **BGP Peer (Customer)**: `10.0.0.1/31` and `2001:db8::1/127`
- **VRF**: Customer1

### BGP Configuration (to add manually)

```bash
# Enter BGP configuration for the VRF
vtysh
configure terminal
router bgp 65000 vrf Customer1
  neighbor 10.0.0.1 remote-as 65001
  neighbor 10.0.0.1 description Customer1-IPv4
  neighbor 2001:db8::1 remote-as 65001
  neighbor 2001:db8::1 description Customer1-IPv6
  address-family ipv4 unicast
    neighbor 10.0.0.1 activate
  exit-address-family
  address-family ipv6 unicast
    neighbor 2001:db8::1 activate
  exit-address-family
exit
```

## Scenario 2: Multiple BGP Peers on Same Interface

Configure multiple sub-interfaces on the same physical interface for different BGP peers, each in their own VRF.

### Configuration

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.0/31 \
  --start-ipv6 2001:db8::0/127 \
  --count 5 \
  --vrf-prefix Customer \
  --print-cli
```

### Result

Creates 5 sub-interfaces with BGP peering IPs:

| Sub-Interface | VLAN | VRF | Local IPv4 | Peer IPv4 | Local IPv6 | Peer IPv6 |
|--------------|------|-----|------------|-----------|------------|-----------|
| Ethernet0.100 | 100 | Customer1 | 10.0.0.0/31 | 10.0.0.1 | 2001:db8::0/127 | 2001:db8::1 |
| Ethernet0.101 | 101 | Customer2 | 10.0.0.2/31 | 10.0.0.3 | 2001:db8::2/127 | 2001:db8::3 |
| Ethernet0.102 | 102 | Customer3 | 10.0.0.4/31 | 10.0.0.5 | 2001:db8::4/127 | 2001:db8::5 |
| Ethernet0.103 | 103 | Customer4 | 10.0.0.6/31 | 10.0.0.7 | 2001:db8::6/127 | 2001:db8::7 |
| Ethernet0.104 | 104 | Customer5 | 10.0.0.8/31 | 10.0.0.9 | 2001:db8::8/127 | 2001:db8::9 |

## Scenario 3: Multiple Interfaces with 3rd Octet Increment

Configure BGP peering across multiple physical interfaces, incrementing the 3rd octet for each interface. This is useful for organizing IP addressing by interface.

### Configuration

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface-list Ethernet384,Ethernet386,Ethernet388 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.0/31 \
  --start-ipv6 fc00:0:0::0/127 \
  --count 3 \
  --vrf-list CustomerA,CustomerB,CustomerC \
  --ip-octet3-increment \
  --ipv6-segment-increment \
  --print-cli
```

### Result

Creates 9 sub-interfaces organized by physical interface:

**Ethernet384** (10.0.0.x):
- Ethernet384.100: 10.0.0.0/31 (peer: 10.0.0.1) - VRF CustomerA
- Ethernet384.101: 10.0.0.2/31 (peer: 10.0.0.3) - VRF CustomerB
- Ethernet384.102: 10.0.0.4/31 (peer: 10.0.0.5) - VRF CustomerC

**Ethernet386** (10.0.1.x):
- Ethernet386.100: 10.0.1.0/31 (peer: 10.0.1.1) - VRF CustomerA
- Ethernet386.101: 10.0.1.2/31 (peer: 10.0.1.3) - VRF CustomerB
- Ethernet386.102: 10.0.1.4/31 (peer: 10.0.1.5) - VRF CustomerC

**Ethernet388** (10.0.2.x):
- Ethernet388.100: 10.0.2.0/31 (peer: 10.0.2.1) - VRF CustomerA
- Ethernet388.101: 10.0.2.2/31 (peer: 10.0.2.3) - VRF CustomerB
- Ethernet388.102: 10.0.2.4/31 (peer: 10.0.2.5) - VRF CustomerC

## Scenario 4: PortChannel with Multiple BGP Peers

Configure BGP peering over a PortChannel (LAG) interface.

### Configuration

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface PortChannel10 \
  --start-vlan-id 200 \
  --start-ip 172.16.0.0/31 \
  --count 3 \
  --vrf-prefix Transit \
  --vrf-start-number 10 \
  --print-cli
```

### Result

Creates 3 sub-interfaces on PortChannel10:
- Po10.200: 172.16.0.0/31 (peer: 172.16.0.1) - VRF Transit10
- Po10.201: 172.16.0.2/31 (peer: 172.16.0.3) - VRF Transit11
- Po10.202: 172.16.0.4/31 (peer: 172.16.0.5) - VRF Transit12

## Scenario 5: Complete BGP Setup with Configuration File

For complex setups, use a YAML configuration file.

### Create Configuration File (bgp_peers.yaml)

```yaml
sub_interfaces:
  - parent_interface: Ethernet0
    vlan_id: 100
    ip_address: 10.1.1.0/31
    ipv6_address: 2001:db8:1::0/127
    vrf_name: ISP_A
    admin_status: up
  
  - parent_interface: Ethernet0
    vlan_id: 101
    ip_address: 10.1.1.2/31
    ipv6_address: 2001:db8:1::2/127
    vrf_name: ISP_B
    admin_status: up
  
  - parent_interface: Ethernet1
    vlan_id: 200
    ip_address: 10.2.1.0/31
    ipv6_address: 2001:db8:2::0/127
    vrf_name: Customer_X
    admin_status: up
  
  - parent_interface: Ethernet1
    vlan_id: 201
    ip_address: 10.2.1.2/31
    ipv6_address: 2001:db8:2::2/127
    vrf_name: Customer_Y
    admin_status: up
```

### Apply Configuration

```bash
python3 configure_vrf_subinterfaces.py \
  --config bgp_peers.yaml \
  --output-cli configure_bgp_interfaces.sh \
  --print-cli
```

### View Neighbor Information

The script automatically shows you the BGP peer IPs:

```
  Ethernet0.100
    Parent: Ethernet0
    VLAN ID: 100
    IPv4: 10.1.1.0/31
    IPv4 Neighbor: 10.1.1.1/31 (point-to-point /31)
    IPv6: 2001:db8:1::0/127
    IPv6 Neighbor: 2001:db8:1::1/127 (point-to-point /127)
    VRF: ISP_A
```

## Best Practices for BGP with VRF Sub-Interfaces

1. **Use /31 for IPv4**: Maximizes IP efficiency (RFC 3021)
2. **Use /127 for IPv6**: Recommended for point-to-point links (RFC 6164)
3. **Separate VRFs per Customer**: Provides isolation and security
4. **Consistent VLAN Numbering**: Use a logical scheme (e.g., VLAN 100-199 for customers)
5. **Document Peer IPs**: The script's summary output helps with documentation

## Quick Reference: BGP Peer IP Calculation

For /31 networks, the script automatically handles the pairing:
- `x.x.x.0/31` → Peer is `x.x.x.1`
- `x.x.x.2/31` → Peer is `x.x.x.3`
- `x.x.x.4/31` → Peer is `x.x.x.5`
- Pattern: Even IP is local, odd IP is peer (or vice versa)

The script shows both IPs in the summary, making BGP configuration straightforward!

## Automated BGP Configuration Generation

For even faster deployment, use the `generate_bgp_config.py` script to automatically generate BGP configuration from your sub-interface config:

```bash
# Generate BGP config with auto-incrementing AS numbers
python3 generate_bgp_config.py \
  --config examples/bgp_peers.yaml \
  --local-asn 65000 \
  --remote-asn-base 65100 \
  --output setup_bgp.sh

# Apply the BGP configuration
bash setup_bgp.sh
```

This automatically:
- Detects all neighbor IPs from /31 and /127 networks
- Creates BGP router instances for each VRF
- Configures both IPv4 and IPv6 address families
- Enables soft-reconfiguration for all neighbors

## Complete Workflow Example

```bash
# Step 1: Generate interface configuration
python3 configure_vrf_subinterfaces.py \
  --config examples/bgp_peers.yaml \
  --output-cli setup_interfaces.sh

# Step 2: Generate BGP configuration
python3 generate_bgp_config.py \
  --config examples/bgp_peers.yaml \
  --local-asn 65000 \
  --remote-asn-base 65100 \
  --output setup_bgp.sh

# Step 3: Apply configurations
sudo bash setup_interfaces.sh
sudo bash setup_bgp.sh

# Step 4: Verify
vtysh -c 'show bgp vrf all summary'
```

See `examples/BGP_QUICK_START.md` for detailed step-by-step instructions!

