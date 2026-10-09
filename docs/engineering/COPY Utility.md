# COPY Utility: Incremental Implementation and Qualification

The consolidated [COPY target specification](COPY%20Specification.md) controls
future implementation. Its plain `=` assignment operator supersedes the
previous `:=` target syntax. Historical qualification below describes the
existing implementation and does not imply the new syntax or transient-only
features are already available.

## Agreed common functionality

The CPX and transient COPY should provide the ordinary copy operations,
including wildcard/multiple-file copying, explicit overwrite control and
attribute preservation. Implement and qualify these in bounded increments.
Richer transient-only syntax and any CPX-to-transient handoff contract remain
separate design work; no handoff ABI is introduced by this increment.

## Current assessment — 2026-10-08

The implementation is shared in `src/cpx/rcp.mac`; `build_rcp_transients.py`
builds COPY.COM from the same command body. Both source/destination and
`destination:=source` forms support explicit drive/user qualifiers and copy
exact filenames or supported source wildcards. Existing destinations are refused
unless `/O` is supplied; exact self-copies are always refused.
R/O, SYS and ARC attributes are already copied after a successful destination
close. Prior native qualification covers all eight attribute combinations in
CPX and transient profiles. MOVE uses the same engine and erases its source
only after successful copy/close and attribute handling.

The agreed common implementation now includes source wildcards/multiple files
and explicit overwrite control. The final two-platform campaign below qualifies
that common subset, including destination DU shorthand. Destination wildcard renaming,
concatenation, device transfers, transformations and the handoff proposal need
separate contracts before implementation.

## Exact-filespec correction — passed targeted checks 2026-10-08

The existing FCB parser silently truncated names longer than eight characters
and extensions longer than three. Thus an overlong source could select an
existing shorter filename, or an overlong destination could create a file
with a different name. COPY/MOVE now validate exact operands before FCB parsing
or file operations. Reject empty names, excessive field lengths, multiple
dots, embedded spaces/control bytes, wildcard operands and embedded colon or
assignment delimiters. A name without an extension, including a trailing dot,
remains valid. DU selection is restored on rejection.

`tools/test_copy_filespec.py` executes the actual validator in both relocated
CPX and transient builds at exact 8.3 boundaries and malformed inputs.
`tools/test_z80pack_copy_filespec.py --report <new-directory>` exercises five
invalid commands per profile, requiring the existing usage diagnostic and
byte-for-byte preservation of all disks. Maximum-width valid source names
still copy their exact payload. CPX cases remove COPY.COM, preventing fallback
from concealing a CPX failure; transient cases unload RCP. The report preserves
binaries, transcripts, runtime media and hash evidence.

Shared code grows from 3,047 to 3,127 bytes (+80). The rounded RCP allocation
rises from 3,072 to 3,328 bytes (+256), affecting available transient memory
while loaded. COPY.COM and the other currently untrimmed RCP-derived transients
also become 3,127 bytes. This is a utility/CPX change; resident BIOS/BDOS code
and their fixed capacities are unchanged. Model 4 qualification and broader
COPY feature qualification remain open.

## Destination DU shorthand — passed targeted checks 2026-10-08

An exact source may be copied to a destination drive/user alone, retaining its
filename: `COPY B1:SOURCE.DAT B3:`. Drive-only destinations use the caller's
current user; combined destinations support users through 31. A missing
source filename is still invalid. Exact self-copy and existing-destination
checks apply after inheriting the name, before destructive work.

The shared parser clears the destination FCB normally and copies only the
source's eleven filename bytes when the destination is just a DU. Effective
source/destination drive and user remain separately captured. Existing data
copying, close ordering and final attribute preservation are unchanged.
The assignment form retains its existing `:=` separator: a DU-only destination
can be written `COPY B4::=B1:SOURCE.DAT` (destination `B4:` plus separator `:=`).
The ordinary source-first form is the simpler spelling. This does not change
the existing meaning of an extensionless destination such as `B:=source`.

`tools/test_z80pack_copy_du.py --report <new-directory>` checks both profiles:
CPX cases have no COPY.COM; transient cases unload RCP. Native transfers to
users 0/3/4/31 retain exact payload and all three source attributes, preserve
source metadata, and return to A0. Self-copy, existing destination, absent
source name and out-of-range destination user all preserve the complete disk
set. Exact-filespec boundary checks and the native malformed-name campaign
remain passing after this parser change.

Shared code grows from 3,127 to 3,153 bytes (+26); RCP allocation remains
3,328 bytes. BIOS/BDOS code is unchanged. Wildcard/multiple-file support,
explicit overwrite control and final two-platform COPY qualification remain.
Handoff remains separate until the agreed common resident COPY work is done.

## Wildcard increment and grouped-extent correction — 2026-10-08

The shared CPX/transient COPY now accepts a bounded source wildcard and a
DU-only destination, for example `COPY B1:F?*.DAT C2:` or
`COPY B4::=B1:F***.DAT`. Question marks match individual filename positions;
a terminal run of stars fills the rest of its field. Reject characters after
that run, overlong fields, destination wildcards and wildcard MOVE. Each
normalized filename is copied once even if it has multiple directory extents.
The implementation rescans between files because ordinary BDOS calls can
invalidate search state. Its workspace has a fixed size; no file list or
per-file allocation is retained. Rescanning has quadratic directory-scan cost.

Existing destinations are still refused. A batch stops on its first error;
previously completed copies remain. The failing existing file and subsequent
files are untouched. A source/destination DU alias is rejected before copying.
The caller's drive/user and default DMA are restored. Source R/O/SYS/ARC
attributes are transferred after destination close.

Qualification exposed an existing BDOS grouped-extent defect. Activating a
physical directory entry copied its last populated logical EX over the
caller's requested EX. Reading skipped subextents; writing revisited earlier
records. Activation now preserves EX and CR, normalizes RC to 128 for an
earlier populated subextent or zero for a later unpopulated subextent, and
retains the directory attributes and allocation map. Targeted probes and
before-fix media are preserved at `/private/tmp/copy-wildcard-qualification`.

The correction costs 20 bytes. Equivalent compaction recovers exactly those
20 bytes: reuse the loaded ALV pointer, share Search First initialization,
remove redundant EX masking and logical-record spill/reload, and shorten one
in-range branch. The old scratch word remains reserved to preserve the frozen
ROM/RAM state span. BDOS remains **3,555 bytes**, with unchanged resident
boundaries, live-state addresses and 40-byte private stack. BIOS is unchanged.
The measured ROM reference baseline loses one absolute branch and two scratch
references; strict relocation checks retain their independent validation.

Validation:

- `test_bdos_grouped_extents.py`: 480 emitted-code activation cases covering
  grouped and ungrouped extents, requested EX, populated EX, and RC boundaries.
- `test_unified_bdos.py` and `test_bdos_recovery.py`: filesystem/record services,
  A/B/A allocation switching, random/sequential I/O, and 24 success/ignore/abort
  transfer cases. Measured private stack high-water is 26 bytes.
- `test_copy_filespec.py`: actual CPX/transient parser boundaries and wildcard
  grammar.
- `test_copy_move.py`: Model 4 source-first/assignment copying, cross-DU data,
  existing-destination refusal, MOVE erasure and caller restoration pass on
  disposable media; the rebuilt Model 4 resident and ownership checks pass.
- Fresh z80pack boot media pass ROM/RAM ownership, relocation, reference,
  packing, and boot-artifact checks.
- `test_z80pack_copy_wildcards.py` with `--format default` and `--format 800k`:
  CPX and transient profiles on EXM=1/8-bit and EXM=0/16-bit allocation formats.
  Each profile copies six files, including a distinct-per-record 513-record
  file, through both grammars and across drives. Exact payload, all source
  attributes and extent counts survive; unrelated metadata and source entries
  remain unchanged. Invalid/no-match/self/existing cases preserve every disk.
  Mid-batch collision tests preserve the existing target and completed copies.
  CPX profiles remove COPY.COM and MOVE.COM; transient profiles unload RCP.

Native reports: `/private/tmp/copy-wildcard-default-final` and
`/private/tmp/copy-wildcard-800k-final`. Reproduce against newly built media:

```sh
python3 tools/build_z80pack_image.py --output /tmp/copy-fresh-runtime
python3 tools/test_z80pack_copy_wildcards.py --image-dir /tmp/copy-fresh-runtime --report /tmp/copy-default
python3 tools/test_z80pack_copy_wildcards.py --format 800k --image-dir /tmp/copy-fresh-runtime --report /tmp/copy-800k
```

Shared RCP code grows from 3,153 to **3,584 bytes** (+431); rounded allocation
increases from 3,328 to 3,584 bytes (+256). Explicit overwrite control and final
two-platform COPY qualification remain. Handoff remains a separate discussion
until the agreed resident COPY functionality is finished.

## Explicit overwrite control — targeted qualification passed, 2026-10-08

A single trailing `/O` explicitly allows replacing existing writable targets:

```text
COPY B1:FOO.DAT C2:FOO.DAT /O
COPY B1:*.DAT C2: /O
COPY C2::=B1:*.DAT /O
```

Without `/O`, existing targets are refused. Self-copy remains refused even
with `/O`. A read-only target reports `READ ONLY`; `/O` does not override file
protection. Wildcard MOVE and MOVE `/O` remain outside this COPY increment.
Unknown, duplicate or misplaced options produce the usage diagnostic before
file operations. Trailing whitespace is allowed in either command grammar.

The engine opens the source before considering replacement. Destination
existence uses BDOS Open rather than Search First: a grouped physical directory
entry can have a nonzero EX even when the file starts at logical extent zero.
The previous Search First check missed these large targets and reported
`NO SPACE` after Make rejected the duplicate. Open supplies both the correct
existence result and target attributes.

Replacement deletes the old target, clears its attributes/allocation state
from the working FCB, and creates the new target. All old extents are removed,
so shortening a file does not leave its old tail. Source attributes are applied
after successful close, including clearing attributes absent on the source.
Replacing a target is **not transactional**: once deletion succeeds, a later
read/write/space failure cannot restore the old contents. Normal copy failure
cleanup still attempts to remove its newly created partial target. Previously
completed batch copies remain.

`test_z80pack_copy_overwrite.py` passes in CPX and transient profiles. CPX
cases have COPY.COM and MOVE.COM absent; transient cases unload RCP. The test
replaces a 769-record target with a distinct-per-record 513-record source,
checks exact payload/extent count/attributes, exercises both grammars and a
three-file wildcard batch containing empty, short and long sources, and
verifies that absent source attributes clear old SYS/ARC bits. Read-only,
self-copy, missing-source and malformed-option cases preserve all disk bytes.
Every command returns to the caller's A0 context; source metadata is preserved.

`test_copy_filespec.py` executes both emitted option parsers and retains exact
8.3/wildcard boundary checks. Native wildcard regressions also pass on both
EXM=1/8-bit and EXM=0/16-bit allocation formats, including cross-drive copying
and safe stopping at a collision without `/O`.

Reports are preserved at `/private/tmp/copy-overwrite-final`,
`/private/tmp/copy-overwrite-wildcard-regression` and
`/private/tmp/copy-overwrite-800k-regression`. Run the overwrite campaign with:

```sh
python3 tools/test_z80pack_copy_overwrite.py --image-dir <fresh-runtime> --report <new-directory>
```

RCP code grows from 3,584 to **3,733 bytes** (+149); rounded allocation grows
from 3,584 to **3,840 bytes** (+256). COPY.COM shares the same 3,733-byte body.
BIOS/BDOS code and memory boundaries are unchanged by this increment. The
agreed common COPY implementation is now present. The final campaign below
closes its utility qualification; the deferred handoff discussion remains.


## Final common COPY qualification — passed, 2026-10-08

Both CPX and transient profiles pass on trs80gp Model 4 and cpmsim. The CPX
cases omit COPY.COM, proving that the resident implementation handles them.
The transient cases unload RCP before running COPY.COM.

Model 4 checks SYSTEM-to-DATA transfers, both command grammars, wildcard
batches, explicit overwrite, all eight R/O/SYS/ARC combinations, zero-length
files, user 31, and restoration to the A0 caller. Payloads and directory
entries are inspected independently after execution. Replacing a 257-record
file with a one-record source removes every old extent and tail. A separate
17-record transfer crosses an allocation-block boundary. The source disk
remains byte-for-byte unchanged and an unrelated destination file survives.

Default collisions, read-only overwrite, self-copy, no matches, malformed
wildcards, destination wildcards, user 32, and duplicate overwrite options
produce the expected errors without changing either disk. Full-directory
failure leaves physical media unchanged. Full-allocation failure removes the
incomplete destination while preserving existing files and their metadata.

The final cpmsim filespec and DU regressions also pass. The retained wildcard
and overwrite campaigns use the same final COPY/RCP binaries on EXM=0 and
EXM=1 formats, including 513-record sources, replacement of longer
769-record targets, attribute preservation, and mid-batch collision behavior.
Earlier copies in a batch remain completed when a later copy fails.

The first large Model 4 batch exceeded its short deadline during native
floppy I/O. A bounded single-record probe completed in 27 seconds; the final
campaign uses smaller transfers for platform checks and retains the larger
extent cases under cpmsim. No production code correction was needed.

Reproduce Model 4 qualification with:

```sh
python3 tools/test_model4_copy.py --report /private/tmp/copy-model4-new
```

Optional `--profile cpx` or `--profile transient` runs one profile. The
qualification uses isolated emulator sessions and disposable media through
the established LaunchServices launcher.

The indexed evidence bundle is
`/private/tmp/copy-final-qualification-2026-10-08/manifest.json`. It preserves
seven passing reports, commands, console captures, fixture/result media,
final binaries, source snapshots and SHA-256 hashes. The collector rejects
reports tested with different COPY/RCP binaries, and checks BDOS hashes where
reported. Reproduce collection with `tools/collect_copy_qualification.py
--output NEW_DIRECTORY --case LABEL=REPORT` for each retained report.

Shared code remains 3,733 bytes, rounded RCP allocation 3,840 bytes, and BDOS
3,555 bytes. The agreed common COPY subset is complete and qualified. Extended
transient features, CPX-to-transient handoff, and the full release conformance
campaign remain separate work.

## CPX-to-transient handoff — agreed diagnostic sequence

The user selected the simpler diagnostic-before-handoff approach. It
supersedes the earlier proposal to retain a fallback diagnostic pointer or
re-enter a CPX after failed lookup:

```text
A0>COPY B2:B*C*.DOC D2:
Invalid filespec -- handing off to COPY.COM
COPY.COM not found
```

Resident COPY prints its local diagnostic. The handoff path appends the
announcement. The CCP then enters its normal transient loader directly,
bypassing further resident/CPX interpretation. If lookup fails, the CCP prints
the named missing-transient diagnostic instead of ordinary unknown-command
output. If lookup succeeds, COPY.COM receives the original command tail and
provides its own result. The user accepts that a valid transient-only form
may first receive a resident diagnostic.

The current CPX interface still has only handled and declined results. Add an
explicit, backward-compatible handoff request; do not interpret unspecified
return-register contents from legacy modules as a third result. A per-command
request must be cleared before another dispatch and must not cause the CCP
to redispatch the same command through the CPX chain. No callback or saved
error-string pointer is required by the agreed sequence.

Only interpretation failures before operational side effects may request
handoff. Restore caller DU and DMA state and preserve the input command tail.
A partially completed operation or an I/O failure must not hand off and repeat
work. Protected-load failures after reclaiming the command environment retain
the existing failure/WBOOT behavior; they cannot return to the old CPX.

A previous disposable prototype measured a 31-byte CCP increase for the now
superseded diagnostic-pointer design: 5,341 to 5,372 bytes, within the existing
5,376-byte allocation. It is not a measurement of this agreed implementation
or of suppression support. No production handoff code or CPX ABI change has
yet been made. BDOS growth is excluded from the implementation scope.

## RCP-owned protected shadow policy — proposed refinement

The user proposes resident controls:

```text
COPY /HANDOFF=OFF
COPY /HANDOFF=ON
```

OFF suppresses automatic handoff for every subsequent resident COPY invocation;
the local diagnostic is still printed, without an announcement or transient
lookup. ON restores automatic handoff. Failed transient lookup does not change
the setting. Both controls must work without COPY.COM and before ordinary
COPY operand parsing. Malformed controls must leave the setting unchanged.

The latest proposal associates the policy with the installed RCP package,
with independent command bits owned by RCP. This revises the earlier whole-
session lifetime: explicit removal of RCP discards its policy, and later
installation starts with defaults. WBOOT, ordinary transient execution, and
CCP/CPX or RSX reconstruction preserve it while RCP remains installed. Cold
boot restores defaults. Do not write this volatile policy into saved CONFIG
state or disk records.

This policy is separate from the one-invocation handoff request. The request
belongs to reconstructible CCP working state and is cleared for every command.
The suppression policy must have explicitly owned storage outside the
reclaimable CCP/CPX regions. A single RCP-owned bitmap is a compact initial
representation. The package owns its bit meanings; the core only initializes
or discards the whole byte. Zero can encode defaults/all handoffs enabled,
with one bits representing explicitly suppressed commands. This encoding
keeps default storage zero-filled without a core dependency on command bits.

The current protected history object demonstrates warm-boot-retained storage,
but its working fields are owned by history and are not free scratch bytes.
Do not borrow them or couple policy reset to history corruption/reinitialization.
Storage placement, cold reset, ABI admission, complete size accounting, and
lifecycle qualification remain implementation work. The bitmap's small data
size alone does not establish the total code cost.

Suppression should govern automatic handoff only; explicitly invoking a
qualified transient remains a separate ordinary program invocation. A query
such as COPY /HANDOFF may be useful, but has not been selected as required syntax.

The user clarified that the trailing Ctrl-C sentence was stray text. It adds
no requirement and does not change COPY cancellation behavior.


### Protected-storage audit — one byte fits without moving existing fields

The active CPX profile begins at `LY_SYS+0096h` and has four eight-byte filename
records. Function 176 rejects a fifth record; its append, enumeration and
removal paths stay inside those 32 bytes. In `gateway.mac`, the initial
8-byte RCP name is followed by 31 zero bytes, so the source actually reserves
39 bytes before `SINIBODY`. Seven existing zero bytes therefore lie outside
the usable profile table.

The first of those bytes, `LY_SYS+00B6h` (currently D67Ah), is a suitable
candidate for a named RCP policy byte. Splitting the existing reservation into
24 zeros after the initial name, one named zero policy byte, and six remaining
reserved zeros produces a byte-identical 248-byte gateway. The table,
`SINIBODY`, every existing field, and the BDOS boundary stay at their original
addresses. No CPX descriptor expansion or protected-data layout shift is
required to reserve the byte.

The disposable assembly comparison and evidence are preserved in
`/private/tmp/rcp-shadow-state-audit`. This proves storage placement only;
production sources are unchanged. Cold-reset instructions, explicit-removal
handling and resident controls still need separate code-size measurement and
lifecycle tests. BDOS remains excluded from growth.

Reset on actual RCP profile removal, not on CPX shutdown: the existing CCP
calls shutdown before ordinary transient execution as well. Duplicate LOAD,
unloading another package, profile reordering, and a failed/no-op profile
request must preserve the RCP byte. Removing RCP resets it; later LOAD then
observes defaults. The package identity used for association/reset must be
explicit, including any supported alternate-filename or duplicate-package
cases; a table slot index or live module address is not a stable identity.
The general per-package shadow-state allocator remains future architecture,
not a requirement for this one-byte RCP implementation.

## Plain-equals COPY assignment — 2026-10-08

Both COPY.COM and RCP.CPX now normalize `destination=source`, including
`B4:=A1:*.COM` where the colon belongs to the destination DU. The extra
separator colon in `B:OUT.DAT:=A:IN.DAT` is rejected. Source-first syntax
remains available; MOVE retains its existing `:=` assignment.

The shared body grows from 3,733 to 3,743 bytes; its 3,840-byte CPX allocation
is unchanged. No BIOS, BDOS or CCP code changes are required.

Qualification: parser execution in both builds verifies exact operand boundaries
and MOVE compatibility. cpmsim runs in both CPX-only and transient profiles
pass cross-DU shorthand, attributes and self-copy checks. Malformed assignments
(empty operands, duplicate equals and retired separator) preserve all media.
Evidence: `/private/tmp/copy-equals-du-20261008/evidence.json` and
`/private/tmp/copy-equals-filespec-20261008/evidence.json`.

## Frozen transient wildcard batch — 2026-10-08

COPY.COM now collects the complete sorted, deduplicated source-name list before
opening any destination. Execution consumes that fixed list instead of rescanning
between writes. The first bounded implementation supports 64 matching files;
65 or more report `COPY BATCH TOO LARGE` before mutation. This capacity is an
explicit interim limit, not a claim that all target transient features are done.

This increment retains DU-only wildcard destinations and rejects same-DU
wildcard copies. For the currently admitted cross-DU form, preserving source
names makes mappings unique and separates every destination from the selected
source set. Destination substitution and its additional overlap/collision checks
remain next. The CPX wildcard engine and all OS code are unchanged.

The transient-only driver is in `src/cpx/copy-batch.inc`; both host and native
transient builders select it only for COPY. COPY.COM is 4,576 bytes, including
704 bytes for the 64-name workspace. Native ZSM4/LINK output is byte-identical
to the host build. Native workspace reservation bytes are emitted explicitly
to match the host assembler's FF filler for reproducible comparison.

Qualification passes parser checks, cpmsim CPX/transient multi-extent wildcard
and attribute regression, a successful 64-file empty-file batch, and a 65-file
overflow leaving the whole source/destination disk unchanged. Evidence:
`/private/tmp/copy-frozen64-clean-20261008/evidence.json`,
`/private/tmp/copy-batch-boundary-final-20261008/evidence.json`, and
`build/utilities/NATIVE-RCP-TRANSIENT-BUILD.LOG`.

## Transient destination substitution and mapping preflight — 2026-10-08

COPY.COM now accepts positional wildcard destination templates in both operand
forms. Literals replace the corresponding source positions, `?` copies one
source position, and a terminal star run copies the remainder of that padded
8.3 field. Examples: `COPY B3:*.DOC=B1:*.COM` and
`COPY B4:X?***.BAK=B1:FOOBAR.COM` produce FOO.DOC and XOOBAR.BAK as specified.
An exact source also supports a destination template.

All admitted transient COPY invocations build and validate their concrete
destination mappings before opening any destination. Duplicate targets and
any target in the selected source set on the same DU (including exact self-copy)
report `COPY DESTINATION CONFLICT` with no mutation, even under `/O`. Generated
names with empty stems, embedded padding or forbidden characters report
`INVALID DESTINATION NAME`. Same-DU mappings to distinct, non-source names are
now allowed. The batch still uses the initial frozen source set even if new
outputs match the original wildcard. Capacity remains 64 source files.

COPY.COM is 5,671 bytes, including separate 704-byte source and destination
name tables. RCP.CPX, other transients and BIOS/BDOS/CCP are unchanged. Native
ZSM4/LINK and host builds are byte-identical. Interactive collision handling,
`/S`, `/V`, reporting and handoff remain later increments.

Qualification: direct execution tests cover positional padding and mapping
conflicts; cpmsim covers transformed names, same-DU frozen batches, rejection
without disk mutation, mapped attributes, 64/65-file capacity, multi-extent
wildcard regression and explicit overwrite. Evidence:
`/private/tmp/copy-mapping-qualified-20261008/evidence.json`,
`/private/tmp/copy-mapping-capacity-final-20261008/evidence.json`,
`/private/tmp/copy-mapping-wildcards-final-20261008/evidence.json`,
`/private/tmp/copy-mapping-overwrite-final-20261008/evidence.json`, and
`build/utilities/NATIVE-RCP-TRANSIENT-BUILD.LOG`.

## Transient /S and read-only continuation — 2026-10-08

COPY.COM now accepts trailing `/S` to skip existing writable destinations and
continue the frozen batch. Repeated `/S` or `/O` is idempotent; mixing the two
in either order is rejected before preflight or mutation. Unknown options are
rejected. Mapping conflicts remain unconditional failures even with `/S`.

An existing read-only destination is preserved and reports READ ONLY; that
file is counted as failed internally and the batch advances, under either
`/S` or `/O`. Writable skipped files report SKIPPED and are counted separately.
Full per-file source/destination reporting and final summaries remain later
work, as do interactive collisions and genuine noninteractive-mode admission.
Without `/S` or `/O`, existing writable collisions retain the current stop
behavior until the interactive collision increment is implemented.

COPY.COM is 5,761 bytes. CPX, other transients and OS binaries are unchanged.
Host and native ZSM4/LINK images remain byte-identical. Qualification covers
mixed skipped/new/read-only files; all-existing batches with byte-identical
media afterward; read-only data, attributes and source directory preservation;
continuation to later files under `/O`; repeated and conflicting switches;
unknown options; preflight rejection under `/S`; destination mapping and
multi-extent overwrite regression. Evidence:
`/private/tmp/copy-skip-20261008/evidence.json`,
`/private/tmp/copy-skip-mapping-regression-20261008/evidence.json`,
`/private/tmp/copy-skip-overwrite-final-20261008/evidence.json`, and
`build/utilities/NATIVE-RCP-TRANSIENT-BUILD.LOG`.

## Interactive choices and explicit /B — 2026-10-08

COPY.COM now prompts for existing writable destinations when neither `/O` nor
`/S` nor `/B` applies. The prompt identifies the concrete source and destination
DU/name. Y overwrites one file, N skips one, O overwrites subsequent writable
collisions, S skips subsequent collisions, and ? displays help and repeats the
prompt. Invalid responses also repeat it. O/S policy is reset on the next
invocation. Interactive rename (R) remains the next increment and is not yet
advertised in this prompt.

Ctrl-C at a collision prompt aborts the invocation before modifying that
destination; completed earlier files remain, later files are not attempted,
and caller DU/DMA are restored. Transfer-phase Ctrl-C handling remains separate
work. Direct console input permits explicit cancellation rather than allowing
an input call to warm-boot past COPY cleanup.

The user selected `/B` as genuinely noninteractive admission. It combines with
`/O` or `/S`; without either, existing writable destinations report FILE EXISTS,
count as failed, and processing continues. Read-only destinations remain
failed and preserved in every mode. SUBMIT alone does not select `/B`: native
qualification proves a SUBMIT file can pause at COPY's collision prompt.

User documentation now covers current transient options in section 4.6 and
COPY batch operation in section 5.7 of `docs/user/users_guide.md`. The target
specification records `/B`. No exported DOCX/PDF regeneration is included.

COPY.COM is 6,220 bytes; CPX and OS code are unchanged. Native and host builds
are byte-identical. Qualification covers Y/N, lowercase input, help/invalid
input, O/S policy reset in one running session, Ctrl-C after one completed
copy, `/B` collision continuation without prompts, SUBMIT prompting, concrete
DU labels (including user 31 and dollar signs), option parsing, mapping tests,
multi-extent wildcard and overwrite regression. Evidence:
`/private/tmp/copy-interactive-qualified-20261008/evidence.json`,
`/private/tmp/copy-interactive-wildcard-regression-20261008/evidence.json`,
`/private/tmp/copy-interactive-overwrite-regression-20261008/evidence.json`, and
`build/utilities/NATIVE-RCP-TRANSIENT-BUILD.LOG`.


## Combined source DU selection — 2026-10-09

COPY.COM links the shared DU include through `copy-scope.inc`. Source parsing
now resolves the scope without changing the current drive/user; the single
conventional destination parser therefore continues to inherit the caller's
original context. Collection iterates the complete source bitmap and freezes
an additional two-byte DU pair per source name. All selected drives are checked
before mapping or destination I/O. A missing source drive aborts collection.

Mapping scans per-source DUs when checking source overlap, rather than relying
on the last selected source location. Duplicate targets remain globally
forbidden. The 64-file capacity is global and rejects the 65th file before
writes. Each actual copy uses its frozen source DU, including prompt labels
and attribute handling. CPX COPY, MOVE.COM, CCP and BDOS are unchanged.

COPY.COM grows from 6,272 to 7,295 bytes. The source DU array adds 128 bytes,
plus the shared 64-byte selection map, 12-byte workspace and driver state.
Native ZSM4/LINK matches host assembly for COPY and all other generated
transients. Lexer and mapping tests pass. Native source-set qualification
covers the two requested selectors, exact output bytes, user-only inheritance,
duplicate-target rejection, overlap with an earlier source DU, invalid sources,
rejected destination sets, unavailable-drive rejection and global overflow.
Sources remain unchanged in every case; rejected batches leave destination
media unchanged. Evidence: `/private/tmp/copy-du-sets-v2-20261009/evidence.json`
and `build/utilities/NATIVE-RCP-TRANSIENT-BUILD.LOG`.

Native destination-mapping, interactive collision/abort/SUBMIT and skip/read-only
regressions also pass with this binary. Reports:
`/private/tmp/copy-du-set-mapping-regression-20261009/evidence.json`,
`/private/tmp/copy-du-set-interactive-regression-20261009/evidence.json`, and
`/private/tmp/copy-du-set-skip-regression-20261009/evidence.json`.
User-guide source now recommends explicit `:COPY`/`.COPY`; exported DOCX/PDF
files are not regenerated. Other transfer-utility adoption is recorded in
Specification 208, with PIP's operation contract still pending.


### 2026-10-09 — Interactive collision rename

COPY.COM now offers R at the collision prompt. Direct counted input supports
lowercase folding, backspace/delete, blank cancellation and explicit Ctrl-C.
Only exact bare 8.3 names are accepted; malformed, qualified and wildcard names
reprompt. The candidate replaces the current frozen mapping only after checking
all other batch destinations and selected sources. Conflicts restore the prior
mapping and reprompt. Existing renamed targets use normal collision handling.

COPY.COM is 7,848 bytes (553 bytes added); native ZSM4/LINK and host assembly
match. Other transients and resident CPX code are unchanged; no BIOS/BDOS/CCP
growth. Filespec and mapping tests pass. Native cpmsim interactive qualification
covers rename validation, editing, blank cancellation, future/past target
conflicts, selected-source overlap, existing replacement names, read-only replacement protection, abort and
unchanged original/source bytes, alongside Y/N/O/S, /B and SUBMIT regressions.
Evidence: `/private/tmp/copy-rename-v3-20261009/evidence.json`.
User-guide source is updated; exported DOCX/PDF files are not regenerated.
Verification, transfer-phase cancellation and final reporting remain pending.


### 2026-10-09 — Verification comparison core

An internal transient-only CTVERIFY routine reopens separate source and
destination FCBs and compares their 128-byte logical records directly. Equal
bytes and simultaneous EOF are required; open failures, read failures, unequal
lengths and mismatches return carry set. Transfer FCBs remain untouched and the
routine restores the transfer DMA buffer before returning. It performs no
writes and does not yet expose /V.

COPY.COM is 8,209 bytes, 361 bytes above the rename increment. Native ZSM4/LINK
matches host assembly for all generated transients. Filespec and mapping tests
pass. A proof-only native caller checks empty, one-record and multi-extent
matches, first/last-byte differences, shorter/longer targets, and missing files,
with byte-identical source/destination media after each verification. Evidence:
`/private/tmp/copy-verify-core-v2-20261009/evidence.json`.

The next increment must connect /V parsing, post-close verification, retry/skip
handling and failed-destination cleanup before making /V available to users.
No BIOS, BDOS, CCP or resident CPX changes are made.


### 2026-10-09 — /V integration and failure handling

/V is now a trailing, repeatable transient option, combinable with /O, /S and
/B. COPY verifies after destination close and before attribute application.
Interactive verification failure provides R/S/? with case-insensitive choices,
help/invalid-choice reprompting and explicit Ctrl-C. Retry removes the failed
output, resets transfer FCBs and repeats copy/verification. Skip removes it and
continues; /B removes and counts it failed without prompting. Ctrl-C removes it
and stops. A removal failure reports WRITE ERROR and stops the batch.

COPY.COM is 8,500 bytes (291 bytes above the comparison core). All generated
transients match native ZSM4/LINK; other transients and resident components are
unchanged. Filespec/mapping tests, comparison-core regressions and the existing
interactive/rename/SUBMIT campaign pass. Native flow tests cover normal
multi-extent verification, option combinations/repetition, one-shot failure then
successful retry, skip/help, /B failure and continuation, abort cleanup, no-/V
bypass, exact data and R/O/SYS preservation. Failure injection is confined to
private test binaries; the release binary contains no injection switch.

Evidence: `/private/tmp/copy-verify-flow-v4-20261009/evidence.json`,
`/private/tmp/copy-v-core-regression-20261009/evidence.json`, and
`/private/tmp/copy-v-interactive-regression-20261009/evidence.json`.
User-guide source is updated; exported DOCX/PDF files are not regenerated.
Transfer-phase cancellation, final reporting and final qualification remain.


### 2026-10-09 — Transfer and verification cancellation

Transient COPY polls direct console input before each transfer or verification
record. Ctrl-C removes the current incomplete/unverified destination and aborts
with earlier completed files untouched. Verification returns a separate
cancellation flag through its ordinary stack frame before invoking cleanup;
it cannot be mistaken for a verify-error prompt. Partial output is closed
before deletion so pending allocations are committed and then released.
Cleanup failure reports WRITE ERROR and stops. /B remains cancellable; polling
never waits and ignores other transfer keys. Cancellation is bounded by the
current synchronous disk operation and next record boundary.

COPY.COM is 8,574 bytes (74 bytes added). Native ZSM4/LINK matches host builds
for all transients. Filespec and mapping checks pass. The native cancellation
harness supplies real Ctrl-C to the production keyboard checker at deterministic
transfer/verification boundaries; only private test binaries contain the
positioning wrapper. It checks removal of current output, earlier-file and
source preservation, caller-DU return and successful allocation reuse by a
subsequent release-binary copy. Evidence:
`/private/tmp/copy-cancel-v4-20261009/evidence.json`.
Verification and collision/rename/SUBMIT regressions pass:
`/private/tmp/copy-cancel-verify-regression-20261009/evidence.json` and
`/private/tmp/copy-cancel-interactive-regression-20261009/evidence.json`.
No resident CPX, CCP, BIOS or BDOS changes. User-guide source is updated;
exported DOCX/PDF files are not regenerated. Reporting and final qualification
remain pending.


### 2026-10-09 — Operand-qualified attribute amendment audit

The COPY Specification records the supplied source/destination bracket qualifier
contract, ARC meaning, /BACKUP behavior and option scope. It replaces exploratory
/A=ARC and placement-inferred scope. User decisions: /BACKUP overrides a
destination ARC-set qualifier; contradictory destination assignments are rejected.
Multi-DU selection already exists. Qualifier parsing, attribute predicates,
destination masks and /BACKUP remain unimplemented. No shared DIR attribute
expression parser currently exists. The specification records the proposed
reusable component and bounded implementation sequence. Cancellation changes
prepared before the amendment remain intact and qualified.


### 2026-10-09 — Leading/trailing global option groups

Transient COPY now strips leading /O /S /B /V groups as well as existing trailing
groups, applies both through one flag routine, and uses the stripped cursor as
the operand base. Repetitions remain idempotent; cross-group /O-/S conflicts are
rejected before operand processing. Unknown, fused and option-only prefixes
fail. No operand-qualified semantics or /BACKUP is enabled yet.

Outside whitespace is trimmed from assignment operands so `destination = source`
works as required; internal filename whitespace remains invalid. Source-first,
assignment and multi-DU source forms retain their existing preflight behavior.
COPY.COM is 8,681 bytes (107 bytes added); other transients and resident
components remain unchanged. Native ZSM4/LINK matches host builds.

Filespec and mapping checks pass, including prefix/suffix flag combinations,
stripped pointers/counts and rejection cases. Native /V flow tests cover leading
source-first and mixed-group spaced assignment, original suffix forms, recovery
and invalid-option/unsupported-qualifier rejection without destination writes.
Native extended DU collection/global preflight/capacity qualification passes
with a leading /B form. Evidence:
`/private/tmp/copy-leading-options-v3-20261009/evidence.json` and
`/private/tmp/copy-leading-du-sets-20261009/evidence.json`.
User guide and architecture status are updated; exported manuals are not
regenerated. Operand qualifier separation and shared attribute parsing are next.


### 2026-10-09 — Operand qualifier splitter foundation

The internal shared component `src/utilities/common/operandqual.inc` splits a
terminal operand-attached bracket block after location/DU parsing. It returns
an unchanged start cursor, filespec length and qualifier content pointer/length.
Empty filespec is permitted for a destination DU-only operand. Malformed,
empty, nested, unclosed or nonterminal blocks and whitespace/control characters
inside qualifiers fail with cleared output pointer/length. It does not interpret
attribute expressions or validate filespecs; those remain separate layers.

CPU execution tests combine the real DU parser and splitter, including
`[A0,C[3,5,7-11],5]:F?*.DAT[!$SYS]`, destination-only qualifiers, aliases,
truncations and maximum-tail boundaries. Native ZSM4/LINK matches host builds.
COPY.COM is 8,787 bytes, 106 bytes above leading-option support; other transients
and resident components are unchanged. Filespec/mapping checks and the native
/V flow regression pass. Native evidence:
`/private/tmp/copy-qualifier-foundation-20261009/evidence.json`.

This is a linked internal foundation, not yet called by public COPY parsing.
Operand qualifiers remain rejected, so no attribute request is silently ignored.
Attribute-expression evaluation and semantic integration are next. No new user
syntax is claimed; exported manuals are not regenerated.


### 2026-10-09 — Shared source attribute predicate compiler

`src/utilities/common/attrselect.inc` compiles bracket contents into an eight-bit
truth mask over RO(bit 0), SYS(bit 1) and ARC(bit 2). It supports RO/RW/SYS/DIR/ARC,
R/O and R/W aliases, case-insensitive tokens and precedence ! > + > comma.
Repeated NOTs invert by parity. Unknown vocabulary, missing operands, malformed
operators, whitespace, parentheses and nonattribute queries are rejected with
cleared result and carry set. HL/B consumes the expression on success.

Execution tests cover 295 expressions against an independent Boolean evaluator
for all eight states, including aliases, contradictions/tautologies and precedence.
The small test CPU gained XOR C instruction support. The component is linked
into COPY's proof carrier but not called by public parsing; qualifier syntax
remains rejected until collection and destination semantics are integrated.
COPY.COM is 9,039 bytes, 252 bytes added. Resident code and other transients do
not grow. The received complete DIR contract is recorded in DIR Specification.md;
its implementation shares this dependency rather than creating another parser.


### 2026-10-09 — Source attribute predicate integration

Transient COPY now accepts source-attached qualifiers in both operand orders.
The DU parser runs first, then the operand splitter and shared attribute compiler.
Absent qualifiers reset the truth mask to FF (all states). Directory collection
evaluates original RO/SYS/ARC metadata before masking filename bytes or freezing
names. Only matching logical files contribute to capacity and mapping safety.
Source qualifiers never modify source metadata. Destination qualifiers and
/BACKUP remain rejected.

COPY.COM is 9,132 bytes, 93 bytes added. Native ZSM4/LINK matches host builds;
other transients and resident components are unchanged. Native qualification
covers all eight states, RO/RW/SYS/DIR/ARC, slash aliases, AND/OR/NOT, leading
options and spaced assignment, multi-extent data, no matches, invalid expressions,
filtered duplicate mappings, retained duplicate rejection and selected-source
overlap. Sources stay byte-identical and rejected cases perform no writes.
Evidence: `/private/tmp/copy-source-select-20261009/evidence.json`.
The native /V recovery regression passes:
`/private/tmp/copy-select-verify-regression-20261009/evidence.json`.
Shared expression/splitter and filespec/mapping tests pass. User-guide source and
architecture status now distinguish implemented source selection from pending
destination and backup operations. Exported manuals are not regenerated.


### 2026-10-10 — Destination attribute overrides

The shared attribute component now exposes AT_STATE, producing disjoint RO/SYS/
ARC set/clear masks for comma-separated literals, negations and aliases. Repeated
equivalent assignments are idempotent; opposing assignments and Boolean-list
operators fail with cleared outputs. CTDSCOPE splits the qualifier before normal
single-DU/filename parsing. Bare qualifier-only destinations are invalid.

CTDATTR adjusts only the three final extension attribute bits after source
inheritance, close and /V. Other file attributes and filename bytes are preserved.
Existing R/O targets remain unconditionally protected. /BACKUP stays rejected.
COPY.COM is 9,359 bytes, 227 bytes added; no resident or other transient growth.

CPU execution tests cover all pairwise vocabulary combinations, alias conflicts,
wrapper boundaries and every three-state override combination over all eight
initial attribute states, preserving unrelated attribute bits. Native qualification
covers both operand orders, source predicates plus wildcard destination templates,
exact multi-extent data and raw directory attributes, contradictions with no
writes, and read-only target rejection despite $RW and /O. Source media remain
unchanged. Native and host builds match for all six transients.
Evidence: `/private/tmp/copy-destination-attrs-v2-20261010/evidence.json`.
Source and /V recovery regressions pass:
`/private/tmp/copy-dest-source-regression-20261010/evidence.json` and
`/private/tmp/copy-dest-verify-regression-20261010/evidence.json`.
User guide and design status updated; exported manuals are not regenerated.


## 2026-10-10 — Explicit backup completion

Transient COPY accepts `/BACKUP` in leading or trailing option groups. It does
not imply `/V`, `/B`, or an ARC source predicate. After successful close and any
requested verification, destination attributes are applied with ARC forced
clear, then source ARC is cleared while other attributes are preserved.
Destination metadata failure prevents the source update. Either metadata
failure retains copied data, counts the file as failed, reports
`DATA COPIED; ATTRIBUTE STATUS INCOMPLETE`, and permits the batch to continue.
Skipped files, failed verification, and incomplete transfers do not clear source
ARC. Contradictory destination qualifiers remain invalid before writes.

COPY.COM is 9,576 bytes (217 bytes above the destination-qualifier increment).
All six native ZSM4/LINK outputs match host builds. No resident CPX, CCP, BIOS,
or BDOS change is required. Native evidence is preserved in
`/private/tmp/copy-backup-full-20261010/evidence.json`: leading/trailing options,
all eight attribute states, read-only sources, multi-extent source/destination
entries, destination ARC override, malformed options, contradictions, skipped
collisions, verification failure, and controlled destination/source metadata
failures. Earlier pending-backup notes describe historical implementation state.


### 2026-10-10 — Per-file transfer errors and cleanup

Transient read/write/close errors now count the current file as failed, print its
source/destination pair and diagnostic, close and delete a created incomplete
destination, and continue the frozen batch when cleanup succeeds. A missing
source at open uses the same per-file failure path. Sequential write status 2
is allocation-full and aborts the remaining batch after cleanup; other nonzero
write statuses report WRITE ERROR. Failure to create a destination retains the
existing conservative NO SPACE stop policy.

Deletion failure reports `INCOMPLETE DESTINATION CLEANUP FAILED` and stops the
batch without claiming removal. The cleanup diagnostic also applies to /V and
cancellation cleanup. Earlier completed copies are preserved. /BACKUP never
clears source ARC for the failed file. Metadata failures after completed data
remain distinct and retain the destination.

COPY.COM is 9,667 bytes, 91 bytes added. All six native builds match host outputs;
resident CPX, CCP, BIOS and BDOS are unchanged. Controlled native faults in
`/private/tmp/copy-errors-20261010/evidence.json` prove read/write/close
continuation, disk-full stopping, deletion-failure stopping, caller DU restoration,
exact earlier/later copies and source ARC behavior. Final allocation reporting,
summary accounting, and complete platform qualification remain separate work.
