# VRF Snake Configuration Generator for N DUTs

## Overview

`generate_vrf_snake_NDUTs.py` extends the single-DUT snake pattern
(`generate_vrf_snake_1DUT.py`) across an arbitrary chain of physical DUTs
wired back-to-back. Traffic enters the **first** DUT's Ethernet0 (TG1) and
exits the **last** DUT's highest-numbered port (TG2); every DUT boundary in
between chains VRF-to-VRF the same way an external loopback cable chains two
VRFs on a single box -- the last port of DUT[k] is wired straight to the
first port of DUT[k+1].

## Why this script exists

Manually continuing `generate_vrf_snake_1DUT.py`'s per-DUT addressing by hand
for a multi-DUT chain breaks: that script always emits `192.168.0.<host>` by
string-concatenating a host counter that resets to a fixed 3rd octet. Once a
chain's total host count runs past 255 (which happens quickly -- three
128-port DUTs need ~385 host addresses) that produces invalid IPv4 literals
like `192.168.0.256` or `192.168.0.512`.

This script computes every address as `start_ip + host_num` via
`ipaddress.IPv4Address` arithmetic instead, so once a DUT's block runs past
`.255` the address correctly rolls into the next octet (e.g.
`192.168.0.250` -> `192.168.1.4`) rather than overflowing a single octet.

It also fixes a second, independent bug in `generate_vrf_snake_1DUT.py`: that
script hardcodes the "high route" destination network to `.64`, which is
only correct for the original 64-port/32-VRF default -- for a 128-port DUT
it silently generates a route to a network nothing is actually attached to.
Here the high-route destination is derived dynamically from the actual
number of VRFs in the whole chain.

## Usage

```bash
./generate_vrf_snake_NDUTs.py \
    --dut-names seag205,seag206,seag207 \
    --ports-per-dut 128 \
    --start-ip 192.168.0.0 \
    --include-ipv6 --start-ipv6 2001:192:168:: \
    --output-dir ./chain3
```

This writes `snake_seag205.json`, `snake_seag206.json`, `snake_seag207.json`
into `./chain3/`, and prints:

- the TGen attachment points (which DUT/port TG1 and TG2 connect to, and
  their assigned IPs)
- every physical cable needed: internal loopbacks (same DUT, consecutive
  VRFs) and cross-DUT links (last port of one DUT to first port of the next)
- per-DUT VRF/interface/static-route counts

Add `--dry-run` to see the same plan without writing any files.

### Key arguments

| Argument | Default | Description |
|----------|---------|--------------|
| `--dut-names` | `dut1,dut2,...` | Comma-separated DUT names; drives output filenames and cable labels |
| `--num-duts` | `2` | Number of DUTs, if `--dut-names` isn't given |
| `--ports-per-dut` | `128` | Ports per DUT (single flow: 2 interfaces per VRF) |
| `--start-ip` | `192.168.0.0` | First IPv4 address of the chain (DUT1's Ethernet0) -- this is the "starting IP" input the chain needs |
| `--include-ipv6` / `--start-ipv6` | off / `2001:192:168::` | Mirror IPv6 (/127) addressing |
| `--base-mac` / `--mac-dut-stride` | `00:00:00:ab:00:00` / `0x040000` | MAC generation; each DUT gets its own MAC range so devices don't collide |
| `--output-dir` / `--output-prefix` | `.` / `snake` | Where files land and how they're named |

## Addressing model

Every global VRF index `g` (0-based, counted across the whole chain, not
per-DUT) gets a host-number pair, identical in shape to the single-DUT
script's per-VRF sequence:

- `g == 0` (the very first VRF, on DUT1): hosts `(0, 2)`
- `g >= 1`: hosts `(2g+1, 2g+2)`

VRF `g`'s second interface and VRF `g+1`'s first interface always land in
the same `/31` (or `/127`) subnet -- that shared subnet **is** the physical
cable between them, whether that cable is an internal loopback (same DUT) or
a cross-DUT link (last port of DUT[k] to first port of DUT[k+1]).

Static routes:
- The very first VRF in the chain is directly attached to TG1, so it only
  gets a route pointing *forward* (toward TG2's subnet).
- The very last VRF in the chain is directly attached to TG2, so it only
  gets a route pointing *backward* (toward TG1's subnet).
- Every VRF in between -- including "Vrf1" and the last VRF on every
  interior DUT, which are NOT the global first/last -- gets both routes,
  exactly like `Vrf2..Vrf(N-1)` in the single-DUT script.

VRF names are **not** globally unique -- every DUT reuses `Vrf1..VrfM`
locally (matching the existing single-DUT convention), since VRFs on
different physical devices can't collide with each other.

## Limitations

- Single-flow only (2 interfaces per VRF); dual-flow chaining across DUTs
  isn't implemented.
- `--ports-per-dut` must be the same for every DUT in the chain.
