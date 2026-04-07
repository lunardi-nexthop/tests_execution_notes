# Complete BGP Setup Example - Start to Finish

This document walks through a complete real-world BGP setup using the VRF sub-interface scripts.

## Scenario

You need to set up BGP peering with 3 ISPs on a single physical interface (Ethernet0), each in their own VRF for routing isolation. You'll use /31 point-to-point networks for efficient IP addressing.

---

## Step 1: Create Configuration File

Create `my_isps.yaml`:

```yaml
sub_interfaces:
  - parent_interface: Ethernet0
    vlan_id: 100
    ip_address: 192.168.1.0/31
    ipv6_address: 2001:db8:1::0/127
    vrf_name: ISP_A
    admin_status: up
  
  - parent_interface: Ethernet0
    vlan_id: 101
    ip_address: 192.168.1.2/31
    ipv6_address: 2001:db8:1::2/127
    vrf_name: ISP_B
    admin_status: up
  
  - parent_interface: Ethernet0
    vlan_id: 102
    ip_address: 192.168.1.4/31
    ipv6_address: 2001:db8:1::4/127
    vrf_name: ISP_C
    admin_status: up
```

---

## Step 2: Generate Interface Configuration

```bash
python3 configure_vrf_subinterfaces.py \
  --config my_isps.yaml \
  --output-cli setup_interfaces.sh \
  --print-cli
```

**Output shows:**
```
  Ethernet0.100
    Parent: Ethernet0
    VLAN ID: 100
    IPv4: 192.168.1.0/31
    IPv4 Neighbor: 192.168.1.1/31 (point-to-point /31)
    IPv6: 2001:db8:1::0/127
    IPv6 Neighbor: 2001:db8:1::1/127 (point-to-point /127)
    VRF: ISP_A

  Ethernet0.101
    IPv4: 192.168.1.2/31
    IPv4 Neighbor: 192.168.1.3/31 (point-to-point /31)
    IPv6: 2001:db8:1::2/127
    IPv6 Neighbor: 2001:db8:1::3/127 (point-to-point /127)
    VRF: ISP_B

  Ethernet0.102
    IPv4: 192.168.1.4/31
    IPv4 Neighbor: 192.168.1.5/31 (point-to-point /31)
    IPv6: 2001:db8:1::4/127
    IPv6 Neighbor: 2001:db8:1::5/127 (point-to-point /127)
    VRF: ISP_C
```

**Key Information Extracted:**
| VRF | Your IPv4 | Peer IPv4 | Your IPv6 | Peer IPv6 |
|-----|-----------|-----------|-----------|-----------|
| ISP_A | 192.168.1.0/31 | 192.168.1.1 | 2001:db8:1::0/127 | 2001:db8:1::1 |
| ISP_B | 192.168.1.2/31 | 192.168.1.3 | 2001:db8:1::2/127 | 2001:db8:1::3 |
| ISP_C | 192.168.1.4/31 | 192.168.1.5 | 2001:db8:1::4/127 | 2001:db8:1::5 |

---

## Step 3: Generate BGP Configuration

```bash
python3 generate_bgp_config.py \
  --config my_isps.yaml \
  --local-asn 65000 \
  --remote-asn-base 65100 \
  --output setup_bgp.sh
```

This automatically creates BGP configuration using the neighbor IPs detected in Step 2!

---

## Step 4: Review Generated Scripts

### Interface Configuration (`setup_interfaces.sh`):
```bash
#!/bin/bash
# Create VRFs
config vrf add ISP_A
config vrf add ISP_B
config vrf add ISP_C

# Configure Ethernet0.100
config subinterface add Ethernet0.100 100
config interface vrf bind Ethernet0.100 ISP_A
config interface ip add Ethernet0.100 192.168.1.0/31
config interface ip add Ethernet0.100 2001:db8:1::0/127
config interface startup Ethernet0.100

# ... (similar for .101 and .102)
```

### BGP Configuration (`setup_bgp.sh`):
```bash
#!/bin/bash
vtysh << 'EOF'
configure terminal

router bgp 65000 vrf ISP_A
  neighbor 192.168.1.1 remote-as 65100
  neighbor 192.168.1.1 description ISP_A-Ethernet0.100-IPv4
  neighbor 2001:db8:1::1 remote-as 65100
  neighbor 2001:db8:1::1 description ISP_A-Ethernet0.100-IPv6
  address-family ipv4 unicast
    neighbor 192.168.1.1 activate
    neighbor 192.168.1.1 soft-reconfiguration inbound
  exit-address-family
  address-family ipv6 unicast
    neighbor 2001:db8:1::1 activate
    neighbor 2001:db8:1::1 soft-reconfiguration inbound
  exit-address-family
exit

# ... (similar for ISP_B and ISP_C)
```

---

## Step 5: Apply Configurations

```bash
# Apply interface configuration
sudo bash setup_interfaces.sh

# Wait a moment for interfaces to come up
sleep 2

# Apply BGP configuration
sudo bash setup_bgp.sh
```

---

## Step 6: Verify Configuration

### Check Interfaces
```bash
show interface Ethernet0.100
show interface Ethernet0.101
show interface Ethernet0.102
```

### Check IP Addresses
```bash
show ip interface | grep Ethernet0
```

Expected output:
```
Ethernet0.100    192.168.1.0/31      ISP_A
Ethernet0.101    192.168.1.2/31      ISP_B
Ethernet0.102    192.168.1.4/31      ISP_C
```

### Check VRFs
```bash
show vrf
```

### Check BGP Summary
```bash
vtysh -c 'show bgp vrf all summary'
```

Expected output:
```
VRF ISP_A:
Neighbor        V    AS MsgRcvd MsgSent   Up/Down State
192.168.1.1     4 65100       0       0  00:00:05 Established
2001:db8:1::1   6 65100       0       0  00:00:05 Established

VRF ISP_B:
Neighbor        V    AS MsgRcvd MsgSent   Up/Down State
192.168.1.3     4 65101       0       0  00:00:05 Established
...
```

---

## Step 7: Test Connectivity

```bash
# Ping IPv4 neighbors
ping -I Ethernet0.100 192.168.1.1
ping -I Ethernet0.101 192.168.1.3
ping -I Ethernet0.102 192.168.1.5

# Ping IPv6 neighbors
ping6 -I Ethernet0.100 2001:db8:1::1
```

---

## Troubleshooting

### BGP Neighbors Not Establishing

1. **Check interface status:**
   ```bash
   show interface Ethernet0.100
   ```

2. **Verify IP connectivity:**
   ```bash
   ping -I Ethernet0.100 192.168.1.1
   ```

3. **Check BGP configuration:**
   ```bash
   vtysh -c 'show running-config' | grep -A 30 "router bgp 65000 vrf ISP_A"
   ```

4. **Check BGP neighbor details:**
   ```bash
   vtysh -c 'show bgp vrf ISP_A neighbors 192.168.1.1'
   ```

---

## Summary

You've successfully:
- ✅ Created 3 VRF sub-interfaces with /31 and /127 networks
- ✅ Automatically detected all BGP neighbor IPs
- ✅ Generated and applied interface configuration
- ✅ Generated and applied BGP configuration
- ✅ Verified BGP peering is established

**Total time:** ~5 minutes (vs. hours of manual configuration!)

**Key Benefits:**
- No manual IP calculation for /31 pairs
- Automatic neighbor detection
- VRF isolation for security
- Dual-stack IPv4/IPv6 support
- Ready-to-use configuration scripts

