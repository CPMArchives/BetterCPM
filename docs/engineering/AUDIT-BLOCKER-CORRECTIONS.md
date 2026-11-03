# Corrections for BCPM-AUD-001 and BCPM-AUD-002

Date: 2026-11-03. Base: `a5bf9a2dfeafec3fbff4d836c014cd7f47ba75e3`
(the audited main commit). Development after frozen core 1.0; this work does
not change historical core, disk or package qualification records.

## Changes and compatibility

**BCPM-AUD-001:** `UB_FCBDRV` now returns both carry and NZ for unsupported
FCB drive bytes. Previously byte 5 (E:) left Z set after `CP 4`; callers of
`UB_FCTX`/`UB_MCTX` testing NZ could operate on the previous drive. `OR A`
before `SCF` suffices because A is already in 4..254 on this error path.
It preserves the carry-based clients, supported A-D selection and existing
`?` handling. Public errors still pass through their existing result paths.

BDOS grows by one byte, from 3436 to 3437 of 3454 allocated bytes. Its state
and private stack move by one byte within that allocation; the measured
ownership inventory follows those symbols. No resident boundary, API version,
public entry, PDS allocation or stack size changes. Foundation stack high-water
remains 26/40 bytes; the selected extent-full regression measures 32/40.

**BCPM-AUD-002:** SYSBUILD and RLMBUILD compare the live gateway address at
0006h with their exclusive workspace ends before selecting SP=3F00h or touching
workspace. SYSBUILD requires 9000h (4000h..8FFFh); RLMBUILD requires 8600h
(including the header at 8200h..85FFh). Equality is sufficient. Rejection prints
an insufficient-active-TPA diagnostic and returns on the caller's stack, with
no file access. Existing `/VER`, `/HELP` and `/H` handling precedes admission.
Each COM grows by 55 bytes at the old revision. Successful packing is unchanged.

Actual same-revision reference/candidate comparisons and final rebuilds were
verified with `component_revision.py plan` and `accept`: BDOS 1.10 revision
001 -> 002; SYSBUILD and RLMBUILD 1.0 revision 005 -> 006. The registry and its
utility TSV projection carry these assignments. API versions are unchanged.
[Assignment receipts](audit-blockers-20261103/) preserve checksums and selected
input fingerprints. Reference bytes match the earlier audit artifacts. Receipts
describe builds based on the recorded main plus the candidate input fingerprints;
they do not assert that uncommitted corrections were present in that main commit.
No new input baseline is installed: these remain development builds.

## Regressions and observed results

- `tools/test_unified_bdos.py`: retains the full foundation regression and adds
  rejection checks for all 250 unsupported drive bytes across 13 public file
  services, including dirty Close and sequential/random writes. Matching live
  directory entries and an established drive-B context expose the original
  stale-context bug. Rejection must perform no BIOS disk I/O or directory change,
  and must preserve caller SP and IX. The added flag assertion fails on the
  original binary and passes after correction.
- `tools/test_native_builder_tpa.py`: 22 emitted-COM tests covering 7001h,
  7801h, 8001h, required-end minus one, equality, plus one and ordinary TPA,
  together with low-memory version/help queries. Canaries cover protected
  memory, private-stack storage and workspace. The original SYSBUILD damages
  the protected canary; both corrected utilities pass.
- `tools/test_audit_blockers_media.py`: native cpmsim rejects E: Delete without
  removing A:TARGET.DAT. A supported stateless RSX reservation lowers the live
  gateway to 8001h; both builders reject safely, queries work, RSX LIST and
  STAT MEM still work, and the entire System disk is unchanged. On a fresh
  normal-TPA boot both builders successfully create and reopen outputs on B:;
  those bytes match the host CCP RLM and SYSTEM.SYS packers exactly.
- Full common/Model 4 cross build and default RAM cpmsim build pass. Ownership
  inventory checks pass for both platforms. Fifteen selected host regression
  scripts pass, including BIOS, Make, write boundaries, grouped extents,
  extent-full handling, service inventory and component tracking helpers.
- Eleven native conformance invocations cover ENTRYTST, BDOSTEST, DIRTEST,
  FILETEST (safe and required), RANDTEST, DISKTEST (safe and required), ERRTEST,
  BIOSTEST and CCPTEST: 270 distinct passing cases, 23 observations, 109
  not-run/excluded cases, and no failure or error rows. Observations and skipped
  cases are not passes. See [validation summary](audit-blockers-20261103/validation.json).

Three broader, unchanged harnesses remain failing: `test_component_registry.py`
hard-codes older unrelated DDT/PIP/BYE/TED/new-utility revision values;
`test_utility_help_layout.py` expects the older `/HELP`-only footer;
`test_utility_versions.py` assumes a single recorded BDOS print pointer and
fails on TED `/VER` (after the corrected builders' checks have passed).
`test_remaining_utility_help.py` passes once TED's separately built COM is
available. This correction does not alter those unrelated test oracles.

## Reproduction

Use an isolated checkout with z80asm Release 2.1, Python 3.11 and cpmtools.
Retain the project's usual prerequisites and build configuration. A fresh
checkout still needs the existing build-order bootstrap (audit finding 004):

```sh
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'tools')
from build_trs80_boot import assemble, SOURCE, BUILD, BOOT_ADDRESS, STAGE1_ADDRESS
assembler = Path.home() / 'bin/z80asm'
assemble(assembler, SOURCE/'boot.mac', BUILD/'boot.bin', BOOT_ADDRESS)
assemble(assembler, SOURCE/'stage1.mac', BUILD/'stage1.bin', STAGE1_ADDRESS)
PY
python3 tools/build_rsxselect.py
python3 tools/build_complete_system.py
python3 tools/test_unified_bdos.py
python3 tools/test_native_builder_tpa.py
python3 tools/component_registry.py --check
```

With a fresh default-layout RAM System disk built from this checkout, its
matching diskdefs, and the supported patched cpmsim runtime:

```sh
python3 tools/test_audit_blockers_media.py \
  --image /path/to/fresh/system.raw --diskdefs /path/to/fresh/diskdefs \
  --simulator /path/to/cpmsim --output /path/to/new-evidence-directory
```

The output directory must not exist. It contains private disks, generated
diagnostic source/COM, transcripts, extracted outputs and result checksums.
The supplied System disk is hash-checked and never modified. For the baseline
negative controls, run the new tests with binaries built from the recorded
audited commit, keeping the test programs outside that immutable snapshot.

## Remaining qualification

The follow-up `tools/test_audit_blockers_model4.py` prepares and resumes three
Model 4 batches: all 13 invalid-drive service entry points, an admitted 8001h
RSX gateway with safe builder/query returns, and normal-TPA native creation of
both host-matching outputs. Preparation checks the production artifacts against
the revision receipts and verifies that the boot image contains that BDOS.
Resume verifies frozen input, runner/helper and emulator hashes, uses private
disk copies and retains screen captures and file-integrity checks. It does not
rebuild or mount release masters. A failed or incomplete run cannot produce an
aggregate PASS record.

```sh
python3 tools/test_audit_blockers_model4.py \
  --prepare-only --output build/blocker-validation/model4
# From a normal macOS Terminal, using the same checkout and emulator:
python3 tools/test_audit_blockers_model4.py \
  --resume --output build/blocker-validation/model4
```

The initial assistant-host LaunchServices preflight returned permission-denied
code 1100. The [preparation record](audit-blockers-20261103/model4-preparation.json)
preserves that historical NOT RUN status. The maintainer subsequently ran the
frozen packet from a normal macOS Terminal on 2026-11-03; all three Model 4
batches passed. The saved input hashes, captures, returned prompts, complete
logical disk comparisons and extracted outputs were independently rechecked.

The [runtime evidence](audit-blockers-20261103/model4-runtime.json) records the
exact BDOS, SYSBUILD, RLMBUILD, runner and emulator hashes, command witnesses,
disk hashes and native product checksums. All 13 invalid-drive entry points
reject; the 8001h gateway and loaded RSX survive both builder refusals and
queries; normal-TPA CCP.RLM and SYSTEM.SYS match the host references. A: remains
unchanged in all three batches; B: remains unchanged in the first two, and its
non-output input files remain unchanged in the successful-build batch.

PR #572 merged as `6c09d0e9c984c123f513b431993bce0a517bd8b0`. These observations
qualify the targeted audit-blocker behavior for the exact implementation
artifacts from `b69664b8dae31b64b5dae86f58a80660f4037b5f`. They do not qualify
subsequently merged Model 4 keyboard/BIOS or shared UI changes. A separate
targeted delta audit and final release qualification remain necessary. Other
audit findings, additional platforms, checked-profile qualification and
release-media publication remain outside this correction.
