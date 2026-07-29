# TH6 L1/physical-layer troubleshooting

Practical `bcmcmd`/diag-shell commands for chasing link-down and signal-integrity issues
on Sea Eagle's TH6 (Tomahawk-6-P, BCM78910) SONiC device. Every command below was run and
its output captured live on **seag158** — do the same before trusting a command that isn't
already in this file; other Broadcom docs/runbooks (including ones for other TH6/TH5
boxes) turned out to have wrong shell (`bsh` vs `dsh`), wrong argument (`EthernetX` vs
logical port number), or just plain different output on this platform. All commands run
from the host through the syncd container:

```bash
docker exec syncd bcmcmd '<command>'
```

Two nested shells matter (see [TH6 Broadcom commands](TH6_broadcom_commands.md)):
`bsh` for `lt`/`pt` logical-table ops, `dsh` for the `phydiag` serdes toolkit. **On
seag158, `ps`, `lt ... PORT_ID==`, and `phydiag` all take the ASIC's numeric logical
port, not the `EthernetX` alias** — passing `Ethernet256` gives
`PortStat: Error: unrecognized port bitmap: Ethernet256` / `ERROR: Failed to parse field
PORT_ID==Ethernet256`. SONiC-native commands (`show ...`, `dump state port`, `sfputil`)
do accept the alias directly.

## 0. Find the ASIC logical port number for an interface

This is the step every other section depends on. Get the interface's first lane from
CONFIG_DB (this is the same number as the ASIC's `PC_PHYS_PORT_ID`, see
[TH6 port-mapping](TH6_port_mapping.md)), then resolve it to the logical port via
`PC_PORT_PHYS_MAP`:
```bash
sonic-db-cli CONFIG_DB hget "PORT|Ethernet256" lanes
# -> 233,234,235,236,237,238,239,240  (first lane = PC_PHYS_PORT_ID)

docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_PHYS_MAP traverse -l PC_PHYS_PORT_ID==233'"
# -> PC_PHYS_PORT_ID=0xe9(233)  PORT_ID=0x7e(126)   <- 126 is the logical port
```
(The CONFIG_DB `index` field, e.g. `33` for `Ethernet256`/`etp33`, is SONiC's own
front-panel numbering — it is **not** the ASIC logical port and won't work in any command
below. Verified: `ps 33` also errors with `unrecognized port bitmap`.)

Everything below uses **126** (`Ethernet256`, up, 8x100G lanes, RS544-2xN FEC, DAC/copper)
as the worked example — swap in the logical port you resolved for your own interface.

## 1. System health

```bash
docker ps                                   # orchagent/syncd/xcvrd containers up?
ps aux | grep xcvrd                         # transceiver daemon running?
docker exec syncd bcmcmd 'ps'               # errors immediately if syncd/ASIC driver is down
```

## 2. Interface config vs. what the ASIC actually programmed

```bash
dump state port Ethernet256 -t              # CONFIG_DB + APPL_DB + ASIC_DB + STATE_DB (alias OK here)
docker exec syncd bcmcmd 'ps 126'           # drivshell port-status table (needs logical port, see step 0)
```
Real captured output (seag158, `Ethernet256`, 8-lane 800G port):
```
              ena/        speed/ link auto    STP                  lrn             max    cut                 loop
        port  link  Lns   duplex scan neg?   state   pause  discrd ops   medium  frame   thru            FEC  back
  d3c28(126)  up     8  800G  FD   HW  No   Forward         Untag   FA Backplane  9122   No    RS544-2xN-ETC
```
**The text prefix in the `port` column (`d3c`, `cd`, `ce`, `xe`, ...) is not a "TH6
naming scheme" — it's the SDK's own port-macro-class label, assigned per-port at ASIC init
time.** Source: `hsdk/hsdk-all/src/bcm/ltsw/port.c`, function `ltsw_port_name_update()` —
every port is stamped based on which `BCMI_LTSW_PORT_TYPE_*` bitmap it falls into:
```c
BCMI_LTSW_DPORT_PBMP_ITER(unit, pbmp, dport, port) {   /* BCMI_LTSW_PORT_TYPE_CDE   */
    sal_snprintf(..., "cd%d", i++);
}
BCMI_LTSW_DPORT_PBMP_ITER(unit, pbmp, dport, port) {   /* BCMI_LTSW_PORT_TYPE_DCCCE */
    sal_snprintf(..., "d3c%d", i++);
}
```
`bcm_int/ltsw/port.h` defines what those classes mean: `DCCCE` is commented literally as
the **800G-class** port-macro (`/*! DCCCE(800) port. */`) → `d3c#`; `CDE` is a lower-speed
class (the ~200G-class port-macro) → `cd#`.

Confirmed this isn't a seag158-vs-seag159 hardware difference — it's the **port_config/
hwsku breakout profile each box booted with**:
- **seag158** = hwsku `NH-4210-F-P128`: 128 native 8-lane/800G ports (`port_config.ini`) →
  classified `DCCCE` at init → `d3c#`.
- **seag159** = hwsku `NH-4210-F-N512`: the same physical cages broken out 4-ways into
  512 ports of 2-lane/200G each (`etp1a/b/c/d` in `port_config.ini`) → classified `CDE`
  at init → `cd#`.
```
root@seag159:/home/admin# bcmcmd 'ps Ethernet0'
ps 54
   cd48( 54)  up     2  200G  FD   HW  No   Forward          None    F Backplane  9122   No        RS544-2xN
```
**Don't hardcode the prefix — only the parenthesized number (the ASIC logical port ID)
is what you use in follow-on `lt`/`phydiag` commands.** If you need to predict the prefix
for a given box, check its hwsku's `port_config.ini` lane count/breakout, not the model
number.

Same data, structured, straight from the LT:
```bash
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_STATUS traverse -l PORT_ID==126'"
```
```
    LINK_TRAINING_DONE=0
    LINK_TRAINING=0
    AUTONEG_DONE=0
    AUTONEG=0
    LOOPBACK=PC_LPBK_NONE
    FEC_MODE=PC_FEC_RS544_2XN_ETC
    REMOTE_FAULT=0
    LOCAL_FAULT=0
    PMD_LANE_RX_LOCK_CHANGE=0
    PMD_LANE_RX_LOCK=0xff(255)
    PMD_RX_LOCK=1
    PHY_DISABLED=0
    MAC_DISABLED=0
    NUM_LANES=8
    SPEED=0xc3500(800000)
    PORT_ID=0x7e(126)
```
The link-manager's own view of PHY link (also confirmed real):
```bash
docker exec syncd bcmcmd "bsh -c 'lt LM_LINK_STATE traverse -l PORT_ID==126'"
# -> LOCAL_FAULT=0  REMOTE_FAULT=0  PHY_LINK=1  LINK_STATE=1  PORT_ID=0x7e(126)
```

Compare number-of-lanes/speed/FEC against the link partner before going any deeper —
most "link down" cases are a config mismatch, not a physical problem. Note this port has
`autoneg=off` in CONFIG_DB, matching `AUTONEG=0` above and `Auto-Neg Mode: disabled` in
`show interfaces autoneg status` — Sea Eagle's copper ports here run forced-speed, not AN.

## 3. Serdes / PMD diagnostics (`phydiag`)

**Quick serdes identification** — one-liner, useful before reaching for the full `dsc`
dump (confirmed live):
```bash
docker exec syncd bcmcmd "dsh -c 'phy info 1'"
```
```
port  mdio    serdes_info
   1: 0x0019  TSCP_G3A0-A0/04/0-1
```
`serdes_info` names the physical port-macro/serdes core (`TSCP_G3A0` here) — this is the
same underlying core `dsc` calls `peregrine3_a0`; different naming layer, same hardware.

**DSC dump** — the single most useful command for "why won't this port link up":
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 dsc'"
```
Real output (truncated to lane 0, healthy link):
```
pm_id = 30
 peregrine3_a0_phy_pmd_info_dump:588 type = 16384 laneMask  = 0xFF
SerDes type          = peregrine3_a0
...
LN (P RX , CDRxN , UC_CFG, UC_STS, RST, STP) SD LCK RXPPM PF(M,L,H) VGA DCO TP(0,1,2) RXFFE(...) DFE(1,2) FLT(M,S) TXPPM TXEQ(...) NLC(U,L) EYE(U,M,L) LINK_TIME SNR BER
 0 (-+P4N ,BRx1:x1, 0x5004, 0x00_0000, 0,0, 01 ) 1  1*   -5 (11, 9,31)  61  -11 (0,44,2) (-23,57,-130,244,30,-23) (13,0) (-2,12) 0 (0,0,0,168,0,0,)(+0,+0) (82,80,80) 504.9 25.52 !chk_en
```
Sea Eagle's serdes core reports as `peregrine3_a0` — don't assume this matches other
TH6/TH5 platforms (other boxes/docs show `peregrine5_pc` or `condor3_pc`; same column
layout, different silicon/microcode). `SD`/`LCK` = signal-detect / CDR lock per lane —
`SD=0` or `LCK=0` on a lane means the serdes never saw a valid signal on that lane; check
the cable/optic and the lane mapping ([TH6 port-mapping](TH6_port_mapping.md)) before
assuming it's a tuning problem.

`dsc` takes an optional mode (`phydiag <port> dsc <option>`, options per on-device help:
`lite|ber|config|cl72|debug|std|state|state_eye|state_lane`). Most just reprint the same
header (not obviously more useful than plain `dsc`), but **`cl72` is genuinely different
and useful** — confirmed live, it gives a clean per-lane link-training/CL72 status instead
of the wall of serdes numbers, good for isolating "is this stuck in link training":
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 dsc cl72'"
```
```
***************************
** LANE 0 CL93n72 Status **
***************************
linktrn_signal_detect         = 1   (1 = Link training FSM in SEND_DATA state;     0 = Link in training state)
linktrn_ieee_training_failure = 0   (1 = Training failure detected;                0 = Training failure not detected)
linktrn_ieee_training_status  = 0   (1 = Start-up protocol in progress;            0 = Start-up protocol complete)
linktrn_ieee_receiver_status  = 0   (1 = Receiver trained and ready to receive;    0 = Receiver training)
```
(repeats per lane). A lane stuck with `linktrn_signal_detect=0` and
`linktrn_ieee_training_status=1` is stuck *in* link training and never reached
`SEND_DATA` — a different failure mode than a lane that's simply unlocked (`dsc`'s
`SD`/`LCK` columns).

**PRBS** (pattern-generator/checker, doesn't need the far end configured for real traffic —
canonical syntax is `Polynomial=<pval>`, though `p=` works as a prefix-matched shorthand):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbs get lane=0-7'"
```
On a port that was never put into PRBS mode this correctly comes back as a failure, not
a hang — don't read this as a link problem:
```
126 : PRBS Failed!
```
To actually run a PRBS check you must `set` it first (this takes the port out of normal
traffic — only do this on a port you know is idle/not carrying real traffic):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbs set Polynomial=31 lane=0-7'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbs get lane=0-7'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbs clear lane=0-7'"
```
Running BER estimate instead of one-shot pass/fail — same `set` caveat applies:
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbsstat start Interval=10'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbsstat counters'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbsstat ber'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 prbsstat stop'"
```
Faster alternative to waiting out a long `prbsstat` run — **`berproj`** projects a BER
estimate from an error histogram once PRBS is locked (per on-device help; requires PRBS
already running and locked, so it shares the "not run live on this link" caveat as PRBS
`set` above):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 berproj HistogramErrorThreshold=0 SampleTime=10'"
```
(`HistogramErrorThreshold` is 3-7, or `0` for auto mode, per the on-device help text.)

**Eye scan** — confirmed safe to run on a live link (link stayed up, no traffic
interruption seen). On seag158 this platform doesn't support a full 2-D eye scan and
falls back to an "eye slice" — a single vertical voltage histogram, not the horizontal
BER-margin plot some other Broadcom docs describe:
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 eyescan type=fast lane=0'"
```
```
2-D eye scan is not supported, running eye slice instead of eye scan
 Each character N represents approximate error rate 1e-N at that location
   191mV : 1.0
   ...
     5mV :  +      <- widest/cleanest point in the eye, near mid-swing
   ...
  -191mV : 1.0
```
Read it as: error rate should climb steeply (higher digit / `:`/`+` marks) as you move
away from the eye center towards the rails — a shallow, noisy-looking profile across the
whole voltage range indicates a closing eye (marginal signal).

**Link Cable Analysis Tool** — per-lane channel/signal analysis (not verified live on
seag158 — puts the lane into a loopback mode, so only run it on a port that's genuinely
idle):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 linkcat mode=lpbk lane=0-7'"
```

**Verbose per-port event logging** — confirmed live, read-only, safe on a running link.
Useful when chasing an intermittent flap: bump a port's event-log verbosity, reproduce,
then check the syncd/kernel log for serdes/link-training events instead of only the final
up/down state:
```bash
docker exec syncd bcmcmd "dsh -c 'phy event_log_mask 126'"        # read current mask
# -> usr_event_log_group_mask: 0x2e0ffff
docker exec syncd bcmcmd "dsh -c 'phy event_log_mask 126 <val>'"  # set (not run live — leave at default unless actively debugging)
```

## 4. FEC health (post-link-up BER)

SONiC CLI (preferred — no diag shell needed; column set on seag158's build also includes
`FEC_PRE_BER_MAX`, `FLR(O)`, `FLR(P)`, `FEC_MAX_T` — expect this to vary by SONiC version):
```bash
show interfaces counters fec-stats
show interfaces counters fec-histogram Ethernet256
```
Raw ASIC-level equivalents (confirmed live, healthy link — all zero):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 fecstat start Interval=5'"   # "FECSTAT thread started ..."
docker exec syncd bcmcmd "dsh -c 'phydiag 126 fecstat counters'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 fecstat ber'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 fecstat stop'"
```
`counters`/`ber` return `FECStat not started` if you skip `start` first — that's the
diag-shell CLI complaining, not the ASIC.

"Flight Data Recorder" — longer-run FEC symbol-error-distribution histogram (confirmed
live). Note: on this device `bin_group` is accepted but ignored
(`FDRStat: bin_group is not used on this device.`) — you still get the full per-symbol-
error-count histogram (`S0`..`S16`) regardless of what you pass:
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 fdrstat start Interval=5'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 fdrstat counters'"
docker exec syncd bcmcmd "dsh -c 'phydiag 126 fdrstat stop'"
```

FEC auto-collect interval is controlled via `PC_PORT_MONITOR`/`PC_PORT_DIAG_CONTROL` (on
seag158 today, `lt PC_PORT_MONITOR lookup` shows `FEC_STAT_AUTO_COLLECT_INTERVAL_S=1` —
don't assume a specific default without checking your own box first). You must disable
auto-collect on the affected ports before changing the interval (it restarts the
collection thread), then re-enable:
```bash
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_MONITOR lookup'"
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_DIAG_CONTROL update PORT_ID=126 FEC_STAT_AUTO_COLLECT=0'"
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_MONITOR update FEC_STAT_AUTO_COLLECT_INTERVAL_S=1'"
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_DIAG_CONTROL update PORT_ID=126 FEC_STAT_AUTO_COLLECT=1'"
```
(Sequence is from [NOS-3870](https://nexthopai.atlassian.net/browse/NOS-3870), which
tracked this default being an unexpectedly long 20s on some TH6 builds — do it per-port
in a loop if you need it across a whole box.)

## 5. TX FIR / signal-integrity tuning

Read current TX FIR taps — confirmed live, real field names differ from generic SDK docs
(`nlc_upper`/`nlc_lower`, not `nlc_%`):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 tx_taps get lane=0'"
```
```
port lane 126.0 : TX TAP
nlc_upper  0
nlc_lower  0
pre3 0
pre2 0
pre1 0
main 168
post1 0
post2 0
post3 32767
```
(`post3 32767` here just means "unset/default", not a real tap value — don't be alarmed
by it.) Setting taps (not run live — this changes an active link's signal integrity in
place; only do this on a port you're actively tuning):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag 126 tx_taps set pre3=0 pre2=0 pre1=-1 main=120 post1=0 post2=1 post3=0 lane=0'"
```
For persistent tuning, push the equivalent values through SONiC's `media_settings.json`
and `config reload` rather than poking the diag shell by hand — that's what actually
survives a reboot/reload.

There's also `phydiag <port> nr_er_lmt_bias get|set bias=<val> [osr=<val>] [lane=<lane-range>]`
— per on-device help, this tunes the NR/ER decision threshold used during link training
(relevant to long/lossy DAC interop tuning). **Tried live on both seag158 and seag159 and
it failed with "Operation failed" on every port tested** — these ports aren't running in
an ER/NR link-training mode, so either it needs that mode enabled first or it's simply not
applicable here. Don't trust this one without re-verifying on a port actually doing ER/NR
training.

## 6. Transceiver / optics (DOM)

```bash
show interface transceiver eeprom --dom Ethernet256
show int transceiver status --verbose Ethernet256
sudo sfputil show eeprom --dom -p Ethernet256
```
Check: `DataPathActivated` per lane, `ConfigSuccess`, and DOM Tx/Rx power + bias against
the module's own alarm/warning thresholds (printed by the same commands). Ethernet256 on
seag158 is actually a copper/DAC port (`Application Advertisement: 800G-ETC-CR8 ...
Copper cable`) — power/bias figures don't apply there; go straight to PRBS/eyescan/dsc
above for copper.

## 7. Link training / autoneg

```bash
show interfaces autoneg status
```
Real captured column for a forced-speed copper port: `Auto-Neg Mode: disabled` (not
`N/A` — that generic value is from a different platform/build). To turn link training on:
```bash
sudo config interface link-training EthernetX on
```
`PC_PORT_STATUS` (section 2) has the ground truth — `AUTONEG`/`AUTONEG_DONE` and
`LINK_TRAINING`/`LINK_TRAINING_DONE` bits. A mismatch (LT/AN on for one side, off for the
other) can leave a link up on some cable lengths/types and down on others — confirm both
ends agree before chasing anything else.

## 8. Cold-reset the ASIC (last resort, not run live)

Only when the diag shell itself is unresponsive, or you genuinely need a fresh power-on —
this bounces the whole chip and takes every port down. **Not verified live** (deliberately
not run against a shared/in-use box) — confirm on an idle unit before trusting it:
```bash
fpga write32 0000:04:00.0 0x8 0x22    # TH6 into reset
fpga write32 0000:04:00.0 0x8 0x422   # TH6 out of reset, sequencing handled by FPGA
```

## Reference

- Command implementations: `hsdk/hsdk-all/libs/sdklt/bcma/include/bcma/bcmpc/bcma_bcmpccmd_phy.h`,
  `..._phydiag.h`, `hsdk/hsdk-all/libs/sdklt/bcma/bcmpc/cmd/bcma_bcmpccmd_portstatus.c`
  (`broadcom-sai-sdk` repo)
- Internal runbook: TraceIQ `runbooks/nexthop_internal/Layer_1_Troubleshooting_Guide.md`
- [TH6 port-mapping](TH6_port_mapping.md) — rule out a lane/port-macro mapping problem
  before treating a serdes symptom as a real signal-integrity issue
- All numbered examples above captured live against **seag158**, logical port 126
  (`Ethernet256`/`etp33`), on 2026-07-29
