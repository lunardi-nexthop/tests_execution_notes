#!/usr/bin/env python3
"""
Script to configure VRF sub-interfaces on SONiC devices.

Usage:
    python configure_vrf_subinterfaces.py --config subinterfaces.yaml
    python configure_vrf_subinterfaces.py --config subinterfaces.json
    python configure_vrf_subinterfaces.py --interactive

Examples:
    # Using YAML config file
    python configure_vrf_subinterfaces.py --config my_subints.yaml --host 10.0.0.1

    # Using JSON config file
    python configure_vrf_subinterfaces.py --config my_subints.json --apply

    # Interactive mode
    python configure_vrf_subinterfaces.py --interactive --host 10.0.0.1
"""

import argparse
import json
import yaml
import sys
import os
from typing import List, Dict, Optional


class SubInterfaceConfig:
    """Represents a single sub-interface configuration."""
    
    def __init__(self, parent_interface: str, vlan_id: int, ip_address: str, 
                 vrf_name: Optional[str] = None, ipv6_address: Optional[str] = None,
                 admin_status: str = "up"):
        self.parent_interface = parent_interface
        self.vlan_id = vlan_id
        self.ip_address = ip_address
        self.ipv6_address = ipv6_address
        self.vrf_name = vrf_name
        self.admin_status = admin_status
        self.name = f"{parent_interface}.{vlan_id}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'parent_interface': self.parent_interface,
            'vlan_id': self.vlan_id,
            'ip_address': self.ip_address,
            'ipv6_address': self.ipv6_address,
            'vrf_name': self.vrf_name,
            'admin_status': self.admin_status,
            'name': self.name
        }


class VRFSubInterfaceConfigurator:
    """Main configurator class for VRF sub-interfaces."""
    
    def __init__(self):
        self.sub_interfaces: List[SubInterfaceConfig] = []
        self.vrfs: set = set()
    
    def add_sub_interface(self, parent_interface: str, vlan_id: int, 
                         ip_address: str, vrf_name: Optional[str] = None,
                         ipv6_address: Optional[str] = None, admin_status: str = "up"):
        """Add a sub-interface configuration."""
        sub_int = SubInterfaceConfig(parent_interface, vlan_id, ip_address, 
                                     vrf_name, ipv6_address, admin_status)
        self.sub_interfaces.append(sub_int)
        if vrf_name:
            self.vrfs.add(vrf_name)
        return sub_int
    
    def load_from_yaml(self, yaml_file: str):
        """Load configuration from YAML file."""
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        for item in config.get('sub_interfaces', []):
            self.add_sub_interface(
                parent_interface=item['parent_interface'],
                vlan_id=item['vlan_id'],
                ip_address=item['ip_address'],
                vrf_name=item.get('vrf_name'),
                ipv6_address=item.get('ipv6_address'),
                admin_status=item.get('admin_status', 'up')
            )
    
    def load_from_json(self, json_file: str):
        """Load configuration from JSON file."""
        with open(json_file, 'r') as f:
            config = json.load(f)
        
        for item in config.get('sub_interfaces', []):
            self.add_sub_interface(
                parent_interface=item['parent_interface'],
                vlan_id=item['vlan_id'],
                ip_address=item['ip_address'],
                vrf_name=item.get('vrf_name'),
                ipv6_address=item.get('ipv6_address'),
                admin_status=item.get('admin_status', 'up')
            )
    
    def generate_config_db_json(self) -> Dict:
        """Generate SONiC config_db.json format."""
        config = {
            "VLAN_SUB_INTERFACE": {}
        }
        
        # Add VRF definitions if any VRFs are used
        if self.vrfs:
            config["VRF"] = {vrf: {} for vrf in self.vrfs}
        
        # Add sub-interface configurations
        for sub_int in self.sub_interfaces:
            # Interface entry with admin status and VRF binding
            interface_config = {
                "admin_status": sub_int.admin_status
            }
            if sub_int.vrf_name:
                interface_config["vrf_name"] = sub_int.vrf_name
            
            config["VLAN_SUB_INTERFACE"][sub_int.name] = interface_config
            
            # IPv4 address entry
            if sub_int.ip_address:
                ip_key = f"{sub_int.name}|{sub_int.ip_address}"
                config["VLAN_SUB_INTERFACE"][ip_key] = {}
            
            # IPv6 address entry
            if sub_int.ipv6_address:
                ipv6_key = f"{sub_int.name}|{sub_int.ipv6_address}"
                config["VLAN_SUB_INTERFACE"][ipv6_key] = {}
        
        return config

    def generate_cli_commands(self) -> List[str]:
        """Generate CLI commands to configure sub-interfaces."""
        commands = []

        # Add VRF creation commands
        for vrf in sorted(self.vrfs):
            commands.append(f"# Create VRF {vrf}")
            commands.append(f"config vrf add {vrf}")
            commands.append("")

        # Add sub-interface configuration commands
        for sub_int in self.sub_interfaces:
            commands.append(f"# Configure {sub_int.name}")

            # Create sub-interface
            commands.append(f"config subinterface add {sub_int.name} {sub_int.vlan_id}")

            # Bind to VRF if specified
            if sub_int.vrf_name:
                commands.append(f"config interface vrf bind {sub_int.name} {sub_int.vrf_name}")

            # Add IPv4 address
            if sub_int.ip_address:
                commands.append(f"config interface ip add {sub_int.name} {sub_int.ip_address}")

            # Add IPv6 address
            if sub_int.ipv6_address:
                commands.append(f"config interface ip add {sub_int.name} {sub_int.ipv6_address}")

            # Set admin status
            if sub_int.admin_status == "up":
                commands.append(f"config interface startup {sub_int.name}")
            else:
                commands.append(f"config interface shutdown {sub_int.name}")

            commands.append("")

        return commands

    def generate_removal_commands(self) -> List[str]:
        """Generate CLI commands to remove sub-interfaces."""
        commands = []

        # Remove sub-interfaces (in reverse order)
        for sub_int in reversed(self.sub_interfaces):
            commands.append(f"# Remove {sub_int.name}")

            # Remove IPv4 address
            if sub_int.ip_address:
                commands.append(f"config interface ip remove {sub_int.name} {sub_int.ip_address}")

            # Remove IPv6 address
            if sub_int.ipv6_address:
                commands.append(f"config interface ip remove {sub_int.name} {sub_int.ipv6_address}")

            # Unbind from VRF if specified
            if sub_int.vrf_name:
                commands.append(f"config interface vrf unbind {sub_int.name}")

            # Remove sub-interface
            commands.append(f"config subinterface del {sub_int.name}")
            commands.append("")

        # Remove VRFs
        for vrf in sorted(self.vrfs, reverse=True):
            commands.append(f"# Remove VRF {vrf}")
            commands.append(f"config vrf del {vrf}")
            commands.append("")

        return commands

    def save_config_db_json(self, output_file: str):
        """Save configuration as config_db.json format."""
        config = self.generate_config_db_json()
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {output_file}")

    def save_cli_commands(self, output_file: str):
        """Save CLI commands to a shell script."""
        commands = self.generate_cli_commands()
        with open(output_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated sub-interface configuration script\n")
            f.write("# Generated by configure_vrf_subinterfaces.py\n\n")
            f.write("\n".join(commands))
        print(f"CLI commands saved to {output_file}")

    def save_removal_script(self, output_file: str):
        """Save removal commands to a shell script."""
        commands = self.generate_removal_commands()
        with open(output_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated sub-interface removal script\n")
            f.write("# Generated by configure_vrf_subinterfaces.py\n\n")
            f.write("\n".join(commands))
        print(f"Removal script saved to {output_file}")

    def print_summary(self):
        """Print configuration summary."""
        print("\n" + "="*60)
        print("Sub-Interface Configuration Summary")
        print("="*60)

        if self.vrfs:
            print(f"\nVRFs: {', '.join(sorted(self.vrfs))}")

        print(f"\nTotal Sub-Interfaces: {len(self.sub_interfaces)}\n")

        for sub_int in self.sub_interfaces:
            print(f"  {sub_int.name}")
            print(f"    Parent: {sub_int.parent_interface}")
            print(f"    VLAN ID: {sub_int.vlan_id}")
            if sub_int.ip_address:
                print(f"    IPv4: {sub_int.ip_address}")
            if sub_int.ipv6_address:
                print(f"    IPv6: {sub_int.ipv6_address}")
            if sub_int.vrf_name:
                print(f"    VRF: {sub_int.vrf_name}")
            print(f"    Admin Status: {sub_int.admin_status}")
            print()

        print("="*60 + "\n")


def interactive_mode():
    """Interactive mode for creating sub-interface configurations."""
    configurator = VRFSubInterfaceConfigurator()

    print("\n" + "="*60)
    print("VRF Sub-Interface Configuration - Interactive Mode")
    print("="*60 + "\n")

    while True:
        print("\nAdd a new sub-interface configuration:")

        parent_interface = input("  Parent interface (e.g., Ethernet0, PortChannel10): ").strip()
        if not parent_interface:
            break

        try:
            vlan_id = int(input("  VLAN ID (e.g., 100): ").strip())
        except ValueError:
            print("  Invalid VLAN ID. Skipping...")
            continue

        ip_address = input("  IPv4 address with prefix (e.g., 10.0.0.1/24): ").strip()

        ipv6_address = input("  IPv6 address with prefix (optional, press Enter to skip): ").strip()
        if not ipv6_address:
            ipv6_address = None

        vrf_name = input("  VRF name (optional, press Enter to skip): ").strip()
        if not vrf_name:
            vrf_name = None

        admin_status = input("  Admin status (up/down, default: up): ").strip().lower()
        if admin_status not in ['up', 'down']:
            admin_status = 'up'

        configurator.add_sub_interface(
            parent_interface=parent_interface,
            vlan_id=vlan_id,
            ip_address=ip_address,
            vrf_name=vrf_name,
            ipv6_address=ipv6_address,
            admin_status=admin_status
        )

        print(f"  ✓ Added {parent_interface}.{vlan_id}")

        more = input("\nAdd another sub-interface? (y/n): ").strip().lower()
        if more != 'y':
            break

    return configurator


def main():
    parser = argparse.ArgumentParser(
        description='Configure VRF sub-interfaces on SONiC devices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick single sub-interface
  %(prog)s --parent-interface Ethernet0 --vlan-id 100 --ip-address 10.0.0.1/24 --vrf-name Vrf1

  # Multiple sub-interfaces with auto-increment
  %(prog)s --parent-interface Ethernet0 --start-vlan-id 100 --start-ip 10.0.0.1/31 --count 5 --vrf-name Vrf1

  # Using config file
  %(prog)s --config my_config.yaml

  # Interactive mode
  %(prog)s --interactive
"""
    )

    # Input methods
    input_group = parser.add_argument_group('Input Methods')
    input_group.add_argument('--config', '-c', help='Configuration file (YAML or JSON)')
    input_group.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')

    # Quick configuration (single sub-interface)
    quick_group = parser.add_argument_group('Quick Configuration (single sub-interface)')
    quick_group.add_argument('--parent-interface', help='Parent interface (e.g., Ethernet0, PortChannel10)')
    quick_group.add_argument('--parent-interface-list', help='Comma-separated list of parent interfaces (e.g., Ethernet384,Ethernet386,Ethernet388)')
    quick_group.add_argument('--vlan-id', type=int, help='VLAN ID')
    quick_group.add_argument('--ip-address', help='IPv4 address with prefix (e.g., 10.0.0.1/24)')
    quick_group.add_argument('--ipv6-address', help='IPv6 address with prefix (optional)')
    quick_group.add_argument('--vrf-name', help='VRF name (optional)')
    quick_group.add_argument('--admin-status', choices=['up', 'down'], default='up',
                           help='Admin status (default: up)')

    # Bulk configuration (multiple sub-interfaces with auto-increment)
    bulk_group = parser.add_argument_group('Bulk Configuration (auto-increment)')
    bulk_group.add_argument('--start-vlan-id', type=int, help='Starting VLAN ID')
    bulk_group.add_argument('--start-ip', help='Starting IP address with prefix (e.g., 10.0.0.1/31)')
    bulk_group.add_argument('--count', type=int, default=1, help='Number of sub-interfaces to create per parent interface')
    bulk_group.add_argument('--vlan-increment', type=int, default=1, help='VLAN ID increment (default: 1)')
    bulk_group.add_argument('--ip-increment', type=int, default=2, help='IP increment (default: 2 for /31)')
    bulk_group.add_argument('--vrf-list', help='Comma-separated list of VRF names (e.g., Vrf1,Vrf2,Vrf3)')
    bulk_group.add_argument('--vrf-prefix', help='VRF name prefix for auto-generation (e.g., Vrf)')
    bulk_group.add_argument('--vrf-start-number', type=int, default=1, help='Starting number for VRF auto-generation (default: 1)')
    bulk_group.add_argument('--vrf-per-parent', action='store_true',
                           help='Restart VRF numbering for each parent interface')

    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output-json', '-j', help='Output config_db.json file')
    output_group.add_argument('--output-cli', '-o', help='Output CLI commands script')
    output_group.add_argument('--output-removal', '-r', help='Output removal script')
    output_group.add_argument('--print-json', action='store_true',
                       help='Print config_db.json to stdout')
    output_group.add_argument('--print-cli', action='store_true',
                       help='Print CLI commands to stdout')
    output_group.add_argument('--print-removal', action='store_true',
                       help='Print removal commands to stdout')

    args = parser.parse_args()

    # Create configurator
    configurator = VRFSubInterfaceConfigurator()

    # Load configuration
    if args.interactive:
        configurator = interactive_mode()
    elif args.config:
        if args.config.endswith('.yaml') or args.config.endswith('.yml'):
            configurator.load_from_yaml(args.config)
        elif args.config.endswith('.json'):
            configurator.load_from_json(args.config)
        else:
            print("Error: Config file must be .yaml, .yml, or .json")
            sys.exit(1)
    elif args.parent_interface and args.vlan_id and args.ip_address:
        # Quick single sub-interface mode
        configurator.add_sub_interface(
            parent_interface=args.parent_interface,
            vlan_id=args.vlan_id,
            ip_address=args.ip_address,
            vrf_name=args.vrf_name,
            ipv6_address=args.ipv6_address,
            admin_status=args.admin_status
        )
    elif (args.parent_interface or args.parent_interface_list) and args.start_vlan_id and args.start_ip:
        # Bulk mode with auto-increment
        import ipaddress

        # Parse starting IP
        try:
            ip_network = ipaddress.ip_network(args.start_ip, strict=False)
            ip_addr = ipaddress.ip_address(args.start_ip.split('/')[0])
            prefix_len = args.start_ip.split('/')[1]
        except Exception as e:
            print(f"Error parsing IP address: {e}")
            sys.exit(1)

        # Get list of parent interfaces
        parent_interfaces = []
        if args.parent_interface_list:
            parent_interfaces = [p.strip() for p in args.parent_interface_list.split(',')]
        elif args.parent_interface:
            parent_interfaces = [args.parent_interface]

        # Track global IP and VRF counter
        global_ip_offset = 0
        global_vrf_counter = args.vrf_start_number

        # Process each parent interface
        for parent_idx, parent_interface in enumerate(parent_interfaces):
            # Determine VRF names for each sub-interface on this parent
            vrf_names = []

            if args.vrf_list:
                # Use provided list of VRF names
                vrf_names = [v.strip() for v in args.vrf_list.split(',')]
                if len(vrf_names) < args.count:
                    # Cycle through the list if not enough VRFs provided
                    vrf_names = (vrf_names * ((args.count // len(vrf_names)) + 1))[:args.count]
            elif args.vrf_prefix:
                # Auto-generate VRF names with prefix and number
                if args.vrf_per_parent:
                    # Restart numbering for each parent
                    for i in range(args.count):
                        vrf_names.append(f"{args.vrf_prefix}{args.vrf_start_number + i}")
                else:
                    # Continue numbering across parents
                    for i in range(args.count):
                        vrf_names.append(f"{args.vrf_prefix}{global_vrf_counter}")
                        global_vrf_counter += 1
            elif args.vrf_name:
                # Use same VRF for all
                vrf_names = [args.vrf_name] * args.count
            else:
                # No VRF
                vrf_names = [None] * args.count

            # Create multiple sub-interfaces for this parent
            for i in range(args.count):
                vlan_id = args.start_vlan_id + (i * args.vlan_increment)
                current_ip = ip_addr + global_ip_offset
                ip_with_prefix = f"{current_ip}/{prefix_len}"

                configurator.add_sub_interface(
                    parent_interface=parent_interface,
                    vlan_id=vlan_id,
                    ip_address=ip_with_prefix,
                    vrf_name=vrf_names[i],
                    ipv6_address=None,
                    admin_status=args.admin_status
                )

                global_ip_offset += args.ip_increment
    else:
        parser.print_help()
        sys.exit(1)

    # Print summary
    configurator.print_summary()

    # Generate outputs
    if args.output_json:
        configurator.save_config_db_json(args.output_json)

    if args.output_cli:
        configurator.save_cli_commands(args.output_cli)

    if args.output_removal:
        configurator.save_removal_script(args.output_removal)

    if args.print_json:
        print("\n" + "="*60)
        print("Config DB JSON Format:")
        print("="*60)
        print(json.dumps(configurator.generate_config_db_json(), indent=4))

    if args.print_cli:
        print("\n" + "="*60)
        print("CLI Commands:")
        print("="*60)
        print("\n".join(configurator.generate_cli_commands()))

    if args.print_removal:
        print("\n" + "="*60)
        print("Removal Commands:")
        print("="*60)
        print("\n".join(configurator.generate_removal_commands()))

    # If no output specified, save defaults
    if not any([args.output_json, args.output_cli, args.output_removal,
                args.print_json, args.print_cli, args.print_removal]):
        configurator.save_config_db_json('subinterface_config.json')
        configurator.save_cli_commands('configure_subinterfaces.sh')
        configurator.save_removal_script('remove_subinterfaces.sh')


if __name__ == '__main__':
    main()

