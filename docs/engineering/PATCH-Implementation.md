# PATCH 1.0 implementation and qualification

Date: 2026-10-28. Development candidate, revision 001. Implementation was
authorized after PR #536 merged. The [functional specification](PATCH-Specification.md)
controls behavior. No paired-platform release acceptance is asserted.

## Implementation

`src/utilities/patch.mac` composes command, instruction scanning, record planning
and transaction modules under `src/utilities/patch/`. It uses the existing exact
DU/filespec validator, bounded command-tail tokenizer, little-endian arithmetic
and cached random-record reader. `tools/build_patch.py` expands these selected
routines and prepares both the cross build and a self-contained native source.
The input closure is recorded in the component build report.

Memory use is fixed. The 9,896-byte COM includes code, strings, buffers and a
512-byte private stack. Its exclusive end is 27A8h. The zero-initialized mutable
state block is 2,286 bytes, with another 121 bytes of MD5 working state and a
128-byte directory buffer outside that block. No whole-file or whole-patch
allocation is made. Stack guards pass the compiled-code campaign.

Preflight first parses all instruction text and resolves INPUT/OUTPUT. It then
visits every original 128-byte record, scanning the complete patch to construct
that record's expected output and write mask. OLD bytes are checked against the
original record buffer; NEW bytes affect a separate buffer. Duplicate writes
are rejected through the per-record mask. Every OLD range is also checked against
the original file length. All records must pass before a temporary output is
created. Output generation and full readback reconstruct the same record plans.
The verification pass compares all 128 bytes of every output record and checks
its complete stored length.

This trades disk passes for bounded RAM and order-independent instructions.
For R input records and P patch bytes, each full planning pass scans roughly
R times P patch bytes; preflight, generation and readback each do this. Large
patches on floppy media can therefore be slow. There is no arbitrary instruction
count limit. Offsets and counters use checked 32-bit arithmetic; BDOS random
record addressing and the target filesystem determine actual accessible sizes.

Every patch scan computes MD5 over the complete stored instruction file,
including padding, and compares it to the initial fingerprint before a planned
record is consumed. The original input is fingerprinted initially and checked
after each full phase using fresh reads. The shared MD5 implementation is used
internally, not exposed as a PATCH option. These are consistency checks, not
signature/authorship verification or a promise against deliberately constructed
MD5 collisions. Keep input and patch media mounted and unchanged throughout a
command; CP/M offers no general concurrent-file locking guarantee.

All outputs are staged, including new destinations. Successful readback precedes
installation. Existing destinations move to a distinct collision-free same-DU
backup, which is removed only after installation. Failed restoration retains
both recovery files and identifies them. A backup-deletion failure leaves a
successful installed output with an explicit warning. Ctrl-C is polled at safe
boundaries; no poll interrupts the immediate backup/install/restore sequence.
No power-loss atomicity or cleanup after nonreturning OS errors is claimed.

The implementation adopts the review defaults: an empty instruction set is an
error; explicit no-op replacements are valid; protected outputs are refused;
new outputs are ordinary read/write, visible files. It also checks protection
again before installation. Help repeats the resolved destination identity and
preserves default No. No extra actions or switches were introduced.

## Measured artifact and builds

PATCH.COM: 9,896 bytes; SHA-256
`9f4bde87442942f3bc735ac454c046abbafb26cdc7948aed609260a46a4866ba`.
It occupies 10K of allocation on the 332K Utilities format.

The version/revision comes from the component registry. Current display is
`PATCH 1.0 (001-dev)`; no baseline has been promoted. The cross build emits
PATCH.COM, PATCH-NATIVE.MAC, native-source identity and selected-input provenance.
The native ZSM4/LINK build under stock CP/M 2.2 produces a byte-identical executable
body and runs the help/precedence and actual patch fixtures. The exported patched
record is independently compared with its expected complete bytes.

Two native integration corrections were made before the final successful run:
BDOS function 35 has no specified accumulator return and must not be diagnosed
from A alone; conventional text EOF must tolerate zero as well as 1Ah padding.
Text before EOF still rejects NUL and unsupported controls. A test-fixture import
that omitted its text EOF exposed zero padding as invalid instruction data; the
fixtures now explicitly contain conventional text EOF.

## Qualification evidence

The checked-in [qualification summary](PATCH-Qualification.json) records the
current artifact, media hashes, executed campaigns and pending platform status.
The focused campaign evidence is also preserved in
`PATCH-Qualification-Evidence.tar.gz` beside this document.

- `tools/test_patch.py`: 87 scenarios executing the compiled Z80 program against
  a register-clobbering, fault-injecting public-BDOS model. Coverage includes
  query precedence, malformed syntax and line boundaries, padding, context
  overlap, write overlap, overruns, overrides, identities, record crossings,
  verbose multi-mismatch reporting, all prompt choices, protection, cancellation,
  transaction collisions, create/write/close/read/rename faults, rollback and
  cleanup failures, deliberately corrupted staged readback, patch changes and
  input changes. No failed preflight creates output.
- `tools/build_native_patch.py`: stock CP/M ZSM4/LINK parity and execution checks.
- `tools/test_patch_media.py`: exact packaged PATCH under BetterCP/M cpmsim,
  repeated help then authorized staged replacement, a 65,792-byte input crossing
  64 KiB, and an unsorted 4,000-instruction patch larger than 64 KiB. Complete
  exported outputs are independently compared byte for byte. Input and patch
  bytes, plus the primary and companion Utilities images, remain unchanged.
- `tools/test_patch_distribution.py`: both packaged platform images, prepared
  native source, selected corresponding-source closure and refusal of incomplete
  or mismatched acceptance receipts. Image construction also checks every file
  readback, filesystem integrity and DMK/raw round trip.
- Registry projection, nine registry tests, Python compilation, documentation
  links/manual embedding and staged whitespace checks pass.

The model is not a physical-disk qualification. The cpmsim run is not a Model 4
run. Revisions and images from earlier runs are not substituted for the current
artifact in the qualification summary.

## Distribution and remaining work

The primary 332K Utilities disk remains at 26 files and 2K free. PATCH.COM and
PATCH.TXT are added to the existing NOAH companion volume, bringing it to five
files, with 258K free on the 332K companion. Independent directory/allocation
inspection confirms exact membership and complete stored bytes on both targets.
Keep NOAH.COM and its matching NOAH.OVL together. With primary Utilities
in B: and the companion in C:, invoke `C0:PATCH` and retain D: as a work disk.
Both raw cpmsim and native Model 4 DMK companion images contain the same PATCH.
Native source, provenance and full corresponding source travel in the host
Utilities package. Candidate inclusion is not release acceptance.

Model 4 qualification is **BLOCKED, not passed or waived**. The existing
read-only launch preflight returns BOOTSTRAP_NOT_PRIVILEGED (1100) for macOS
LaunchServices, preventing AppKit application registration in this execution
context. It stops before starting trs80gp; another crash was not induced.
See [the launch diagnosis](194%20macOS%20trs80gp%20Test%20Launch.md).
PATCH needs its own Model 4 run when that host permission issue is resolved,
or a separately authorized manual qualification/disposition. Previous utility
waivers do not apply automatically.

No acceptance receipt, baseline promotion or public release is produced here.
Historical Digital Research translations remain a separate project.
