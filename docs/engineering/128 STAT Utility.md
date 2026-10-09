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
STAT target:
```

`filespec` and disk operands additionally accept BetterCP/M numeric selectors
`5:` and `C3:`. A temporary selection is restored before STAT returns.

`STAT target:` is a BetterCP/M inverse IOBYTE query. It accepts the standard
targets in the assignment table: TTY, CRT, BAT, UC1, PTR, UR1, UR2, PTP, UP1,
UP2, LPT and UL1, each followed by a colon. For example, `STAT CRT:` prints
`CRT: assigned to CON:` and `CRT: assigned to LST:` if both selections use CRT.
Every matching logical device is printed in CON/RDR/PUN/LST order; an unused
target prints `target: not assigned`. Unknown targets and additional operands
are rejected. Trailing spaces are allowed. Queries do not change the IOBYTE.
The result describes the current selector mapping, not hardware availability
or readiness. User-created endpoints remain outside the 1.0 scope.

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
| `STAT`, `d:`, `d:=R/O` | cpmsim: logged drives, R/W and R/O, independently counted 240K free-space fixture, assignment to only B, WBOOT clearing, rejection of `d:=R/W`, B3 restoration | Model 4: exact A:/B: status and free space, B-only R/O vector, WBOOT clearing and rejected R/W; Targeted Model 4 drive parity passed |
| File statistics and wildcards | Both platforms: exact 161/513-record totals, allocation/entry counts and sorted wildcard output; cpmsim: 100 sorted files on 800K; instruction checks: parser forms and 257-summary sorting | Targeted native and boundary checks passed |
| `$S` logical size | Both platforms: sparse logical size 513 versus one recorded record and ordinary 161-record reporting; instruction checks: all 24 formatting bits | Passed targeted parity; retain final release evidence |
| `$R/O`, `$R/W`, `$SYS`, `$DIR` | Both platforms: wildcard updates across every matching extent, complete logical-media comparisons and read-only rejection; cpmsim: single-file updates; instruction checks: all valid success slots and FFh failure | Passed targeted parity; retain final release evidence |
| `DSK:`, `d:DSK:` | cpmsim: exact 332K/800K DPB fields, one/two logged drives and context restoration; Model 4: exact 780K A: and 800K B: fields, one/two logged drives; instruction checks: word-carry boundaries | Targeted Model 4 drive parity passed |
| `USR:` | cpmsim: empty disk, users 0/3/15/31 and B3 restoration; Model 4: populated users 0/3/15 and return to A0 | Targeted Model 4 empty-disk and B3 restoration passed |
| `DEV:` and assignments | Instruction checks: all 16 legal selector values and unrelated-bit preservation; cpmsim: assignment lists, inspection and malformed operands; Model 4: default mapping, assignment list and inspection | Actual BIOS routing is a separate open 1.0 requirement |
| `VAL:` | cpmsim: legal selector matrix, file options, multiple assignments, BAT explanation and unchanged IOBYTE | Both native platforms have targeted VAL coverage |

The fixed 64-file summary buffer has been removed. Storage is bounded by both
the selected directory and available transient memory; executed-code checks
cover 384 summaries, capacity bounds and explicit overflow. Those checks do
not substitute for a native large-directory listing through the full BDOS path;
the 100-file 800K qualification below now supplies that separate evidence.

### Qualification closure — 2026-10-08

The agreed STAT utility behavior and retained edge-case campaign are qualified.
The targeted native campaigns cover both platforms; the corrected MEM report
passes on each. This is utility qualification, not completion of the full 1.0
system conformance campaign or a claim that every BIOS selector routes I/O.
Actual BIOS IOBYTE routing remains a separately tracked release requirement.

Final STAT.COM is 5,912 bytes, SHA-256
`a4ca926e0de437a2da529a67b03c998db58d9d500801fa7d1ace0aa1eec4e1f4`.
`tools/collect_stat_qualification.py` consolidates passing reports, final binary,
source snapshots, transcripts, media, invocations and per-file hashes in a
local bundle. Earlier independent cases retain their original binary hashes;
the final change is confined to the MEM range endpoint. Corrected native MEM
campaigns and summary boundary guards run the final binary. Retained screen
tails in full-directory tests supplement the complete 100-file listing check.

### Edge cases retained for final qualification

The following cases are covered by the retained targeted campaigns and
executed-code boundary tests:

- Empty disk and wildcard patterns matching no files.
- Invocation from a nonzero user: restore drive/user after both success and
  malformed-input or operation failures.
- Full directory and insufficient summary workspace: explicit failure without
  memory corruption; retain the existing executed-code capacity checks and
  native large-directory evidence rather than repeating them unnecessarily.
- MEM with resident RSXs and with invalid/unavailable system metadata.
- Malformed DU qualifiers and trailing operands through the native command
  path, including checks that errors preserve the original drive/user.

No additional missing command family was identified by this reconciliation.
The outstanding items are coverage gaps; a test may still expose a defect that
requires a bounded correction.

### Wildcard attribute qualification — passed 2026-10-08

`tools/test_z80pack_stat_attributes.py --report <new-directory>` creates private
media and applies all four attribute options to `B:MATCH*.DAT`. The selected
files occupy one and three physical extents on the 332K format; initial R/O,
SYS and ARC bits differ between them. A nonmatching three-extent file and a
matching filename in user 3 act as preservation controls.

After each command, the test compares the entire disk image with a separately
constructed expected image permitting only the requested high-bit change in
every matching directory entry. This also verifies preservation of file data,
allocation/extent metadata, ARC, other attributes, other users and nonmatching
files. A test-only read-only wrapper checks both failure messages and exact
whole-image preservation. Production STAT is unmodified.

The report retains STAT and the rejection wrapper, before/after images,
command transcripts and JSON evidence with STAT, simulator and image hashes.
The qualification run passed with 5,912-byte STAT.COM, SHA-256
`dedb8d3c4d8a91ec1e3313f3fe021441d7773a4e3194ff4b54eb9d2d713367ac`.

### Native large-directory/800K qualification — passed 2026-10-08

`tools/test_z80pack_stat_800k.py --report <new-directory>` creates private
Montezuma Micro 80T DS DATA media and activates its binding through the native
Function 181 setup used by the native-build harness. B is the test disk; C is
an empty companion configured by that shared setup program.

The fixture contains 100 files inserted in reverse order and 105 physical
directory entries. Two files contain 161 and 513 records, occupying two and
five entries respectively. The test verifies exactly 100 ascending output
rows, every row's recorded/allocation/entry totals, all 800K DPB fields, and
512K free space independently calculated from raw allocation entries. The
entire B image remains unchanged after inspection. The report retains the
private media, setup and STAT binaries, transcript and JSON hash evidence.

### Model 4 device-interface parity — passed 2026-10-08

`tools/test_model4_stat_devices.py --report <new-directory>` captures eight
commands covering the cold 95h mapping, multiple assignments, both CRT inverse
matches, PTP's assignment, unused UP1, unknown/malformed targets, and unchanged
mapping after queries. The entire private boot disk remains unchanged.

The emulator waits for the expected output and the returned `A0>` prompt,
distinguishing it from the command echo. Output alone is insufficient: the
initial timing probe showed that warm boot could still be in progress after
STAT printed its result. Assertions scope each expected line to output after
the corresponding command echo, so retained earlier screen lines cannot count
as fresh results. All eight retained captures passed those assertions.

The report retains STAT, boot media, invocation, screen captures and decoded
text, plus hash evidence. This closes this bounded device-interface group;
other Model 4 command families and actual BIOS IOBYTE routing remain open.

### Model 4 file-statistics and DU parity — passed 2026-10-08

`tools/test_model4_stat_files.py --report <new-directory>` captures six native
commands. Exact checks cover 161 and 513 recorded records, 22K and 66K allocated,
and two and five physical entries. Five reverse-created files must each appear
once in ascending wildcard output. Numeric `3:` and combined `A3:` select the
user-3 fixture, then return to A0:. A final unqualified lookup reports File Not
Found, confirming no user-0 copy was accidentally selected or created.

Every capture must show the completed return to the original prompt, and the
entire private medium remains unchanged. The report retains STAT, boot media,
invocation, decoded screen captures and binary/emulator/media hashes. Remaining
Model 4 groups include drive/DPB/user reports,
help and the BetterCP/M memory report.

### Model 4 sparse `$S` parity — passed 2026-10-08

`tools/test_model4_stat_sparse.py --report <new-directory>` creates a sparse
file through native Make, random Write at record 512 and Close. Raw directory
checks confirm two physical entries, one recorded record and one 2K allocation
block. STAT reports 513 logical records, one recorded record, 2K allocated and
two entries. An ordinary 161-record file reports identical logical and recorded
counts, 22K allocated and two entries. Inspection leaves the whole medium
unchanged.

The report retains the creator source/binary, STAT, the pre-inspection image,
invocations, captures and hash evidence. The harness requires explicit output
and a returned prompt, then allows a short keyboard-settling interval before
another command. The fixture creator is checked by its unique completion marker
and prompt without requiring retention of its original command echo.

### Model 4 wildcard attribute parity — passed 2026-10-08

`tools/test_model4_stat_attributes.py --report <new-directory>` applies R/O,
R/W, SYS and DIR to two files occupying seven physical entries. Initial
attributes differ, including ARC on one selected file. A nonmatching five-entry
file and a matching filename in user 3 serve as preservation controls.

After each operation, the complete extracted logical image must equal an
independently constructed expected image permitting only the requested
attribute-bit changes. This verifies every selected extent and preserves
unrelated metadata and payload. A test-only R/O wrapper checks both per-file
rejection messages and exact physical DMK preservation. Each operation requires
completion output and a returned prompt. The report retains STAT, the wrapper,
initial/updated media, invocations, screen captures and hash evidence. No
production STAT or OS change was required.

### Model 4 drive/DPB/user reports — targeted cases passed 2026-10-08

`tools/test_model4_stat_reports.py --report <new-directory>` checks five
commands in independently bounded launches: bare STAT, A:, DSK:, A:DSK:
and USR:. The private medium's directory and allocation pointers independently
establish 706K free and populated users 0, 3 and 15. Both DPB forms must report
all ten exact fields of the installed 780K SYSTEM profile, including 6,240
records, 390 allocation blocks, 128 directory/check entries and two reserved
tracks. Every command returns to A0 and leaves the complete DMK unchanged.

The initial combined run stalled after its first capture; separate launches
completed the standard cases. An additional A3:USR: test was removed because
that command is outside the specified grammar. The final assertions passed
against the five retained captures using `--verify-existing`, which also checks
that each retained invocation matches the expected command. No production
code change was required. R/O lifecycle, multiple-drive reporting, empty-disk
user enumeration and nonzero-user context restoration remain separate cases.

### Model 4 R/O lifecycle and multiple-drive reports — passed 2026-10-08

`tools/test_model4_stat_drives.py --report <new-directory>` qualifies both
remaining drive-report groups on private A:/B: media. A: uses the 780K SYSTEM
profile; B: uses the default unreserved 800K DATA profile. Independently counted
A: allocation gives 678K free; B: has only its reserved directory blocks and
796K free. Bare STAT reports only logged A:, while the two-drive case reports
both drives in order. Both full DPB reports match all ten expected fields,
including their different record/track values and reserved-track counts.
Explicit B:DSK: reports only B: and returns to A0.

Test-only wrappers select/log B: immediately before STAT's vector snapshot,
using public BDOS calls because WBOOT clears logged-drive state. Another
wrapper sets B: R/O and checks the resulting status. A FINISH wrapper observes
Function 29 before WBOOT and requires the exact vector 0002h after B:=R/O.
The following command in the same emulator session confirms both drives R/W,
proving WBOOT clearing. B:=R/W produces Invalid STAT command. Every case
preserves both complete physical DMK images.

The assignment diagnostic overwrites its command echo on screen, so that
capture requires its unique B ONLY READ-ONLY marker and the returned prompt.
Final assertions passed against retained captures with `--resume`, which
validates invocation identity and runs only missing cases. Reports retain
STAT, wrapper binaries/listings, media, invocations, captures and hashes.
Production STAT remains 5,912 bytes with its unchanged SHA-256; no OS code
change was required.

### Model 4 empty media and context restoration — passed 2026-10-08

`tools/test_model4_stat_context.py --report <new-directory>` qualifies nine
native commands after a test-only entry wrapper selects B: and user 3 through
public BDOS calls, before STAT captures its original context. Every capture
must return to B3. The blank 800K B: reports Active User 3 with no populated
users and no wildcard matches. Cross-DU A0: file lookup reports exact one-record,
2K, one-entry totals; a missing file returns File Not Found. A:DSK: reports
only the selected A: and restores B3. Both A32: and user-only 32: qualifiers
are rejected, as are a trailing operand and a nonterminal wildcard.

Both complete DMK images remain unchanged after every case. The harness's
initial numeric assertion was corrected to accept the canonical zero-padded
output; final assertions passed with --resume, validating retained invocation
identity and executing the remaining cases. The report preserves production
STAT, the context wrapper and listing, invocations, captures, images and hashes.
No production STAT or OS correction was required. Help/MEM parity and the
remaining resource/metadata edge-case evidence remain open.

### Model 4 help, MEM and resource edge cases — passed 2026-10-08

`tools/test_model4_stat_help_memory.py --report <new-directory>` checks the
complete VAL help and selector matrix, then MEM with no RSX and with ECHO
loaded through the real manager and runtime overlays. Every reported range
must have the correct inclusive size, descend without gaps or overlaps, and
together cover all 65,536 bytes. The maximum COM size must agree with the
live gateway boundary and shrink after loading the RSX. Test-only copies
redirect metadata lookup to absent, invalid-signature and unsupported-version
records; all reject the record without printing a map or changing media.
The real ECB is never modified by these rejection fixtures.

The loaded-RSX case exposed a three-byte gap in STAT's map: the original
CP/M gateway location remains reserved but is inactive while the active
gateway moves lower. STAT now includes those bytes in the loaded-RSX
allocation range. The original gateway location is retained for the no-RSX
layout; no memory-layout or lifecycle change was made. The correction changes
only an immediate endpoint value, retaining the 5,912-byte utility size.
Final STAT SHA-256 is
`a4ca926e0de437a2da529a67b03c998db58d9d500801fa7d1ace0aa1eec4e1f4`.
The initial fixture lacked RSX runtime overlays and incorrectly expected a
LOAD success message; the completed campaign uses the required overlays,
silent LOAD success and the returned prompt. All final checks passed.

`tools/test_stat_capacity.py` exercises actual summary code at zero, one,
100, 128 and 384 available slots, requiring explicit overflow and preservation
of guard bytes beyond each workspace. It also retains the existing 384-summary
and multi-extent aggregation checks. These checks passed on the corrected
STAT binary.

`tools/test_model4_stat_capacity.py --report <new-directory>` fills all 128
directory entries, including 119 reverse-created matching files. The native
listing completes with the expected sorted tail and exact per-file totals.
A test-only zero-slot copy rejects a SYS attribute request with the explicit
insufficient-memory diagnostic before any mutation; the complete medium
remains unchanged. Full-listing coverage is supplied by the existing 100-file
campaign; this full-directory case checks the retained screen tail and normal
completion. Resource cases ran before the independent MEM endpoint correction.

### Native cpmsim MEM parity — passed 2026-10-08

`tools/test_z80pack_stat_memory.py --report <new-directory>` checks the final
STAT binary with no RSX, with ECHO loaded and after unload. Complete maps must
cover all 64K without gaps or overlaps; the maximum COM size agrees with the
live gateway and returns to its original value after unload. Missing, invalid
signature and unsupported-version metadata records all produce the specified
rejection diagnostic without printing a map. All four complete runtime disk
images remain unchanged. The report preserves binaries, transcripts, commands,
media and hashes. This closes native MEM parity and the retained metadata
edge cases. Actual BIOS IOBYTE routing remains a separate release requirement.


### Shared extended DU inspection — 2026-10-09

STAT now links the Specification 208 assembly include for bracketed selector
forms. Before selecting any location, it validates the complete scope,
filespec and file option. Extended selectors admit file inspection only,
with no option or `$S`; missing patterns, drive-wide DSK/read-only assignments
and attribute changes are rejected. Conventional syntax remains on its
established parser path and retains its output.

The driver visits the bitmap once in canonical order. Each location is headed
by its DU, and extended file rows include the user number. Every iteration
restores the original parsed FCB because logical-size reporting may replace
its name. Unavailable drive selection reports the requested DU and continues.
The ordinary FINISH path restores the caller's drive/user.

STAT.COM is 6,839 bytes; this is transient utility growth only. The shared
include is expanded by `tools/build_stat.py` at build time; no OS service,
BDOS change or CPX change is involved. Documentation source is updated;
DOCX/PDF exports are not regenerated.

Qualification passes on disposable cpmsim media: user lists, descending and
duplicate selections, `$S`, user 31, the compound user-only inheritance example
from caller B2, unavailable-drive continuation, malformed scopes, rejected
attribute/drive-wide set operations, and conventional single-DU output.
All three mounted fixture images remain byte-identical after every case;
caller prompts confirm restoration. Evidence:
`/private/tmp/stat-du-sets-v3-20261009/evidence.json`.
Parser, 24-bit logical size, sorting, attribute result and summary-capacity
regressions pass. Native ZSM4 parity of the shared include is already recorded
in Specification 208; this increment does not claim native whole-STAT assembly
parity or new trs80gp qualification.
