#!/usr/bin/env python3
"""
Script to generate SONiC JSON configuration files for single DUT snake tests.
Based on the vrf3.json pattern with 32 VRFs, 2 interfaces per VRF.
Supports simple loopback routing within a single device.
"""

import json
import argparse
import sys
import ipaddress
from collections import OrderedDict


def generate_mac_address(base_mac, ethernet_num):
    """Generate MAC address based on base MAC and ethernet number."""
    # Convert base MAC to integer, add ethernet number, convert back
    mac_parts = base_mac.split(':')
    mac_int = int(''.join(mac_parts), 16)
    new_mac_int = mac_int + ethernet_num
    new_mac_hex = f"{new_mac_int:012x}"
    return ':'.join([new_mac_hex[i:i+2] for i in range(0, 12, 2)])


def generate_single_dut_snake_config(output_file, base_network, static_route_network,
                                   include_ipv6, base_mac, dual_flow=False, second_flow_network="172.16.0",
                                   num_interfaces=64):
    """Generate SONiC configuration for single DUT snake test (like vrf3.json pattern)."""

    # Calculate number of VRFs based on interfaces
    if dual_flow:
        interfaces_per_vrf = 4
    else:
        interfaces_per_vrf = 2

    num_vrfs = num_interfaces // interfaces_per_vrf

    if num_interfaces % interfaces_per_vrf != 0:
        print(f"Warning: num_interfaces ({num_interfaces}) is not evenly divisible by interfaces_per_vrf ({interfaces_per_vrf})")
        print(f"Will create {num_vrfs} VRFs with {interfaces_per_vrf} interfaces each = {num_vrfs * interfaces_per_vrf} total interfaces")

    if dual_flow:
        print(f"Generating dual-flow single DUT snake test configuration")
        print(f"{num_vrfs} VRFs, 4 interfaces per VRF (2 flows)")
        print(f"Total interfaces: {num_interfaces}")
        print(f"First flow: Ethernet0,8,16,24... with {base_network}.x IPs")
        print(f"Second flow: Ethernet4,12,20,28... with {second_flow_network}.x IPs")
    else:
        print(f"Generating single DUT snake test configuration")
        print(f"{num_vrfs} VRFs, 2 interfaces per VRF (single flow)")
        print(f"Total interfaces: {num_interfaces}")
        print(f"Interface increment: 8")

    config = OrderedDict()
    config['INTERFACE'] = OrderedDict()
    config['VRF'] = OrderedDict()
    config['STATIC_ROUTE'] = OrderedDict()

    # Store VRF interface information for static route generation
    vrf_interfaces = {}

    # Generate interfaces for all VRFs
    for vrf_index in range(num_vrfs):
        vrf_name = f"Vrf{vrf_index + 1}"

        # Add VRF to VRF section
        config['VRF'][vrf_name] = {}
        vrf_interfaces[vrf_name] = []

        if dual_flow:
            # Generate 4 interfaces per VRF (2 flows × 2 interfaces each)
            interfaces_per_flow = 2
            total_interfaces = 4
        else:
            # Generate 2 interfaces per VRF (single flow)
            interfaces_per_flow = 2
            total_interfaces = 2

        for interface_index in range(total_interfaces):
            if dual_flow:
                # Dual flow mode: alternate between flows
                if interface_index < 2:
                    # First flow: Ethernet0,8,16,24... using base_network (interface_index 0,1)
                    flow_index = 0
                    flow_interface_index = interface_index
                    ethernet_num = vrf_index * 16 + flow_interface_index * 8
                    current_network = base_network
                else:
                    # Second flow: Ethernet4,12,20,28... using second_flow_network (interface_index 2,3)
                    flow_index = 1
                    flow_interface_index = interface_index - 2
                    ethernet_num = vrf_index * 16 + 4 + flow_interface_index * 8
                    current_network = second_flow_network
            else:
                # Single flow mode: original pattern
                ethernet_num = vrf_index * 16 + interface_index * 8
                current_network = base_network
                flow_index = 0
                flow_interface_index = interface_index

            interface_name = f"Ethernet{ethernet_num}"

            # Generate MAC address (Ethernet number directly corresponds to MAC)
            mac_addr = generate_mac_address(base_mac, ethernet_num)

            # Add interface with VRF assignment and MAC address
            config['INTERFACE'][interface_name] = {
                "mac_addr": mac_addr,
                "vrf_name": vrf_name
            }

            # Calculate IP address based on flow and VRF
            if dual_flow and flow_index == 1:
                # Second flow (second_flow_network): different IP pattern
                if vrf_index == 0:  # Vrf1 special case
                    host_num = flow_interface_index * 2  # 0, 2
                else:
                    # For other VRFs: start at 3 and allocate 2 consecutive numbers per VRF
                    base_host = 3 + (vrf_index - 1) * 2
                    host_num = base_host + flow_interface_index
            else:
                # First flow (base_network): original pattern
                if vrf_index == 0:  # Vrf1 special case
                    host_num = flow_interface_index * 2  # 0, 2
                else:
                    # For other VRFs: start at 3 and allocate 2 consecutive numbers per VRF
                    base_host = 3 + (vrf_index - 1) * 2
                    host_num = base_host + flow_interface_index

            # Create IP address
            ip_address = f"{current_network}.{host_num}/31"
            ip_key = f"{interface_name}|{ip_address}"
            config['INTERFACE'][ip_key] = {}

            # Add IPv6 address if requested
            if include_ipv6:
                if dual_flow and flow_index == 1:
                    # Second flow IPv6: use different prefix
                    ipv6_address = f"2001:{current_network.replace('.', ':')}::{host_num}/127"
                else:
                    # First flow IPv6: original pattern
                    ipv6_address = f"2000:{current_network.replace('.', ':')}::{host_num}/127"
                ipv6_key = f"{interface_name}|{ipv6_address}"
                config['INTERFACE'][ipv6_key] = {}

            # Store interface info for static route generation
            vrf_interfaces[vrf_name].append({
                'interface_name': interface_name,
                'ip_address': ip_address,
                'host_num': host_num,
                'flow_index': flow_index if dual_flow else 0,
                'network': current_network
            })

    # Generate static routes for single DUT snake test
    print("Generating static routes...")
    generate_single_dut_static_routes(config, vrf_interfaces, static_route_network, dual_flow)

    # Write the configuration
    try:
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Calculate statistics
        total_interfaces = len([k for k in config['INTERFACE'].keys() if '|' not in k])
        total_static_routes = len(config['STATIC_ROUTE'])

        print(f"Successfully generated single DUT snake configuration.")
        print(f"Output file: {output_file}")
        print(f"VRFs created: {len(config['VRF'])}")
        print(f"Interfaces per VRF: 2")
        print(f"Total interfaces created: {total_interfaces}")
        print(f"Static routes created: {total_static_routes}")
        print(f"Base network used: {base_network}")

    except Exception as e:
        print(f"Error writing output file '{output_file}': {e}")
        sys.exit(1)


def generate_single_dut_static_routes(config, vrf_interfaces, static_route_network, dual_flow=False):
    """Generate static routes for single DUT snake test based on actual interface IPs."""

    # Find the lowest and highest host IPs across all VRFs to determine route destinations
    all_host_nums = []
    for vrf_name, interfaces in vrf_interfaces.items():
        for iface in interfaces:
            all_host_nums.append(iface['host_num'])

    if not all_host_nums:
        return

    min_host = min(all_host_nums)
    max_host = max(all_host_nums)

    # Calculate low and high route destinations
    # Low route: points to the minimum IP (typically 0)
    # High route: points to IP beyond the maximum used IP
    low_route_ip = min_host
    high_route_ip = max_host + 2  # +2 to get the next /31 subnet beyond the last interface

    for vrf_name, interfaces in vrf_interfaces.items():
        if dual_flow and len(interfaces) < 4:
            continue  # Need at least 4 interfaces for dual flow
        elif not dual_flow and len(interfaces) < 2:
            continue  # Need at least 2 interfaces for single flow

        vrf_number = int(vrf_name.replace('Vrf', ''))

        if dual_flow:
            # Dual flow mode: generate routes for both flows
            # First flow interfaces: indices 0,1 (base_network)
            # Second flow interfaces: indices 2,3 (second_flow_network)

            first_flow_interfaces = interfaces[0:2]  # Ethernet0,8 / Ethernet16,24 etc.
            second_flow_interfaces = interfaces[2:4]  # Ethernet4,12 / Ethernet20,28 etc.

            # Get network prefix for first flow
            first_flow_network = first_flow_interfaces[0]['network']

            # Generate routes for first flow (base_network pattern)
            if vrf_number == 1:
                # Vrf1 special case: only has one route (high route)
                second_interface = first_flow_interfaces[1]  # Ethernet8

                ip_parts = second_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr + 1)

                route_key = f"{vrf_name}|{first_flow_network}.{high_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": second_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }
            else:
                # Vrf2+: have two routes each for first flow
                first_interface = first_flow_interfaces[0]
                second_interface = first_flow_interfaces[1]

                # First route: low route using first interface
                ip_parts = first_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr - 1)

                route_key = f"{vrf_name}|{first_flow_network}.{low_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": first_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }

                # Second route: high route using second interface
                ip_parts = second_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr + 1)

                route_key = f"{vrf_name}|{first_flow_network}.{high_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": second_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }

            # Generate routes for second flow (second_flow_network pattern)
            second_flow_network = second_flow_interfaces[0]['network']

            if vrf_number == 1:
                # Vrf1 special case: only has one route (high route)
                second_interface = second_flow_interfaces[1]  # Ethernet12

                ip_parts = second_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr + 1)

                route_key = f"{vrf_name}|{second_flow_network}.{high_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": second_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }
            else:
                # Vrf2+: have two routes each for second flow
                first_interface = second_flow_interfaces[0]
                second_interface = second_flow_interfaces[1]

                # First route: low route using first interface
                ip_parts = first_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr - 1)

                route_key = f"{vrf_name}|{second_flow_network}.{low_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": first_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }

                # Second route: high route using second interface
                ip_parts = second_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr + 1)

                route_key = f"{vrf_name}|{second_flow_network}.{high_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": second_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }
        else:
            # Single flow mode: dynamic route calculation
            interface_network = interfaces[0]['network']

            if vrf_number == 1:
                # Vrf1 special case: only has one route (high route)
                second_interface = interfaces[1]  # Use second interface (Ethernet8)

                # Parse IP address to get nexthop (IP + 1)
                ip_parts = second_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr + 1)

                route_key = f"{vrf_name}|{interface_network}.{high_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": second_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }
            else:
                # Vrf2+: have two routes each
                first_interface = interfaces[0]
                second_interface = interfaces[1]

                # First route: low route using first interface
                ip_parts = first_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr - 1)

                route_key = f"{vrf_name}|{interface_network}.{low_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": first_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }

                # Second route: high route using second interface
                ip_parts = second_interface['ip_address'].split('/')
                ip_addr = ipaddress.IPv4Address(ip_parts[0])
                nexthop = str(ip_addr + 1)

                route_key = f"{vrf_name}|{interface_network}.{high_route_ip}/31"
                config['STATIC_ROUTE'][route_key] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": second_interface['interface_name'],
                    "nexthop": nexthop,
                    "nexthop-vrf": vrf_name
                }


def main():
    parser = argparse.ArgumentParser(
        description='Generate SONiC JSON configuration files for single DUT snake tests',
        epilog='''
Examples:
  %(prog)s --output single_dut_snake.json                    # Basic single DUT snake config (64 interfaces default)
  %(prog)s --output snake_ipv6.json --include-ipv6           # Include IPv6 addresses
  %(prog)s --dual-flow --output dual_snake.json              # Dual flow (1x800G + 2x400G)
  %(prog)s --base-network 10.0.0 --output custom_snake.json # Custom base network
  %(prog)s --num-interfaces 128 --output large_snake.json    # Custom number of interfaces
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--output', type=str, default='single_dut_snake.json',
                        help='Output file path (default: single_dut_snake.json)')
    parser.add_argument('--num-interfaces', type=int, default=64,
                        help='Total number of interfaces to configure (default: 64)')
    parser.add_argument('--base-network', type=str, default='192.168.0',
                        help='Base IP network (default: 192.168.0)')
    parser.add_argument('--static-route-network', type=str, default='192.168',
                        help='Static route network base (default: 192.168)')
    parser.add_argument('--base-mac', type=str, default='00:00:00:ab:00:00',
                        help='Base MAC address (default: 00:00:00:ab:00:00)')
    parser.add_argument('--include-ipv6', action='store_true',
                        help='Include IPv6 addresses (/127)')
    parser.add_argument('--dual-flow', action='store_true',
                        help='Generate dual flow configuration (1x800G + 2x400G)')
    parser.add_argument('--second-flow-network', type=str, default='172.16.0',
                        help='Second flow IP network (default: 172.16.0)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be generated without creating files')

    args = parser.parse_args()

    # Calculate number of VRFs
    interfaces_per_vrf = 4 if args.dual_flow else 2
    num_vrfs = args.num_interfaces // interfaces_per_vrf

    if args.dry_run:
        print("DRY RUN MODE - No files will be created")
        print(f"Would create: {args.output}")
        print(f"Total interfaces: {args.num_interfaces}")
        print(f"VRFs: {num_vrfs}")
        if args.dual_flow:
            print(f"Interfaces per VRF: 4 (dual flow)")
            print(f"First flow network: {args.base_network}")
            print(f"Second flow network: {args.second_flow_network}")
        else:
            print(f"Interfaces per VRF: 2")
            print(f"Base network: {args.base_network}")
        print(f"Static route network: {args.static_route_network}")
        print(f"Include IPv6: {args.include_ipv6}")
        print(f"Dual flow: {args.dual_flow}")
        return

    # Generate the configuration
    generate_single_dut_snake_config(
        args.output, args.base_network, args.static_route_network,
        args.include_ipv6, args.base_mac, args.dual_flow, args.second_flow_network,
        args.num_interfaces
    )


if __name__ == "__main__":
    main()
