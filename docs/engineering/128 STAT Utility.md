# BetterCP/M STAT

## Status

Initial stock-compatible implementation with numeric DU selection and the
BetterCP/M `MEM` report. Named-directory aliases remain deferred until the
shared resident named-DU resolver is implemented.

## Commands

The utility implements the CP/M 2.2 STAT operand families:

```text
STAT
STAT filespec [$S|$R/O|$R/W|$SYS|$DIR]
STAT d:
STAT d:=R/O
STAT DSK: | d:DSK:
STAT USR:
STAT DEV:
STAT VAL:
STAT CON:=device: | RDR:=device: | PUN:=device: | LST:=device:
```

`filespec` and disk operands additionally accept BetterCP/M numeric selectors
`5:` and `C3:`. A temporary selection is restored before STAT returns.

## Memory report

`STAT MEM` validates the version-1 BetterCP/M Extension Control Block and
reports byte-exact live values for:

- the current TPA and maximum loadable whole-record COM image;
- protected memory consumed by the active RSX allocation;
- the page-rounded CCP image and the complete reclaimable CCP/CPX region;
- persistent command-environment data/reservations; and
- protected core, disk workspace, and buffers.

The TPA boundary comes from the conventional word at `0006h`; the COM ceiling
is rounded down to a complete 128-byte load record. Movable command
environment values come from the ECB. Fixed protected boundaries are expanded
from the canonical `layout.inc` at build time, keeping the report synchronized
with the exact system image at no resident-memory cost.

## Verification

`tools/test_stat.py` builds a disposable physical-format disk and exercises
the memory report, multi-extent aggregation, numeric-user selection and state
restoration, DPB report, operand inventory, IOBYTE assignment, and file
attribute update.
