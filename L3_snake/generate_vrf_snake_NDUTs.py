#!/usr/bin/env python3
"""
Generate SONiC JSON configs for an N-DUT L3 VRF snake chain.

Extends the single-DUT snake pattern (generate_vrf_snake_1DUT.py) across
several physical DUTs wired back-to-back. Traffic enters the FIRST DUT's
Ethernet0 (TG1) and exits the LAST DUT's highest-numbered port (TG2).
Interior DUT boundaries chain VRF-to-VRF the same way an external loopback
cable chains two VRFs on a single box: the last port of DUT[k] is wired to
the first port of DUT[k+1].

This fixes the bug from manually continuing generate_vrf_snake_1DUT.py's
per-DUT host numbering by hand: that script emits "192.168.0.<host>" by
string concatenation. Once a chain's host count runs past 255 that produces
invalid literals like ".256" or ".512". Here, every address is
`start_ip + host_num` computed via ipaddress.IPv4Address arithmetic, so once
a DUT's block runs past .255 the address correctly rolls into the next octet.

Example -- 3x seag205/206/207, 128 ports each, single flow:

    ./generate_vrf_snake_NDUTs.py \
        --dut-names seag205,seag206,seag207 \
        --ports-per-dut 128 \
        --start-ip 192.168.0.0 \
        --include-ipv6 --start-ipv6 2001:192:168:: \
        --output-dir /tmp/snake3
"""

import argparse
import ipaddress
import json
import sys
from collections import OrderedDict


def generate_mac(base_mac, offset):
    mac_int = int(base_mac.replace(':', ''), 16) + offset
    mac_hex = f"{mac_int:012x}"
    return ':'.join(mac_hex[i:i + 2] for i in range(0, 12, 2))


def host_pair(g):
    if g == 0:
        return 0, 2
    base = 2 * g + 1
    return base, base + 1


def build_chain(num_duts, ports_per_dut, start_ip, base_mac, mac_dut_stride,
                 include_ipv6, start_ipv6):
    if ports_per_dut % 2 != 0:
        raise ValueError("--ports-per-dut must be even (2 interfaces per VRF)")

    vrfs_per_dut = ports_per_dut // 2
    total_vrfs = num_duts * vrfs_per_dut

    start_addr = ipaddress.IPv4Address(start_ip)
    start_addr6 = ipaddress.IPv6Address(start_ipv6) if include_ipv6 else None

    low_net_host = 0
    high_net_host = 2 * total_vrfs

    def ip4(host):
        return start_addr + host

    def ip6(host):
        return start_addr6 + host if include_ipv6 else None

    low_net4 = f"{ip4(low_net_host)}/31"
    high_net4 = f"{ip4(high_net_host)}/31"
    low_net6 = f"{ip6(low_net_host)}/127" if include_ipv6 else None
    high_net6 = f"{ip6(high_net_host)}/127" if include_ipv6 else None

    dut_configs = [OrderedDict([('INTERFACE', OrderedDict()),
                                 ('VRF', OrderedDict()),
                                 ('STATIC_ROUTE', OrderedDict())])
                   for _ in range(num_duts)]

    cables = []
    tg_info = {}

    for g in range(total_vrfs):
        dut_id = g // vrfs_per_dut
        local_vrf_index = g % vrfs_per_dut
        vrf_name = f"Vrf{local_vrf_index + 1}"
        cfg = dut_configs[dut_id]

        cfg['VRF'][vrf_name] = {}

        p0 = local_vrf_index * 16
        p1 = p0 + 8
        if_a = f"Ethernet{p0}"
        if_b = f"Ethernet{p1}"

        host_a, host_b = host_pair(g)
        mac_offset = dut_id * mac_dut_stride
        for if_name, host, eth_num in ((if_a, host_a, p0), (if_b, host_b, p1)):
            cfg["INTERFACE"][if_name] = {
                "mac_addr": generate_mac(base_mac, mac_offset + eth_num),
                "vrf_name": vrf_name,
            }
            cfg["INTERFACE"][f"{if_name}|{ip4(host)}/31"] = {}
            if include_ipv6:
                cfg["INTERFACE"][f"{if_name}|{ip6(host)}/127"] = {}

        is_first = (g == 0)
        is_last = (g == total_vrfs - 1)
        def add_route(dest4, dest6, ifname, nexthop_host):
            cfg["STATIC_ROUTE"][f"{vrf_name}|{dest4}"] = {
                "blackhole": "false",
                "distance": "0",
                "ifname": ifname,
                "nexthop": str(ip4(nexthop_host)),
                "nexthop-vrf": vrf_name,
            }
            if include_ipv6:
                cfg["STATIC_ROUTE"][f"{vrf_name}|{dest6}"] = {
                    "blackhole": "false",
                    "distance": "0",
                    "ifname": ifname,
                    "nexthop": str(ip6(nexthop_host)),
                    "nexthop-vrf": vrf_name,
                }

        if is_first:
            add_route(high_net4, high_net6, if_b, host_b + 1)
        elif is_last:
            add_route(low_net4, low_net6, if_a, host_a - 1)
        else:
            add_route(low_net4, low_net6, if_a, host_a - 1)
            add_route(high_net4, high_net6, if_b, host_b + 1)

        if local_vrf_index > 0:
            prev_local = local_vrf_index - 1
            prev_p1 = prev_local * 16 + 8
            cables.append(f"DUT{dut_id + 1} Ethernet{prev_p1} -- DUT{dut_id + 1} {if_a}  (loopback, {vrf_name} from Vrf{prev_local + 1})")
        elif dut_id > 0:
            prev_dut = dut_id - 1
            prev_last_p1 = (vrfs_per_dut - 1) * 16 + 8
            cables.append(f"DUT{prev_dut + 1} Ethernet{prev_last_p1} -- DUT{dut_id + 1} {if_a}  (cross-DUT link)")
        else:
            tg_info["tg1_dut"] = dut_id + 1
            tg_info["tg1_dut_if"] = if_a
            tg_info["tg1_ip"] = str(ip4(low_net_host + 1))
            if include_ipv6:
                tg_info["tg1_ipv6"] = str(ip6(low_net_host + 1))

        if is_last:
            tg_info["tg2_dut"] = dut_id + 1
            tg_info["tg2_dut_if"] = if_b
            tg_info["tg2_ip"] = str(ip4(high_net_host + 1))
            if include_ipv6:
                tg_info["tg2_ipv6"] = str(ip6(high_net_host + 1))

    return dut_configs, cables, tg_info, vrfs_per_dut, total_vrfs


def main():
    parser = argparse.ArgumentParser(
        description='Generate SONiC JSON configs for an N-DUT L3 VRF snake chain',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--num-duts', type=int, default=None,
                        help='Number of DUTs in the chain (inferred from --dut-names if given)')
    parser.add_argument('--dut-names', type=str, default=None,
                        help='Comma-separated DUT names, e.g. seag205,seag206,seag207')
    parser.add_argument('--ports-per-dut', type=int, default=128,
                        help='Ports per DUT, single flow = 2 interfaces per VRF (default: 128)')
    parser.add_argument('--start-ip', type=str, default='192.168.0.0',
                        help='First IPv4 address of the chain, i.e. DUT1 Ethernet0 (default: 192.168.0.0)')
    parser.add_argument('--include-ipv6', action='store_true',
                        help='Also generate IPv6 (/127) addressing')
    parser.add_argument('--start-ipv6', type=str, default='2001:192:168::',
                        help='First IPv6 address of the chain (default: 2001:192:168::)')
    parser.add_argument('--base-mac', type=str, default='00:00:00:ab:00:00',
                        help='Base MAC address (default: 00:00:00:ab:00:00)')
    parser.add_argument('--mac-dut-stride', type=lambda x: int(x, 0), default=0x040000,
                        help='Integer added to the MAC base per DUT index (default: 0x040000)')
    parser.add_argument('--output-dir', type=str, default='.',
                        help='Directory to write per-DUT JSON files into (default: current dir)')
    parser.add_argument('--output-prefix', type=str, default='snake',
                        help='Filename prefix; files written as prefix_dutname.json (default: snake)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print the plan without writing files')

    args = parser.parse_args()

    if args.dut_names:
        dut_names = [n.strip() for n in args.dut_names.split(',') if n.strip()]
        num_duts = len(dut_names)
        if args.num_duts and args.num_duts != num_duts:
            print(f"Error: --num-duts {args.num_duts} conflicts with {num_duts} names in --dut-names", file=sys.stderr)
            sys.exit(1)
    else:
        num_duts = args.num_duts or 2
        dut_names = [f"dut{i + 1}" for i in range(num_duts)]

    if num_duts < 1:
        print("Error: need at least 1 DUT", file=sys.stderr)
        sys.exit(1)

    try:
        dut_configs, cables, tg_info, vrfs_per_dut, total_vrfs = build_chain(
            num_duts=num_duts,
            ports_per_dut=args.ports_per_dut,
            start_ip=args.start_ip,
            base_mac=args.base_mac,
            mac_dut_stride=args.mac_dut_stride,
            include_ipv6=args.include_ipv6,
            start_ipv6=args.start_ipv6,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Chain of {num_duts} DUTs ({dut_names}), {args.ports_per_dut} ports each")
    print(f"VRFs per DUT: {vrfs_per_dut}   Total VRFs in chain: {total_vrfs}")

    tg1_ipv6 = tg_info.get('tg1_ipv6', '')
    tg2_ipv6 = tg_info.get('tg2_ipv6', '')
    tg1_extra = f" / {tg1_ipv6}" if args.include_ipv6 else ""
    tg2_extra = f" / {tg2_ipv6}" if args.include_ipv6 else ""

    tg1_dut_name = dut_names[tg_info['tg1_dut'] - 1]
    tg2_dut_name = dut_names[tg_info['tg2_dut'] - 1]
    tg1_if = tg_info['tg1_dut_if']
    tg2_if = tg_info['tg2_dut_if']
    tg1_ip = tg_info['tg1_ip']
    tg2_ip = tg_info['tg2_ip']

    print(f"TG1 -- {tg1_dut_name} {tg1_if}  (TG1 = {tg1_ip}{tg1_extra})")
    print(f"TG2 -- {tg2_dut_name} {tg2_if}  (TG2 = {tg2_ip}{tg2_extra})")
    print()
    print(f"Physical cabling required ({len(cables)} cables):")
    for c in cables:
        for i, name in enumerate(dut_names):
            c = c.replace(f"DUT{i + 1} ", f"{name} ")
        print(f"  {c}")
    print()

    if args.dry_run:
        for i, cfg in enumerate(dut_configs):
            n_if = len([k for k in cfg['INTERFACE'] if '|' not in k])
            n_vrf = len(cfg['VRF'])
            n_sr = len(cfg['STATIC_ROUTE'])
            print(f"{dut_names[i]}: {n_vrf} VRFs, {n_if} interfaces, {n_sr} static routes")
        print()
        print("DRY RUN - no files written")
        return

    import os
    os.makedirs(args.output_dir, exist_ok=True)
    for i, cfg in enumerate(dut_configs):
        fname = f"{args.output_prefix}_{dut_names[i]}.json"
        out_path = os.path.join(args.output_dir, fname)
        with open(out_path, 'w') as f:
            json.dump(cfg, f, indent=2)
        n_if = len([k for k in cfg['INTERFACE'] if '|' not in k])
        n_vrf = len(cfg['VRF'])
        n_sr = len(cfg['STATIC_ROUTE'])
        print(f"Wrote {out_path}  ({n_vrf} VRFs, {n_if} interfaces, {n_sr} static routes)")


if __name__ == "__main__":
    main()
