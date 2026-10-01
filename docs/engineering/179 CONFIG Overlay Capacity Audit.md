# CONFIG overlay capacity audit

## Scope

This is the bounded size audit requested before implementing the name-based
BetterCP/M Function 176 CPX-profile interface. It examines the generated
control-overlay listing for obvious dead code, duplication, and clear shorter
equivalents. It does not change the Function 176 ABI or production code.

The baseline is commit `611aa45`. `tools/build_system.py` reports a 975-byte
CONFIG overlay in the fixed 1,024-byte `LY_CFG` workspace, leaving 49 bytes.

## Generated size map

| Region | Bytes | Address range |
|---|---:|---|
| Entry vectors | 21 | `F000h-F014h` |
| Drive-binding validation and commit | 547 | `F015h-F237h` |
| Track-format control | 212 | `F238h-F30Bh` |
| Provisional CPX profile control | 152 | `F30Ch-F3A3h` |
| Physical/logical profile queries | 39 | `F3A4h-F3CAh` |
| Overlay scratch | 4 | `F3CBh-F3CEh` |

All executable labels are reachable from an exported entry or an internal
branch/fall-through path. The audit found no dead routine or unused feature
large enough to solve the capacity problem.

The repeated FDF-capability check and several long branches to common error
returns offer only small savings. Factoring or replacing them would alter the
already-qualified disk-validation path for fewer than ten obvious bytes.
Converting groups of absolute error jumps into local trampolines might recover
additional bytes, but that is instruction-level compression across unrelated
disk code, not a clear maintainability improvement. The formatter's repeated
seek is intentional: it renews drive selection and motor timing before WRITE
TRACK. The profile-query entries already share their copy tail.

## Local CPX opportunity

The provisional 152-byte CPX region contains the removable assumptions that
make the current interface non-general:

- a one-byte RCP/HELLO membership mask;
- two compiled-in eight-byte module names;
- reconstruction code that regenerates the table in fixed RCP-then-HELLO
  order; and
- numeric dispatch for only those two modules.

The accepted name-based interface can instead enumerate and edit the existing
ordered four-record reconstruction table directly. A compact implementation can
walk the 12-byte request once, share one name validator and one table-search
routine, shift records in place on removal, and append new records without a
separate flags-to-table rebuild.

The protected extension image currently ends at `E647h`, one byte before the
`E648h` disk-service boundary. Expanding its existing one-byte `BCX_MVAL`
scratch cell into a two-byte saved request pointer consumes exactly that spare
byte and avoids repeated request-address setup in the overlay. It does not move
the disk service, change the TPA, or alter the memory map.

This is the only obvious compaction route with enough potential value and a
small blast radius. The earlier straightforward implementation measured 264
bytes for the CPX region, 112 bytes larger than the provisional handler and 63
bytes beyond the overlay limit. The compact implementation must be assembled
and measured rather than accepted from an estimate. It should proceed only if
it preserves manager-side normalized-name validation and fits without changing
the disk-control regions.

## Implementation acceptance

The next increment may replace only the provisional CPX handler and its scratch
cell. Accept it only when all of the following hold:

- the extension image ends at or before `E648h`;
- the CONFIG overlay is no larger than 1,024 bytes;
- Function 176 preserves `DE`, enforces request version 1, validates the
  upper-case space-padded name, and implements ordered enumeration, idempotent
  load, and idempotent unload;
- the four-record profile limit and existing reconstruction order remain
  unchanged;
- focused unit tests cover invalid requests, duplicates, capacity, enumeration,
  removal order, and arbitrary names; and
- the existing CPX reconstruction and runtime-manager regressions pass.

If the compact handler does not meet those gates, stop. Do not compress the
disk-validation or formatting paths merely to force it into the overlay. The
1.0 fallback remains caller-side validation; broader workspace redesign remains
part of the recorded post-1.0 architectural review.
