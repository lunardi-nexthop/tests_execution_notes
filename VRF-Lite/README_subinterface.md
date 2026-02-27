# VRF Sub-Interface Configuration Script

A flexible Python script to easily configure VRF-enabled sub-interfaces on SONiC devices.

## Why Use This Script?

**No YAML files required!** This script provides a powerful CLI interface for quick configurations:

- 🚀 **One-liner configurations** - No need to create YAML files for simple setups
- 📈 **Bulk operations** - Create 100+ sub-interfaces with a single command
- 🔢 **Auto-increment** - Automatically increment VLAN IDs, IP addresses, and VRF names
- 🎯 **Multiple modes** - CLI arguments, interactive prompts, or config files (your choice)
- 🧹 **Automatic cleanup** - Generates removal scripts for easy teardown

## Features

- ✅ **Quick CLI mode** - Single command for simple configurations (no YAML required!)
- ✅ **Bulk mode** - Auto-increment VLAN IDs, IPs, and VRF names
- ✅ **Interactive mode** - Guided prompts for easy setup
- ✅ **Config file support** - YAML or JSON (optional, not required)
- ✅ Generates SONiC config_db.json format
- ✅ Generates CLI commands for manual execution
- ✅ Generates removal scripts for cleanup
- ✅ Supports IPv4 and IPv6
- ✅ VRF binding support
- ✅ Works with physical interfaces and PortChannels

## Quick Start

### 1. Quick CLI Mode (Fastest - No YAML Required!)

**Single sub-interface:**
```bash
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.1/24 \
  --vrf-name Vrf1
```

**Multiple sub-interfaces with auto-increment:**
```bash
# Create 5 sub-interfaces on Ethernet0 with auto-incrementing VLANs and IPs
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 5 \
  --vrf-name Vrf1
```

**Bulk configuration across multiple interfaces:**
```bash
# Create sub-interfaces on multiple parent interfaces
python configure_vrf_subinterfaces.py \
  --parent-interface-list Ethernet384,Ethernet386,Ethernet388 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 3 \
  --vrf-prefix Vrf \
  --vrf-start-number 1
```

### 2. Interactive Mode (Guided)

```bash
python configure_vrf_subinterfaces.py --interactive
```

Follow the prompts to define your sub-interfaces.

### 3. Using YAML Configuration File (Optional)

Create a YAML file:

```yaml
sub_interfaces:
  - parent_interface: Ethernet0
    vlan_id: 100
    ip_address: 10.0.100.1/24
    vrf_name: Vrf1
    admin_status: up

  - parent_interface: Ethernet4
    vlan_id: 200
    ip_address: 10.0.200.1/24
    ipv6_address: fc00:200::1/64
    vrf_name: Vrf2
    admin_status: up
```

Generate configuration:

```bash
python configure_vrf_subinterfaces.py --config my_config.yaml
```

### 4. Using JSON Configuration File (Optional)

```bash
python configure_vrf_subinterfaces.py --config example_subinterfaces.json
```

## Configuration Parameters

### Quick CLI Mode Parameters

**Single Sub-Interface:**
| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--parent-interface` | ✅ Yes | Parent interface name | `Ethernet0`, `PortChannel10` |
| `--vlan-id` | ✅ Yes | VLAN ID (802.1Q tag) | `100`, `200` |
| `--ip-address` | ✅ Yes | IPv4 address with prefix | `10.0.0.1/24` |
| `--vrf-name` | ❌ No | VRF name (optional) | `Vrf1`, `Vrf2` |
| `--ipv6-address` | ❌ No | IPv6 address with prefix | `fc00::1/64` |
| `--admin-status` | ❌ No | Admin status (default: up) | `up`, `down` |

**Bulk Mode (Auto-Increment):**
| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--parent-interface` | One required | Single parent interface | `Ethernet0` |
| `--parent-interface-list` | One required | Comma-separated parent interfaces | `Ethernet384,Ethernet386` |
| `--start-vlan-id` | ✅ Yes | Starting VLAN ID | `100` |
| `--start-ip` | ✅ Yes | Starting IP address with prefix | `10.0.0.1/31` |
| `--count` | ❌ No | Number of sub-interfaces per parent (default: 1) | `5` |
| `--vlan-increment` | ❌ No | VLAN ID increment (default: 1) | `1`, `10` |
| `--ip-increment` | ❌ No | IP increment within same interface (default: 2 for /31) | `2`, `4` |
| `--ip-octet3-increment` | ❌ No | Increment 3rd octet by 1 for each parent interface | flag |
| `--vrf-name` | ❌ No | Single VRF for all sub-interfaces | `Vrf1` |
| `--vrf-list` | ❌ No | Comma-separated VRF names | `Vrf1,Vrf2,Vrf3` |
| `--vrf-prefix` | ❌ No | VRF name prefix for auto-generation | `Vrf` |
| `--vrf-start-number` | ❌ No | Starting number for VRF auto-gen (default: 1) | `1`, `100` |
| `--vrf-per-parent` | ❌ No | Restart VRF numbering per parent | flag |

### Config File Format (YAML/JSON)

Each sub-interface requires:

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `parent_interface` | ✅ Yes | Parent interface name | `Ethernet0`, `PortChannel10` |
| `vlan_id` | ✅ Yes | VLAN ID (802.1Q tag) | `100`, `200` |
| `ip_address` | ✅ Yes | IPv4 address with prefix | `10.0.0.1/24` |
| `vrf_name` | ❌ No | VRF name (optional) | `Vrf1`, `Vrf2` |
| `ipv6_address` | ❌ No | IPv6 address with prefix | `fc00::1/64` |
| `admin_status` | ❌ No | Admin status (default: up) | `up`, `down` |

## Output Options

### Generate All Outputs (Default)

By default, the script generates three files:

```bash
# Using CLI mode (no YAML required)
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.1/24 \
  --vrf-name Vrf1

# Or using config file
python configure_vrf_subinterfaces.py --config my_config.yaml
```

This creates:
- `subinterface_config.json` - SONiC config_db format
- `configure_subinterfaces.sh` - CLI commands to apply
- `remove_subinterfaces.sh` - CLI commands to remove

### Custom Output Files

```bash
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.1/24 \
  --output-json /tmp/my_config.json \
  --output-cli /tmp/apply.sh \
  --output-removal /tmp/cleanup.sh
```

### Print to Console

```bash
# Print config_db.json format
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.1/24 \
  --print-json

# Print CLI commands
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 5 \
  --print-cli

# Print removal commands
python configure_vrf_subinterfaces.py --interactive --print-removal
```

## Usage Examples

### Example 1: Simple Single Sub-Interface (CLI)

```bash
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 192.168.100.1/24 \
  --vrf-name CustomerA
```

### Example 2: Bulk Creation with Auto-Increment

```bash
# Create 10 sub-interfaces with auto-incrementing VLANs (100-109) and IPs
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 10 \
  --vrf-name Vrf1
```

### Example 3: Multiple VRFs with Auto-Generation

```bash
# Create 5 sub-interfaces, each in a different VRF (Vrf1, Vrf2, Vrf3, Vrf4, Vrf5)
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 5 \
  --vrf-prefix Vrf \
  --vrf-start-number 1
```

### Example 4: Multiple Parent Interfaces

```bash
# Create sub-interfaces on 3 different parent interfaces
python configure_vrf_subinterfaces.py \
  --parent-interface-list Ethernet384,Ethernet386,Ethernet388 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 3 \
  --vrf-list Vrf1,Vrf2,Vrf3
```

### Example 5: Multiple Interfaces with 3rd Octet Increment

```bash
# Create sub-interfaces where 3rd octet increments per interface
# Ethernet384: 10.0.0.x, Ethernet386: 10.0.1.x, Ethernet388: 10.0.2.x
python configure_vrf_subinterfaces.py \
  --parent-interface-list Ethernet384,Ethernet386,Ethernet388 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 3 \
  --vrf-list Vrf1,Vrf2,Vrf3 \
  --ip-octet3-increment
```

**Result:**
- **Ethernet384**: Vrf1=10.0.0.1/31, Vrf2=10.0.0.3/31, Vrf3=10.0.0.5/31
- **Ethernet386**: Vrf1=10.0.1.1/31, Vrf2=10.0.1.3/31, Vrf3=10.0.1.5/31
- **Ethernet388**: Vrf1=10.0.2.1/31, Vrf2=10.0.2.3/31, Vrf3=10.0.2.5/31

The 3rd octet increments by 1 for each interface, while the 4th octet increments by 2 (for /31) for each VRF within the same interface.

### Example 6: Dual-Stack (IPv4 + IPv6) - Using Config File

```yaml
sub_interfaces:
  - parent_interface: Ethernet0
    vlan_id: 100
    ip_address: 10.0.100.1/24
    ipv6_address: fc00:100::1/64
    vrf_name: Vrf1
```

```bash
python configure_vrf_subinterfaces.py --config dual_stack.yaml
```

### Example 7: PortChannel Sub-Interfaces

```bash
python configure_vrf_subinterfaces.py \
  --parent-interface PortChannel10 \
  --vlan-id 100 \
  --ip-address 10.0.100.1/24 \
  --vrf-name Vrf1
```

## Applying Configuration

### Method 1: Using config_db.json

```bash
# Generate config
python configure_vrf_subinterfaces.py --config my_config.yaml

# Copy to DUT and apply
scp subinterface_config.json admin@sonic-dut:/tmp/
ssh admin@sonic-dut "sonic-cfggen -j /tmp/subinterface_config.json --write-to-db"
```

### Method 2: Using CLI Commands

```bash
# Generate CLI script
python configure_vrf_subinterfaces.py --config my_config.yaml

# Copy and execute on DUT
scp configure_subinterfaces.sh admin@sonic-dut:/tmp/
ssh admin@sonic-dut "bash /tmp/configure_subinterfaces.sh"
```

## Removing Configuration

```bash
# Use the generated removal script
scp remove_subinterfaces.sh admin@sonic-dut:/tmp/
ssh admin@sonic-dut "bash /tmp/remove_subinterfaces.sh"
```

## Complete Workflow Examples

### Workflow 1: Quick CLI Mode (No YAML Required)

```bash
# 1. Generate configuration using CLI arguments
python configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 5 \
  --vrf-name Vrf1

# 2. Review the generated files
cat subinterface_config.json
cat configure_subinterfaces.sh

# 3. Apply to DUT
scp configure_subinterfaces.sh admin@10.0.0.1:/tmp/
ssh admin@10.0.0.1 "bash /tmp/configure_subinterfaces.sh"

# 4. Verify
ssh admin@10.0.0.1 "show interface status | grep '\\.'"
ssh admin@10.0.0.1 "show vrf"
```

### Workflow 2: Using Config File (Optional)

```bash
# 1. Create configuration file
cat > my_subints.yaml << EOF
sub_interfaces:
  - parent_interface: Ethernet0
    vlan_id: 100
    ip_address: 10.0.100.1/24
    vrf_name: Vrf1
  - parent_interface: Ethernet0
    vlan_id: 200
    ip_address: 10.0.200.1/24
    vrf_name: Vrf2
EOF

# 2. Generate all outputs
python configure_vrf_subinterfaces.py --config my_subints.yaml

# 3. Review the configuration
cat subinterface_config.json

# 4. Apply to DUT
scp configure_subinterfaces.sh admin@10.0.0.1:/tmp/
ssh admin@10.0.0.1 "bash /tmp/configure_subinterfaces.sh"

# 5. Verify
ssh admin@10.0.0.1 "show interface status | grep '\\.'"
ssh admin@10.0.0.1 "show vrf"
```

## Tips

1. **No YAML required**: Use CLI arguments for quick configurations - YAML/JSON files are optional
2. **Bulk operations**: Use `--start-vlan-id`, `--start-ip`, and `--count` for creating multiple sub-interfaces at once
3. **Auto-increment**: IP addresses and VLAN IDs automatically increment based on `--ip-increment` and `--vlan-increment`
4. **VRF auto-generation**: Use `--vrf-prefix` to automatically generate VRF names (e.g., Vrf1, Vrf2, Vrf3...)
5. **Remove parent from VLAN first**: Before creating sub-interfaces, remove the parent interface from any VLAN membership
6. **VLAN ID matching**: The VLAN ID in the sub-interface name must match the 802.1Q tag
7. **VRF creation**: VRFs are automatically created if they don't exist
8. **Testing**: Always test in a lab environment first

## Troubleshooting

### Check if sub-interfaces were created
```bash
show interface status | grep "\."
```

### Verify VRF binding
```bash
show vrf
```

### Check config_db
```bash
redis-cli -n 4 keys "VLAN_SUB_INTERFACE|*"
```

### View specific sub-interface config
```bash
redis-cli -n 4 hgetall "VLAN_SUB_INTERFACE|Ethernet0.100"
```

