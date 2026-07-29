# TH6 Broadcom commands

Notes on driving the Broadcom diag shell on a Tomahawk-6 (TH6) SONiC device.
All commands are executed from the host through the syncd container:

```bash
docker exec syncd bcmcmd '<command>'
```

## The two shells

- **drivshell** — what `bcmcmd` talks to directly. `help` lists its command surface.
- **BCM LT shell (`bsh`)** — nested shell reachable from drivshell; this is where the
  logical-table (`lt`) and physical-table (`pt`) operations live. The classic drivshell
  does *not* expose LT ops directly.

```bash
docker exec syncd bcmcmd 'help'                # drivshell commands
docker exec syncd bcmcmd 'help BcmltSHell'     # -> usage: bsh [-c <command>]
docker exec syncd bcmcmd "bsh -c '?'"          # bsh-only commands (lt, pt, ...)
docker exec syncd bcmcmd "bsh -c 'help lt'"    # lt <table> traverse [-l] syntax
```

## Useful `lt` idioms

```bash
docker exec syncd bcmcmd "bsh -c 'lt list -b <PREFIX>'"   # list tables by name prefix
docker exec syncd bcmcmd "bsh -c 'lt list -d <TABLE>'"    # field docs for a table
docker exec syncd bcmcmd "bsh -c 'lt <TABLE> traverse -l'" # dump all entries
```

## Topics

- [TH6 port-mapping](TH6_port_mapping.md) — logical port ↔ physical lane ↔ port-macro
  mapping via `PC_*` tables, cross-checked against SONiC CONFIG_DB.
- [TH6 L1/physical-layer troubleshooting](TH6_L1_troubleshooting.md) — `phydiag`/`dsc`,
  PRBS, eye scan, FEC/BER, TX FIR tuning, link training.
