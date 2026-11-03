# Merged release checkpoint — 3 November 2026

Production source: `232f059a032b58a4079d394c35a81a164f393da3`, the main
checkpoint containing #571–#574. Builds use the isolated
`validation/merged-release-232f059` worktree. RC564 masters are preserved.

**Both RAM System candidates and both paired Utilities sets are built.
cpmsim card accounting is reconciled. The supplied native suite and three
monitor campaigns pass on the identical Model 4 image. Release acceptance remains open.**

The normal combined System preparation stopped at
`test_rom_profile_ram_map.py:main`: `bdos-live-state template source drifted
from ownership inventory`. The relevant files are
`metadata/rom-profile-ram-z80pack.tsv` and `metadata/rom-ram-ownership.tsv`.
The original failed build log is retained. The independent Model 4 worktree
already contains a separate, unmerged reconciliation; it was not incorporated
or duplicated here.

Ordinary cpmsim operation uses the RAM System image. To continue that applicable
campaign, its tracks were built with the existing
`build_z80pack_image.py --ram-only --system-tracks-only` mode. The original
manifest, capacity, CONFIG fingerprint/cold-patch and independent file validators
constructed both platforms' RAM distributions. The exact preparation script is
archived. This is explicitly a RAM campaign, not a passing combined build or ROM
qualification. No production source, core, utility or shared-library API changed.

## Exact candidates

| Artifact | SHA-256 |
| --- | --- |
| cpmsim RAM System | `e44e39f9dd938da9039853296867ea8b099fc93e8389dd19d138794d7569169b` |
| Model 4 RAM System | `83e9ac2daa566312d5825a39d0f0ac4e3ef04cf83446aac7b493db30640edc5d` |
| cpmsim primary Utilities | `d175636d1393e0f3dd52ee48cad5b195ba23e699af16d821935cf2f1dcb041e6` |
| Model 4 primary Utilities | `534766b9ec95f59f4f5f6783005605468d01a79970bf01f52f4da1c248db0bb4` |
| cpmsim NOAH companion | `a5eacfe263f90433a21bec5825ff63d9feb8510aec1ae1b64f8b0da841234cce` |
| Model 4 NOAH companion | `4a3f7fc10d5f4f0ef5a5e3906e15810c4478e638ae13db0e1d70daa12102cc7f` |

Images/receipts are in `build/merged232-ram-systems/{z80pack,trs80gp}` and
`build/merged232-utilities-checkout`. System construction checks pass; cpmsim
cold/warm boot and exit checks pass. Independent Utilities inspection checks
exact membership, record bytes, user placement, allocation and native conversion.
The primary cpmsim Utilities volume retains one free 2-KiB block.

Runtime and qualification cpmsim profiles were reconstructed from the pinned
upstream Git objects, using `build_qualified_cpmsim.py`. Runtime campaigns use
the new runtime executable explicitly. The qualification profile is built but
is not assigned runtime passes merely by existing. Full environment manifests
remain in `build/merged232-{runtime,qualification}/environment.json`; archived
summaries retain their hashes, source/patch pins, commands and toolchain identity.

## Automated results

All eleven reviewed returning groups pass with no failed/error rows. FILETEST
and DISKTEST use the existing required-group full-disk fixtures. Suite revision
is `a9a878fcd2e36698c7e856654a85847a004fdd20`; all program/source checksums match
its pinned build manifest. These exact existing suite binaries were reused,
not represented as a new suite assembly.

Fresh supplemental runs pass for console output/input, read-only recovery,
resident ecology, ordinary/full-TPA returns, batch input, DRI/BetterCP/M
directory-full comparison, the case-preserving CCP profile, media changes,
fault recovery, documentary I/O, character routing and protected-mutation/
Function-37 accounting. BIOS, BIOS retry, CCP, unified BDOS, native builder TPA,
registry and expanded UI/query checks pass. The two-session shipped workflow
passes; all seven TYPE/ED/CONFIG application cases pass after the harness fix below.
Both UI media campaigns pass on the fresh runtime and new System image:
24 checksum/DASM/BYE phases and 22 diagnostic/XSUB phases, with independent
input/file/filesystem checks.

The existing card-to-oracle review mapping was retained, with every runtime or
controlled witness replaced by a fresh campaign result. Only byte-identical
specification documents were retained. Mapping provenance and witness hashes
are archived; no historical runtime pass was imported.

| Accounting classification | Cards |
| --- | ---: |
| PASS_SUITE | 273 |
| PASS_EXTERNAL | 98 |
| PASS_CONTROLLED | 56 |
| PASS_PROFILE | 2 |
| PROFILE_DIFFERENCE | 3 |
| OBSERVED_EXTERNAL_PROFILE | 1 |
| OBSERVED | 24 |
| NOT_RUN_NONGUARANTEED | 119 |
| OUTSIDE_BASELINE | 50 |
| NOT_APPLICABLE | 1 |

All 627 cards are accounted for, with no open required-card reconciliation.
This is not 627 passes, physical-device qualification, Model 4 runtime
qualification or release acceptance. The established differences for
case-preserving command tails and fixed-A0 lookup remain explicit.

## Harness correction and operator workload

`run_validation_cpmsim_applications.py` expected the obsolete resident VER
wording when testing saved cold-start commands. The actual current output is
the resident RCP identity. The runner now checks the canonical
`banner('VER', resident=True)` including CR/LF. It also resolves CLI paths before
entering private working directories. Data-preservation, cold-start-record and
application assertions are unchanged; the corrected seven-case run passes.

Earlier configuration/harness trials remain separate from final passes: missing
private pyte, relative executable/root arguments, the obsolete banner and an
incorrect staged-artifact directory for source-companion packaging. The Utilities
packager correctly requires a tracked source checkout; the final build uses it.
Private test dependencies were copied into the worktree and hashed rather than
installed globally. No failed trial is relabeled as an application pass.

The remaining native work is consolidated. The existing
`run_release_model4_conformance.py` accepts optional `--audit-blockers PACKET`
to run its seven returning-group jobs and the three prepared audit-blocker
scenarios in one invocation. It records runner identity and keeps separate
logs/results for each job. Ordinary existing invocations retain their scope.
The local packet was prepared without execution. Subsequently supplied native
results cover the same seven suite jobs on an exactly matching System image;
the separate successful audit-blocker packet matches the production artifact
hashes. Their bounded assertions are retained below. The new aggregate batch
option itself has only CLI/syntax checks; no native execution of that wrapper
is claimed.

`build/merged232-validation/Run-Model4-Qualification.command` is prepared for a
normal Terminal launch. It requires one start, without per-test operator input.
It is a future convenience, not another requirement to run the already passing
checks. Reuse the verified native evidence below; do not ask the maintainer to
repeat this packet merely because it lives in another worktree.

## Evidence and reproduction

[Index](evidence/2026-11-03-merged-release/results.json),
[receipts/logs/scripts](evidence/2026-11-03-merged-release/receipts-and-logs.tar.gz),
and [checksums](evidence/2026-11-03-merged-release/SHA256SUMS.txt).
The archive preserves exact build/test command arrays, new System receipts,
Utilities inventory, fresh 627-card matrix/review mapping, initial failures,
corrected runs and native preparation. Archived System summaries omit only the
large redundant `release_record` component envelopes and retain the SHA-256 of
the complete original receipt. Full receipts and production image bytes are retained in
the isolated worktree, with the hashes above.

Representative commands from the worktree:

```sh
python3 -B tools/build_qualified_cpmsim.py --source /Users/nathanael/projects/git/z80pack --output build/merged232-runtime --profile runtime
python3 -B tools/build_complete_system.py
python3 -B tools/build_utilities_disk.py --build --output build/merged232-utilities-checkout
python3 -B tools/test_utilities_inventory.py --artifacts . --images build/merged232-utilities-checkout --output build/merged232-validation/utilities-inventory.json
python3 -B tools/run_validation_returning.py --baseline "$BASELINE" --diskdefs "$BASELINE/diskdefs" --suite "$SUITE" --simulator "$SIMULATOR" --output "$EVIDENCE/returning" --program FILETEST --file-required
python3 -B tools/reconcile_validation_accounting.py --suite "$SUITE" --baseline "$BASELINE" --returning "$EVIDENCE/returning" --external "$EVIDENCE" --reviewed "$EVIDENCE/reviewed-fresh.json" --output "$EVIDENCE/accounting"
```

Use fresh output directories and the recorded build bootstrap order. The
archived preparation script gives the complete RAM-track and two-platform
manifest construction sequence; command arrays give each focused campaign's
flags. `$BASELINE`, `$SUITE`, `$SIMULATOR` and `$EVIDENCE` denote the absolute
paths recorded in the receipts. pyte-based runs use the private dependency path
recorded in `python-deps.json`.

Remaining gates are the normal combined-build reconciliation, profile/release
review, documentation and fresh-package installation. Selected native suite,
monitor and matching-artifact audit-blocker gates are closed as recorded below. No release
masters were promoted, no tag or release was published, and no main merge was
performed in this workstream.

## Supplied native pass: reuse matching bytes

The maintainer supplied `model4-bios-requal-20261103-150136/conformance/result.json`
with PASS_SELECTED_GROUPS for all seven jobs (eleven reviewed suite programs).
Its original source checkpoint is `0bd7f127ebca849fe613c7a36b3cd9c1c38314a8`;
its System SHA-256 is exactly the `83e9ac…` image above. Different source
checkpoints produced identical disk bytes. Keep the original receipt identity
and reuse its bounded assertions, rather than invent a new execution from this
worktree. Suite program checksums match the pinned a9a878f revision.

All three companion monitor runs also pass: ADM3A, VT52 and ANSI. Their receipts
include stage checks, matching shipped-file hashes, unchanged system tracks,
filesystem status zero, and unload/53K assertions. All use the same recorded
emulator. Captured summaries, receipt statuses, exact baseline bytes, program
hashes, monitor runner identity and shipped-file inventories were rechecked.
This does not claim an exhaustive terminal protocol or an audible-bell test.

The separate `BetterCPM-audit-blockers/build/blocker-validation/model4-final`
receipt passes invalid-drive rejection, low-TPA refusal/query returns and both
normal-TPA builders. Its BDOS/SYSBUILD/RLMBUILD hashes match this worktree's
products exactly, under the same emulator. These are matching-artifact assertions
on private diagnostic fixtures; their boot disk is not relabeled as the whole
distribution image. No repeat of those targeted tests is required here.

[Native evidence and scope](evidence/2026-11-03-merged-native-pass/results.json)
and its capture archive preserve the supplied and supporting receipts. The
original prepared/NOT RUN records above remain historical. The supplied
`result(1).json` and `result(2).json` contain the same aggregate receipt.
