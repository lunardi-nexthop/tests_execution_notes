# VRF Snake Configuration Generator for Single DUT

## Overview

The `generate_vrf_snake_1DUT.py` script generates SONiC JSON configuration files for single Device Under Test (DUT) snake topology tests. This configuration creates a loopback routing pattern within a single device using VRFs (Virtual Routing and Forwarding) to isolate traffic flows.

## What is a Snake Test?

A snake test is a network testing topology where traffic flows through multiple interfaces on a device in a serpentine (snake-like) pattern. Traffic enters one interface, gets routed internally through the device, and exits through another interface, which then loops back externally to re-enter the device, creating a continuous flow path.

## Topology

The script generates configurations based on the following architecture:

```
External Traffic Generator (IXIA)
    ↓ IXIA 1.1 (192.168.0.1/31)
    ↓
┌───────────────────────────────────┐
│         Single DUT Device         │
│                                   │
│  ┌─────────────────────────────┐ │
│  │ Vrf1                        │ │
│  │  - Ethernet0  (192.168.0.1) │ │──→ External loopback
│  │  - Ethernet8  (192.168.0.2) │ │←──
│  └─────────────────────────────┘ │
│                                   │
│  ┌─────────────────────────────┐ │
│  │ Vrf2                        │ │
│  │  - Ethernet24 (192.168.0.3) │ │──→ External loopback
│  │  - Ethernet16 (192.168.0.4) │ │←──
│  └─────────────────────────────┘ │
│                                   │
│  ... (Vrf3 - Vrf29)               │
│                                   │
│  ┌─────────────────────────────┐ │
│  │ Vrf31                       │ │
│  │  - Ethernet472              │ │──→ External loopback
│  │  - Ethernet480              │ │←──
│  └─────────────────────────────┘ │
│                                   │
│  ┌─────────────────────────────┐ │
│  │ Vrf32                       │ │
│  │  - Ethernet464              │ │
│  │  - Ethernet504              │ │──→ IXIA 2.1 (192.168.0.65/31)
│  └─────────────────────────────┘ │
└───────────────────────────────────┘
```

### Traffic Flow Pattern

- **Flow 1**: 192.168.0.1 → 192.168.0.65 (forward direction)
- **Flow 2**: 192.168.0.65 → 192.168.0.1 (reverse direction)

Traffic enters at IXIA 1.1, flows through all 32 VRFs in a snake pattern via external loopbacks, and exits at IXIA 2.1.

## Configuration Details

### Default Configuration (Single Flow Mode)

- **VRFs**: 32 VRFs (Vrf1 through Vrf32)
- **Interfaces per VRF**: 2 interfaces
- **Total Interfaces**: 64 interfaces
- **Interface Naming**: Ethernet0, Ethernet8, Ethernet16, Ethernet24, ... Ethernet504
- **Interface Increment**: 8 (each interface number increases by 8)
- **IP Addressing**: 192.168.0.x/31 (default, configurable)
- **MAC Addressing**: Sequential based on Ethernet number

### Interface Assignment Pattern

For each VRF (index 0-31):
- **First interface**: Ethernet{vrf_index * 16 + 0}
- **Second interface**: Ethernet{vrf_index * 16 + 8}

Examples:
- Vrf1: Ethernet0, Ethernet8
- Vrf2: Ethernet16, Ethernet24
- Vrf3: Ethernet32, Ethernet40
- Vrf32: Ethernet464, Ethernet504

### Static Routes

The script generates static routes to enable the snake traffic flow:

- **Vrf1**: One route (192.168.0.64/31) via Ethernet8
- **Vrf2-Vrf32**: Two routes each:
  - Route to 192.168.0.0/31 via first interface
  - Route to 192.168.0.64/31 via second interface

## Usage

### Basic Usage

```bash
./generate_vrf_snake_1DUT.py --output single_dut_snake.json
```

### Common Options

```bash
# Generate with IPv6 addresses
./generate_vrf_snake_1DUT.py --output snake_ipv6.json --include-ipv6

# Use custom base network
./generate_vrf_snake_1DUT.py --base-network 10.0.0 --output custom_snake.json

# Dual flow mode (advanced)
./generate_vrf_snake_1DUT.py --dual-flow --output dual_snake.json

# Dry run (preview without creating files)
./generate_vrf_snake_1DUT.py --dry-run
```

### Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--output` | `single_dut_snake.json` | Output file path |
| `--base-network` | `192.168.0` | Base IP network for interfaces |
| `--static-route-network` | `192.168` | Static route network base |
| `--base-mac` | `00:00:00:ab:00:00` | Base MAC address |
| `--include-ipv6` | `False` | Include IPv6 addresses (/127) |
| `--dual-flow` | `False` | Generate dual flow configuration |
| `--second-flow-network` | (varies) | Second flow IP network (dual-flow mode) |
| `--dry-run` | `False` | Preview without creating files |

## Output

The script generates a SONiC-compatible JSON configuration file with three main sections:

1. **INTERFACE**: Interface configurations with VRF assignments, IP addresses, and MAC addresses
2. **VRF**: VRF definitions
3. **STATIC_ROUTE**: Static routes for traffic forwarding

### Example Output Structure

```json
{
  "INTERFACE": {
    "Ethernet0": {
      "mac_addr": "00:00:00:ab:00:00",
      "vrf_name": "Vrf1"
    },
    "Ethernet0|192.168.0.0/31": {},
    ...
  },
  "VRF": {
    "Vrf1": {},
    ...
  },
  "STATIC_ROUTE": {
    "Vrf1|192.168.0.64/31": {
      "blackhole": "false",
      "distance": "0",
      "ifname": "Ethernet8",
      "nexthop": "192.168.0.3",
      "nexthop-vrf": "Vrf1"
    },
    ...
  }
}
```

## Use Cases

- **Performance Testing**: Measure throughput and latency across multiple VRFs
- **Scale Testing**: Validate device behavior with 32 VRFs and 64 interfaces
- **VRF Isolation Testing**: Verify traffic isolation between VRFs
- **Routing Validation**: Test static route functionality in VRF context

## Notes

- External loopback cables are required to connect interface pairs for the snake topology
- The configuration assumes /31 subnets (point-to-point links)
- MAC addresses are automatically generated based on interface numbers
- IPv6 support is optional and uses /127 subnets when enabled

