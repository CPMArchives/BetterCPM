# COPY Utility: Incremental Implementation and Qualification

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
