# CONFIG engineering-specification alignment

## Authority and current status

The current CONFIG engineering specification is the implementation baseline.
Builds 003–008 close inspection/startup and drive CLI gaps; they do not declare CONFIG complete.
The spec's cost/backend gates remain required for proposed runtime facilities.

| Requirement | Current status |
| --- | --- |
| Implemented domains only in menu | Corrected: F–J retained; A–E placeholders removed |
| Utility identity | Menu and /VER use the same metadata-owned version/build |
| Full command-tail validation | Implemented before INIT, catalogue reads or changes |
| /SHOW | Active and saved physical/logical settings, saved startup; embedded CRC-32 validation; no external reference |
| /STARTUP="..." | Confirmed, verified startup-only save; does not execute command |
| /DEFAULT | Pending-only semantics agreed; implementation/default-domain sources open |
| Drive command-line parity | Builds 006–007 physical fields and logical binding/format selection implemented; Build 008 scalar workbench fields implemented; Build 009 single-slot sector-map fields implemented |
| Persistent IOBYTE, printer and serial | Backend/space findings recorded in [runtime audit](CONFIG%20Runtime%20Audit.md); persistence and runtime prototype costs remain open |
| Native build | Build 007 dual-profile ZSM4/LINK and cross assembly match at 14,716 bytes |

The no-longer-offered keyboard/video sections are outside CONFIG's 1.0 scope;
printer/serial/IOBYTE entries may be added only when actual supported facilities
are implemented and qualified. An unavailable backend must not become a fake
working menu item.

## Command semantics and safety

No operands enters the existing menu. `/SHOW` returns without a completion
pause and does not alter the disk. Invalid/extra operands fail before INIT or
file access. `/VER` remains standalone and pure. Valid quoted startup command
text is parsed as data, avoiding false version detection on `/VER` inside it.

`/STARTUP="..."` prepares a complete canonical BCST record and uses the
established pending-only save path. It asks the existing Y/N question. A decline
returns immediately; acceptance writes/verifies both protected startup records
and uses the existing rollback on failure. It neither executes the command nor
saves active drive profiles. Empty text disables startup. The CLI's command
capacity is bounded by the complete CCP tail, including option/quote overhead.

## Evidence

- `test_config_command_line.py`: full-tail parsing, quoting, rejection before
  side effects, identity purity, menu scope and metadata-owned title.
- `test_config_startup_save.py`: first/second-record failures restore old BCST;
  rollback failure reports possible damage; CLI reports do not pause or claim
  success after failure.
- `qualify_config_command_line.py`: six live cpmsim cases on private disks:
  /SHOW, malformed request, declined save, accepted save, quoted /VER data and
  disabling startup. Inspection/decline/invalid cases preserve the entire image;
  accepted saves alter only BCST's two physical records, checked with the
  independent host parser. Evidence: build/config-command-line/run-_xywifnc.
- `build_native_config.py`: actual ZSM4/LINK parity, with deterministic reserved
  workspace bytes. Existing common utility identity tests continue to pass.

These checks do not yet establish final Model 4, clean-distribution or all-domain
CONFIG conformance. All remaining rows above must be addressed before closure.

## PIP and DUP reconciliation

PIP Build 026 passes all 18 focused campaigns. Its completion qualification
supersedes historical development notes; the obsolete opening work-review
heading now states that status. DUP Build 003 passes direct parser/dispatch and
cleanup tests; the specification version example is updated, while the
command-line report identifies Build 002 as the introduction of that feature.
DUP's explicitly retained legacy menu title is part of its present contract.

The final parser rejects overlong command-tail lengths before reading operands
and accepts the maximum 127-byte CLI tail without overwriting its text buffer.
Final artifact repeat: `build/config-command-line/run-d9cgmira`.

## Build 004: saved drive inspection — historical (superseded by Build 005)

The existing save-all reader now has an inspection branch after full checked
carrier reading and comparison, before fetching current settings or writing.
`/SHOW` snapshots only editable saved fields, restores the shared catalogue,
and prints saved profiles/bindings separately using the existing renderers.
Missing/invalid reference files, carrier mismatch and recoverable reads fail
without invented defaults, confirmation, completion pauses, or writes.

`test_config_saved_inspection.py` exercises early/middle/final reference failures,
carrier-read failure and mismatched installed carrier; it checks that inspection
never requests activation or write operations. Its existing Z80 test emulator
now implements RR B, used by the unchanged carrier-size helper.
`qualify_config_saved_inspection.py` checks real cpmsim execution with temporary
active changes (physical head-settle 20, B bound to drive 2), while saved defaults
remain unchanged (original head-settle, B bound to drive 1). It also checks
missing, invalid and wrong-build references; every image remains byte-identical.

The matching SYSGEN.DAT was omitted from the distribution manifest even though
CONFIG's existing save-all path already requires it. The maintainer approved packaging that data file
for both targets. Each builder emits a platform-specific reference artifact,
and the manifest installs it in user 0. Old images must be rebuilt to include it.

Final Build 004 cpmsim evidence: `build/config-saved-inspection/run-hnzpsdz8`
and `build/config-command-line/run-ayahhyvo`. Native CONFIG is byte-identical
at 13,404 bytes. Existing `test_config_save_all.py` passes Model 4 combined
active/pending saves, cold-boot checks and recoverable-write rollback after the
reader refactor. The ordinary parser, startup failure and 166 identity checks
also pass. No BIOS/BDOS resident bytes are added.

Model 4 saved-inspection evidence:
`build/test-results/config-saved-inspection-model4/run-qkqezaxa`.
`test_config_saved_inspection_model4.py` confirms saved B remains bound to
physical drive 1 after active B is moved to 2, returns to the CCP without a
keypress, and leaves the complete DMK unchanged. The capture delay allows the
emulated floppy to finish the checked carrier read.

## Build 004 reference packaging — historical (removed in Build 005)

The maintainer approved SYSGEN.DAT on both System Disks. Each platform builder
exports the exact reference it uses for its development image, and distribution
qualification compares it with the resident carrier installed on the candidate
disk. A missing or mismatched reference fails before publication. The manifest
and user manual identify this as required CONFIG data, separate from the
SYSTEM.SYS package accepted by SYSGEN.COM.

Clean distribution qualification with the reference-integrity gate passes for
both targets: `/private/tmp/config-saved-distribution-final/release-cb7dc6d9022b-03cf4292ecb7`.
The cpmsim System Disk has 28 files and 150K free; Model 4 has 25 files and
602K free. All reference bytes match the installed resident payload and geometry,
and filesystem/file-integrity/boot qualification passes. The 12 distribution
unit checks include missing, truncated, altered and wrong-geometry references.
An installed cpmsim CONFIG /SHOW run also passes without supplying extra files:
`/private/tmp/config-packaged-cpmsim-ncr0fof6/transcript.bin`.

Installed Model 4 CONFIG /SHOW also passes with packaged program/reference bytes
and the cold-start command disabled only on a disposable copy:
`/private/tmp/config-packaged-model4-no-startup-bhsv5d7n/screen.txt`.
A separate attempt to type CONFIG automatically after the normal startup script
was inconclusive (early capture, then launcher timeout). It is not counted as
passing that combined startup/inspection interaction. The clean builder's
ordinary startup/monitor boot checks pass independently; the isolated inspection
check above does not replace final interactive release validation.

## Build 005: compact embedded CRC-32 validation

The maintainer approved trying CRC-32 instead of the full reference file.
Inspection and save-all now read the actual disk carrier, retain its exact
original bytes for rollback, normalize only the established editable ranges,
and compare CRC-32/ISO-HDLC against a build-generated 20-byte descriptor.
The proposed carrier is restored after validation. Layout/geometry/bounds checks,
confirmation, readback verification and rollback retain their existing roles.
This is an accidental-corruption check, not authentication or exact comparison.

CONFIG with both platform records is 13,413 bytes (9 bytes above Build 004);
a Model 4-only artifact is 13,393 bytes. Neither needs the 6,784-byte SYSGEN.DAT.
The builders and distribution manifest no longer install that file. Native
build-media preparation changes only masked bindings and checks that its
fingerprint remains valid, rather than rebuilding a reference file.

`test_config_validation.py` checks independent exact-mask construction, immutable
DPH bytes, layout bounds and ambiguous-profile rejection. The Z80 implementation
passes the standard CRC vector, empty/byte-pattern/full-carrier vectors against
Python zlib, editable-field changes, fixed-byte corruption at the beginning,
middle and end, layout/geometry rejection, carrier-read errors and original-byte
preservation. The unit inspection path permits no file operations or writes.

Live cpmsim checks run with SYSGEN.DAT explicitly absent and reject deliberately
wrong embedded CRC/layout records without changing the image. Evidence:
`build/config-saved-inspection/run-uyr758kc`. Native ZSM4/LINK produces identical
13,413-byte output. Parser/startup rollback and 166 identity checks still pass.

Final CRC-only clean distribution evidence:
`/private/tmp/config-crc-distribution/release-9e9b057cbf5f-976604b4bd7c`.
Both candidates pass filesystem/file-integrity/embedded-fingerprint and ordinary
boot qualification, with no SYSGEN.DAT in either namespace. cpmsim has 27 files
and 158K free; Model 4 has 24 files and 610K free (8K allocation recovered on each).
Final cpmsim negative/inspection campaign: `build/config-saved-inspection/run-wxb71fsk`.
Final Model 4 inspection: `build/test-results/config-saved-inspection-model4/run-ephpkf4d`.
The Model 4 combined active/pending save, cold-boot checks and recoverable-write
rollback campaign also passes without the reference file. Both inspection and
save-all entry points reject CRC/layout/geometry/read failures before requesting
confirmation or writes. Native parity remains 13,413 bytes with both records.

## Build 006: physical-profile command-line parity

The named `/PHYSICAL=n` form updates one active profile with one or more
validated fields, preserving unspecified values and the existing separate-save
contract. It needs no format catalogue and performs no filesystem writes.
The whole request is validated before INIT. Public backend validation remains
in force. Boot A:'s track/side compatibility is now checked before physical
changes through either menu F or CLI; incompatible non-system bindings retain
the established detach/reset behavior. Cleanup failures are reported as partial
changes, never as full success or no change.

`test_config_physical_cli.py` checks constrained values, step-code translation,
malformed/duplicate/late-invalid operands before any I/O, merged profile commits,
boot geometry protection, safe boot timing, rejected profile/guard reads,
detach/reset operations, and injected cleanup query/detach failures.
`qualify_config_physical_cli.py` reads all active physical/logical state through
an independent public-API probe. On private cpmsim disks without DISK.FDB it
checks compound updates, boot-geometry rejection, invalid-tail atomicity, safe
boot timing, unchanged disk bytes and restoration on cold boot. Evidence:
`build/config-physical-cli/run-czc2h09a`.
Native ZSM4/LINK and cross output match at 14,124 bytes with both CRC records.

Logical binding/format selection/workbench CLI, `/DEFAULT`, and the required
IOBYTE/printer/serial audits remain open. This increment does not declare full
CONFIG specification alignment.

Model 4 CLI qualification also passes:
`build/test-results/config-physical-cli-model4/run-3klbruf8`.
Independent API snapshots prove the compound profile change, incompatible-binding
detachment and rejected boot shrink; the complete DMK remains byte-identical.
The fixed-delay harness waits for floppy loads before sending later commands.
Unit checks cover the existing menu PHSAVE entry as well as CLI application, so
the new boot guard is exercised through both paths. Parser/startup failure and
166 utility identity checks pass. No resident BIOS/BDOS bytes are added; the
transient has 1,492 bytes left before its existing 3E00h program/stack boundary.

## Build 007: logical binding and format-selection CLI

Add `/LOGICAL=B /PHYSICAL=1 /FORMAT="name"` and `/LOGICAL=B /UNBIND` with
active-only state and separate persistence. Parsing rejects A:, extra operands,
overlong/control/empty quoted names and malformed fields before INIT/I/O.
Format names use the displayed 32-byte catalogue description, not unstable row
numbers. Unique case-insensitive resolution, shared FDB normalization, geometry
compatibility and backend validation all precede mutation. Success resets only
the selected logical drive. Unbinding needs no FDB. Catalogue failures now return
without pausing for CONFIG CLI callers while retaining interactive behavior;
DUP's abort alias resolves to its existing target and its binary is unchanged.

`test_config_logical_cli.py` checks parser bounds and version-data handling,
unknown/duplicate/unsupported formats, incompatible geometry, backend failures,
unbind/reset behavior and CLI-versus-interactive catalogue error policy.
`qualify_config_logical_cli.py` exercises the real validated catalogue, malformed
CRC and missing files, ambiguous names with a repaired catalogue checksum,
actual backend binding/unbind, incompatible geometry, cold-boot restoration and
byte-identical disk media. Evidence: `build/config-logical-cli/run-33r7bwqh`.
Native ZSM4/LINK matches cross output at 14,716 bytes with two CRC records.
Existing physical CLI/parser/startup recovery, all 107 native FDB bindings and
166 utility identity checks pass.

Format-workbench field CLI, `/DEFAULT`, and peripheral audits remain open.
The transient has 900 bytes left before its existing code/stack boundary;
no resident BIOS/BDOS storage or ABI growth is introduced.

Model 4 qualification passes using real Shift-2 quotation-mark chords:
`build/test-results/config-logical-cli-model4/run-1c2svxt0`.
Independent snapshots check the complete binding after catalogue-based format
selection, unbind preserving its remaining fields, unrelated active state and
byte-identical disk media. The batch keyboard helper now supports the existing
Model 4 quote chord; no OS keyboard-driver change is involved.

## Build 008: scalar format-workbench CLI

`/EDIT=B` through `/EDIT=D` accepts named scalar fields, merges only supplied
values into a private copy, checks physical compatibility and submits one
validated backend update. Complete parsing precedes INIT and filesystem/backend
access. It requires no catalogue and retains separate persistence. Numeric word
and byte overflow, duplicate/unknown fields and A: are rejected. Sector-ID and
size-map slot commands, `/DEFAULT`, and runtime proposal gates remain open.

`test_config_edit_cli.py` covers all 16 named fields, word bounds, invalid tails
before I/O, exact preservation of unrelated binding bytes, geometry/read/commit
failures and selected-drive reset. Existing logical/physical CLI, common parser
and 166 identity checks pass. Native ZSM4/LINK matches cross assembly at 15,294
bytes with one embedded validation profile: 322 bytes below the transient cap.
A second profile costs another 20 bytes. No resident bytes are added.

`qualify_config_edit_cli.py` checks a real cpmsim accepted edit, backend rejection,
late-invalid request and protected A: request using independent public-API state
snapshots. Whole disk images remain unchanged; cold boot restores saved state.
Evidence: `build/config-edit-cli/run-dg__oori`. This increment has not yet had a
new Model 4 interactive campaign or clean distribution rebuild.

## Build 009: sector-map slot CLI and explicit-map validation

`/EDIT=B /SLOT=1 /ID=200` edits an ID; `/CODE=0` through `/CODE=3` edits its
packed size. One physical-order slot is accepted per invocation, optionally with
scalar changes in the same validated request. Missing slots/values, duplicates,
byte/slot/code overflow and late invalid fields fail before I/O. The CLI shares
menu I's first-mixed seeding and bit packing; startup text and edit scratch now
reuse exclusive transient storage, without changing the stack or workspace map.

A live negative test exposed the setter's legacy uniform fast path dropping an
explicit size map. CONFIG now invokes FDF.RSX's checked normalization before
committing explicit maps, through both menu and CLI. Missing support and invalid
maps leave active state unchanged. The underlying BIOS setter is unchanged;
this is a CONFIG precommit safety correction, documented in source and manuals.

Unit checks cover all 32 packed slots and four size codes on uniform and mixed
starting maps, preserved bytes, parser rejection before I/O and FDF validation
success/failure. Existing scalar/physical/logical/parser and 166 identity checks
pass. Native ZSM4/LINK matches at 15,411 bytes with one validation profile:
205 transient bytes remain, or 185 with a second profile. No resident growth.

The real cpmsim campaign accepts an ID edit and a consistent mixed-size edit
with FDF.RSX, rejects duplicate IDs, missing mixed support, invalid operands and
protected A:, and checks every active byte, unchanged disk images and cold reset.
Evidence: `build/config-edit-cli/run-afkjidqv`. The programmer guide's SYSGEN
size statement is corrected to 3,700 bytes for Build 003 in this increment.

Model 4 qualification passes with actual matrix-key input and four independent
state snapshots: `build/test-results/config-map-cli-model4/run-y6f4ymoz`.
The accepted ID changes only its selected byte; duplicate and inconsistent-size
requests preserve the complete binding and unrelated state. The whole DMK is
unchanged. This is focused qualification, not a clean distribution rebuild.
