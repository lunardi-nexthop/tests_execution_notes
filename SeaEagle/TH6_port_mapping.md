# TH6 port-mapping

Goal: verify the lane-mapping (logical port ↔ physical lane ↔ port-macro/core) on a
TH6 device (seag159). All Broadcom commands run via `docker exec syncd bcmcmd "..."`.

## 1. Discover the diag shell's command surface

```bash
docker exec syncd bcmcmd 'help'
```

## 2. Reach the LT (logical table) ops

The classic drivshell doesn't expose LT ops directly — you have to drop into the
nested BCM LT shell (`bsh`):

```bash
docker exec syncd bcmcmd 'help BcmltSHell'   # -> usage: bsh [-c <command>]
docker exec syncd bcmcmd "bsh -c '?'"        # -> lists lt, pt, and other bsh-only commands
docker exec syncd bcmcmd "bsh -c 'help lt'"  # -> lt <table> traverse [-l] syntax
```

## 3. Find the relevant logical tables

```bash
docker exec syncd bcmcmd "bsh -c 'lt list -b PC_'"
# -> PC_PORT_PHYS_MAP, PC_PHYS_PORT, PC_PORT, PC_PM_CORE, etc.

docker exec syncd bcmcmd "bsh -c 'lt list -d PC_PHYS_PORT'"
# field docs: PC_PHYS_PORT_ID -> (PC_PM_ID, PM_PHYS_PORT)
```

## 4. Dump the two tables that give the mapping

```bash
docker exec syncd bcmcmd "bsh -c 'lt PC_PORT_PHYS_MAP traverse -l'"
# logical PORT_ID <-> PC_PHYS_PORT_ID (130 entries)

docker exec syncd bcmcmd "bsh -c 'lt PC_PHYS_PORT traverse -l'"
# PC_PHYS_PORT_ID -> PC_PM_ID (datapath) + PM_PHYS_PORT (lane-in-core) (1062 entries)
```

## 5. Cross-reference with SONiC CONFIG_DB

```bash
sonic-db-cli CONFIG_DB hget "PORT|EthernetN" lanes
```

SONiC's `lanes` values are literally the same numbering space as the ASIC's
`PC_PHYS_PORT_ID`, so the two datasets can be joined directly.

## Verification result

Lane-mapping is correctly defined — **zero anomalies across all 129 ports**.

For every interface, all 8 (or 4, for the mgmt port) physical lanes resolve to one
single, consistent `PC_PM_ID` (the port-macro/datapath core), with `PM_PHYS_PORT`
running sequentially 0,1,2,...,7 — i.e. no interface has lanes split across two
different cores, and no core is missing a lane in sequence.
