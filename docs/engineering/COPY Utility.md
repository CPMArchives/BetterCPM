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
