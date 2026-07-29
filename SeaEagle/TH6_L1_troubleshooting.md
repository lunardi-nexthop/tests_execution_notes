# TH6 L1/physical-layer troubleshooting

Practical `bcmcmd`/diag-shell commands for chasing link-down and signal-integrity issues
on a TH6 (Tomahawk-6, BCM7891x — TH6-P/BCM78910 is Sea Eagle's ASIC, TH6-C/BCM78914 is
Black Kite's) SONiC device. Command syntax below is cross-checked against the Broadcom
HSDK/SAI source (`broadcom-sai-sdk` repo — `bcma_bcmpccmd_phy.h`, `bcma_bcmpccmd_phydiag.h`,
`bcma_bcmpccmd_portstatus.c`) and against real captured output from our own boxes
(golf/humm/blkt testbeds). All commands run from the host through the syncd container:

```bash
docker exec syncd bcmcmd '<command>'
```

Two nested shells matter here (see [TH6 Broadcom commands](TH6_broadcom_commands.md)):
`bsh` for `lt`/`pt` logical-table ops, `dsh` for the `phydiag`/`phy diag` serdes toolkit
(same dispatch — bsh's own help text says "the syntax for 'phy diag' is identical to
'phydiag'"). On our devices the captured PHY/serdes commands consistently go through
`dsh -c`, not `bsh -c` — use `bsh` for `lt` table traversal and `dsh` for `phydiag`.

## Troubleshooting flow

1. System health — are the relevant processes even up
2. Interface config — does CONFIG_DB/APPL_DB/ASIC_DB agree with what's programmed
3. L1 sublayers, top to bottom: PMD/transceiver → PMA/serdes → FEC → RS/MAC

## 1. System health

```bash
docker ps                                   # orchagent/syncd/xcvrd containers up?
ps aux | grep xcvrd                         # transceiver daemon running?
docker exec syncd bcmcmd 'ps'               # errors immediately if syncd/ASIC driver is down
```

## 2. Interface config vs. what the ASIC actually programmed

```bash
dump state port EthernetX -t                # CONFIG_DB + APPL_DB + ASIC_DB + STATE_DB in one dump
docker exec syncd bcmcmd 'ps EthernetX'     # drivshell port-status table
```
```
        port  link  Lns   speed/duplex  scan  auto neg?   ...    FEC         loopback
   d3c0(  1)  up     8    800G  FD       HW   No                 RS544-2xN
```

Same data, structured, straight from the LT (useful for scripting / exact field values):
```bash
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_STATUS traverse -l PORT_ID==EthernetX'"
```
Key fields: `STATUS`, `PMD_RX_LOCK`, `PMD_LANE_RX_LOCK` (per-lane bitmask), `AUTONEG`,
`AUTONEG_DONE`, `LINK_TRAINING`, `LINK_TRAINING_DONE`, `FEC_MODE`, `LOOPBACK`,
`REMOTE_FAULT`, `LOCAL_FAULT`. The link-manager's own view of PHY link:
```bash
docker exec syncd bcmcmd "bsh -c 'lt LM_LINK_STATE traverse -l PORT_ID==EthernetX'"
```

Compare number-of-lanes/speed/FEC against the link partner before going any deeper —
most "link down" cases are a config mismatch, not a physical problem.

## 3. Serdes / PMD diagnostics (`phydiag`)

**DSC dump** — the single most useful command for "why won't this port link up":
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX dsc'"
```
Prints one row per lane:
```
LN (P RX , CDRxN , UC_CFG, UC_STS, RST, STP) SD LCK RXPPM PF(M,L,H) VGA DCO TP(0,1,2)
  RXFFE(n3,n2,n1,m,p1,p2) DFE(1,2) FLT(M,S) TXPPM TXEQ(n3,n2,n1,m,p1,p2) NLC(U,L)
  EYE(U,M,L) LINK_TIME SNR BER
```
`SD`/`LCK` = signal-detect / CDR lock per lane — `SD=0` or `LCK=0` on a lane means the
serdes never saw a valid signal on that lane; check the cable/optic and the lane mapping
([TH6 port-mapping](TH6_port_mapping.md)) before assuming it's a tuning problem. `TXEQ`
is the current TX FIR taps, `EYE`/`SNR`/`BER` are the running link-quality figures.

**PRBS** (pattern-generator/checker, doesn't need the far end configured for real traffic):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX prbs set p=3 lane=0,1'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX prbs get lane=0,1'"
# "268 : PRBS OK!" -> pattern-locked, error-free since last clear/set
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX prbs clear lane=0,1'"
```
Running BER estimate instead of one-shot pass/fail:
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX prbsstat start Interval=10'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX prbsstat counters'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX prbsstat ber'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX prbsstat stop'"
```
If a lane won't lock PRBS at all, that's a hard signal-integrity/cabling problem, not
a config one — cross-check `linkcat` (below) and the physical connection.

**Eye scan** — signal-integrity margin on a locked, quiet link:
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX eyescan type=fast lane=0-7'"
```

**Link Cable Analysis Tool** — per-lane channel/signal analysis, good for telling a bad
cable/lane apart from a bad TX tuning value:
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX linkcat mode=lpbk lane=0-7'"
```

## 4. FEC health (post-link-up BER)

SONiC CLI (preferred — no diag shell needed):
```bash
show interfaces counters fec-stats
show interfaces counters fec-histogram EthernetX
```
Raw ASIC-level equivalents feeding those CLI commands:
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX fecstat start Interval=10'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX fecstat counters'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX fecstat ber'"
```
"Flight Data Recorder" — longer-run FEC symbol-error-distribution histogram (the per-lane
bins behind `fec-histogram`):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX fdrstat start bin_group=both Interval=10'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX fdrstat counters'"
```

FEC auto-collect defaults to a 20s polling interval on TH6. To tighten it while chasing
an intermittent BER event, go through `PC_PORT_MONITOR`/`PC_PORT_DIAG_CONTROL` — you must
disable auto-collect on the affected ports before changing the interval (it restarts the
collection thread), then re-enable:
```bash
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_MONITOR lookup'"
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_DIAG_CONTROL update PORT_ID=EthernetX FEC_STAT_AUTO_COLLECT=0'"
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_MONITOR update FEC_STAT_AUTO_COLLECT_INTERVAL_S=1'"
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_DIAG_CONTROL update PORT_ID=EthernetX FEC_STAT_AUTO_COLLECT=1'"
```
(This is exactly the sequence from [NOS-3870](https://nexthopai.atlassian.net/browse/NOS-3870) —
do it per-port in a loop if you need it across a whole box.)

## 5. TX FIR / signal-integrity tuning

Read/set current TX FIR taps (same command family as `phydiag`, syntax from the HSDK
`PHY`/`PHYDiag` command headers):
```bash
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX tx_taps get lane=0'"
docker exec syncd bcmcmd "dsh -c 'phydiag EthernetX tx_taps set pre3=0 pre2=0 pre1=-1 main=120 post1=0 post2=1 post3=0 lane=0'"
```
For persistent tuning, push the equivalent values through SONiC's `media_settings.json`
and `config reload` rather than poking the diag shell by hand — that's what actually
survives a reboot/reload.

## 6. Transceiver / optics (DOM)

```bash
show interface transceiver eeprom --dom EthernetX
show int transceiver status --verbose EthernetX
sudo sfputil show eeprom --dom -p EthernetX
```
Check: `DataPathActivated` per lane, `ConfigSuccess`, and DOM Tx/Rx power + bias against
the module's own alarm/warning thresholds (printed by the same commands). For copper
(DAC) cables, power/bias figures don't apply — go straight to PRBS/eyescan above.

## 7. Link training / autoneg

```bash
show interfaces autoneg status
sudo config interface link-training EthernetX on
```
`PC_PORT_STATUS` (section 2) has the ground truth — `AUTONEG`/`AUTONEG_DONE` and
`LINK_TRAINING`/`LINK_TRAINING_DONE` bits. A mismatch (LT/AN on for one side, off for the
other) can leave a link up on some cable lengths/types and down on others — confirm both
ends agree before chasing anything else.

## 8. Cold-reset the ASIC (last resort)

Only when the diag shell itself is unresponsive, or you genuinely need a fresh power-on —
this bounces the whole chip and takes every port down:
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
