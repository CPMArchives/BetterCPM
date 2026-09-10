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
prints one exhaustive map from `FFFFh` down through page zero. Each row is an
inclusive address range with its byte count and owner. Fixed core components,
buffers, the PDS, loaded RSXs, the movable gateway, loaded CPXs, the CCP, the
transient area below the CCP, page zero, and platform-reserved addresses appear
as distinct, non-overlapping regions. Empty RSX and CPX ranges are omitted.

The maximum loadable whole-record COM size follows the map. It may include the
currently loaded CCP and CPXs because those components are reclaimable; it is
therefore a capability of the mapped layout rather than another memory region.

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
