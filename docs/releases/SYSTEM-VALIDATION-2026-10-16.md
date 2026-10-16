# BetterCP/M system validation — 2026-10-16

## Scope and baseline

This campaign covers the core OS and completed cpmsim and Model 4 System Disks.
Utilities Disk and CP/M Tools Disk validation is excluded and will be conducted
separately after their contents are finalized and built. Fixes arising from this
campaign belong to validation. Documentation alignment follows that phase.

Baseline: merged PR 350, `8127eab362bb88bb0805cd3bef15479a980c9514`.
The checkout was clean before source snapshotting. New baseline images were
assembled from isolated snapshots; no previous feature qualification was copied
into this campaign as a fresh pass. Subsequent roadmap/ledger edits do not
change the runtime source represented by these images.

Environment and executable hashes are retained in
`build/validation/8127eab/environment.json`. Host: macOS; host assembler z80asm
2.1; cpmsim release 1.39; trs80gp 2.5.8. Exact executable hashes, source revisions,
Python version and filesystem-tool identities are recorded there. Native suite
assembly uses the pinned suite's ZSM4 and DRI LINK, with their hashes recorded.

Independent suite revision: `a9a878fcd2e36698c7e856654a85847a004fdd20`.
The source checkout was clean and was not modified. A private clone at
`/private/tmp/bettercpm-validation-suite-a9a878f` supplied a fresh native build.

## Ordered campaign ledger

| Stage | Status | Evidence / next work |
| --- | --- | --- |
| 1. Clean builds, contents, boot, baseline console/memory | In progress; initial gates pass | Both distributions pass build/boot/integrity; focused BIOS/CCP and native editing/unload pass. Additional console/startup-failure/repeated-return cases remain. |
| 2. Fresh conformance suite | Started | All 13 programs rebuilt; cpmsim CPUTEST executed. Other programs and Model 4 suite runs remain. |
| 3. CPX/RSX lifecycle, relocation, ROM protection | Not run in this campaign | Run against this baseline; previous monitor qualification is background evidence only. |
| 4. Resident/transient command integration | Not run | Selectors, protection, prompts, explicit transient invocation, feature diagnostics and caller-state restoration. |
| 5. Utility operations and failure recovery | Not run | System-disk utilities only; disposable images and independent filesystem inspection. |
| 6. Monitors and applications | Not run | Fresh cross-platform campaign; do not substitute earlier feature-specific results. |
| 7. End-to-end release workflows | Not run | User sessions, configuration persistence, system export/install and reboot. |
| 8. Closure and final acceptance reruns | Not run | Resolve failures, identify accepted limits, rebuild and rerun against final revision/images. |

A status of not run is not a pass. Observations and explicit suite exclusions
are recorded independently from required tests. No claim of system-wide
completion is made by these first results.

## Executed baseline checks

- Fresh build and real boot of both System Disks: PASS.
- Manifest/file integrity, filesystem checks and CONFIG fingerprint: PASS on
  both targets. No planned System Disk omissions.
- Distribution failure gates: 13 tests PASS.
- Focused assembled Model 4 BIOS checks: 17 vector contracts, character
  transport, disk state, all 80 logical-record reads/writes, error paths and
  sector translation PASS. These CPU/stub checks do not certify physical media.
- Focused CCP checks: parsing, DU execution, navigation, monitor commands and
  CPX dispatch PASS. This is not the complete CCP conformance campaign.
- Native Model 4 command editing: Backspace/redisplay under startup ADM3A/M4SCRN
  PASS; loaded pair reports 50K, removing both leaves no RSXs and restores 53K.
  Evidence: `build/validation/8127eab/native-console-editing.log` and
  `/private/tmp/bettercpm-validation-8127eab-work/trs80gp/build/monitor-development/native-campaign/editing-alctv_cl/`.

Isolated build roots:
`/private/tmp/bettercpm-validation-8127eab-work/{z80pack,trs80gp}`.
Evidence/image generation:
`/private/tmp/bettercpm-validation-8127eab/release-8127eab362bb-762feca17a63/`.
Full reports, boot captures, filesystem results, included-file hashes and build
logs are retained. Report copies and a compact summary are also under
`build/validation/8127eab/`.

| Target | Files | Free space | Image SHA-256 |
| --- | ---: | ---: | --- |
| cpmsim | 30 | 148 KiB | `a2fecfa1c5de5103bb9b1fe4fd8d5b3794fc478b622bcf70c8b1bc6846462a4a` |
| Model 4 | 29 | 596 KiB | `a8dd41b7dbd4404b659730fee8c443281a93cfa9fe402281bf774708077d824b` |

## Fresh suite build and first execution

All twelve test programs and SCRATCH rebuilt natively with zero assembly errors.
Every resulting COM matches the published binary in the pinned clean source
checkout. `suite-build-results.json` records all 13 hashes/comparisons; the fresh
build log is `build/validation/8127eab/suite-build-qualified-env.log`.

On a disposable copy of the exact clean cpmsim baseline, `CPUTEST /ALL` reports:

```text
Summary: 2 pass, 0 fail, 0 error, 1 observed, 2 not-run
```

Items 0623/0624 are the required automatic checks. Item 0626 is an observation;
0625/0627 are explicit exclusions and are not counted as passes. The reference
image hash was verified before and after the run and remained unchanged.
Transcript, test-program hash and result:
`build/validation/8127eab/cpmsim-cputest/`.
This is one suite program on one target, not a complete conformance result.

## Findings and instrument issues

- **E001 — resolved host configuration:** the suite builder's default simulator
  path did not match this installation. Supplying the recorded executable then
  exposed a missing cpmsim helper PATH (`cpmrecv`). Supplying the simulator's
  `srctools` path allowed all 13 native builds to pass. Both initial failure logs
  are retained. These failures occurred in the host build environment, not
  BetterCP/M. Subsequent commands must record/use that qualified helper path.
- **T001 — pending instrument preparation:** the old compatibility capture tool
  assumes a sibling suite checkout, legacy test media and direct native app
  launch. Prepare a runner against the pinned fresh suite, this exact baseline,
  disposable scratch fixtures and the current macOS launch wrapper before
  adopting its results. Historical verdict-merging scripts must not turn old
  observations into fresh passes.
- **D001 — documentation alignment later:** DISTRIBUTION-BUILD still describes
  PIP/WHEREIS/editor omissions and separate runtime-helper files in outdated
  introductory text. The current manifest/build reports have no planned System
  Disk omissions. Record this for the separate documentation-alignment phase;
  it is not an OS failure or a reason to change validated runtime artifacts.

No OS defect has been identified by the executed checks so far. Most campaign
coverage remains pending, so that statement is not an acceptance verdict.

## Immediate continuation

Finish baseline console/startup and memory cases. Prepare fresh disposable
multi-drive suite fixtures and the current capture runner, then execute the
remaining conformance programs, retaining per-item classifications and explicit
operator/fault-injection requirements. Fix blocking defects as found and rerun
the affected checks before broadening the campaign.
