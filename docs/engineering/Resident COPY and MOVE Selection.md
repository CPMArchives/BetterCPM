# Shared resident COPY/MOVE selection

Resident COPY and MOVE share one selector driver and one record-copy engine in
RCP.CPX. The MOVE flag adds source erasure after successful destination close
and attribute application. No source is erased after a failed copy. A source
erase failure reports `COPY MADE; SOURCE NOT ERASED`.

## Operand contract

- Source: one or many DUs/files using the common DU, bounded-filespec and
  attribute-expression parsers.
- Destination: exactly one resolved DU. Set notation is accepted only when its
  bitmap contains one DU. A DU-only target preserves each source filename.
- An exact target filename requires exactly one selected source file.
- Destination wildcard substitution and attribute assignments remain transient
  COPY features. Resident COPY retains trailing `/O`; MOVE does not overwrite.
- COPY and MOVE both use `destination=source` for destination-first syntax.
  The operator is `=`, not Pascal-style `:=`. In `MOVE B3:=A0:README.TXT`,
  the colon belongs to destination `B3:` and must be preserved. An exact
  destination is `MOVE B:MOVED.DAT=A:SOURCE.DAT`; an extra colon after the
  destination filename is invalid. Source-first syntax works for both.

Preflight covers the full source set before any destination changes. Reject
multiple sources with the same generated destination, destinations overlapping
selected sources, protected existing targets and read-only MOVE sources.
Repeated selector terms are deduplicated. Empty source DUs contribute no files;
an entirely empty selection reports `NO FILE`. System files are eligible unless
excluded by the source predicate. Caller drive/user are restored.

Execution stops on an unexpected copy/close/attribute/delete failure. Earlier
successful operations are not rolled back. Existing per-file cleanup and MOVE
source-deletion ordering are retained.

## Implementation and memory

`src/cpx/copy-select.inc` is included once in the resident RCP expansion. It
uses REN's lexical directory scanner, fixed scratch workspace, shared selector
and predicate evaluator. Collision checks rescan other selected DUs instead of
allocating an unbounded source list. COPY leaves originals intact; MOVE erases
only the completed original, so lexical progress remains valid.

The replaced operand parser and wildcard driver are omitted from the resident
image. Legacy transient expansion remains unchanged. BIOS, BDOS, protected
state and CPX descriptors are unchanged.

RCP Build 003 is 6,856 bytes, 51 bytes more than Build 002. Rounded allocation
remains 6,912 bytes. Its 744 relocations fit the existing 1,536-byte carrier
header. Native and cross builds produce identical code.

## Qualification

`tools/test_resident_copy_move_select.py` covers public-command cases on
z80pack and Model 4. It independently checks final directory names, source
retention/deletion, RO/SYS/ARC preservation and payloads including multi-extent
files. Rejected z80pack operations leave their media unchanged. Cases include
multiple source DUs, a deduplicated single-DU target, multi-DU target rejection,
invalid patterns, duplicate names, later-source collisions, self-copy,
read-only protection, explicit replacement, destination-first MOVE, and newly
created targets which match the original selector. An initially empty destination DU is excluded from
execution rescans; an exact target performs the single preflight operation once.

The shared relocated-selector checks, utility identity/dispatch checks and REN
regression provide coverage for routines reused by the new driver.

## Plain-equals MOVE correction — 2026-10-20

The shared assignment splitter no longer consumes a colon before `=` for MOVE.
Both commands retain the complete destination operand, including a DU-only
colon. Source-first syntax and file-copy/delete ordering are unchanged.
The obsolete `MOVE B:NAME.DAT:=A:NAME.DAT` and doubled-DU-colon forms are invalid.

`test_move_assignment.py` executes the production splitter at three resident
relocation origins and in both transient images: 70 cases cover exact names,
DU-only and user-only destinations, deduplicated selectors and source-first
operands. It checks the captured destination remains `B3:` for both
`B3:=A0:README.TXT` and `B3:=A2:README.TXT`. The old parser fails this regression.
The media suite adds exact-target assignment, DU-only multi-file MOVE and
obsolete-separator rejection with source/destination payload and attribute checks.

RCP Build 013 is 7,126 payload bytes (20 fewer), still allocated 7,168 bytes,
with 741 relocations. Native ZSM4/LINK matches the host build byte for byte.
The transient binaries also contain this shared body, so their executable
revision counters advance with RCP; MOVE's fallback retains its RCP identity.
No BDOS, BIOS, CCP or protected-memory changes are required.

Focused validation for this correction passes:

- `test_move_assignment.py`: all 70 production-code operand-boundary cases.
- `test_copy_filespec.py` and `test_copy_mapping.py`: transient parsing,
  option handling and mapping/preflight regressions.
- `test_rcp_shared_selector.py`: shared selectors at three relocation origins.
- `test_resident_type.py`: shared carrier relocation and ordinary TYPE behavior.
- `test_utility_versions.py`: all 166 identity/dispatch/pure-query checks.
- `test_resident_copy_move_select.py --platform z80pack`: all 28 cases,
  with independently inspected payloads, attributes and rejected-operation
  whole-disk preservation (`build/test-results/move-assignment-z80pack-final`).
- `test_copy_move.py`: Model 4 exact-target and DU-only cross-drive/user moves,
  source deletion, overwrite protection, payloads and restored caller context.

## Native transient build parity — 2026-10-20

The native builder previously prepared its common transient source separately
from the host builder and omitted `ver-banner.inc` code/data. This left the
native USER/CLS/VER/MOVE body 180 bytes shorter and shifted symbol addresses;
COPY inherited the same preparation gap. DIR used its own already-matching
preparation path. This was source-preparation drift, not an assembler or MOVE
execution discrepancy.

Both builders now call `transient_source()` before their assembler-specific
normalization. The host output remains byte-identical to the preceding corrected
MOVE build. Native ZSM4/LINK now matches all six transient outputs:

| Program | Byte-identical bytes |
| --- | ---: |
| DIR.COM | 9,789 |
| USER.COM | 4,916 |
| CLS.COM | 4,916 |
| VER.COM | 4,916 |
| COPY.COM | 11,418 |
| MOVE.COM | 4,916 |

`build/utilities/NATIVE-RCP-TRANSIENT-BUILD.LOG` records the actual native
assembly/link transcript. The 70 operand-boundary, filespec/mapping and 166
utility-identity regressions pass after sharing preparation. No further
executable build-counter increase is required for an identical host rebuild.

## Model 4 qualification closure — 2026-10-20

The complete 28-case Model 4 selector campaign passes on the corrected RCP:
`build/test-results/move-assignment-model4-complete/evidence.json`. It runs the
full batch to completion under trs80gp, then independently inspects directory
entries, all payloads, attributes, source retention/deletion and unrelated files.
This includes multi-extent files, exact destination assignment, DU-only and
multi-DU-source moves, deduplicated destination selectors and both obsolete
separator rejections. The successful focused cross-drive/user regression is
retained in addition to this full campaign. No reduced fixture or substituted
subset is counted as the completed 28-case result.

Together with the 28-case z80pack campaign, 70 parser cases, 166 utility-identity
checks, native RCP parity and all-six native transient parity, this closes the
MOVE syntax correction's recorded qualification gaps. This is qualification
of the bounded correction, not a declaration of a complete OS release.
