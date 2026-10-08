# BetterCP/M STAT

## Status

The agreed CP/M 2.2 command families are implemented, with numeric DU selection
and the BetterCP/M `MEM` report. Targeted cpmsim and instruction-level checks
cover the corrections recorded below. Final two-platform qualification remains
open; implementation status is not a claim of release qualification.
Named-directory aliases remain deferred until the shared resident named-DU
resolver is implemented.

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

`tools/test_z80pack_stat_files.py` also verifies exact file totals, sorting,
parser rejection, device assignments and DPB fields on private cpmsim media.
Its `USR:` checks cover an empty disk and a disk populated in users 0, 3, 15
and 31, including return to B3: after enumeration. These checks test STAT's
IOBYTE inspection/assignment interface; actual BIOS device routing remains
separate release qualification.

`tools/test_z80pack_stat_drives.py` qualifies logged-drive status, an exact
free-space fixture, temporary drive read-only assignment, clearing on warm
start, rejection of the unsupported R/W assignment and B3: context restoration.
Test-only wrappers populate the login vector or inspect the public read-only
vector before STAT's normal exit reaches WBOOT; production STAT is unchanged.

## Compatibility reconciliation — 2026-10-08

This checklist reconciles the agreed stock command contract with the tests
present in the repository. It does not claim byte-for-byte DRI output identity.

| Command family | Current evidence | Qualification limit |
| --- | --- | --- |
| `STAT`, `d:`, `d:=R/O` | cpmsim: logged drives, R/W and R/O, independently counted 240K free-space fixture, assignment to only B, WBOOT clearing, rejection of `d:=R/W`, B3 restoration | Model 4 parity remains |
| File statistics and wildcards | cpmsim: exact 161/513-record totals, allocation and physical-entry counts, 24 sorted files; instruction checks: accepted/rejected wildcard forms and 257-summary sorting | Native listing beyond 64 files remains |
| `$S` logical size | cpmsim: sparse logical size 513 versus one recorded record; instruction checks: all 24 formatting bits | Model 4 sparse-file parity remains |
| `$R/O`, `$R/W`, `$SYS`, `$DIR` | cpmsim: single-file updates and read-only rejection; instruction checks: all valid directory-slot success returns and FFh failure | Wildcard updates with raw-directory verification remain |
| `DSK:`, `d:DSK:` | cpmsim: exact 332K DPB fields, one/two logged drives and context restoration; instruction checks: 800K capacity and word-carry boundaries | Native 800K and Model 4 parity remain |
| `USR:` | cpmsim: empty disk, users 0/3/15/31 and B3 restoration | Model 4 parity remains |
| `DEV:` and assignments | Instruction checks: all 16 legal selector values and unrelated-bit preservation; cpmsim: assignment lists, inspection and malformed operands | Actual BIOS routing is a separate open 1.0 requirement |
| `VAL:` | cpmsim: legal selector matrix, file options, multiple assignments, BAT explanation and unchanged IOBYTE | Model 4 parity remains |

The fixed 64-file summary buffer has been removed. Storage is bounded by both
the selected directory and available transient memory; executed-code checks
cover 384 summaries, capacity bounds and explicit overflow. Those checks do
not substitute for a native large-directory listing through the full BDOS path.

### Remaining bounded qualification

1. Apply all four attribute operations to wildcard-selected files on private
   media. Check the actual directory attribute bits across every matching
   extent, preserve unrelated bits and nonmatching files, and verify reported
   failure leaves the target unchanged.
2. List more than 64 files on a native 800K/128-entry disk. Verify complete,
   sorted output, exact multi-extent totals and 800K DPB/free-space reporting.
3. Bring the Model 4/trs80gp campaign up to the same required command cases,
   using completion/output evidence rather than fixed delays. The existing
   `test_stat.py` is smoke coverage: several assertions check only broad text
   presence, and each invocation uses a fixed four-second run delay. Its
   existence alone is not evidence that the current implementation passes.
4. Preserve the final platform binaries, commands and results, including the
   numeric DU and `MEM` extensions, and close the separate BIOS IOBYTE routing
   qualification before claiming device assignments operate on both platforms.

No additional missing command family was identified by this reconciliation.
The outstanding items are coverage gaps; a test may still expose a defect that
requires a bounded correction.
