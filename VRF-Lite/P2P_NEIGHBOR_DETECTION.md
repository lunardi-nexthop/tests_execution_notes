# Point-to-Point Neighbor Detection

## Overview

The script now includes intelligent detection and handling of point-to-point networks:
- **IPv4 /31 networks** (RFC 3021) - 2 usable host addresses
- **IPv6 /127 networks** (RFC 6164) - 2 usable host addresses

## Features

### 1. Automatic Neighbor Detection

The script automatically detects when you're using /31 or /127 networks and shows you the neighboring host IP address.

**Example:**
```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.0/31 \
  --ipv6-address fc00::0/127 \
  --vrf-name Vrf1
```

**Output:**
```
  Ethernet0.100
    Parent: Ethernet0
    VLAN ID: 100
    IPv4: 10.0.0.0/31
    IPv4 Neighbor: 10.0.0.1/31 (point-to-point /31)
    IPv6: fc00::0/127
    IPv6 Neighbor: fc00::1/127 (point-to-point /127)
    VRF: Vrf1
```

### 2. Automatic IP Normalization

When you provide an IP address that's part of a /31 or /127 network, the script automatically normalizes it to the base IP of the pair.

**Example:**
- Input: `10.0.0.1/31` → Normalized to: `10.0.0.0/31`
- Input: `fc00::1/127` → Normalized to: `fc00::/127`

This ensures consistent IP allocation when using bulk mode.

### 3. Helper Functions

Three new helper functions are available:

#### `get_point_to_point_neighbor(ip_with_prefix)`
Returns the neighboring IP address for /31 or /127 networks.

```python
>>> get_point_to_point_neighbor("10.0.0.0/31")
"10.0.0.1/31"

>>> get_point_to_point_neighbor("10.0.0.1/31")
"10.0.0.0/31"

>>> get_point_to_point_neighbor("fc00::0/127")
"fc00::1/127"
```

#### `is_point_to_point_network(ip_with_prefix)`
Checks if an IP address is part of a point-to-point network.

```python
>>> is_point_to_point_network("10.0.0.0/31")
True

>>> is_point_to_point_network("10.0.0.0/24")
False
```

#### `get_network_base_ip(ip_with_prefix)`
Returns the base (first) IP address of a point-to-point network.

```python
>>> get_network_base_ip("10.0.0.1/31")
"10.0.0.0/31"

>>> get_network_base_ip("fc00::1/127")
"fc00::/127"
```

### 4. SubInterfaceConfig Methods

Each `SubInterfaceConfig` object now has methods to work with point-to-point networks:

- `get_neighbor_ipv4()` - Get the neighboring IPv4 address
- `get_neighbor_ipv6()` - Get the neighboring IPv6 address
- `is_ipv4_point_to_point()` - Check if IPv4 is /31
- `is_ipv6_point_to_point()` - Check if IPv6 is /127

## Usage Examples

### Example 1: Single Interface with /31 and /127

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --vlan-id 100 \
  --ip-address 10.0.0.0/31 \
  --ipv6-address fc00::0/127 \
  --vrf-name Vrf1 \
  --print-cli
```

### Example 2: Multiple Interfaces with 3rd Octet Increment

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface-list Ethernet384,Ethernet386,Ethernet388 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.0/31 \
  --start-ipv6 fc00::0/127 \
  --count 3 \
  --vrf-list Vrf1,Vrf2,Vrf3 \
  --ip-octet3-increment \
  --ipv6-segment-increment \
  --print-cli
```

This creates:
- Ethernet384: 10.0.0.0/31, 10.0.0.2/31, 10.0.0.4/31
- Ethernet386: 10.0.1.0/31, 10.0.1.2/31, 10.0.1.4/31
- Ethernet388: 10.0.2.0/31, 10.0.2.2/31, 10.0.2.4/31

### Example 3: Using the "Other" IP in the Pair

If you accidentally provide the second IP in a /31 pair, the script normalizes it:

```bash
python3 configure_vrf_subinterfaces.py \
  --parent-interface Ethernet0 \
  --start-vlan-id 100 \
  --start-ip 10.0.0.1/31 \
  --count 3
```

**Output:**
```
INFO: Detected /31 point-to-point network
      Starting IP: 10.0.0.1/31
      Neighbor IP: 10.0.0.0/31
      Normalized to base IP: 10.0.0.0/31
```

The script will use 10.0.0.0/31, 10.0.0.2/31, 10.0.0.4/31 (properly incrementing by 2).

## Testing

Run the test script to verify the functionality:

```bash
python3 test_p2p_neighbor.py
```

This tests all the helper functions and demonstrates the neighbor detection capabilities.

