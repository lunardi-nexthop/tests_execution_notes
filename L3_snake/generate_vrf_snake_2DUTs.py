#!/usr/bin/env python3
"""
Generate SONiC NOS JSON configs for two DUTs:

- DUT1:  vrf-ge101.json  (VRF names: Vrf1..Vrf32)
- DUT2:  vrf-ge102.json  (VRF names: Vrf_1..Vrf_32)

Topology:
- 32 VRFs.
- Each VRF has 2 ports per DUT, spaced by 8:
  * DUT1: Ethernet0,8,16,...,504  (0 is TG1; 504 is last VRF’s right link)
  * DUT2: Ethernet0,8,16,...,504  (0 is TG2; 504 is last VRF’s left link)
- Traffic generators:
  * TG1 ↔ DUT1 Ethernet0
  * TG2 ↔ DUT2 Ethernet0
- Addressing defaults match your JSONs:
  * TG1–DUT1: 192.168.0.0/31   (DUT1 = .0)
  * DUT1–DUT2 links: start 192.168.0.2/31, increment by 2
  * TG2–DUT2: 192.168.0.254/31 (DUT2 = .254)

Use --family v6 and provide IPv6 addresses to generate v6 configs.
"""

import argparse
import ipaddress
import json
from collections import OrderedDict

def gen_configs(
    num_vrfs: int = 32,
    family: str = "ipv4",
    tg1_ip_str: str = "192.168.0.0",      # DUT1 IP to TG1
    tg2_ip_str: str = "192.168.0.254",    # DUT2 IP to TG2
    interconnect_start_str: str = "192.168.0.2",
    prefixlen_v4: int = 31,
    prefixlen_v6: int = 127,
):
    ip_version = 4 if family == "ipv4" else 6
    tg1_ip = ipaddress.ip_address(tg1_ip_str)
    tg2_ip = ipaddress.ip_address(tg2_ip_str)
    inter_base = ipaddress.ip_address(interconnect_start_str)
    step = 2  # distance between peers in a /31 or /127

    prefixlen = prefixlen_v4 if ip_version == 4 else prefixlen_v6
    tg1_net = ipaddress.ip_network(f"{tg1_ip}/{prefixlen}", strict=False)
    tg2_net = ipaddress.ip_network(f"{tg2_ip}/{prefixlen}", strict=False)

    # Port layout on each DUT
    def left_ports_for_vrf(i: int):
        # DUT1: VRF i → Ethernet(16*(i-1)) and +8
        p0 = 16 * (i - 1)
        p1 = p0 + 8
        return p0, p1

    def right_ports_for_vrf(i: int):
        # DUT2: VRF 1..N-1 → Ethernet(8+16*(i-1)) and +8
        #       VRF N      → Ethernet0 (TG2) and 504 (cross-link)
        if i < num_vrfs:
            p0 = 8 + 16 * (i - 1)
            p1 = p0 + 8
        else:
            p0 = 0
            p1 = 504
        return p0, p1

    # Per-port IP addressing
    def left_ip_for_port(p: int):
        if p == 0:
            return tg1_ip
        idx = p // 8 - 1           # 8,16,...,504 → 0..62
        return inter_base + step * idx

    def right_ip_for_port(p: int):
        if p == 0:
            return tg2_ip
        idx = p // 8 - 1
        return inter_base + step * idx + 1

    # DUT1 (vrf-ge101.json) ----------------------------------------------
    iface_left = OrderedDict()
    for i in range(1, num_vrfs + 1):
        vrf = f"Vrf{i}"
        p0, p1 = left_ports_for_vrf(i)
        for p in (p0, p1):
            name = f"Ethernet{p}"
            iface_left[name] = {"vrf_name": vrf}
            ip_ = left_ip_for_port(p)
            iface_left[f"{name}|{ip_}/{prefixlen}"] = {}

    vrf_left = OrderedDict((f"Vrf{i}", {}) for i in range(1, num_vrfs + 1))

    sr_left = OrderedDict()
    # Routes towards TG1 network (all VRFs except Vrf1, which is directly attached)
    for i in range(2, num_vrfs + 1):
        p0, _ = left_ports_for_vrf(i)
        key = f"Vrf{i}|{tg1_net.with_prefixlen}"
        sr_left[key] = {
            "blackhole": "false",
            "distance": "0",
            "ifname": f"Ethernet{p0}",
            "nexthop": str(right_ip_for_port(p0)),
            "nexthop-vrf": f"Vrf{i}",
        }
    # Routes towards TG2 network (all VRFs)
    for i in range(1, num_vrfs + 1):
        _, p1 = left_ports_for_vrf(i)
        key = f"Vrf{i}|{tg2_net.with_prefixlen}"
        sr_left[key] = {
            "blackhole": "false",
            "distance": "0",
            "ifname": f"Ethernet{p1}",
            "nexthop": str(right_ip_for_port(p1)),
            "nexthop-vrf": f"Vrf{i}",
        }

    config_left = {
        "INTERFACE": iface_left,
        "VRF": vrf_left,
        "STATIC_ROUTE": sr_left,
    }

    # DUT2 (vrf-ge102.json) ----------------------------------------------
    iface_right = OrderedDict()
    for i in range(1, num_vrfs + 1):
        vrf = f"Vrf_{i}"
        p0, p1 = right_ports_for_vrf(i)
        for p in (p0, p1):
            name = f"Ethernet{p}"
            iface_right[name] = {"vrf_name": vrf}
            ip_ = right_ip_for_port(p)
            iface_right[f"{name}|{ip_}/{prefixlen}"] = {}

    vrf_right = OrderedDict((f"Vrf_{i}", {}) for i in range(1, num_vrfs + 1))

    sr_right = OrderedDict()
    # VRFs 1..N-1: routes to TG1 and TG2
    for i in range(1, num_vrfs):
        p0, p1 = right_ports_for_vrf(i)
        vrf = f"Vrf_{i}"

        key1 = f"{vrf}|{tg1_net.with_prefixlen}"
        sr_right[key1] = {
            "blackhole": "false",
            "distance": "0",
            "ifname": f"Ethernet{p0}",
            "nexthop": str(left_ip_for_port(p0)),
            "nexthop-vrf": vrf,
        }

        key2 = f"{vrf}|{tg2_net.with_prefixlen}"
        sr_right[key2] = {
            "blackhole": "false",
            "distance": "0",
            "ifname": f"Ethernet{p1}",
            "nexthop": str(left_ip_for_port(p1)),
            "nexthop-vrf": vrf,
        }

    # VRF_N (connected to TG2): route back to TG1 only via cross-link
    i = num_vrfs
    _, p1 = right_ports_for_vrf(i)
    vrf = f"Vrf_{i}"
    key_last = f"{vrf}|{tg1_net.with_prefixlen}"
    sr_right[key_last] = {
        "blackhole": "false",
        "distance": "0",
        "ifname": f"Ethernet{p1}",
        "nexthop": str(left_ip_for_port(p1)),
        "nexthop-vrf": vrf,
    }

    config_right = {
        "INTERFACE": iface_right,
        "VRF": vrf_right,
        "STATIC_ROUTE": sr_right,
    }

    return config_left, config_right

def main():
    parser = argparse.ArgumentParser(
        description="Generate SONiC NOS VRF configs for two DUTs."
    )
    parser.add_argument("--family", choices=["v4", "v6"], default="v4",
                        help="IP family (default: v4)")
    parser.add_argument("--num-vrfs", type=int, default=32)
    parser.add_argument("--tg1-ip", help="DUT1 IP towards TG1")
    parser.add_argument("--tg2-ip", help="DUT2 IP towards TG2")
    parser.add_argument("--interconnect-start",
                        help="DUT1 IP of first DUT1–DUT2 link")
    parser.add_argument("--v4-prefixlen", type=int, default=31)
    parser.add_argument("--v6-prefixlen", type=int, default=127)
    parser.add_argument("--left-out", default="vrf-ge101.json")
    parser.add_argument("--right-out", default="vrf-ge102.json")
    args = parser.parse_args()

    if args.family == "v4":
        family = "ipv4"
        tg1 = args.tg1_ip or "192.168.0.0"
        tg2 = args.tg2_ip or "192.168.0.254"
        inter = args.interconnect_start or "192.168.0.2"
    else:
        family = "ipv6"
        tg1 = args.tg1_ip or "2001:db8::"
        tg2 = args.tg2_ip or "2001:db8::fe"
        inter = args.interconnect_start or "2001:db8::2"

    left_cfg, right_cfg = gen_configs(
        num_vrfs=args.num_vrfs,
        family=family,
        tg1_ip_str=tg1,
        tg2_ip_str=tg2,
        interconnect_start_str=inter,
        prefixlen_v4=args.v4_prefixlen,
        prefixlen_v6=args.v6_prefixlen,
    )

    with open(args.left_out, "w") as f:
        json.dump(left_cfg, f, indent=2)
    with open(args.right_out, "w") as f:
        json.dump(right_cfg, f, indent=2)

    print(f"Wrote {args.left_out} (DUT1) and {args.right_out} (DUT2)")

if __name__ == "__main__":
    main()
