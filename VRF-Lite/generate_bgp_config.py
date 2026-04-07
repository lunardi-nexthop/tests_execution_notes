#!/usr/bin/env python3
"""
Generate BGP configuration from VRF sub-interface configuration.

This script reads a sub-interface configuration (YAML/JSON) and generates
the corresponding BGP peering configuration, automatically using the neighbor
IPs from /31 and /127 point-to-point networks.

Usage:
    python3 generate_bgp_config.py --config bgp_peers.yaml --local-asn 65000
    python3 generate_bgp_config.py --config bgp_peers.yaml --local-asn 65000 --remote-asn-base 65100
"""

import argparse
import sys
from configure_vrf_subinterfaces import (
    VRFSubInterfaceConfigurator,
    get_point_to_point_neighbor
)


def generate_bgp_config(configurator, local_asn, remote_asn_base=None, remote_asn_map=None):
    """
    Generate BGP configuration for all sub-interfaces.
    
    Args:
        configurator: VRFSubInterfaceConfigurator instance
        local_asn: Local AS number
        remote_asn_base: Base AS number for auto-generating remote ASNs
        remote_asn_map: Dictionary mapping VRF names to remote AS numbers
    """
    lines = []
    lines.append("#!/bin/bash")
    lines.append("# Auto-generated BGP configuration")
    lines.append(f"# Local ASN: {local_asn}")
    lines.append("")
    lines.append("vtysh << 'EOF'")
    lines.append("configure terminal")
    lines.append("")
    
    # Group sub-interfaces by VRF
    vrf_subints = {}
    for sub_int in configurator.sub_interfaces:
        if sub_int.vrf_name:
            if sub_int.vrf_name not in vrf_subints:
                vrf_subints[sub_int.vrf_name] = []
            vrf_subints[sub_int.vrf_name].append(sub_int)
    
    # Generate BGP config for each VRF
    vrf_counter = 0
    for vrf_name in sorted(vrf_subints.keys()):
        sub_ints = vrf_subints[vrf_name]
        
        # Determine remote ASN
        if remote_asn_map and vrf_name in remote_asn_map:
            remote_asn = remote_asn_map[vrf_name]
        elif remote_asn_base:
            remote_asn = remote_asn_base + vrf_counter
            vrf_counter += 1
        else:
            remote_asn = "XXXXX"  # Placeholder
        
        lines.append(f"! ============================================================")
        lines.append(f"! VRF: {vrf_name}")
        lines.append(f"! ============================================================")
        lines.append(f"router bgp {local_asn} vrf {vrf_name}")
        
        # Configure neighbors for each sub-interface in this VRF
        for sub_int in sub_ints:
            # IPv4 neighbor
            if sub_int.ip_address:
                ipv4_neighbor = get_point_to_point_neighbor(sub_int.ip_address)
                if ipv4_neighbor:
                    neighbor_ip = ipv4_neighbor.split('/')[0]
                    lines.append(f"  neighbor {neighbor_ip} remote-as {remote_asn}")
                    lines.append(f"  neighbor {neighbor_ip} description {vrf_name}-{sub_int.name}-IPv4")
            
            # IPv6 neighbor
            if sub_int.ipv6_address:
                ipv6_neighbor = get_point_to_point_neighbor(sub_int.ipv6_address)
                if ipv6_neighbor:
                    neighbor_ip = ipv6_neighbor.split('/')[0]
                    lines.append(f"  neighbor {neighbor_ip} remote-as {remote_asn}")
                    lines.append(f"  neighbor {neighbor_ip} description {vrf_name}-{sub_int.name}-IPv6")
        
        lines.append("  !")
        
        # IPv4 address family
        lines.append("  address-family ipv4 unicast")
        for sub_int in sub_ints:
            if sub_int.ip_address:
                ipv4_neighbor = get_point_to_point_neighbor(sub_int.ip_address)
                if ipv4_neighbor:
                    neighbor_ip = ipv4_neighbor.split('/')[0]
                    lines.append(f"    neighbor {neighbor_ip} activate")
                    lines.append(f"    neighbor {neighbor_ip} soft-reconfiguration inbound")
        lines.append("  exit-address-family")
        lines.append("  !")
        
        # IPv6 address family
        has_ipv6 = any(sub_int.ipv6_address for sub_int in sub_ints)
        if has_ipv6:
            lines.append("  address-family ipv6 unicast")
            for sub_int in sub_ints:
                if sub_int.ipv6_address:
                    ipv6_neighbor = get_point_to_point_neighbor(sub_int.ipv6_address)
                    if ipv6_neighbor:
                        neighbor_ip = ipv6_neighbor.split('/')[0]
                        lines.append(f"    neighbor {neighbor_ip} activate")
                        lines.append(f"    neighbor {neighbor_ip} soft-reconfiguration inbound")
            lines.append("  exit-address-family")
            lines.append("  !")
        
        lines.append("exit")
        lines.append("")
    
    lines.append("end")
    lines.append("write memory")
    lines.append("EOF")
    lines.append("")
    lines.append('echo "BGP configuration completed!"')
    lines.append('echo ""')
    lines.append('echo "Verify with: vtysh -c \'show bgp vrf all summary\'"')
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate BGP configuration from sub-interface config'
    )
    
    parser.add_argument('--config', '-c', required=True,
                       help='Sub-interface configuration file (YAML or JSON)')
    parser.add_argument('--local-asn', type=int, required=True,
                       help='Local BGP AS number')
    parser.add_argument('--remote-asn-base', type=int,
                       help='Base AS number for auto-generating remote ASNs (increments per VRF)')
    parser.add_argument('--output', '-o',
                       help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Load configuration
    configurator = VRFSubInterfaceConfigurator()
    
    if args.config.endswith('.yaml') or args.config.endswith('.yml'):
        configurator.load_from_yaml(args.config)
    elif args.config.endswith('.json'):
        configurator.load_from_json(args.config)
    else:
        print("Error: Config file must be .yaml, .yml, or .json")
        sys.exit(1)
    
    # Generate BGP configuration
    bgp_config = generate_bgp_config(
        configurator,
        args.local_asn,
        args.remote_asn_base
    )
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(bgp_config)
        print(f"BGP configuration saved to {args.output}")
    else:
        print(bgp_config)


if __name__ == '__main__':
    main()

