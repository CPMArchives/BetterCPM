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

The initial baseline checks did not identify an OS defect. The subsequent
returning-suite checks below found V001; validation is not an acceptance verdict.

## Immediate continuation

Finish baseline console/startup and memory cases. Prepare fresh disposable
multi-drive suite fixtures and the current capture runner, then execute the
remaining conformance programs, retaining per-item classifications and explicit
operator/fault-injection requirements. Fix blocking defects as found and rerun
the affected checks before broadening the campaign.


## Returning-suite continuation

`tools/run_validation_returning.py` prepares fresh private baseline copies,
checks baseline and rebuilt program hashes, retains per-item classifications,
and verifies that the immutable reference image remains unchanged.

- ENTRYTST /GROUP:REQUIRED: 23 pass, 2 fail (0023/0024), 13 not-run.
  Evidence: `build/validation/8127eab/returning/entrytst-1uthwa_n/`.
- ENTRYTST /0023 reproduces alone: `entrytst-q96azx64/`.
- ECOTEST /GROUP:REQUIRED initially failed 0513 because the runner omitted
  the documented one-record BTONE.DAT fixture (`ecotest-cvstux1t/`). The runner
  now verifies and installs that fixture. A fresh run (`ecotest-4be9cj4p/`)
  reports 1 pass, 0 fail/error, 4 not-run. This is a resolved instrument issue;
  the first transcript remains retained, not relabelled as a pass.

**V001 — corrected; original returning-suite regression passes.** ENTRYTST's FCB
requests EX=0, while its 16,768-byte file has EX=1 in this disk's EXM=1
physical extent. An independent probe returns FF with EX=0 even after explicit
DMA=0080h, but succeeds with EX='?' and writes the expected default DMA.
The loader already resets the DMA correctly. DRI's
[BDOS source, `searchloop`/`searchext` and `compext`](https://github.com/brouhaha/cpm22/blob/master/bdos.asm)
masks EXM bits when comparing extents; BetterCP/M's UB_ITLIT currently compares
literal low-five-bit EX values. Thus these failing rows expose a search
compatibility defect, not a default-DMA defect or an invalid test. Correct the
comparison within the resident budget, add focused EXM coverage, and rerun the
original unmodified suite before closing V001.

The first focused-BDOS attempt also found an instrument prerequisite: this
isolated distribution build does not generate `build/bdos/directory.bin`, which
`test_bdos.py` expects. No BDOS pass is claimed from that unsuccessful launch.

## CONFIG menu change during validation

CONFIG Build 012 rearranges the menu to A startup, B IOBYTE, C drives,
D formats, E format editor and S save. All destinations plus Ctrl-C exit pass
the dispatch check; native ZSM4/LINK and cross assembly are byte-identical at
15,431 bytes. This is a post-baseline candidate and must be included in the next
qualified distribution build; it does not alter the immutable 8127eab evidence.


## V001 correction and candidate qualification

The corrected production iterator masks EXM on both FCB and directory EX.
A shared field-index calculation saves four bytes, keeping the net growth to
two bytes: BDOS is now 3,454/3,454 bytes, with no TPA or public ABI change.
Native ZSM4/LINK and host assembly are byte-identical. Focused execution covers
EXM 0/1/3/7/15, same/different groups, EX high bits, wildcard EX, name mismatch,
and the name-only path. Evidence: `v001-native-bdos-qualified.log` and
`v001-extent-groups.log` beneath `build/validation/8127eab/`.

The two-byte code growth shifts BDOS state/template anchors. Checked ownership
and ROM packing measurements are updated: 5,520 immutable source bytes,
800 packed-code relocation words (one additional live DPB reference), ROM boot
entry FE12h, 460 bytes spare after boot integration. These are measured updates;
no inventory completeness or protection checks are removed.

A clean isolated candidate build, including CONFIG Build 012, passed both
platforms' filesystem, file-integrity, CONFIG-fingerprint and boot gates:
`/private/tmp/bettercpm-validation-v001i/release-d58b15bf0646-7935825168c7/`.
This candidate is based on d58b15b plus local changes, **not** a new clean Git
revision. Its source-input hashes are retained in the reports.

| Target | Files | Free | SHA-256 |
| --- | ---: | ---: | --- |
| cpmsim | 30 | 148 KiB | `2bb183647e6cdb36c111bb071088d1470add0ab446cd5ae9221a3ebfb2472e93` |
| Model 4 | 29 | 596 KiB | `b63d062ebe38249ed24490414f9f5df572efcecced6af080b7e43e0ba0619a54` |

The conformance reference copy is hash-identical to that published candidate.
Original, unmodified rebuilt suite programs report:

| Command | Pass | Fail/error | Observed | Not-run/excluded | Evidence directory under v001-returning |
| --- | ---: | ---: | ---: | ---: | --- |
| ENTRYTST /GROUP:REQUIRED | 25 | 0 | 0 | 13 | entrytst-wuj1mz44 |
| BDOSTEST /GROUP:GATEWAY | 9 | 0 | 5 | 3 | bdostest-8od1sn6o |
| CPUTEST /ALL | 2 | 0 | 1 | 2 | cputest-u2rj9vbi |
| ECOTEST /GROUP:REQUIRED | 1 | 0 | 0 | 4 | ecotest-gpsuks2j |

These are selected returning checks on cpmsim, not complete suite coverage or
fresh Model 4 conformance. Baseline BDOSTEST gateway evidence is additionally
retained in `returning/bdostest-rhk7z7gn/`.

## Guarded ROM continuation and next finding

The distribution build intentionally uses system-tracks-only media; guarded
ROM lifecycle testing additionally requires dedicated ROM development disks
and relocated CONFIG fixtures. These were freshly generated in
`/private/tmp/bettercpm-validation-v001-rom-media/`. An earlier missing-fixture
attempt is retained and is not counted as an execution failure.

The guard harness still expected 704 runtime-overlay relocations. Both the
original clean 8127eab build and corrected candidate independently emit 812
across 18 files with zero unresolved references. The assertion now uses that
verified count; no unresolved reference is admitted.

**V002 — open ROM system-stack reserve failure.** The protected ROM run
completed its scripted cold/warm boot and CPX/RSX lifecycle commands without
a protection violation, but its final system-stack reserve check fails:
26 bytes used from 32, leaving six bytes; acceptance requires at least eight.
Guard primitive checks also pass (CPU/DMA writes and guest guard changes are
rejected). This is **not** a guarded-ROM campaign pass. No assertion has been
relaxed. Determine whether the reserve loss predates V001, identify the deepest
call path, recover the required reserve, and repeat the guarded campaign.
Evidence: `v001-rom-xip-full.log` and `v001-rom-xip-retained.log`. High-water
reports are now saved before reserve validation so failing measurements survive.
Workspace-lifetime validation following the failed stack gate has not run.

The older `test_unified_bdos.py` also fails its console-ready instrumentation
before reaching directory tests; it patches a BIOS leaf assuming older console
routing. No full unit-suite pass is claimed from it. The new focused extent
regression executes the production comparison directly; original ENTRYTST
provides independent public-BDOS coverage of the actual defect.
