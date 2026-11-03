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
With the audit follow-up applied, start in a checkout with no build output.

```sh
python3 tools/build_complete_system.py
python3 tools/test_unified_bdos.py
python3 tools/test_native_builder_tpa.py
python3 tools/test_z80_block_transfer.py
python3 tools/component_registry.py --check
```

For the whole-disk no-write assertions, use a fresh default-layout RAM System
disk built from this checkout with an empty cold-start command, its matching
diskdefs, and the supported patched cpmsim runtime. The distribution default
runs `SUBMIT STARTUP`, which writes to A: during ordinary boot.

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


## Audit follow-up on 3 November 2026

The implementation is `36ca7754908242d2d00891892ff5581148b6e31b`, based on
`3cfe33dd014e6af61b60433879e121a1aaab1d1f` after the Model 4 requalification
merge. These results cover the default layout on the two 1.0 platforms.

**BCPM-AUD-004.** The complete builder now assembles the boot sector and RSX
selector before the disk utilities measure their sizes. The distribution
builder calls that same entry point. From a checkout with no `build/`,
the direct command above produced the same 197 binary products as the parent's
bootstrapped Model 4 build, including SYSBUILD.COM, RLMBUILD.COM, SYSTEM.SYS
and the development DMK. The cpmsim distribution build matched all 240 binary
products in the corresponding parent build. The comparison included COM, BIN,
RLM, CPX, RSX, SYS, ROM, HEX, DSK and DMK files, matched by relative path.

**BCPM-AUD-005.** The small runner now transfers a byte before decrementing BC
for LDIR and LDDR. It fetches the instruction again if the copy overwrites its
opcode. The regression failed on both zero-count instructions in the parent.
For each direction, the updated runner and the pinned z80pack CPU core agreed
on 65,536, 1 and 65,535 transfers for initial counts 0, 1 and FFFFh. Four
overlap and opcode-overwrite cases also agreed on all memory bytes and BC, DE
and HL. The small runner still does not deliver interrupts during block copies.

**BCPM-AUD-003.** Defer full validation of corrupt CCP history to post-1.0.
Manually seeded lengths 0, 128 and 255 caused out-of-bounds writes on the full
core. In contrast, 5,000 valid insertions and 11,078 recalls agreed with the
reference history and preserved both guards. The audit found no supported
producer of the malformed records. The six-byte length check tried outside
the source tree left two bytes free and did not validate record traversal,
the used span or insertion. Reopen before release if supported input can
produce an invalid record, or if the CCP history writer or PDS layout changes.
BCPM-AUD-006 stays with the manuals workstream. BCPM-AUD-007 remains post-1.0.

**BIOS assignment.** Guarded builds at revision 001 compared the original audit
commit with the requalification merge. Both platform variants proposed revision
002. Final builds from the implementation commit passed independent acceptance
for each target at BIOS 1.14 revision 002, API 1.7. Collection now records
the emitted cpmsim BIOS from `build/z80pack/bios.bin` and the Model 4 BIOS from
`build/bios/bios.bin`. The former collector picked the Model 4 binary in a
cpmsim staging directory containing both. The archive contains all six guarded
reports and binaries, both proposals, and both final assignment records.
[BIOS revision evidence](audit-blockers-20261103/bios-revision-002.tar.gz)

To replay acceptance from the repository root, set `evidence` to a fresh
directory, then run the following commands.

```sh
mkdir "$evidence"
tar -xzf docs/engineering/audit-blockers-20261103/bios-revision-002.tar.gz -C "$evidence"
for t in trs80gp z80pack; do
  python3 tools/component_revision.py accept \
    --reference-report "$evidence/reference/$t.json" --reference-artifact "$evidence/reference/$t.bin" \
    --candidate-report "$evidence/candidate/$t.json" --candidate-artifact "$evidence/candidate/$t.bin" \
    --proposal "$evidence/proposals/$t.json" \
    --final-report "$evidence/final/$t.json" --final-artifact "$evidence/final/$t.bin" \
    --output "$evidence/$t-replayed.json" && cmp "$evidence/$t-replayed.json" "$evidence/acceptances/$t.json" || exit 1
done
```

**Media and tests.** Fresh System disks matched both published qualification
hashes, distinct from the development images above. cpmsim booted its new
disk. The byte-identical Model 4 DMK binds the earlier 269-pass native run
to this candidate. The new run performed host file and geometry checks on the
DMK. [Platform qualification and image hashes](Model4-BIOS-Requalification.md)

The cpmsim blocker harness passed with the empty cold-start command. A:
retained its exact bytes and the two builders produced the host reference
outputs on B:. On the distribution's default startup image the same harness
stopped at its no-write assertion. A boot-only control reproduced all 159
changed bytes without invoking a diagnostic or builder.

Fifteen host test scripts passed, including BIOS, CCP, BDOS, both history
suites, builder TPA, CRC, MD5SUM, block transfers and component identity
checks. The checked-profile suite still reports one missing import in its
isolated fixture and one source-closure assertion failure. Both reproduced
on the unmodified parent. Checked profiles and final release publication
remain separate decisions. [Validation record](audit-blockers-20261103/audit-follow-up.json)
