# BGP Quick Start Guide

## Complete Workflow: From Zero to BGP Peering

This guide shows you how to set up BGP peering using VRF sub-interfaces with /31 point-to-point networks.

---

## Step 1: Generate Sub-Interface Configuration

### Option A: Using Command Line (Quick Setup)

For a single BGP peer:

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.0/31 \
  --ipv6-address 2001:db8::0/127 \
  --vrf-name Customer1 \
  --output-cli setup_interfaces.sh
```

For multiple BGP peers:

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.0/31 \
  --start-ipv6 2001:db8::0/127 \
  --count 5 \
  --vrf-prefix Customer \
  --output-cli setup_interfaces.sh
```

### Option B: Using YAML Configuration File

Create `my_bgp_peers.yaml`:

```yaml
sub_interfaces:
  - parent_interface: Ethernet0
    vlan_id: 100
    ip_address: 10.0.0.0/31
    ipv6_address: 2001:db8::0/127
    vrf_name: Customer1
    admin_status: up
  
  - parent_interface: Ethernet0
    vlan_id: 101
    ip_address: 10.0.0.2/31
    ipv6_address: 2001:db8::2/127
    vrf_name: Customer2
    admin_status: up
```

Generate configuration:

```bash
python3 configure_vrf_subinterfaces.py \
  --config my_bgp_peers.yaml \
  --output-cli setup_interfaces.sh
```

---

## Step 2: Review the Configuration

The script shows you the neighbor IPs automatically:

```
  Ethernet0.100
    Parent: Ethernet0
    VLAN ID: 100
    IPv4: 10.0.0.0/31
    IPv4 Neighbor: 10.0.0.1/31 (point-to-point /31)
    IPv6: 2001:db8::0/127
    IPv6 Neighbor: 2001:db8::1/127 (point-to-point /127)
    VRF: Customer1
```

**Key Information:**
- **Your Router**: 10.0.0.0/31 and 2001:db8::0/127
- **BGP Peer**: 10.0.0.1/31 and 2001:db8::1/127

---

## Step 3: Apply Interface Configuration

```bash
# Make the script executable
chmod +x setup_interfaces.sh

# Apply the configuration
sudo bash setup_interfaces.sh
```

---

## Step 4: Configure BGP

Now configure BGP using the neighbor IPs shown in Step 2:

```bash
vtysh
configure terminal

# Create BGP instance for the VRF
router bgp 65000 vrf Customer1
  # Configure IPv4 neighbor (use the neighbor IP from Step 2)
  neighbor 10.0.0.1 remote-as 65001
  neighbor 10.0.0.1 description Customer1-IPv4
  
  # Configure IPv6 neighbor
  neighbor 2001:db8::1 remote-as 65001
  neighbor 2001:db8::1 description Customer1-IPv6
  
  # Activate IPv4 address family
  address-family ipv4 unicast
    neighbor 10.0.0.1 activate
    neighbor 10.0.0.1 soft-reconfiguration inbound
  exit-address-family
  
  # Activate IPv6 address family
  address-family ipv6 unicast
    neighbor 2001:db8::1 activate
    neighbor 2001:db8::1 soft-reconfiguration inbound
  exit-address-family
exit

end
write memory
```

---

## Step 5: Verify BGP Peering

```bash
# Check all BGP neighbors across all VRFs
vtysh -c 'show bgp vrf all summary'

# Check specific VRF
vtysh -c 'show bgp vrf Customer1 summary'

# Check neighbor details
vtysh -c 'show bgp vrf Customer1 neighbors 10.0.0.1'

# Check received routes
vtysh -c 'show bgp vrf Customer1 ipv4 unicast'
vtysh -c 'show bgp vrf Customer1 ipv6 unicast'
```

---

## Real-World Example: Multiple Customers

### Scenario
You have 3 customers, each needs BGP peering on Ethernet0 with different VLANs.

### Step 1: Generate Configuration

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.0/31 \
  --start-ipv6 2001:db8::0/127 \
  --count 3 \
  --vrf-list CustomerA,CustomerB,CustomerC \
  --output-cli setup_3customers.sh \
  --print-cli
```

### Step 2: Note the Neighbor IPs

From the output:
- **CustomerA**: Your IP: 10.0.0.0/31, Peer: 10.0.0.1/31
- **CustomerB**: Your IP: 10.0.0.2/31, Peer: 10.0.0.3/31
- **CustomerC**: Your IP: 10.0.0.4/31, Peer: 10.0.0.5/31

### Step 3: Apply Configuration

```bash
sudo bash setup_3customers.sh
```

### Step 4: Configure BGP for All Customers

```bash
vtysh << EOF
configure terminal

router bgp 65000 vrf CustomerA
  neighbor 10.0.0.1 remote-as 65101
  neighbor 10.0.0.1 description CustomerA
  address-family ipv4 unicast
    neighbor 10.0.0.1 activate
  exit-address-family
exit

router bgp 65000 vrf CustomerB
  neighbor 10.0.0.3 remote-as 65102
  neighbor 10.0.0.3 description CustomerB
  address-family ipv4 unicast
    neighbor 10.0.0.3 activate
  exit-address-family
exit

router bgp 65000 vrf CustomerC
  neighbor 10.0.0.5 remote-as 65103
  neighbor 10.0.0.5 description CustomerC
  address-family ipv4 unicast
    neighbor 10.0.0.5 activate
  exit-address-family
exit

end
write memory
EOF
```

---

## Troubleshooting

### BGP Neighbor Not Coming Up

1. **Check interface status:**
   ```bash
   show interface Ethernet0.100
   ```

2. **Verify IP addressing:**
   ```bash
   show ip interface Ethernet0.100
   ```

3. **Check VRF binding:**
   ```bash
   show vrf
   ```

4. **Verify BGP configuration:**
   ```bash
   vtysh -c 'show running-config' | grep -A 20 "router bgp"
   ```

5. **Check connectivity:**
   ```bash
   ping -I Ethernet0.100 10.0.0.1
   ```

---

## Summary

The script makes BGP setup easy by:
1. ✅ Automatically detecting /31 and /127 networks
2. ✅ Showing you the neighbor IP addresses
3. ✅ Generating ready-to-use configuration scripts
4. ✅ Handling VRF isolation automatically

You just need to:
1. Run the script to generate interface config
2. Apply the interface configuration
3. Configure BGP with the neighbor IPs shown by the script
4. Verify peering is up!

