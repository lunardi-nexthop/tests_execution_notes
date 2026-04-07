# BGP VRF Sub-Interface Examples

This directory contains practical examples for setting up BGP peering using VRF sub-interfaces with point-to-point /31 and /127 networks.

## Quick Demo

The fastest way to see the scripts in action:

```bash
# 1. Generate interface configuration
python3 ../configure_vrf_subinterfaces.py \
  --config simple_bgp_demo.yaml \
  --output-cli setup_demo_interfaces.sh \
  --print-cli

# 2. Generate BGP configuration (automatically detects neighbor IPs!)
python3 ../generate_bgp_config.py \
  --config simple_bgp_demo.yaml \
  --local-asn 65000 \
  --remote-asn-base 65100 \
  --output setup_demo_bgp.sh

# 3. View the generated configurations
cat setup_demo_interfaces.sh
cat setup_demo_bgp.sh
```

## Example Files

### 1. `simple_bgp_demo.yaml`
Simple 3-ISP uplink configuration on a single interface.

**What it creates:**
- 3 sub-interfaces on Ethernet0 (VLANs 100-102)
- 3 VRFs (ISP1, ISP2, ISP3)
- /31 point-to-point networks for efficient IP usage

**Usage:**
```bash
python3 ../configure_vrf_subinterfaces.py --config simple_bgp_demo.yaml
```

### 2. `bgp_peers.yaml`
Complete multi-interface BGP setup with ISPs, customers, and transit providers.

**What it creates:**
- ISP uplinks on Ethernet0
- Customer peering on Ethernet1
- Transit providers on PortChannel10
- Both IPv4 (/31) and IPv6 (/127) addressing

**Usage:**
```bash
python3 ../configure_vrf_subinterfaces.py --config bgp_peers.yaml --print-cli
python3 ../generate_bgp_config.py --config bgp_peers.yaml --local-asn 65000 --remote-asn-base 65100
```

### 3. `configure_bgp_peers.sh`
Manually crafted BGP configuration script showing advanced features like:
- Route maps
- Prefix lists
- Per-neighbor policies

**Usage:**
```bash
# First apply interface configuration, then:
bash configure_bgp_peers.sh
```

## Documentation

- **`BGP_QUICK_START.md`** - Step-by-step guide from zero to working BGP
- **`../BGP_USAGE_EXAMPLES.md`** - Comprehensive usage scenarios
- **`../P2P_NEIGHBOR_DETECTION.md`** - Technical details on /31 and /127 handling

## Common Workflows

### Workflow 1: Quick Single Peer Setup

```bash
# One command to create interface config
python3 ../configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.0/31 \
  --vrf-name Customer1 \
  --output-cli setup.sh

# Apply it
sudo bash setup.sh

# Configure BGP manually using the neighbor IP shown in the summary
# (The script tells you the neighbor is 10.0.0.1/31)
```

### Workflow 2: Multiple Peers with Auto-Generated BGP

```bash
# Create YAML config file (see simple_bgp_demo.yaml as template)
# Then generate everything:

python3 ../configure_vrf_subinterfaces.py \
  --config my_peers.yaml \
  --output-cli setup_interfaces.sh

python3 ../generate_bgp_config.py \
  --config my_peers.yaml \
  --local-asn 65000 \
  --remote-asn-base 65100 \
  --output setup_bgp.sh

# Apply both
sudo bash setup_interfaces.sh
sudo bash setup_bgp.sh
```

### Workflow 3: Bulk Creation with Command Line

```bash
# Create 10 BGP peers in one command
python3 ../configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.0/31 \
  --count 10 \
  --vrf-prefix Customer \
  --output-cli setup_10_peers.sh

# The script automatically:
# - Uses /31 networks (10.0.0.0/31, 10.0.0.2/31, 10.0.0.4/31, ...)
# - Shows you all neighbor IPs
# - Creates VRFs (Customer1, Customer2, ..., Customer10)
```

## Key Features Demonstrated

### ✅ Automatic Neighbor Detection
The scripts automatically detect and show you the BGP peer IP for /31 and /127 networks:

```
  Ethernet0.100
    IPv4: 10.0.0.0/31
    IPv4 Neighbor: 10.0.0.1/31 (point-to-point /31)
```

### ✅ IP Normalization
If you provide `10.0.0.1/31`, the script normalizes it to `10.0.0.0/31` and increments correctly.

### ✅ Dual-Stack Support
All examples support both IPv4 (/31) and IPv6 (/127) addressing.

### ✅ VRF Isolation
Each BGP peer gets its own VRF for complete routing isolation.

## Verification Commands

After applying configurations:

```bash
# Check interfaces
show interface status
show ip interface

# Check VRFs
show vrf

# Check BGP
vtysh -c 'show bgp vrf all summary'
vtysh -c 'show bgp vrf ISP1 neighbors'
vtysh -c 'show bgp vrf ISP1 ipv4 unicast'

# Test connectivity
ping -I Ethernet0.100 192.168.1.1
```

## Tips

1. **Always review before applying** - Use `--print-cli` to see what will be configured
2. **Start small** - Test with one peer before scaling to many
3. **Use YAML for complex setups** - Easier to maintain than long command lines
4. **Let the script calculate neighbors** - Don't manually figure out /31 pairs
5. **Save your configs** - Keep the YAML files in version control

## Need Help?

See the main documentation:
- `BGP_QUICK_START.md` - Complete walkthrough
- `../P2P_NEIGHBOR_DETECTION.md` - How /31 and /127 detection works
- `../BGP_USAGE_EXAMPLES.md` - More scenarios and examples

