#!/usr/bin/env python3
"""
Script to generate SONiC JSON configuration files for single DUT snake tests
with breakout ports.

Based on generate_vrf_snake_1DUT.py. Adds --num-breakout-ports (1x800G, 2x400G,
4x200G) and --num-fp-ports (number of physical front panel ports). The number of
logical interfaces, VRFs, IPv4/IPv6 addresses and static routes are derived from
the breakout factor and the number of physical front panel ports.

Each physical front panel port owns 8 SONiC lanes and is broken out into
'breakout' logical sub-ports (one per flow). Two physical front panel ports form
a single VRF, so num_vrfs = num_fp_ports / 2 and each VRF has 2 * breakout
logical interfaces. Every flow runs its own independent snake using its own IPv4
network (third octet incremented by --flow-increment per flow).

IPv6 addressing mirrors IPv4 in both the third and last octets:
  192.168.0.32/31  <->  2001:192:168:0::32/127   (= 2001:192:168::32/127)
  192.168.10.32/31 <->  2001:192:168:10::32/127
The IPv4 third octet becomes the IPv6 4th group, and the IPv4 last octet
becomes the IPv6 host — both displayed as their decimal digits via the
decimal-as-hex trick: int("10", 16) = 16 displays as '10' in hex.
"""

import json
import argparse
import sys
import ipaddress
from collections import OrderedDict


BREAKOUT_MAP = {
    "1x800G": 1,
    "2x400G": 2,
    "4x200G": 4,
}

LANES_PER_FP_PORT = 8


def generate_mac_address(base_mac, ethernet_num):
    """Generate MAC address based on base MAC and ethernet (lane) number."""
    mac_parts = base_mac.split(':')
    mac_int = int(''.join(mac_parts), 16)
    new_mac_int = mac_int + ethernet_num
    new_mac_hex = f"{new_mac_int:012x}"
    return ':'.join([new_mac_hex[i:i + 2] for i in range(0, 12, 2)])


def flow_network(base_network, flow_index, flow_increment):
    """Return the IPv4 network prefix (first 3 octets) for a given flow."""
    octets = base_network.split('.')
    octets[2] = str(int(octets[2]) + flow_index * flow_increment)
    return '.'.join(octets)



def get_ipv6_base_int(ipv6_base_network):
    """Return the integer base address of the IPv6 /64 network."""
    net = ipaddress.IPv6Network(ipv6_base_network, strict=False)
    return int(net.network_address)


def flow_ipv6_base_int(root_ipv6_base_int, flow_third_octet):
    """Return the per-flow IPv6 base integer.

    The IPv4 third octet is encoded into the IPv6 4th 16-bit group using the
    decimal-as-hex trick so the displayed hex digits match the decimal value:
      192.168.10.x  ->  2001:192:168:10::x   (int("10",16)=16, displays as '10')
      192.168.20.x  ->  2001:192:168:20::x
    """
    return root_ipv6_base_int + int(str(flow_third_octet), 16) * (2 ** 64)


def ipv6_host_int(host_num):
    """Convert a decimal host number to the IPv6 host integer so that the
    displayed hex representation matches the decimal digits.

    IPv6Address formats in hex, so to display '32' in both:
      IPv4: 192.168.0.32   (32 decimal)
      IPv6: 2001:192:168::32  (0x32 = 50 decimal added to base)

    We interpret the decimal digits of host_num as hex: int("32", 16) = 50.
    For single-digit values 0-9 this is a no-op.
    """
    return int(str(host_num), 16)


def vrf_host_numbers(vrf_number):
    """Return the two host numbers used by a VRF (one per physical port)."""
    if vrf_number == 1:
        return [0, 2]
    base_host = 3 + (vrf_number - 2) * 2
    return [base_host, base_host + 1]


def generate_breakout_snake_config(output_file, base_network, base_mac,
                                   num_fp_ports, breakout, flow_increment,
                                   include_ipv6, ipv6_base_network='2001:192:168::/64'):
    """Generate SONiC configuration for single DUT breakout snake test."""

    num_flows = breakout
    subport_lane_step = LANES_PER_FP_PORT // breakout

    fp_ports_per_vrf = 2
    num_vrfs = num_fp_ports // fp_ports_per_vrf
    logical_per_vrf = fp_ports_per_vrf * breakout
    total_logical = num_fp_ports * breakout

    if num_fp_ports % fp_ports_per_vrf != 0:
        print(f"Warning: num_fp_ports ({num_fp_ports}) is not even; "
              f"creating {num_vrfs} VRFs covering {num_vrfs * fp_ports_per_vrf} ports")

    print("Generating breakout single DUT snake test configuration")
    print(f"Breakout: {breakout} sub-ports per physical port ({num_flows} flows)")
    print(f"Physical front panel ports: {num_fp_ports}")
    print(f"VRFs: {num_vrfs} ({fp_ports_per_vrf} physical ports per VRF)")
    print(f"Logical interfaces per VRF: {logical_per_vrf}")
    print(f"Total logical interfaces: {total_logical}")
    for f in range(num_flows):
        print(f"  Flow {f + 1} network: {flow_network(base_network, f, flow_increment)}.x")

    config = OrderedDict()
    config['INTERFACE'] = OrderedDict()
    config['VRF'] = OrderedDict()
    config['STATIC_ROUTE'] = OrderedDict()

    # Root IPv6 base (no flow offset yet); per-flow base computed inside the loop.
    root_ipv6_base_int = get_ipv6_base_int(ipv6_base_network) if include_ipv6 else None
    base_third_octet = int(base_network.split('.')[2])

    # vrf_interfaces[vrf_name][flow_index] = [portA_info, portB_info]
    vrf_interfaces = {}

    for vi in range(num_vrfs):
        vrf_number = vi + 1
        vrf_name = f"Vrf{vrf_number}"
        config['VRF'][vrf_name] = {}
        vrf_interfaces[vrf_name] = {f: [] for f in range(num_flows)}

        host_nums = vrf_host_numbers(vrf_number)

        for pj in range(fp_ports_per_vrf):
            port_base_lane = vi * 16 + pj * LANES_PER_FP_PORT
            host_num = host_nums[pj]
            for f in range(num_flows):
                lane = port_base_lane + f * subport_lane_step
                interface_name = f"Ethernet{lane}"
                net = flow_network(base_network, f, flow_increment)
                mac_addr = generate_mac_address(base_mac, lane)
                flow_third_octet = base_third_octet + f * flow_increment

                config['INTERFACE'][interface_name] = {
                    "mac_addr": mac_addr,
                    "vrf_name": vrf_name,
                }
                ip_address = f"{net}.{host_num}/31"
                config['INTERFACE'][f"{interface_name}|{ip_address}"] = {}

                if include_ipv6:
                    f_ipv6_base = flow_ipv6_base_int(root_ipv6_base_int, flow_third_octet)
                    ipv6_addr = ipaddress.IPv6Address(f_ipv6_base + ipv6_host_int(host_num))
                    config['INTERFACE'][f"{interface_name}|{ipv6_addr}/127"] = {}

                vrf_interfaces[vrf_name][f].append({
                    'interface_name': interface_name,
                    'host_num': host_num,
                    'network': net,
                })

    print("Generating static routes...")
    generate_breakout_static_routes(config, vrf_interfaces, num_vrfs,
                                    num_flows, include_ipv6, ipv6_base_network,
                                    base_network, flow_increment)

    try:
        with open(output_file, 'w') as fh:
            json.dump(config, fh, indent=2)

        total_interfaces = len([k for k in config['INTERFACE'].keys() if '|' not in k])
        print("Successfully generated single DUT breakout snake configuration.")
        print(f"Output file: {output_file}")
        print(f"VRFs created: {len(config['VRF'])}")
        print(f"Total logical interfaces created: {total_interfaces}")
        print(f"Static routes created: {len(config['STATIC_ROUTE'])}")
    except Exception as e:
        print(f"Error writing output file '{output_file}': {e}")
        sys.exit(1)


def _add_route(config, vrf_name, dest_network, dest_host, ifname, nexthop):
    route_key = f"{vrf_name}|{dest_network}.{dest_host}/31"
    config['STATIC_ROUTE'][route_key] = {
        "blackhole": "false",
        "distance": "0",
        "ifname": ifname,
        "nexthop": nexthop,
        "nexthop-vrf": vrf_name,
    }


def _add_ipv6_route(config, vrf_name, ipv6_base_int, dest_host, ifname, nexthop_host):
    dest_addr = ipaddress.IPv6Address(ipv6_base_int + ipv6_host_int(dest_host))
    nexthop_addr = ipaddress.IPv6Address(ipv6_base_int + ipv6_host_int(nexthop_host))
    route_key = f"{vrf_name}|{dest_addr}/127"
    config['STATIC_ROUTE'][route_key] = {
        "blackhole": "false",
        "distance": "0",
        "ifname": ifname,
        "nexthop": str(nexthop_addr),
        "nexthop-vrf": vrf_name,
    }


def generate_breakout_static_routes(config, vrf_interfaces, num_vrfs,
                                    num_flows, include_ipv6,
                                    ipv6_base_network='2001:192:168::/64',
                                    base_network='192.168.0', flow_increment=10):
    """Generate static routes for the breakout snake test, one snake per flow.

    Each flow forms an independent snake whose endpoints are the left tgen
    (network .0/31) and the right tgen (network .{2*num_vrfs}/31). For every VRF
    the first physical port carries the low (left) route and the second physical
    port carries the high (right) route. Vrf1 only owns the high route because
    its first port faces the left tgen directly.
    """
    low_route_host = 0
    high_route_host = 2 * num_vrfs
    root_ipv6_base_int = get_ipv6_base_int(ipv6_base_network) if include_ipv6 else None
    base_third_octet = int(base_network.split('.')[2])

    for vi in range(num_vrfs):
        vrf_number = vi + 1
        vrf_name = f"Vrf{vrf_number}"
        for f in range(num_flows):
            ifaces = vrf_interfaces[vrf_name][f]
            if len(ifaces) < 2:
                continue
            first_iface, second_iface = ifaces[0], ifaces[1]
            net = first_iface['network']
            flow_third_octet = base_third_octet + f * flow_increment
            f_ipv6_base = (flow_ipv6_base_int(root_ipv6_base_int, flow_third_octet)
                           if include_ipv6 else None)

            if vrf_number != 1:
                # Low route towards the left tgen via the first physical port.
                low_nexthop = str(ipaddress.IPv4Address(
                    f"{net}.{first_iface['host_num']}") - 1)
                _add_route(config, vrf_name, net, low_route_host,
                           first_iface['interface_name'], low_nexthop)
                if include_ipv6:
                    _add_ipv6_route(config, vrf_name, f_ipv6_base,
                                    low_route_host,
                                    first_iface['interface_name'],
                                    first_iface['host_num'] - 1)

            # High route towards the right tgen via the second physical port.
            high_nexthop = str(ipaddress.IPv4Address(
                f"{net}.{second_iface['host_num']}") + 1)
            _add_route(config, vrf_name, net, high_route_host,
                       second_iface['interface_name'], high_nexthop)
            if include_ipv6:
                _add_ipv6_route(config, vrf_name, f_ipv6_base,
                                high_route_host,
                                second_iface['interface_name'],
                                second_iface['host_num'] + 1)


def main():
    parser = argparse.ArgumentParser(
        description='Generate SONiC JSON configuration files for single DUT breakout snake tests',
        epilog='''
Examples:
  %(prog)s --output breakout_snake.json                              # 1x800G, 64 fp ports (default)
  %(prog)s --num-breakout-ports 2x400G --output snake_2x400.json     # 2x400G, 64 fp ports
  %(prog)s --num-breakout-ports 4x200G --num-fp-ports 64 --include-ipv6 --output snake_4x200.json
  %(prog)s --num-breakout-ports 2x400G --num-fp-ports 128 --output snake_128fp.json
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--output', type=str, default='single_dut_snake_breakout.json',
                        help='Output file path (default: single_dut_snake_breakout.json)')
    parser.add_argument('--num-breakout-ports', type=str, default='1x800G',
                        choices=sorted(BREAKOUT_MAP.keys()),
                        help='Breakout mode per physical port (default: 1x800G)')
    parser.add_argument('--num-fp-ports', type=int, default=64,
                        help='Number of physical front panel ports (default: 64)')
    parser.add_argument('--base-network', type=str, default='192.168.0',
                        help='Base IPv4 network for the first flow (default: 192.168.0)')
    parser.add_argument('--flow-increment', type=int, default=10,
                        help='Third-octet increment added per flow (default: 10)')
    parser.add_argument('--base-mac', type=str, default='00:00:00:ab:00:00',
                        help='Base MAC address (default: 00:00:00:ab:00:00)')
    parser.add_argument('--include-ipv6', action='store_true',
                        help='Include IPv6 addresses (/127)')
    parser.add_argument('--ipv6-base-network', type=str, default='2001:192:168::/64',
                        help='IPv6 base /64 network; the IPv4 last octet is used as the '
                             'IPv6 host (e.g. 192.168.0.32 -> 2001:192:168::32) '
                             '(default: 2001:192:168::/64)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be generated without creating files')

    args = parser.parse_args()

    breakout = BREAKOUT_MAP[args.num_breakout_ports]
    num_vrfs = args.num_fp_ports // 2

    if args.dry_run:
        print("DRY RUN MODE - No files will be created")
        print(f"Would create: {args.output}")
        print(f"Breakout mode: {args.num_breakout_ports} ({breakout} sub-ports/port)")
        print(f"Physical front panel ports: {args.num_fp_ports}")
        print(f"VRFs: {num_vrfs}")
        print(f"Logical interfaces per VRF: {2 * breakout}")
        print(f"Total logical interfaces: {args.num_fp_ports * breakout}")
        print(f"Base network: {args.base_network}")
        print(f"Flow increment: {args.flow_increment}")
        print(f"Include IPv6: {args.include_ipv6}")
        if args.include_ipv6:
            print(f"IPv6 base network: {args.ipv6_base_network}")
        return

    generate_breakout_snake_config(
        args.output, args.base_network, args.base_mac,
        args.num_fp_ports, breakout, args.flow_increment,
        args.include_ipv6, args.ipv6_base_network
    )


if __name__ == "__main__":
    main()
