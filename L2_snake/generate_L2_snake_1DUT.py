#!/usr/bin/env python3
"""
Script to generate SONiC JSON configuration files for L2 snake tests.
Creates VLAN configuration with flexible interface settings.
Default: 64 ports with VLANs 100-131 using 8-port increments.
"""

import json
import argparse
import sys
from collections import OrderedDict


def generate_l2_snake_config(output_file, num_interfaces=64, start_vlan=100,
                              port_increment=8, tagging_mode='untagged'):
    """
    Generate SONiC VLAN configuration for L2 snake test.

    Args:
        output_file: Output JSON file path
        num_interfaces: Total number of interfaces to configure (default: 64)
        start_vlan: Starting VLAN ID (default: 100)
        port_increment: Port number increment between pairs (default: 8)
        tagging_mode: VLAN tagging mode - 'untagged' or 'tagged' (default: 'untagged')
    """

    # Ports are numbered as multiples of port_increment: Ethernet0, Ethernet8, Ethernet16...
    # Each VLAN pairs two consecutive physical ports (adjacent in snake topology):
    #   Vlan0: (Eth0, Eth8), Vlan1: (Eth16, Eth24), Vlan2: (Eth32, Eth40), ...
    # Total VLANs = num_interfaces // 2

    max_vlans = num_interfaces // 2

    print(f"Generating L2 snake configuration")
    print(f"Total interfaces: {num_interfaces}")
    print(f"VLANs to create: {max_vlans}")
    print(f"Ports per VLAN: 2")
    print(f"Port increment: {port_increment}")
    print(f"VLAN range: {start_vlan} to {start_vlan + max_vlans - 1}")
    print(f"Tagging mode: {tagging_mode}")

    config = OrderedDict()
    config['VLAN'] = OrderedDict()
    config['VLAN_MEMBER'] = OrderedDict()

    # Track which VLANs are actually created
    vlans_created = 0

    # Generate VLANs and VLAN members
    for vlan_offset in range(max_vlans):
        vlan_id = start_vlan + vlan_offset
        vlan_name = f"Vlan{vlan_id}"

        eth_port1 = vlan_offset * 2 * port_increment
        eth_port2 = eth_port1 + port_increment

        # Add VLAN definition
        config['VLAN'][vlan_name] = {
            "vlanid": str(vlan_id)
        }

        # Add VLAN members
        interface1 = f"Ethernet{eth_port1}"
        interface2 = f"Ethernet{eth_port2}"

        member1_key = f"{vlan_name}|{interface1}"
        member2_key = f"{vlan_name}|{interface2}"

        config['VLAN_MEMBER'][member1_key] = {
            "tagging_mode": tagging_mode
        }
        config['VLAN_MEMBER'][member2_key] = {
            "tagging_mode": tagging_mode
        }

        vlans_created += 1

    # Write the configuration
    try:
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Calculate statistics
        total_vlan_members = len(config['VLAN_MEMBER'])

        print(f"\nSuccessfully generated L2 snake configuration.")
        print(f"Output file: {output_file}")
        print(f"VLANs created: {vlans_created}")
        print(f"VLAN members created: {total_vlan_members}")
        print(f"\nTo apply configuration:")
        print(f"  config load {output_file}")

    except Exception as e:
        print(f"Error writing output file '{output_file}': {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Generate SONiC JSON configuration files for L2 snake tests',
        epilog='''
Examples:
  %(prog)s --output l2_snake.json                              # Default 64 interfaces
  %(prog)s --num-interfaces 128 --output l2_snake_128.json     # 128 interfaces
  %(prog)s --start-vlan 200 --port-increment 16 --output custom.json  # Custom settings
  %(prog)s --tagging-mode tagged --output tagged_vlan.json     # Tagged VLANs
  %(prog)s --dry-run                                           # Preview without creating files
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--output', type=str, default='l2_snake.json',
                        help='Output file path (default: l2_snake.json)')
    parser.add_argument('--num-interfaces', type=int, default=64,
                        help='Total number of interfaces to configure (default: 64)')
    parser.add_argument('--start-vlan', type=int, default=100,
                        help='Starting VLAN ID (default: 100)')
    parser.add_argument('--port-increment', type=int, default=8,
                        help='Port number increment between VLAN pairs (default: 8)')
    parser.add_argument('--tagging-mode', type=str, default='untagged',
                        choices=['untagged', 'tagged'],
                        help='VLAN tagging mode (default: untagged)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be generated without creating files')

    args = parser.parse_args()

    # Validate inputs
    if args.num_interfaces < 2:
        print("Error: num_interfaces must be at least 2")
        sys.exit(1)

    if args.start_vlan < 1 or args.start_vlan > 4094:
        print("Error: start_vlan must be between 1 and 4094")
        sys.exit(1)

    if args.port_increment < 1:
        print("Error: port_increment must be at least 1")
        sys.exit(1)

    max_vlans = args.num_interfaces // 2

    if args.dry_run:
        print("DRY RUN MODE - No files will be created")
        print(f"Would create: {args.output}")
        print(f"Total interfaces: {args.num_interfaces}")
        print(f"VLANs: {max_vlans}")
        print(f"Ports per VLAN: 2")
        print(f"Port increment: {args.port_increment}")
        print(f"VLAN range: {args.start_vlan} to {args.start_vlan + max_vlans - 1}")
        print(f"Tagging mode: {args.tagging_mode}")
        return

    # Generate the configuration
    generate_l2_snake_config(
        args.output, args.num_interfaces, args.start_vlan,
        args.port_increment, args.tagging_mode
    )


if __name__ == "__main__":
    main()
