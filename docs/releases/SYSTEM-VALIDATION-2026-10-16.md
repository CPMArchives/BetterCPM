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
| 2. Fresh conformance suite | Selected returning groups pass on both platforms | V010–V012 refresh production BDOS/file/random and native DIR/CCP/entry/CPU/ecology/disk-safe, BIOS/error-safe and selected console evidence. Manual, device, terminal-outcome and applicability gaps remain explicitly open. |
| 3. CPX/RSX lifecycle, relocation, ROM protection | Automated checks pass after cold-start fix | V016 identifies and clears an uninitialized cold-entry loader-recovery flag. Poisoned-RAM initializer test, 32 pristine-media cold boots and guarded lifecycle/stack/workspace checks pass. Focused production monitor relocation checks pass on both backends (V015). Deferred manual/device checks remain explicit. |
| 4. Resident/transient command integration | Partial; fresh native file workflow passes | V013 covers native file workflows. V021/V023–V027 add shipped cpmsim ERA/REN/COPY/MOVE/DIR/STAT/TYPE selectors, protection, reporting and controlled recovery. Broader native repetition and caller-state cases remain. |
| 5. Utility operations and failure recovery | Partial; selected ED/CONFIG/DUP/SYSGEN checks pass | V013–V014 verify ED/CONFIG cases; V017 adds shipped cpmsim DUP format/copy/check and SYSGEN named export/reinstall/reboot; V018 adds native named SYSGEN and controlled recovery/parser checks. V019 adds native DUP format/copy/check/CRC recovery; V020 adds native disk-source SYSGEN safeguards/install/reboot. V021/V023–V028 add cpmsim selector/protection/reporting and controlled COPY/TYPE/ED/CONFIG recovery checks. Remaining utilities, native repetition and broader device faults remain. |
| 6. Monitors and applications | Selected cross-platform regressions pass | V013–V014 exercise all three shipped monitor/backend pairs, native file workflows and cpmsim TYPE paging/file boundaries. Broader applications, audio/manual/device and exhaustive protocol coverage are not implied. |
| 7. End-to-end release workflows | Partial; CONFIG startup cold boot passes | V014 confirms saved startup executes only on next cold boot. V017 adds cpmsim named system export/install/reboot. V018 verifies the native named-package round trip; V020 verifies disk-source installation/reboot. Other complete release workflows remain. |
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

**V002 — corrected; protected ROM reserve and lifecycle checks pass.** The protected ROM run
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


## V002 correction

A private guarded-emulator trace (`stack-audit/trace.log` and the retained
`/private/tmp/bettercpm-stack-trace/transcript.txt`) locates the deepest stack
writes in CPX.COM's UV_MATCH before it installs its private stack. The shared
recognizer saves HL merely to compare one character. Replacing that operation
with XOR/DFh-mask comparison saves two peak stack bytes and four code bytes.
This is independent of the preceding V001 BDOS change. Stack sizes, minimum
reserve, public interfaces and unloaded 53K TPA remain unchanged.

- `stack-audit/version-stack.log`: all byte substitutions at each of four token
  positions preserve the old match behavior; caller registers retained; peak
  24/32 bytes, reserve eight.
- `stack-audit/utility-versions.log`: 166 existing identity/resident-dispatch/
  invalid-usage/fall-through checks pass on freshly rebuilt programs.
- `stack-audit/native-cpx_utility.log`: CPX.COM 910 bytes, native/cross identical.
- `stack-audit/native-config.log`: dual-profile CONFIG 15,457 bytes, native/cross
  identical. CONFIG is now Build 013; other linked consumers' build counters
  also advance for the common-source fix.
- `stack-audit/rom-xip.log`: full protected-ROM execution, guard primitives,
  CPX/RSX lifecycle and workspace-lifetime campaign pass with fresh development
  media `/private/tmp/bettercpm-validation-v002-rom-media/`.

| Stack | Used/capacity | Reserve |
| --- | ---: | ---: |
| Loader | 20/64 | 44 |
| System | 24/32 | 8 |
| BDOS | 28/40 | 12 |

The protected ROM manifest and high-water report are retained in that media's
`rom/rom-xip-qualification.json` and `rom/rom-stack-qualification.json`.
Original failed runs are not relabelled. Native Model 4 and wider conformance
coverage remain separate pending campaign work.


The post-fix returning regression repeats all four selected groups with zero
failures/errors: ENTRYTST 25 pass, BDOSTEST gateway 9 pass/5 observed, CPUTEST
2 pass/1 observed, ECOTEST 1 pass. The same 22 excluded/manual rows remain
not-run. Evidence is in `stack-audit/returning/` (entrytst-ymqvjg44,
bdostest-go9wct1o, cputest-cyqm6yjo, ecotest-gcgp2fn2). Native RCP payload parity
also passes at 7,146 bytes (`stack-audit/native-rcp.log`).

An initial V002 distribution build correctly refused publication because the
new regression-test source was added while the build was running. Its candidate
is retained, not published; the subsequent V002b build starts from unchanged
inputs including that test. This is a provenance guard, not a runtime failure.


Final V002b candidate qualification passes both platforms: filesystem, file
integrity, CONFIG fingerprint and native boot. The release is `/private/tmp/bettercpm-validation-v002b/release-39f450442dbc-608a1bd7f308`.
The cpmsim conformance reference is hash-identical to the published image.

| Target | SHA-256 |
| --- | --- |
| z80pack | `a6590279ff439f04902b7bd16ce3dde8cf5b3c58cc674264b0dfadf21cb9ea46` |
| trs80gp | `f84377b81af00db7e34f2003c47c24b8e7f06304dedc7aff88739a09f02f0b0a` |

Evidence: `stack-audit/v002b-distribution-build.log`. V002 is closed; broader
system-wide validation remains in progress. This local candidate includes
uncommitted changes after PR #352 and does not claim a clean release revision.


## File and directory conformance continuation

The returning runner now prepares a private System Disk A and expendable data
media B/C/D in the same known format. Programs and canonical runtime payload
are installed on B, including user-one BTUSR and RO-marked BTRO; C gets the
canonical BFILE-000 record. Search-pair names are installed for BDOSTEST. D is
prepared for RANDTEST lifecycle and FILETEST required coverage with a
128-record BTFULL (record 127 contains FULL-127), BTREL, and allocation filler;
zero-length files fill the remaining directory slots. Geometry and extent
capacity come from the selected disk definition. Each program gets a new media
set; originals remain unchanged. Fixture source hashes and transcripts are
retained. The runner additionally records initial/final private disk hashes.

| Selected group | Pass | Fail/error | Not-run | Evidence under file-directory |
| --- | ---: | ---: | ---: | --- |
| DIRTEST /SAFE | 49 | 0 | 0 listed | dirtest-evgrncfc |
| FILETEST /SAFE | 28 | 0 | 0 listed | filetest-d9jgxsvl |
| FILETEST /GROUP:REQUIRED | 68 | 0 | 2 | filetest-hafxnow6 |
| RANDTEST /SAFE | 39 | 0 | 2 | randtest-y5dkoj2g |
| BDOSTEST /GROUP:REQUIRED | 56 | 0 | 3 | bdostest-xiyiqdd4 |

`/SAFE` selects subsets; zero listed not-run does not mean all catalog items
were exercised. FILETEST required coverage supersedes its narrower safe group
for coverage counting; BDOSTEST required similarly includes prior gateway
checks. No failures remain in these prepared groups; full conformance is not
yet complete and Model 4 execution is still pending for these groups.

Instrument corrections (initial evidence retained):

- DIRTEST's first attempt stopped at Bad Sector after two passes because the
  runner had not mounted C for explicit-drive search. That attempt was stopped,
  not counted as a completed group. Fresh C/D images and the cross fixture
  resolved it.
- RANDTEST initially reported 0556 failing and 0557 passing with Prereq=FF
  because D lacked BTFULL. Neither initial result is accepted as evidence of
  the lifecycle contract. The prepared D run reports Prereq=00 for both and
  passes 0556/0557. Missing prerequisite is an instrument failure here, not an
  OS failure or a pass for 0557.
- Expanded FILETEST initially failed 0253 because its D fixture was data-full
  but still had free directory slots (`filetest-bnkaajlb`). Adding the missing
  zero-length directory fillers produces the complete passing required group.

These issues reinforce that an aggregate's advertised safe/required label is
not a substitute for auditing each case's fixture requirements. No suite source
or oracle was changed to obtain the passing results.


Final fingerprinted reruns (`file-directory-final/`) retain the same results:

- `bdostest-dr5lfj6o`: BDOSTEST /GROUP:REQUIRED — 56 pass; 3 listed not-run; zero fail/error.
- `dirtest-aqui_a1e`: DIRTEST /SAFE — 49 pass; 0 listed not-run; zero fail/error.
- `filetest-ejxhw4h6`: FILETEST /GROUP:REQUIRED — 68 pass; 2 listed not-run; zero fail/error.
- `randtest-u68ftu1_`: RANDTEST /SAFE — 39 pass; 2 listed not-run; zero fail/error.


## Console, BIOS, disk and logical-error continuation

On private copies of the same hash-verified V002b cpmsim candidate:

| Group | Pass | Observed | Not-run | Evidence under console-disk |
| --- | ---: | ---: | ---: | --- |
| BIOSTEST /SAFE | 5 | 11 | 30 | biostest-zzmarq0q |
| ERRTEST /SAFE | 5 | 12 | 26 | errtest-ztf0_tv3 |
| DISKTEST /SAFE | 7 | 0 | 0 listed | disktest-w25l0xbc |
| DISKTEST /GROUP:REQUIRED | 11 | 0 | 6 | disktest-yqmuvvr8 |
| CONSTEST /0052 through /0058 | 7 | 0 | other cases unselected | constest-output-h1ktac5e |

All selected checks pass with zero fail/error. Disk required coverage includes
the safe rows, so those seven are not additional unique passes. Its prepared D
has full allocation but available directory slots (unlike FILETEST 0253's
full-directory fixture). After the suite's allocation-failure/release checks,
host cpmtools extracts BTFULL and compares every byte with the original
128-record control file; the data is unchanged. The six terminal procedures
remain not-run, not implicit passes.

`run_validation_console.py` supplies each confirmation only after independently
matching literal OBSERVED bytes and EXPECTED framing for the reviewed case.
It does not parse the utility's own EXPECTED text into an oracle or blindly
answer Yes. The seven cases cover Functions 2/9, literal dollar output,
termination/empty strings and CR/LF. They do not qualify rendering, timing,
input editing, or separate character devices.

Instrument findings retained separately:

- CONSTEST /SAFE still invokes confirmation prompts for required output cards,
  despite its aggregate-mode commentary. The unattended run was stopped at
  0052; no aggregate result is accepted. This selector is removed from the
  generic unattended runner. Other interactive cases need explicit scripts.
- DISKTEST's protection rows require a mounted B, even without destructive
  scratch work. Its initial A-only run stopped at Bad Sector. Mounting private
  B/C/D resolved it. The required allocation aggregate intentionally finishes
  on A after Function 13; correcting the runner's expected return prompt
  resolved a capture timeout after the already-completed eleven passing rows.

### BDOS unit instrument repair and recovery coverage

The old foundation harness decoded presumed CALL operands behind BIOS console
vectors. Monitor routing had changed that instruction shape. It now supplies
explicit deterministic public-BIOS character providers, including a
nonblocking LIST sink and the BIOS-required FFh ready/7-bit input conventions.
The test no longer purports to verify normalization inside a replaced BIOS
provider. The production physical-read mapping remains in use for disk tests;
fresh BIOS conformance and live console observations are separate evidence.

With that instrument corrected, the current emitted 3,454-byte BDOS passes its
foundation (directory/allocation/extents/record transfers, A/B/A workspace
reconstruction; 26-byte private-stack high-water). The recovery campaign
passes 24 wrapper success/ignore/abort combinations, then filesystem foundation
paths with faults injected after candidate physical I/O (28-byte high-water).
Evidence: `console-disk/bdos-foundation.log` and `bdos-recovery.log`.
These are assembled-code unit/injection checks, not substitutes for ERRTEST
physical-fault procedures and real operator recovery through a live CCP.


### Live final-BIOS operator recovery

`run_validation_faults.py` boots three separate private cpmsim disks, installs
the reviewed FAULTMORE boundary provider and canonical BTONE, and observes the
real candidate BDOS operator path. The provider first completes a healthy read,
then installs one-shot failing final READ/WRITE entries, restoring each vector
before reporting failure. It counts both provider hits.

Fresh results (`console-disk/operator-recovery-k11vx70z/`):

- With no answer, Bad Sector is printed and the read caller remains suspended
  through a 0.5-second observation window.
- I resumes the read and write callers; both failing provider calls are counted.
- Ctrl-C abandons the read caller, rebuilds the CCP, and permits VER and BYE.

All three pass, with source/program/fixture/emulator hashes, full transcripts,
and original-image hash preservation recorded. This qualifies the final-BIOS
boundary and live recovery; it does not prove controller retry behavior or
promise data after ignored errors. No individual unexecuted ERRTEST fault card
is relabelled as a pass. The separate 17-vector BIOS contract campaign also
passes character transport, 80 reads/writes, failure paths and sector
translation (`console-disk/bios-vectors.log`).

### Model 4 first run and capture correction

The first native run retained CPU and ecology screens, with 2 and 1 required
passes respectively. DISKTEST /SAFE reported failures in 0373/0375/0376/0377.
The runner incorrectly waited only for a passing summary, leaving the emulator
idle at the CCP after the failed report. The user supplied a screenshot of the
completed failures; it is retained with the original private disks and screens
in `console-disk/model4-returning-vdyug6ff/`.

The secondary fixture was also incorrectly formatted: default Model 4 B has
OFF=0 and 800K data capacity, whereas the runner retained A's 20K system-track
prefix. The corrected B image is entirely E5-formatted data. The runner now
waits for the last row regardless of pass/fail, captures the completed report,
and records failed results before raising an error. LaunchServices cleanup now
terminates its own emulator if a capture is cancelled; normal/cancel/timeout
paths are covered by `test_trs80gp_launch.py`. No OS code was changed for these
instrument corrections. The corrected native rerun determines whether the
four original reports are explained by that fixture mismatch.


The corrected Model 4 screenshot now shows all seven DISKTEST /SAFE rows
passing, including 0373/0375/0376/0377. With the boot prefix removed from OFF=0
B, those original reports are resolved as a fixture error; no OS change or
weaker disk oracle was needed. The same run retains CPU and ecology passing
screens. This is the first fresh native Model 4 suite subset in this campaign,
not a substitute for the still-pending wider Model 4 groups.


Final native capture result: `console-disk/model4-returning-3ewl9l9z/result.json`
records three passing groups (CPU 2 required, ecology 1, disk state 7), with
program/fixture/emulator/baseline hashes and retained native screen captures.
The baseline DMK hash remains unchanged. `model4-corrected.log` records normal
completion of the emulator and capture runner.

### Independently observed console input

After PR #354, the unchanged V002b candidate was tested with the pinned,
unmodified CONSTEST under cpmsim. `run_validation_console_input.py` supplies
confirmation only after checking literal returned bytes and independently
rendering the input echo with pyte. It does not accept the suite's printed
EXPECTED text as its oracle.

All 13 selected required cases pass: 0083/0084 (Function 6 returned character
and no echo), 0093/0094 (Function 1 returned character and echo), and
0106/0108/0109/0111/0112/0113/0114/0115/0122 (Function 10 returned buffers,
CR/LF termination, one-character capacity, echo, Backspace and prompt-column
preservation). Every case returns to the CCP, followed by a normal BYE halt.

Evidence: `console-input/constest-input-305q8ijr/` contains the full transcript
and result manifest with baseline, program and simulator hashes, keystrokes,
expected returned bytes and the observer module location. The original image
hash is unchanged. The earlier nine-case run is retained in
`console-input/constest-input-pwi0agwq/`; its counts overlap, not add to, the
13-case result. These checks do not establish timing, other editing controls,
control-key recovery or native Model 4 input behavior. No OS defect was found
in this subset.

### Console control editing and terminal-outcome recovery

The expanded external observer now covers 19 cases on the same unchanged
candidate. Added cases 0116/0118/0119/0120/0121 check literal DEL input,
Ctrl-E physical continuation, Ctrl-R retained-line redisplay, Ctrl-U line
deletion and Ctrl-X visual erasure, checking both returned buffers and rendered
screen contents before confirmation. Case 0117 has a separate terminal-outcome
oracle: initial Ctrl-C reaches the CCP without the Function 10 return diagnostic
or confirmation prompt, then VER succeeds and BYE halts normally. It is recorded
as an external recovery pass, not a nonexistent suite PASS row.

All 19 pass in `console-controls/constest-input-e2o8j_mz/`. Its result records
pyte's version as well as its module location. The initial 18-case expansion is
retained in `console-controls/constest-input-exo0ejyy/`. These totals supersede,
rather than add to, the earlier 13-case input coverage. No OS changes were
required. Native Model 4 input, blocking/queue timing, printer echo and further
console/device cases remain outside this evidence.

### Console readiness and blocking input

The final expanded run, `console-readiness/constest-input-nntpnd90/`, records
22 successful cases: 21 required (including externally observed 0117 recovery)
and one DRI-CONSOLE profile case, 0104. Added required case 0085 reports A=00
with an emptied queue. Case 0092 produces no output during an externally
monitored 0.5-second interval, then echoes the supplied B and returns A=42.
Profile case 0104 consumes the single supplied K after Function 11 detects it,
echoes it once and returns A=4B. No extra input is supplied to release it.

The session helper now supports a silence expectation which monitors the PTY
throughout the interval and rejects pending or newly arriving output. Two
provider tests verify a quiet interval and rejection of premature output.
This establishes the bounded observation, not arbitrary-duration timing.

An initial runner expected 0104's result to have required classification R;
the pinned suite correctly printed profile classification X and the runner
timed out at the CCP. That transcript is retained under `console-readiness/`.
The runner was corrected to preserve X, and the complete rerun passed. No OS
change was made. Totals overlap earlier console-input runs; do not add them.

### Native Model 4 input observations

`run_validation_model4_input.py` boots a separate private copy of the unchanged
V002b Model 4 System Disk for each case and supplies actual keyboard-matrix
events. The normal startup monitor configuration is retained. The runner does
not insert guest-buffer bytes and does not answer the suite's Y/N confirmation.
It captures the screen at that prompt, then independently checks the literal
returned buffer and the final visible input, including preservation of the
prompt. These are external observations, not suite PASS rows.

All three selected cases pass:

- 0106: AB followed by Enter displays AB and returns count 02/data [AB].
- 0115: AB, Backspace, C, Enter displays AC and returns count 02/data [AC].
- 0121: AB, Ctrl-X, CD, Enter erases AB, preserves the prompt, displays CD and
  returns count 02/data [CD].

Evidence: `model4-input/model4-input-18qrinln/` contains per-case private images,
native screen-memory captures, decoded screens and a result manifest with
baseline/program/emulator hashes and keystrokes. The original baseline hash is
unchanged. Each emulator exited after its capture. No OS defect was found.
This small native subset does not establish other editing controls, timing,
other monitor configurations or return-to-CCP behavior for these cards.

### Character echo and flow-control continuation

`console-echo/constest-input-peeneiha/` records 29 successful cases on the
unchanged cpmsim candidate: 28 required (including the external 0117 recovery
observation) and one DRI-CONSOLE profile case. Added cases 0095..0100 verify
literal CR/LF echo, Backspace followed by X overwriting C, TAB expanded to
seven spaces after column-one A, suppressed Ctrl-A echo with A=01, and shared
Function 9/Function 1 column state. Expected echo bytes are independent literals
checked before confirmation. The TAB checks assert spaces rather than merely
accepting a host terminal's interpretation of a TAB byte.

Case 0101 receives Ctrl-S, remains silent for 0.25 seconds, receives Ctrl-Q,
remains silent for another 0.25 seconds, then receives X and echoes/returns
exactly X (A=58). This is bounded live pause/resume evidence, not a general
performance guarantee. The earlier 28-case expansion is retained in
`console-echo/constest-input-c6q1o113/`; counts overlap. No OS change was needed.

### Native control editing continuation

The `--group controls` extension to the native input runner retains separate
private disks and captures for Ctrl-E (0118), Ctrl-R (0119) and Ctrl-U (0120).
All three returned-buffer and visible-line checks pass in
`model4-controls/model4-input-hu9q5yhk/`: Ctrl-E continues physically while
retaining ABCD; Ctrl-R redisplays the retained AB before appending CD; Ctrl-U
starts a fresh line and returns only CD. The checks require the expected
physical newline, not merely the concatenated characters. No suite confirmation
is supplied for these three cards. Native Ctrl-C recovery is recorded separately
when its terminal-outcome check completes.

Native 0117 also reaches the CCP and executes resident VER /VER, leaving its
version line and a final A0> prompt. The caller-return diagnostic and suite
confirmation are absent. The first runner incorrectly also required the typed
`A0>VER /VER` command to remain visible, so its original `result.json` reports
that case FAIL. The retained screen contains the executed version output but
not the command echo. This is an observer error, not an OS failure.

The corrected `recovery_checks` requires the resident VER identity, final CCP
prompt and absence of the caller-return/confirmation diagnostics; command echo
is not a recovery contract. Four observer checks reject a startup banner,
caller-return diagnostic and missing final prompt, while accepting a successful
version result without command echo. Applying that corrected oracle to the
unchanged native capture passes all four conditions. `recovery-reviewed.json`
records that review and capture hashes separately; the original failure report
is preserved. This was a review of retained evidence, not a new emulator run.
The native batch therefore provides three editing observations plus one
terminal-outcome recovery observation. No OS change was needed.

### Counted-input maximum-byte continuation

The expanded cpmsim run in `console-capacity/constest-input-3ap51m4z/` passes
30 cases: 29 required, including the external 0117 recovery observation, plus
one DRI-CONSOLE profile case. Added 0107 runs two Function 10 calls: maximum 1
returns Z without Enter; maximum FFh accepts Q and returns on Enter. Both
returned buffers and visible echoes are independently checked before the single
case confirmation. This tests the maximum-byte settings, not filling all 255
positions (the suite recipe enters only Q in its second call).

The initial observer in `constest-input-gynprvlu/` incorrectly assumed only one
CR before the reporter's OBSERVED line. The corrected observer separates the
report at its literal CR/LF marker, checks the count/data and compares rendered
input echo, matching the existing buffered-input oracle. The returned values
were already correct; no OS change was made. Earlier run totals overlap.

### Native Model 4 entry-contract group

The returning runner's new `--group entry` executes the pinned, unmodified
ENTRYTST /GROUP:REQUIRED on the unchanged V002b Model 4 System Disk, with its
normal startup monitor configuration. The final native screen reports
25 pass, 0 fail, 0 error, 0 observations. Required automatic checks include
entry/page-zero and default DMA behavior, BDOS/BIOS structure access, IOBYTE
coherence and Function 40 scratch-file writes. Manual cards remain not run;
they are not promoted by the aggregate summary.

Evidence: `model4-entry/model4-returning-thc9ovky/` retains private A/B disks,
program/baseline/emulator hashes, native screen-memory captures and decoded
screens. The final screen retains the aggregate summary and trailing rows;
it is not a complete scrolling per-item transcript. The original DMK hash
remains unchanged and the emulator exited normally.

An independent post-run filesystem audit extracts all 29 shipped files from
the original and exercised disk and compares their complete CP/M record bytes.
All 29 are unchanged; ENT40.$$$ is absent after the Function 40 cleanup.
`file-audit/result.json` records per-file hashes, with extracted before/after
raw media, files and a final directory listing retained beside it. The runner
now performs that audit automatically for entry-group runs. The first run's
audit was applied to its retained disk after the emulator completed. No OS
change was required.

### Native Model 4 directory conformance

`run_validation_model4_directory.py` prepares separate private B/C data media
with OFF=0, 400 allocation blocks and 128 directory entries. It installs the
pinned DIRTEST and canonical suite fixtures on B, BTUSR.DAT in users 0 and 1,
read-only BTRO.DAT, and the canonical BTBFILE.DAT on C. The normal V002b System
Disk and startup monitor configuration remain on A. Program, fixture, emulator
and baseline hashes are recorded with before/after private-disk hashes.

The completed run in `model4-directory/dirtest-irm5e5c6/` reports:

```text
Summary: 49 pass, 0 fail, 0 error, 0 observations
```

Its final native screen includes row 0566 and the summary; automatic exit after
that capture is intentional. It is not a crash. The capture retains trailing
rows rather than a complete scrolling transcript. Coverage includes searches,
extents, cross-drive behavior, scoped delete/rename, attributes and user areas.
Manual/protected-error procedures excluded by /SAFE remain untested.

Independent post-run checks pass for both exercised data filesystems, with
`fsck.cpm -T raw -n` checking extent fields/connectivity. All 29 shipped files
on A remain byte-identical to their original CP/M records. `data-audit.json`,
`file-audit/`, raw extractions, filesystem logs and native captures are retained.
No OS defect was found in this group. Native BDOSTEST remains next; the runner
supports its separately prepared BDSA/BDSB fixture but it has not yet been run.

Instrument corrections are retained separately:

- `dirtest-fd1ondpo/`: a short drive-change delay lost part of the command.
- `dirtest-lc5ju1a3/`: the emulator's B-prompt text wait failed to advance despite
  a visible idle prompt. Both were stopped without a suite verdict; their
  private media and `instrument.json` are retained.
- The successful rerun uses a conservative drive-change delay and captures the
  ready B prompt before supplying the command. The native runner allows a
  longer overall timeout for subsequent filesystem groups.
- The first post-run C filesystem invocation omitted explicit raw image type;
  cpmtools autodetection reported a misleading open error despite the file
  existing. With `-T raw`, both data disks pass. The original error is retained
  as `c-filesystem-autodetect.txt`; no image or OS code was changed to obtain
  the passing checks. Audits were rerun on the same retained disks, and the
  result manifest now contains both successful audits. Future results remain
  pending/error until audits complete, separately from the suite verdict.

### Native Model 4 BDOS required group

Qualification correction (V006): the initial fixtures below were later found
to have misplaced data. Preserve the printed result as historical output;
acceptance requires the corrected-fixture rerun documented under V006.

The prepared native BDOSTEST /GROUP:REQUIRED run passes 56 cases, with zero
failures/errors, on the unchanged V002b Model 4 candidate. Three manual required
procedures remain not run. Evidence: `model4-bdos/bdostest-ksglji1p/`, including
fixture/program/baseline/emulator hashes, the readiness and final native screen
captures, and initial/final private disk hashes. Both data filesystems pass the
explicit-raw extent/connectivity checks. All 29 shipped System Disk files are
unchanged in the independent record-byte audit. No native BDOS defect was found
in this selected group.

### V003 — transient-entry page-zero drive byte

Fresh pinned CCPTEST /GROUP:REQUIRED on V002b reports 11 passes, one failure
(0007), and 29 not-run cards in `ccp-returning/ccptest-myd99ji8/`. An independent
probe confirms page-zero 0004h=AFh while BDOS reports drive A/user 0; source review
finds no CCP initialization of that byte. The probe's source, assembly and
transcript are retained in `ccp-returning/pagezero-itofokb_/`.

DRI's [CP/M 2.2 CCP source](https://github.com/brouhaha/cpm22/blob/master/ccp.asm)
(`saveuser`, `setdiska`, `readcom`) distinguishes packed prompt-time user/drive
state from the drive-only byte used after command acquisition. The fix publishes
the caller's default drive from Function 25 immediately after temporary lookup
DU restoration and before protected loader handoff. BDOS still owns live drive
and the full 0..31 user state; 0004h is not made authoritative for warm start.
The command-entry contract is recorded in FULL-TPA-COM-LOADING.md.

The CCP grows 5442 to 5450 bytes; allocation stays 5632, relocations stay 488,
and the module is 6474 bytes within the 6656-byte carrier. No BIOS/BDOS layout or
unloaded TPA change is needed. Focused CCP parsing/navigation/CPX tests pass.
The loader EOF/error/fallback providers now also verify the published caller
drive, starting with a poisoned 0004h; all eight combinations pass.

The diagnostic carrier candidate passes 12 automatic CCP cases and 25 entry
cases. Its independent A0/A3/B3 probe loads A0:PZPROBE while correctly publishing
the caller's drive and retaining its user. The first diagnostic probe mistakenly
used drive-only A:PZPROBE while in user 3, where the file was absent; that failed
instrument transcript is retained separately in `v003-candidate/`, not called
an OS regression. The corrected DU probe is in `v003-candidate-du/`.

An isolated production cpmsim System Disk was then rebuilt and qualified from
current sources, not patched media:
`/private/tmp/bettercpm-validation-v003/release-575684f2c167-7ea54835900f/z80pack/`.
Its source-input hashes identify the local V003 change atop 575684f; this is not
a claim of a clean merged release revision. Boot, manifest, file integrity,
CONFIG binding and filesystem qualification pass (`v003-distribution.log`).
On this rebuilt image, CCPTEST reports 12 pass/29 not run in
`ccp-production/ccptest-iny0q020/`, and ENTRYTST reports 25 pass/13 not run in
`ccp-production/entrytst-t78fg4ut/`. No failures/errors. The independent caller-DU
probe also passes on an unchanged production carrier in
`ccp-returning/v003-production-probe/`. Original reference hashes are unchanged.

V003 is corrected and live-qualified on cpmsim. The native Model 4 post-fix run,
guarded-ROM regression and final rebuilt-image acceptance remain pending; earlier
native results explicitly refer to V002b. Conformance validation remains partial.

### V003 guarded-ROM regression

Fresh ROM media were rebuilt from the pushed V003 CCP source in
`/private/tmp/bettercpm-validation-v003-rom-media/`. The locked-ROM qualification
passes execute-in-place, CPU writes, DMA writes, attempted guest unlock/boundary
changes, reset protection and unchanged ordinary mode. The integrated boot
campaign also passes CPX/RSX load/list/reconstruction/unload and workspace checks.
ROM external inventories remain 44 reloader references, 72 CCP references and
812 address words across 18 RSX-overlay files; no accepted boundary was relaxed.

Measured stack high-water values are unchanged: system 24/32 bytes (8 reserve),
BDOS 28/40 (12 reserve), loader 20/64 (44 reserve). The workspace remains 1024
bytes with its three qualified exclusive lifetimes and 907-byte CONFIG overlay.
Evidence: `ccp-returning/v003-rom-build.log`, `v003-rom-xip.log` and the copied
hash-bound qualification reports in `v003-rom-reports/`. These results close
V003's guarded-ROM regression pending item; native post-fix evidence follows.

The independent production-image probe was also repeated in user 31 on A and B,
loading explicitly from A0. It publishes drive 00/01 at 0004h while Function 32
still returns user 1Fh, then returns to the original DU. Evidence:
`ccp-returning/v003-production-user31/`. The drive-byte fix therefore does not
truncate BetterCP/M's extended user state in this live qualification.

### V003 native build publication gate

The isolated Model 4 production build passed filesystem/file integrity, CONFIG
binding and boot/CPX/VER/ED identity checks. Publication was then correctly
blocked because `tools/run_validation_model4.py` changed while the build ran.
The snapshot input manifest was compared with current inputs: this validation
runner is the only changed input; every runtime source, metadata and third-party
input is unchanged. `v003-native-source-diff.json` records that comparison.

The qualified private candidate is retained at
`/private/tmp/bettercpm-validation-v003-native-work/candidate-bettercpm-dist-kzh01wwh/trs80gp/`,
with report/image/source hashes bound to 2fc1b8b. It is used only for private
post-fix conformance, not published as an immutable release. The publication
gate was not bypassed. The build log is `v003-native-distribution.log`.


### V003 native post-fix conformance

The hash-verified, unpublished Model 4 candidate passes both fresh pinned groups:
CCPTEST /GROUP:REQUIRED reports 12 pass, zero fail/error; ENTRYTST
/GROUP:REQUIRED reports 25 pass, zero fail/error. Manual cards remain not run.
Evidence: `v003-native-ccp/model4-returning-9djlv_40/`, with private media,
program/baseline/emulator hashes, native captures and decoded final screens.
As elsewhere, the screenshots retain the summaries and trailing rows rather
than every scrolled item. All 29 shipped files remain unchanged in the
independent post-run extraction audit, and ENT40.$$$ is absent. Reference image
hashes are unchanged and the emulator exited normally.

The native runner now exposes this two-group `--group ccp` campaign. It retains
its conservative reconstruction delay between commands, but omits the unused
final delay after the last retained result; it then exits explicitly. No
conformance predicate or stack/memory limit was relaxed.

V003's targeted post-fix native and guarded-ROM regressions now pass. The
separate publication gate remains enforced; final acceptance must still rebuild
from an agreed stable revision. Fresh conformance is still partial: manual,
terminal, fault, device and remaining platform cases require their explicit
procedures and cannot be inferred from these aggregate counts.


### Repeated transient termination and reconstruction

`run_validation_ccp_returns.py` executes the pinned CCPTEST's selected 0025
(JMP 0000h) and 0028 (entry RET) procedures, plus an independent fixture making
a real BDOS Function 0 call. Every return is followed by a separately assembled
public-state witness which checks drive, user and the page-zero TPA ceiling.
Three cycles of all routes in A0, B3 and B31 pass: 27 external observations.
The final CPX list contains RCP, the RSX list is empty, and the cold-start banner
appears exactly once across the entire session. These are external procedure
verdicts, not fabricated suite PASS rows. Reference image hashes are unchanged.

Evidence: `ccp-returns/ccp-returns-e4011fqm/` contains the final normal-mode run,
fixture hashes, full transcript and result manifest. The earlier equivalent
27-case run is retained in `ccp-returns/ccp-returns-qw5suc4l/`; counts overlap.
The image is the production-built V003 cpmsim candidate.

The full-TPA mode uses 424-record (54,272-byte) patterned programs on private B0
media. It independently verifies every payload byte beyond the first two code
records before exercising RET, JMP 0000h or Function 0. A preceding PAINT.COM
fills that region with 5Ah, returns through protected WBOOT, and lets the new
load distinguish stale memory from genuinely loaded A5h records. The program
code stays below the painted region. Only private copies are exercised.

With caller A0, all three routes pass for three cycles after overwriting CCP
code. A 425-record program with the same executable prefix is independently
extracted to verify installed bytes, then rejected without executing its marker
or reporting an unknown file/disk error; the caller's state and working prompt
return. This gives 10 external user-zero observations in
`ccp-full-tpa/ccp-returns-ngxj73j9/`. It does not close cross-user coverage.

### V004 — corrected: cpmsim and manual-native qualification plus file audit

The full-TPA run from caller B3, explicitly loading B0:ERET, executes a truncated
program. After the independent pre-paint, the first wrong payload byte is at
4100h and remains 5Ah: the next record after the first 16 KiB of the COM was not
loaded. Same-user A0 loads pass. The failing probe returns through WBOOT to B3,
but its failure marker prevents a pass verdict. Source review finds
CCP_LURST restores the caller's user before CL_NEXT finishes sequential reads;
the next extent lookup therefore occurs in the caller's user rather than the
file's lookup user. Normal EOF is then accepted prematurely.

Reproduction evidence on V003:
`ccp-full-tpa/ccp-returns-_1ehbm51/` (with pre-paint and diagnostic first address).
Earlier unpainted runs are retained in `ccp-returns-0c18ozxw/` and
`ccp-returns-pt1b05ri/`; stale A5h data from prior successful loads hid the first
missing region, so their first differing address was later in memory.
A repeat on the older V002b candidate gives the same 4100h/5Ah witness in
`ccp-full-tpa-v002/ccp-returns-_m9s4mvt/`. V004 therefore predates V003's page-zero
fix. Failure manifests retain completed observations, fixture/baseline hashes
and the failure text. No full cross-user or oversized-all-context pass is claimed.

At the end of the preceding tranche, V004 was an unresolved validation blocker.
The correction needed to retain the
lookup user for every extent read while still restoring the caller before
program entry, on failure and for lifecycle callbacks. Load-abort context and
the fixed resident-memory/stack budgets must also be checked; moving restoration
without qualifying those paths would have been insufficient. No production change for
V004 had been made at that point. The qualification below supersedes that status;
fresh conformance remains incomplete.

#### V004 correction and evidence

The CCP now retains the actual opened-file user through all protected extent
reads, while CPX shutdown still sees the caller. Successful execution and
returning errors restore the original user. An armed page-zero lookup marker
also lets stable WBOOT recover the caller before reconstruction when BIOS
Ctrl-C bypasses normal reader return. Successful EOF disarms it; a program's
own later user selection is not reverted.

This correction has passed:

- `v004-full-tpa/ccp-returns-kdl0s3w9/`: 27 repeated full-TPA cases with lookup
  user 0 from callers A0/B3/B31, plus oversize rejection (28 external checks).
- `v004-user7-full-tpa/ccp-returns-kh5i7usr/`: the same 28 checks with lookup
  user 7. Independent prepaint prevents missing records being hidden by old data.
- `v004-loader-abort-final/loader-abort-pi7xab3a/`: one-shot final BIOS
  READ fault while the protected destination is at least C000h, after CCP-prefix
  overwrite; Ctrl-C returns from B7 lookup to B31 with RCP reconstructed and
  no partial program executed. This uses empty RSX reconstruction slots only
  on the isolated no-RSX fixture. It does not qualify controller retries.
- `v004-fallback-userchange/`: full-size unqualified A0 fallback from B31;
  separate program changes user to 5 and returns to B5, proving ordinary
  WBOOT does not revert a program-selected user.
- `v004-ccp/ccptest-25abh_v0/`: fresh pinned CCPTEST required group, 12 pass,
  29 not-run; no fail/error rows.
- Assembled loader result providers (EOF 1, logical failure 2, final error FF,
  and oversize), with ordinary/fallback lookup, assert read-user selection,
  caller-user CPX shutdown, arguments, page-zero drive and execution boundaries.
  Cold/warm history tests cover armed recovery for callers 0/3/31 and disarmed
  ordinary user preservation. Focused CCP tests pass.
- Native ZSM4/LINK gateway assembly is byte-identical (248 bytes).

The cpmsim candidate is
`/private/tmp/bettercpm-validation-v004b/release-31eb7b0f96a8-7fbdbe2c5bb5/z80pack`.
Its report records the full input hashes (dirty candidate atop 31eb7b0).
Full ROM media is `/private/tmp/bettercpm-validation-v004-rom-media`; guarded
CPU/DMA protection, boot, transient returns and CPX/RSX lifecycle pass. The
initial XIP attempt used system-tracks-only output without `rom-config.json`;
it failed for that missing artifact, then passed after the complete ROM build.
No runtime failure is inferred from the incomplete test setup.

Memory remains: 53K unloaded TPA, gateway 248 bytes, BDOS 3,454 bytes, extension
425 bytes and Model 4 BIOS 757 bytes. CCP is now 5,475 / 5,632 bytes, allocation
unchanged; module 6,499 / 6,656 bytes, 488 relocations. Guarded ROM stack use:
system 24/32, BDOS 28/40, loader 18/64. The address inventory has 799 code
operands (475 ROM, 324 RAM), all accounted, plus 105 CONFIG overlay operands.

`test_system.py` still stops at its old console port fixture (`IN without a
controlled port fixture`); repeating it against the unchanged V003 resident
reproduces the same failure. It is not counted as a pass or a new V004 defect.
Fresh conformance and the overall validation campaign remain incomplete.

The fresh V004 ENTRYTST required run also passes: 25 pass, 13 not-run in
`v004-entry/entrytst-fk5ggchb/`. Function-182 empty/active gateway tests,
subsystem-version checks and BDOS-178 portable cursor checks (ADM3A/VT52 through
both backends) pass after sharing the extension epilogue/cursor setup.

Native full-TPA qualification is **not complete**. The production Model 4
candidate boot/filesystem qualification passed, but source-identity publication
correctly rejected runner/build-helper changes during the build. Its retained
candidate is
`/private/tmp/bettercpm-validation-v004-native-work/candidate-bettercpm-dist-kh6savgh/trs80gp`.
`v004-native-source-diff.json` confirms no runtime-source difference from the
current fix; the candidate is not represented as a published release.

Preliminary native full-TPA captures were stopped after finding excessive
fixed delays and an unmet unloaded-profile prerequisite. The final isolated
fixture replaces only STARTUP.SUB with a banner-only script and explicitly
waits for D501h before proceeding. Its extracted startup text is independently
verified. Nevertheless no automated capture checkpoint was reached after more
than six minutes, and repeated live UI inspection failed with ScreenCaptureKit
-3811. The owned process was stopped. Cause of the missing checkpoint remains
unestablished; neither an OS failure nor an emulator cause is inferred.
`v004-native-isolated/model4-full-tpa-lnywz2m8/incomplete.json` retains this
status, arguments and private images. No native full-TPA pass is claimed.
The new runner requires route-specific success markers, post-command public
state, oversize rejection and independent shipped-file audits (excluding the
predeclared STARTUP.SUB fixture change). This native check must be completed
before V004 is fully closed in the validation campaign.

#### Manual Model 4 evidence supplied 2026-10-16, 21:25–21:32

The user supplied two screenshots from the prepared manual fixture. The first
shows `STATE D=00 U=00 TOP=D501` and A0 prompt. The second shows navigation to
B31, `A0:PAINT`, `FULL-TPA RET ENTERED`, then
`STATE D=01 U=1F TOP=D501` and B31 prompt. In context of the requested manual
procedure this records a passing full-TPA RET check with preserved caller DU
and unloaded ceiling. The ERET and STATE invocation lines themselves are not
visible in the second screenshot; the success marker and resulting state are.
Copies and screenshot hashes are retained in `v004-manual-model4/` with an
observation manifest. This supersedes the absence of native RET evidence,
not the incomplete automated run. JUMP, Function 0, oversize rejection and the
independent post-run file audit are still pending; no whole-native-run pass
is claimed.

The 21:38 user screenshot adds `FULL-TPA JUMP ENTERED` followed by a subsequent
B31 command prompt, and `FULL-TPA FUNCTION0 ENTERED` followed by
`STATE D=01 U=1F TOP=D501` and B31 prompt. These record manual JUMP and
Function-0 behavioral passes; the per-JUMP state output itself is not visible.
Oversize rejection and independent post-run file audit remain pending.

### V005 — corrected: interactive command termination overwrites the command line

The same manual screenshots show immediate transient output replacing its
invocation line. Source inspection confirms CCP_EDFIN redraws the final command
and emits CR (13) without LF (10) before dispatch. This explains why programs
that begin with printable text overwrite the command, while programs that
supply their own leading newline appear normal. The submitted-command echo
already emits CR/LF. This is a CCP presentation issue; no emulator cause is
required to explain it. The correction below is separate from V004's loader
qualification.

#### Manual oversize result, 21:40

The user screenshot shows B31 invoking `A7:OVERRET`, then
`STATE D=01 U=1F TOP=D501` without an intervening FULL-TPA success marker.
The subsequent state witness establishes rejection returned control without
executing the oversized program and preserved caller drive/user and TPA.
The final prompt is outside the screenshot crop. Evidence and hash are retained
as `v004-manual-model4/oversize.png`. All requested manual behavioral checks
(initial ceiling, RET, JUMP, Function 0, oversized-file rejection) now have
user-supplied evidence. The automated capture run remains incomplete and the
independent native post-run file audit remains pending; neither is inferred
from these manual screenshots. V005's command-line newline defect remains open.

#### V005 correction and verification

Interactive completion now emits LF immediately after its final CR. The
completed command therefore remains visible when a program starts printing
without its own leading newline. Empty commands also complete with CR/LF.
BDOS Function 10, submitted-command echo and command contents are unchanged.
The CCP gains seven bytes: 5,482 / 5,632; module 6,506 / 6,656; 488 relocations.
No resident allocation or unloaded 53K TPA change occurs.

`tools/test_ccp_command_newline.py` first failed against the old assembled
CCP with `b'\rA0> \r'`. It now captures exact final CR/LF for empty, bare and
argument-bearing commands, including an interior logical cursor, and verifies
that immediate newline-free output follows the LF. Focused CCP tests and all
eight protected loader-result-provider combinations also pass.

A clean isolated cpmsim distribution build passes at
`/private/tmp/bettercpm-validation-v005/release-da2a8d821492-3c2103f18c0d/z80pack`.
`v005-command-newline/` retains the live transcript, fixture source/binary,
runner and hashes: both `PROBE` and `PROBE ONE.TXT` are followed by literal
CR/LF before `NEWLINE PROBE`, whose program deliberately emits no leading
newline. Empty-line entry also returns to a prompt. These are live cpmsim
observations, not a native Model 4 visual pass.

The V005 cpmsim candidate also passes a fresh one-cycle full-TPA return run:
RET, JP 0 and Function 0 from A0/B3/B31 plus oversize rejection (10 external
checks), in `v005-full-tpa/ccp-returns-697tmih9/`. This verifies the presentation
change did not regress the newly corrected cross-user loader paths.

## Post-loader validation continuation

### Native manual-test disk audit — PASS

After the user's RET, JUMP, Function-0 and oversize observations, a stable host
snapshot was taken of `/private/tmp/BetterCPM-manual-loader/a.dmk`; hashes before
and after copying matched. Snapshot SHA-256:
`1deac72546d51801f6220b356cab8d5914a50785757b755de0fd282750b1cd6c`.
No emulator was launched or modified for this audit.

Independent extraction compares all 28 shipped files other than the declared
STARTUP.SUB override against the original candidate: every file is unchanged.
The banner-only STARTUP.SUB and all six fixtures (STATE, PAINT, ERET, EJUMP,
EFN0, OVERRET) also match their expected contents at record granularity in the
correct users. The reserved system area is byte-identical, and read-only
`fsck.cpm -T raw` passes extent-field/connectivity checks. Evidence, extraction
outputs, hashes, audit runner and filesystem report are in
`v004-manual-model4/post-run-audit/`.

This closes V004's outstanding independent native disk audit. Together with
the manual screenshots and cpmsim fault/boundary results, the requested loader
checks pass. The earlier automatic native capture remains an incomplete
instrument run, not a retroactive pass. Final merged-revision acceptance and
other campaign stages still remain.

### ECOTEST external resident-command procedures — cpmsim PASS

The pinned, unmodified `suite/src/ECOTEST.ASM` procedures for 0569, 0575,
0577 and 0579 were exercised at the real CCP on private V005 disks.
`tools/run_validation_resident_ecology.py` records the procedure-source,
runner, simulator and fixture hashes. Final evidence:
`resident-ecology/resident-ecology-qozlon94/`.

- **0569 semantic set:** DIR lists the actual padded KEEP.TXT entry; REN changes
  KEEP.TXT to NEW.TXT; TYPE emits its known content; ERA removes NEW.TXT;
  USER 3 is independently observed through public state, then restored. SAVE
  is verified as described below. The caller returns to A0 and test files
  are removed.
- **0575 SAVE mapping:** resident POKE initializes every byte 0100h..01FFh to
  00h..FFh, with no transient execution or warm reconstruction before
  `SAVE 1 ECOSAVE.COM`. Independent host extraction proves the file is exactly
  256 bytes with that pattern. It is then erased through resident ERA.
- **0577 TYPE byte stream:** an exact 128-byte record contains graphics, CR/LF
  and BEL (07h), without padding or an embedded text EOF. The captured output
  contains the complete exact record. This tests control-byte transport;
  terminal presentation is not substituted for byte evidence.
- **0579 ordinary recovery:** DIR, ERA, REN and TYPE use missing filenames;
  SAVE uses an invalid page count. Each emits the expected diagnostic, returns
  a usable B0 prompt, preserves D=01/U=00/TOP=D501, and permits a subsequent
  resident TYPE of the known file.

Both sessions terminate normally. Independent checks find the B: scratch
filesystem empty and clean, the A0 STATE fixture removed, and all 30 shipped
System Disk files byte-identical to the baseline. The original baseline hash
is unchanged. Five bad-command subcases and the other three observations are
not eight new suite rows: these are external evidence for four manual cards.
The suite's aggregate output is not rewritten. Native equivalents and the
remaining manual/device/terminal-outcome cases are still outstanding.

### Read-only terminal procedures — eight fresh cpmsim passes

`tools/run_validation_readonly_outcomes.py` exercises the pinned, byte-verified
RANDTEST and DISKTEST binaries against independent private V005 image copies.
Final evidence: `readonly-terminal/readonly-outcomes-_rydhwb7/`, including the
executed runner, transcripts, prepared whole-disk copies, per-case results,
filesystem checks and extracted System Disk files.

| Items | Attempt | Observed terminal outcome |
| --- | --- | --- |
| 0368, 0369 | Sequential/random write to file-read-only BTRO.DAT | File R/O, then usable B0 prompt |
| 0379 | Make on software-protected D: | Disk R/O, then usable D0 prompt |
| 0380, 0381 | Sequential/random write on protected D: | Disk R/O, then usable D0 prompt |
| 0382 | Delete on protected D: | Disk R/O, then usable D0 prompt |
| 0383 | Rename on protected D: | Disk R/O, then usable D0 prompt |
| 0384 | Mutation after protection | Disk R/O, then usable D0 prompt |

All eight protected disks are byte-identical before and after their attempts,
including the complete directory and data area. Independent checks verify the
BTRO read-only T1 bit remains set and every protected filesystem is clean.
Every case then executes the public-state witness (correct selected drive,
user zero, TOP=D501), resident VER and BYE. All 30 shipped A0 files are extracted
and compared independently after each case; none changes. The immutable
baseline hash is unchanged. D: was prepared with the canonical 128-record
BTFULL, release record and allocation filler; its selection occurs through the
suite's real operator gate, not a patched test.

These are external terminal outcomes, not in-process PASS rows. The returning
aggregate reports still list their terminal cards as not-run; those reports
are not edited. The suite binaries/sources and frozen protection oracles are
unchanged. Native equivalents remain outstanding.

Profile distinction: the pinned terminal-outcome workflow describes DRI's key
acknowledgement. Existing BetterCP/M specification 74 and the earlier protected-
disk qualification instead use the diagnostic followed by immediate WBOOT.
The provider explicitly tests that established BetterCP/M profile without
injecting a stray acknowledgement into the resumed CCP. These results do not
claim DRI acknowledgement/presentation equivalence.

Instrument note: an initial compact eight-case run passed the protection
checks (`readonly-outcomes-ewuyztt1/`). A strengthened report-mode attempt
(`readonly-outcomes-0ep96y8x/`) then stopped on a harness expectation for a
`LEDGER` preamble. Source review confirms pinned RANDTEST's INDHEAD emits only
the report header before its terminal call; the CASE/LEDGER block is deferred
until result reporting, which WBOOT prevents. The revised provider matches
`REQUESTED_SCOPE /0368` or `/0369` from the executable's canonicalized report
header, or DISKTEST's explicit numbered request, before accepting the expected
diagnostic and external recovery. The intermediate failed assertion is not an
OS failure or a completed group. A subsequent eight-case run passed
(`readonly-outcomes-37kfbymh/`); the final run above additionally audits all
shipped files after each case and is the accepted evidence.


## V006 native FILETEST — host fixture mapping corrected

PR 365 and PR 366 are merged. The cpmsim read-only terminal outcomes from
PR 366 still do not qualify native equivalents.

A fresh isolated production Model 4 image containing the cross-user loader and
interactive CR/LF fixes passed build, boot and distribution integrity gates:
`/private/tmp/bettercpm-validation-v006-native/release-0f4b28052ee5-de016a44feeb/trs80gp`.
No OS source or binary changed during this investigation.

### Initial failure and independent diagnosis

`v006-native-file/filetest-x5a4fuzj/` returned 50 pass, 18 fail, zero error,
zero observations and two not-run. Failed items were 0167, 0172, 0173, 0174,
0175, 0179, 0219, 0220, 0221, 0222, 0223, 0224, 0226, 0228, 0229, 0230,
0231 and 0243. This is retained as output from invalid fixture media, not an
accepted OS failure result or a completed qualification.

The unchanged `/0172:REPORT` reproduced Open=03, Read=00 and a failed record
comparison. An instruction trace showed failure on the first byte. A separate
run stopped at the comparison entry (PC=2CCA) and saved physical RAM before
WBOOT could overwrite the transient. The expected marker at B383 was intact
(`ONE`), while the entire guarded DMA record at B644 contained E5. Its FCB
correctly named BTONE.DAT and declared allocation block 46; the raw bytes at
46*2048=94208 were indeed E5. Host extraction nevertheless returned the
canonical `ONE-000` record, actually stored at raw offset 186368.

Evidence and diagnostic scope are retained in
`v006-native-file-investigation/`, including the unchanged isolated-case
report, instruction trace, paused RAM snapshot, shipped-file audit and
`finding.json`. The RAM snapshot is a diagnostic checkpoint, not a suite pass.
All 29 shipped A: files remained unchanged during the isolated returning case.

A minimal host-only reproduction created separate 128-byte A/B/C/D files.
With `-T raw`, the second file declared block 3 (offset 6144), but its bytes
were written at offset 11264. Subsequent host extraction used the same wrong
mapping, concealing the error. With `-T raw,pcw800`, all four files occupied
their declared physical blocks. The existing cpmtools/LibDsk versions are
recorded in the campaign environment; the behavior is consistent with the
[upstream geometry-probe robustness fix](https://sources.debian.org/patches/cpmtools/2.23-7/cpmtools-libdsk-probe-robustness.patch/),
which describes retained incorrect sidedness after a failed geometry probe.
Pinning the raw driver alone does not pin its geometry.

### Corrected native qualification

The native runner now explicitly selects `raw,pcw800` for these 80-cylinder,
two-sided, 10x512-byte-sector raw images. This changes the host fixture/audit
path, not guest disk geometry or any BIOS/BDOS code. Before launching, an
independent decoder walks raw directory entries and 16-bit allocation maps,
checks every fixture's contents against its source, checks dense extent
boundaries, checks the RO fixture attribute, rejects shared/out-of-range blocks, and
verifies all 128 D: entries and 400 blocks (including its directory) are used.
It rejects the original misplaced BTONE fixture. Host-tool round trips are
not used as the sole proof of placement.

`v006-native-file-corrected/filetest-36j_o_hf/` reports:

```text
Summary: 68 pass, 0 fail, 0 error, 0 observations, 2 not-run
```

This uses the unchanged pinned suite binary and the same V006 OS image.
All 18 apparent failures disappear with correct fixture placement. Native
manual terminal cards 0368/0369 remain not-run; the summary is not edited to
count the earlier cpmsim external outcomes as native passes. Captures retain
drive readiness, final summary and trailing rows, not a full scrolling trace.

Post-run B:/C:/D: filesystem checks pass. D: is byte-identical to its initial
fully allocated fixture (SHA-256
`5722a607cc9d6393d69e81f6ae41d416ff3a0c3c64639197e104b808e1598409`).
All 29 shipped A: files are unchanged and, using explicit geometry, each also
matches its manifest source hash. The immutable baseline hash is unchanged.
The final independent preflight and stricter audit functions were rerun on the
retained images after additional decoder hardening during the native run;
`final-verification/` and the additional result fields retain those checks.
Future runner invocations save the executed runner and shared audit source.

`test_model4_validation_fixtures.py` passes a dense two-extent fixture with a
16-bit block above 255 and an RO attribute. It rejects displaced record data,
shared allocation and a missing record at the extent boundary. The focused
unified BDOS mapping/stack test also passes (3454 bytes; 26-byte private-stack
high-water). No memory footprint or unloaded 53K TPA changes were required.

### Impact on earlier native evidence and diagnostic limits

A retrospective direct-block audit of all initial fixtures in
`model4-directory/dirtest-irm5e5c6/` passes; its original 49-pass DIR result
retains its canonical fixture premise. The earlier native BDOSTEST media
(`model4-bdos/bdostest-ksglji1p/`) does show the mapping fault: its declared
BTONE block contains `BIG-096`. Its printed 56-pass result is retained as
historical output but requires a corrected-fixture rerun before acceptance.
The replacement run on V006 is
`v006-native-bdos-corrected/bdostest-8csddn9w/`:

```text
Summary: 56 pass, 0 fail, 0 error, 0 observations
3 manual REQUIRED procedures were listed but not run.
```

All its fixtures pass the independent direct-block decoder before launch.
Both data filesystems pass explicit-geometry checks; all 29 shipped A: files
match their manifest hashes and are unchanged. Its executed runner and shared
audit source are retained with the result. The three manual required cards
remain not-run. This corrected-fixture result supersedes the earlier native
BDOS qualification.

The abandoned diagnostic attempts supplied no additional verdicts. One waited
for aggregate `Summary:` in individual report mode (which emits `END_CASE`);
a shorter-wait attempt supplied no usable capture. Later added startup/probe
files used the same faulty host mapping and did not produce usable reports.
These runs were stopped. They are not additional OS failures. The accepted
isolated report and RAM checkpoint use the unchanged suite binary. A manual
post-run audit recheck initially supplied a relative working path twice; the
retained open error was corrected by using the absolute evidence directory,
and all final audits above then passed on the same images.

## V007: native random-I/O exhaustion fixture corrected

The native RANDTEST `/SAFE` run reached passing card 0345 but did not produce
an aggregate result before the runner's 900-second timeout. Retained evidence
is `build/validation/8127eab/v007-native-random/randtest-d2xai76k/`.
This is incomplete evidence, not a pass and not yet an attributed OS defect.
The independently decoded B: fixture starts with exactly 64 free 2K blocks;
its free blocks are 336 through 399, exercising 16-bit allocation numbers.
D: is prepared allocation- and directory-full for the later failure cases.

Card 0346 writes random records until BDOS returns a failure, without normal
intermediate output. `tools/build_rand0346_diagnostic.py` makes a separately
named `R346DBG.COM` from the pinned source without changing the suite. It
prints before preparation, before random writes at record 000000h and every
128 records thereafter, and prints the stopping record and BDOS return code
when the loop returns. Record numbers and return codes are hexadecimal.
Checkpoint printing preserves the loop's registers and flags and leaves its
DMA address unchanged. The test's existing success criterion and cleanup
remain in place. This instrument is diagnostic only: acceptance still needs
the unchanged suite to complete after the cause is resolved.

The diagnostic copy assembles with zero errors (36,236 bytes). Its source,
listing and source/binary hashes are retained in the separate
`v007-native-random/diagnostic-0346/` evidence directory. An isolated native
run was captured; the following investigation supersedes the suspected-stall
interpretation, but the original timeout remains incomplete evidence.

### Exhaustion fixture diagnosis

The first diagnostic was intentionally stopped after a 100-second observation
window, with no second 128-record checkpoint. A finer diagnostic
(`--every-write`) reports before and after each write, preserving all loop
registers and flags. A focused CPU execution check verifies AF/BC/DE/HL/SP
preservation, including the disk-full return A=02h. In
`v007-native-random/diagnostic-0346-each-write/`, the 30-second observation
shows records 0 through 3 returning successfully and record 4 starting. The
test is making slow progress; absence of a coarse checkpoint is not a hang.
The requested automated RAM dump produced no retained RAM file and supplies
no additional evidence.

The separately retained `diagnostic-0346-one-free-block/` starts with exactly
one free 2K allocation block, number 399. Records 0 through 15 succeed;
record 16 (000010h) returns 02h, followed by:

```text
0346  P  R  Prereq/Open=00; random-I/O=02
Summary: 1 pass, 0 fail, 0 error
```

Post-run independent raw-block decoding verifies every B: input unchanged,
the temporary file absent and one free block restored. The filesystem check
passes. This is an instrumented diagnosis, not unchanged-suite qualification.

The native RANDTEST runner now leaves one free block. The other required
writers each use a single-block temporary file and remove it; reads crossing
extents use preinstalled canonical fixtures. This bounds card 0346 to 16
successful writes while retaining its actual allocation-exhaustion oracle
and a 16-bit block number. No OS code or pinned suite code was changed.
The unchanged `/SAFE` rerun on this fixture completes in
`build/validation/8127eab/v007-native-random-bounded/randtest-5f9phoe3/`:

```text
Summary: 39 pass, 0 fail, 0 error, 0 observations, 2 not-run
```

The program hash remains the pinned suite's
`041bddda388acdf9284566ab7c410ca5a520198b78a3973ba1af1d84a329f2c0`.
The final capture explicitly shows card 0346 passing with random-I/O=02h.
Cards 0368 and 0369 remain listed not-run; their native external read-only
terminal-outcome procedures are still pending. They are not aggregate passes.

B:/C:/D: filesystem checks pass. Independent post-run direct-block decoding
verifies all original input contents and exact live-file inventories, including
restoration of B:'s one free block and removal of all temporary files. D: is
byte-identical to the full fixture, hash
`5722a607cc9d6393d69e81f6ae41d416ff3a0c3c64639197e104b808e1598409`.
All 29 shipped A: files are unchanged and match their manifest source hashes;
the immutable System Disk baseline is unchanged. Executed runner/audit sources,
fixture preflight, trailing screen/summary and post-run audits are retained.
This capture does not provide a complete scrolling transcript.

The fixture decoder regression checks pass, including rejection of an incorrect
free-space declaration. The bounded correctness run requires no OS memory
growth or behavior change. The diagnostic demonstrates continuing writes,
not a reproduced write-loop hang. It does not establish acceptable performance.

### Open performance finding: unexpectedly slow native random writes

Reducing the fixture resolves the conformance-run duration, not the underlying
performance concern. The short diagnostic shows four successful writes in a
30-second observation window. An hours-long duration for filling 128K was an
extrapolation from that sample, not a completed timed measurement. Console
instrumentation and emulator timing effects have not been separated from OS
disk-path costs. Do not classify this as ordinary floppy latency without that
investigation.

Measure identical sequential and random writes without per-record console
output, recording elapsed time and exact successful record counts. Compare
low and high allocation blocks and sparse versus densely occupied directories.
Count directory scans, physical sector reads/writes and allocation-vector work
per operation, and verify emulator speed/latency settings. Compare the same
workload with a historical Model 4 CP/M baseline where practical. Distinguish
instrumentation, emulator timing, BIOS caching/mapping and BDOS algorithm costs
before attributing the slowdown. This performance finding remains open; the
39-pass result establishes correctness only on the bounded fixture.


## V008: native write-path performance measurements

The native write-speed concern remains open, but is now reproduced without
per-record diagnostic output. `tools/run_validation_native_write_profile.py`
builds a separate PERF8 probe. Each measured phase writes eight 128-byte A5h
records to a fresh file, using Function 21 or Function 34. NOP trace fences
exclude preparation, console boundary messages, Close, Delete and warm boot.
The random phase uses record numbers 0–7 in the same extent. The sequential
phase sets the same random-record field before each call, so probe-loop work
is comparable. No production OS code is changed.

Both runs use the immutable V006 native System Disk, the same emulator, Model 4,
`-turbo`, the same eight-record workload and native 800K data geometry. Results
are emulated CPU t-states including controller waits, not host wall-clock
benchmarks or a measured original-hardware throughput claim.

| Data fixture | Sequential t-states | Random t-states | Random/sequential | Logical BIOS reads, seq/random | Logical BIOS writes, seq/random |
| --- | ---: | ---: | ---: | ---: | ---: |
| Empty directory, first free block 2 | 14,461,090 | 26,630,160 | 1.84 | 1 / 8 | 9 / 16 |
| Dense directory, first free block 399 | 27,302,780 | 224,440,792 | 8.22 | 17 / 272 | 9 / 16 |

The dense fixture contains 64 live directory extents and one free block; it is
not a fully occupied directory. Directory occupancy and data-block position
vary together in this comparison, so their individual timing contributions
have not been isolated. The read-count difference directly establishes much
more directory I/O. Trace counts are filtered between the probe fences, rather
than including program loading or boot activity.

Evidence directories under `build/validation/8127eab/`:

- `v008-write-profile-dense/native-write-v_b8qc25/`
- `v008-write-profile-empty/native-write-62ijcwg8/`

The empty-disk run also traces resident physical-transfer request vectors:
sequential uses 10 reads and 9 writes; random uses 24 reads and 16 writes.
These are request-entry counts, not counts of controller retry attempts. The
dense run did not include those physical vectors in its trace; its physical
counts are not claimed as measured.

Source attribution: production `src/bdos/unified.mac` has UB_RDECODE call
UB_CCORE for a populated dirty FCB before decoding each random position.
UB_RWCOMMON then calls UB_EXTENT/UB_ACTIVATE, scanning to reopen the requested
extent even when it is the same extent. UB_PUBLISH also finds the directory
entry to commit changed metadata. The repeated scans account for the large
logical read count on the dense fixture. In `src/bios/bios.mac`, BIO_PREP
invokes the resident physical read for each logical transfer; BIOWRITE then
invokes the physical write. There is no physical-sector cache-hit bypass in
this path. Source behavior and measured request counts support an OS I/O-cost
finding; simulated disk latency amplifies those requests. Neither measurement
establishes that emulator latency itself is excessive or faulty.

Both probes finish successfully. Independent post-run checks verify the eight
A5h payload records in block 399 or 2, original live directory entries and all
allocated input blocks unchanged, temporary file absent, clean B: filesystem,
and all 29 shipped System Disk files unchanged and matching manifest hashes.
Deleted scratch slots and unallocated data can legitimately retain test bytes.

The first run's initial host trace parser rejected reused TPA fence addresses;
the instruction trace and completed native capture were retained. Reanalysis
matches the fence NOP opcode, excluding earlier boot/loader instructions at
those addresses, and accepts padded t-state fields. The original executed
runner and corrected analysis source are both retained. The empty-disk run
uses the corrected parser directly. A later independent payload check was
recorded in each result. These are profiling-tool corrections, not OS test
failures or new emulator runs.

Next: audit a same-extent random-I/O fast path that retains dirty active FCB
state instead of closing/reopening it unnecessarily. Qualify compatibility,
allocation publication, cross-extent transitions, error recovery and protected
ROM behavior, and audit memory cost before production changes. The unloaded
53K TPA contract remains in force. Physical-sector caching is a separate
potential optimization with buffer-invalidation and memory costs; it has not
been implemented or approved by these measurements.


## V009: private same-extent random-I/O candidate audit

Production BDOS remains unchanged. `tools/audit_random_same_extent.py` emits
baseline and candidate copies under `build/audit/random-same-extent/` for
bounded qualification. The candidate compares the requested logical EX/S2 with
a populated active FCB before deciding to close and reopen it. Same-extent
operations retain live RC/allocation/dirty state. A zero-RC FCB takes the normal
activation path, preserving lookup through bare search FCBs and the existing
empty-file behavior. An EX byte with high flags also conservatively takes the
normal path. R2 rejection still occurs before FCB mutation.

The decoder returns carry to request ordinary extent activation; random callers
preserve that flag while supplying their read/write mode. Real extent changes
still close the old populated extent before changing its stored EX/S2 and
activating the target. Common
read/write cores retain their drive, geometry and protection gates. RES 7,A
updates CR without destroying the carry result. The focused CPU interpreter
now implements this actual Z80 opcode with unchanged flags.

### Memory and ABI

The candidate recovers space through four fall-through wrappers (Close, Make,
sequential Read and sequential Write), four ordinary tail calls in console
services, and one in-range relative branch. A compact random-position decoder
uses R0 bit 7 as the carry input while forming EX from R1. There is no new
resident state and no reduction in private-stack capacity.

The unpadded candidate is 3452 bytes versus the baseline's 3454. Two zero bytes
before mutable state keep the linked state addresses, including OLDSP, DMA,
drive/user, console state, and both stack boundaries identical to the baseline.
Thus the tested candidate still occupies exactly 3454 bytes. No BIOS, extension
or TPA boundary moves; the unloaded 53K contract is preserved by construction.
The host audit asserts these invariants and leaves production source unchanged.

### CPU and assembler checks

`test_random_same_extent_candidate.py` passes 27,648 position/transition cases,
covering every R1 value, both halves of R0, S2 changes, zero/populated RC and
clean/dirty FCB state. It verifies preserved live fields and random position,
required slow-path Close calls, carry output, and stack balance. Its fake Close
clobbers ordinary registers to verify saved decoded positions survive a call.

The exact candidate also passes the existing unified-BDOS public-call tests,
480 grouped-activation cases and the existing grouped directory-comparison
matrix, with runtime writes to BDOS code rejected by the CPU harness. Fixtures
are installed before execution; fixture patching is not counted as an allowed
OS code write. The measured private-stack high-water remains 26 bytes of 40.
This is guarded CPU coverage, not complete protected-ROM profile qualification.

ZSM4/DRI LINK emits 3454 byte-identical candidate bytes. The first build invocation
lacked cpmsim's helper directory on PATH and could not boot the assembler disk;
correcting the tool environment produces the accepted native build. It is not
an OS or candidate failure. Host/native logs and CPU results are retained in
the audit directory.

### Native performance comparison

A private copy of the V006 System Disk has only its installed 3454-byte BDOS
payload replaced, after verifying it equals the baseline emitted binary.
Every other raw byte is preserved and all core state addresses remain pinned.
The report labels this image a private comparison baseline: its packaged system
and CONFIG validation references are deliberately still the baseline and it is
not distributable. No saved-configuration or SYSGEN operations are qualified
with it. Production integration must rebuild all dependent artifacts.

On the same dense data image and eight-record PERF8 workload as V008:

| Measured phase | Baseline t-states | Candidate t-states | Logical reads, baseline/candidate | Logical writes, baseline/candidate |
| --- | ---: | ---: | ---: | ---: |
| Sequential | 27,302,780 | 27,302,730 | 17 / 17 | 9 / 9 |
| Random, same extent | 224,440,792 | 37,038,063 | 272 / 34 | 16 / 9 |

This is about 6.06 times faster in emulated CPU cycles for the random phase;
no per-record console output is inside the measured interval. The zero-RC
fallback and allocation publication still cause initial directory work. No
physical-sector cache is added. The candidate trace also counts 43 physical
read requests and 9 physical write requests in the random phase; these are
request entries, not controller retry attempts.

Evidence: `build/audit/random-same-extent/native-dense-profile/native-write-3f74sdmy/`.
The final eight A5h records, preserved input blocks/live entries, removed
temporary file, clean filesystem and all 29 shipped System Disk files pass
independent audits. Native candidate equality with the current emitted audit
binary is checked after the run. Sequential performance is essentially unchanged.

The unchanged native RANDTEST /SAFE candidate run completes with 39 pass,
zero fail, zero error and two manual read-only cases not run. Evidence:
`native-random-required/randtest-od146s_1/` under the audit directory. All
B:/C:/D: inputs match their canonical source bytes; exact live-file inventories
are restored, B: again has one free block, D: remains byte-identical to its full
fixture, and all filesystems are clean. All 29 shipped A: files are unchanged.
The code is still a private payload comparison, not a rebuilt release.

Additional focused checks cover 24 high-EX-flag fallback cases and all 256 flag
values for RES 7,A with four input bytes (1024 instruction cases). Before
production promotion, remaining gates include full dependent rebuilds,
cross-platform/ROM and error-recovery qualification, and broader regression
coverage of unclosed and cross-extent write/zero-fill/read lifecycles. The two
native manual read-only outcomes remain unqualified for this candidate.
These measurements do not close all write-performance concerns.


### Deferred non-automated coverage after PR 370

PR 370 is merged. At the user's request, tests not completed automatically
are recorded here for later attention; no operator action is requested now.
Neither the private candidate results nor the following deferrals establish
whole-system acceptance. The production BDOS integration remains in progress.

| Coverage | Outstanding evidence / disposition |
| --- | --- |
| Native FILETEST/RANDTEST 0368, 0369 | File-read-only sequential/random writes, recovery to the CCP, and independent unchanged-disk audits. The two aggregate not-run rows remain not run. Earlier V005 cpmsim external outcomes passed; they do not qualify the new BDOS integration. |
| Native DISKTEST 0379–0384 | Software-protected-disk Make, sequential/random write, Delete, Rename and post-protection mutation terminal outcomes, recovery and unchanged-disk audits. Earlier cpmsim external outcomes passed; native equivalents remain outstanding. |
| BDOSTEST 0143, 0420, 0519 | Three manual REQUIRED cards: prepared SCRATCH /BLANK fixture, buffered-input session, and BIOS resource inspection. Corrected native required runs explicitly leave these not run. |
| BDOSTEST 0154 | Unavailable-drive terminal procedure, classified as a manual/profile case; applicability and accepted platform outcome must be recorded separately. |
| Native ECOTEST 0569, 0575, 0577, 0579 | Real-CCP semantic, SAVE, TYPE-byte-stream and ordinary command-recovery procedures. Earlier V005 cpmsim external evidence exists; corresponding native transcripts remain outstanding. |
| Remaining console, BIOS, error, CCP and device/media procedures | Retain the individual observed/not-run results in the preceding ledger. Review applicability and perform required operator/device procedures later; optional, unsupported and out-of-scope rows must be distinguished from missing required coverage. |

This is the deferred manual/external-evidence register, not a claim that every
catalog not-run row is an applicable manual test. Visual monitor and application
checks and the other later campaign stages also remain separate from the
returning conformance tests. Automated production rebuild, ROM, recovery and
regression qualification continues independently; a skipped test is never
converted to a pass merely because another platform or an earlier image passed.


## V010 — production same-extent integration, qualification in progress

Promote the audited same-extent path to production BDOS 1.8 (API unchanged).
BDOS remains exactly 3454 bytes, with frozen mutable-state/stack addresses and
53K unloaded TPA preserved. The historical prototype generator now directs
integrated trees to the production test instead of reapplying the patch.

The production guarded decoder/activation matrix passes, including 27,648
position/transition cases, the grouped activation/comparison checks and RES
flag preservation. Public service inventory and injected I/O recovery checks
pass. Recovery stack high-water is 28 of 40 bytes, identical to the baseline;
the normal foundation measurement of 26 bytes is not a universal maximum.

The first dependent rebuild stopped at stale ROM reference-count expectations.
Removing four wrapper CALL operands and one absolute JP operand reduces the
inventory by five words. The updated checks retain independent decoding,
classification, target validation and shifted-layout checks: 794 references,
470 immutable-ROM targets and 324 live-RAM targets. Independent relocation
verification passes with 783 changed words, 11 already-final words and 1548
changed bytes. This was a qualification expectation failure, not a runtime
failure. A fresh complete distribution rebuild and rebuilt-image runtime
qualification remain outstanding; private V009 image results do not substitute
for them. Deferred manual coverage is listed above and remains unqualified.


### Fresh production cpmsim observations

Native ZSM4/DRI LINK produces 3454 byte-identical production BDOS 1.8 bytes
(`NATIVE-BDOS-BUILD.LOG`). The fresh isolated z80pack candidate under
`/private/tmp/bettercpm-v010-production-r2/work/candidate-bettercpm-dist-34e1j4kw/z80pack/`
was used for independent private-copy returning runs. Evidence under
`/private/tmp/bettercpm-v010-production-runtime/`:

| Group | Evidence directory | Pass | Not run | Fail/error rows |
| --- | --- | ---: | ---: | ---: |
| FILETEST /GROUP:REQUIRED | filetest-ej22jbix | 68 | 2 | 0 |
| RANDTEST /SAFE | randtest-olkp97ng | 39 | 2 | 0 |
| BDOSTEST /GROUP:REQUIRED | bdostest-l_rw1g3a | 56 | 3 | 0 |

The runner verifies the pinned suite binary and unchanged reference image;
these are returning-group observations, not independent post-run filesystem
acceptance or completion of deferred terminal outcomes. Native Model 4 and
full release qualification remain in progress.


The complete isolated two-platform distribution build subsequently exits zero.
Accepted generation:
`/private/tmp/bettercpm-v010-production-r2/releases/release-833d1b8129eb-6492f1365985/`.
Both z80pack and trs80gp System Disks pass their distribution qualification:
30 files/148K free and 29 files/596K free respectively, with no planned manifest
items missing. Build transcript: `/private/tmp/random-production-r2.log`.
This closes the dependent distribution-build gate, including rebuilt package
and CONFIG references; it does not close native Model 4 conformance, independent
post-run filesystem audits, or broader runtime qualification. The generation
was captured from 833d1b8 before the subsequent documentation-only commits.


## V011 — native production integration qualification

PR 371 is merged as `7e905ae`. All tracked source/tool/metadata inputs from
accepted generation `release-833d1b8129eb-6492f1365985` match the merged tree;
subsequent differences were documentation only. Native runs use private copies
of that generation, System Disk SHA-256
`5d562d5cbd00eaebab8870251d7f233c480bebf5aeb13edf6a564d77366d6312`.
The pinned suite binaries are unchanged. Evidence is retained under
`/private/tmp/bettercpm-v010-native/`.

### Native RANDTEST — PASS

`randtest-d8r_3fxj` completes RANDTEST /SAFE with 39 pass, zero fail/error,
and two manual read-only cards not run. The final capture retains the aggregate
summary and trailing rows, not a complete scrolling transcript. Before boot,
the independent raw-block decoder checks canonical file contents, dense
extents, 16-bit allocation maps, RO attributes, one free B: allocation block,
and the completely full D: fixture. Its corruption-rejection self-test passes.

Post-run B:/C:/D: filesystem checks pass. The separate retained
`audit-inputs.py` re-decodes every original input against source bytes and
checks exact live-file inventories: all input files survive unchanged, B:
again has one free block, and D: remains byte-identical to its full fixture.
All 29 shipped A: files match their manifest hashes and remain unchanged.
The immutable baseline hash is unchanged. Native required FILETEST is next;
other groups and the deferred manual register remain open.


### Native FILETEST — PASS

`filetest-b6_wiwvx` completes FILETEST /GROUP:REQUIRED with 68 pass, zero
fail/error and two manual cards not run. The runner's independent raw fixture
preflight, explicit-geometry post-run filesystem checks, unchanged-full-D:
check and all 29 shipped-file manifest/content checks pass. The retained
post-run `audit-inputs.py` additionally decodes every original B:/C:/D: input
against its canonical source and checks exact live-file inventories; all pass.
The baseline image is unchanged. Final summary/trailing-row captures do not
constitute a complete scrolling transcript. BDOSTEST required qualification
continues next; no deferred manual card is promoted to PASS.


### Native BDOSTEST — PASS

`bdostest-1co8eu3l` completes BDOSTEST /GROUP:REQUIRED with 56 pass, zero
fail/error and three manual REQUIRED procedures not run. Both data filesystems
pass. Independent post-run decoding verifies every original B:/C: input and
exact live-file inventories, and all 29 shipped A: files match their manifest
hashes and remain unchanged. The baseline image is unchanged. The retained
runner/audit sources, readiness/final captures and result JSON document the
run. No complete scrolling transcript or manual outcome is claimed.

### Remaining native coverage

The fresh production file/random/BDOS gates above are complete. Fresh native
DIR, CPU/ecology/disk-safe, CCP/entry and focused application/monitor regression
coverage remain to be progressed separately; earlier image results are retained
as historical evidence. The deferred manual/external-evidence register remains
open at the user's request. System-wide validation is not complete, and these
three successful groups do not imply completion of other campaign stages.


### Native DIRTEST — PASS

On the same source-identical production generation, DIRTEST /SAFE completes
with 49 pass, zero fail/error and zero observations. Evidence:
`/private/tmp/bettercpm-v011-native/dirtest-zn178x45/`.
Independent fixture preflight and post-run direct-block decoding pass; all
original B:/C: input contents and exact live-file inventories are preserved.
Both data filesystems pass, all 29 shipped A: files match their manifest hashes
and remain unchanged, and the immutable baseline hash is unchanged. The retained
runner/audit scripts and result JSON document these checks. Final summary and
trailing-row captures are not a complete scrolling transcript.


### Native CCP and entry/return — PASS

`/private/tmp/bettercpm-v011-native/model4-returning-pmrlb1_3/` completes
CCPTEST /GROUP:REQUIRED (12 pass) and ENTRYTST /GROUP:REQUIRED (25 pass), both
with zero fail/error. The final captures retain summaries and trailing rows, including visible
not-run cards; they do not provide a complete catalog count. Manual and
excluded cards are not promoted to passes. All 29 shipped A: files
match their manifest hashes and remain unchanged; Function 40 scratch is absent.
An additional retained `audit-filesystem.py` verifies the final System Disk
filesystem with explicit geometry. The baseline hash remains unchanged.
These are selected returning-group results, not complete terminal/CCP coverage.


### Native CPU, ecology and disk-safe — PASS

`/private/tmp/bettercpm-v011-native/model4-returning-s2927d1c/` completes:

| Group | Pass | Fail | Error | Observed | Explicit not-run |
| --- | ---: | ---: | ---: | ---: | ---: |
| CPUTEST /ALL | 2 | 0 | 0 | 1 | 2 |
| ECOTEST /GROUP:REQUIRED | 1 | 0 | 0 | 0 | 4 |
| DISKTEST /SAFE | 7 | 0 | 0 | 0 | Summary does not enumerate exclusions |

The saved screens contain successive summaries; each verdict is matched to its
own command. Observations/not-run are not passes, and /SAFE is not a claim of
full DISKTEST coverage. The independent post-run filesystem check passes;
all 29 shipped files match their manifest hashes and remain unchanged. The
secondary B: raw image remains exactly E5-filled throughout. Retained
`audit-filesystem.py` reproduces these checks. The baseline remains unchanged.

### Campaign position after these runs

Fresh native production returning groups now cover random, file, BDOS,
directory, CCP, entry, CPU, ecology and disk-safe checks, with no failure/error
verdict in the selected groups. Focused console/BIOS/error and application/
monitor regression, applicability review, and later validation stages still
remain. The deferred manual/external-evidence register stays open. These
results do not close system-wide validation.


## V012 — native console, BIOS and safe-error continuation

PR 373 is merged as `88caf71`. The production generation and pinned suite are
unchanged from V011. The native returning runner gains a `bios-error` group,
waiting for each catalog's final row before capturing its summary, and runs
both suites on private media. Evidence:
`/private/tmp/bettercpm-v012-native/model4-returning-jt1wu2vy/`.

| Native group | Pass | Fail | Error | Observed | Untested/not-run |
| --- | ---: | ---: | ---: | ---: | ---: |
| BIOSTEST /SAFE | 5 | 0 | 0 | 11 | 30 |
| ERRTEST /SAFE | 5 | 0 | 0 | 12 | 26 |

All 29 shipped files match their manifest hashes and remain unchanged. The
additional retained `audit-filesystem.py` verifies the final System Disk
filesystem, and the baseline hash remains unchanged. Captures contain summaries
and trailing rows, not a full scrolling transcript. Untested BIOS procedures
include required, profile and out-of-scope cards; this is not full BIOS/fault
coverage. Observed behavior without a portable guarantee is not counted as a
pass. Deferred manual/external procedures remain open.


### Native basic console observations — PASS

`/private/tmp/bettercpm-v012-native/model4-input-uyyb8g_h/` independently
observes CONSTEST 0106 (AB/Enter), 0115 (AB/Backspace/C) and 0121
(AB/Ctrl-X/CD). All three display the expected edit while preserving the
prompt and return the exact expected count/data buffer. Keyboard-matrix events
are supplied through trs80gp; guest input buffers are not patched. The runner
does not answer the suite's Y/N confirmation, so these are external observations,
not fabricated suite PASS rows.

Each case uses its own private disk and retains the native screen capture,
keystrokes and program/emulator/baseline hashes. Retained `audit-files.py`
independently checks all 29 shipped files against their manifest and original
contents after every case and verifies each final System Disk filesystem.
All pass, and the immutable baseline remains unchanged. Native line controls
and Ctrl-C recovery continue separately.


### Native line controls and Ctrl-C recovery — PASS

`/private/tmp/bettercpm-v012-native/model4-input-x5gsbz40/` independently
observes four additional cases, each from a fresh cold boot:

| Case | Native observation |
| --- | --- |
| 0118 | Ctrl-E starts a new display line and retains ABCD in the returned buffer. |
| 0119 | Ctrl-R redisplays the retained text and returns ABCD. |
| 0120 | Ctrl-U starts a new line, discards the old input and returns CD. |
| 0117 | Initial Ctrl-C abandons the interrupted caller; VER /VER executes and a final A0 prompt is usable. |

All literal buffer/display predicates pass. Recovery requires executed resident
VER version output, the final prompt and absence of the caller-return marker
or suite confirmation. The four observer regression tests pass, including
rejection of startup-banner-only and failed-recovery transcripts. These are
external observations, not suite confirmation/PASS rows. Retained
`audit-files.py` verifies clean filesystems and all 29 shipped files against
their manifest/original contents after every case. All pass; the baseline is
unchanged. Combined with the basic group, seven distinct native console cases
are observed successfully. No OS change is required.

### Coverage limits and next work

This batch closes the selected native BIOS-safe, error-safe and seven console
observation checks. It does not establish every console timing/queue/device
property, controlled physical-media fault behavior, or every BIOS catalog
procedure. Untested/manual items remain in the deferred register rather than
being inferred from safe-group successes. Application/monitor regression and
the remaining campaign stages still require separate qualification; whole-
system validation is not complete.


## V013 — shipped-image monitor and application regression

The console/BIOS/error record is pushed in PR 374. These next regressions use
private copies of the same qualified production generation. Existing shipped
programs, RSXs and STARTUP.SUB are left intact; only private exercise scripts
and completion witnesses are added. This avoids substituting development
binaries for the release artifacts under validation.

### Native ADM-3A and VT52 — PASS

Evidence under `/private/tmp/bettercpm-v013-native/`:

| Pair | Evidence | Selected checks |
| --- | --- | --- |
| ADM3A + M4SCRN | adm3a-17i2vb52 | Positioned text, parser reset, movement/tab, reverse video, line erasure, cursor query, keyboard A:[], unload/53K |
| VT52 + M4SCRN | vt52-61p9zlpw | Positioned text, tab/margin, parser reset, EOL/EOS erasure, unload/53K |

Each run verifies the loaded pair, completes the shipped test utility, unloads
both providers, observes no RSXs loaded and 53K TPA, then executes an independent
completion witness. All 29 shipped files match their manifest hashes and remain
unchanged; final System Disk filesystems are clean and baseline hashes unchanged.
These are selected screen-memory assertions, not exhaustive protocol coverage
or an audible-bell qualification.

The first ADM-3A checker used a 23-byte slice for a 24-byte marker. Its assertion
failed after all seven captures had been retained. Correcting the checker and
running the full capture/integrity audit on those same images passes. The
original executed runner and failure log remain alongside the corrected audit
source/result; no OS or monitor code changed. The new `--audit-only` mode
rechecks retained captures without relaunching or modifying the test disk.


### Native ANSI — PASS

`/private/tmp/bettercpm-v013-native/ansi-nvfgfw3z/` passes the shipped ANSI +
M4SCRN regression: text at row 5/column 10, reverse attributes only on the
selected word, erased suffix, parser reset and unload of both providers with
53K TPA restored. An independent completion witness executes afterward.
All 29 shipped files match their manifest hashes and remain unchanged; the
filesystem is clean and baseline hash unchanged. This closes the selected
three-personality Model 4 screen regression, not every ANSI/VT100 feature or
cross-platform/real-terminal compatibility. Audio remains separately untested.


### Native shipped file utilities and ED — PASS

`/private/tmp/bettercpm-v013-native/applications-y4tjmfvc/` exercises the shipped
binaries on a private System Disk and disposable B: data disk. PIP copies B1's
source; transient COPY /V /B copies it to B3; transient REN renames the PIP copy;
transient TYPE displays its ALPHA/BETA text; transient ERA /Y removes it.
Resident COPY/REN/TYPE/ERA repeat the ordinary workflow on a separate B3 name.
Two independent display captures verify the actual TYPE text, with a clear-screen
witness between paths so stale output cannot satisfy the second check.

ED then inserts NEW before an existing B7:CASE.TXT and saves. Independent raw
file decoding verifies NEWOLD text, the original OLD text in CASE.BAK, the
unchanged user-0 CASE.TXT sentinel and unchanged B1 source/B3 verified copy.
The exact five-file final inventory contains no renamed/erased intermediates
or CASE.$$$. Distinct output-only completion witnesses establish execution
through both the file workflow and ED save. This smoke case does not separately
qualify caller-DU restoration, every error path, paging or every utility option.

Both final filesystems pass explicit-geometry checks. All 29 shipped files,
including STARTUP.SUB, match their manifest hashes and remain unchanged; the
immutable baseline remains unchanged. The executed runner, invocation, screen
captures and result JSON are retained. Original run logs are archived in each
V013 evidence directory, including the first ADM checker assertion failure.
No OS change is required by these regressions.

### Remaining application/monitor coverage

This batch qualifies selected native screen tests for all three personalities
and a representative shipped file-utility/ED workflow. cpmsim/host-terminal
backend regression, broader utility/application scenarios (including TYPE paging
and CONFIG/DUP/SYSGEN persistence/media operations), and later campaign stages
remain separate work. Audio/manual/device tests remain deferred as recorded;
whole-system validation is not complete.


## V014 — cpmsim shipped monitors and broader applications

Native results are pushed in PR 375. These cpmsim runs retain all shipped
programs/providers from the same qualified production generation. New runners
copy the release images, add only disposable data fixtures and independently
compare all 30 shipped files with their manifest hashes and original contents.
All accepted runs below pass final filesystem checks, and the immutable
baseline remains unchanged. Terminal rendering uses pyte 0.8.2 from
`/private/tmp/vt52-qualification-venv/`; it is a software terminal oracle,
not physical-terminal qualification. No OS change was required.

### Shipped personality + ANSISCRN pairs — PASS

Evidence under `/private/tmp/bettercpm-v014-cpmsim/`:

| Pair | Evidence |
| --- | --- |
| ADM3A + ANSISCRN | adm3a-0c907kgn |
| VT52 + ANSISCRN | vt52-jkg7xyq5 |
| ANSI + ANSISCRN | ansi-jfcgyyii |

All three verify loaded-pair listings, rendered first-page position, shipped
test-utility completion, unload of both providers and restored 53K TPA.
ADM3A checks cursor queries, visibility controls and keyboard input; VT52 checks
its identification reply and ANSI-host erase/address output without leaked
VT52 addresses. ANSI checks rendered reverse attributes, erased suffix and
parser reset. These are selected RAM-profile backend regressions, not guarded
ROM, audio, exhaustive protocol or physical host-terminal certification.

### TYPE with ANSI monitor — PASS

Accepted evidence under `/private/tmp/bettercpm-v014-applications-r2/`:

- `type-paging-jqfddvhf`: Ctrl-C/Space forward, comma/Ctrl-R back, EOF no-op
  bell and Ctrl-Q quit. Hidden bytes after Ctrl-Z are not displayed and the
  source file remains unchanged.
- `type-boundaries-4kxkaaq1`: the continuous final page includes both file
  banners; `>` brings the second banner to row zero even at final EOF, and
  `<` restores the first banner to row zero. Both sources remain unchanged.

The first checker incorrectly required the initial display's banner on row
zero. The initial display has a leading blank line; the navigation pages do
put the selected banner on row zero. Retained captures establish that distinction.
The corrected checker allows an initial margin but keeps strict row-zero
assertions for `>` and `<`. No TYPE implementation change was made.

### ED and CONFIG lifecycle — PASS

Accepted evidence under `/private/tmp/bettercpm-v014-lifecycle/`:

| Case | Evidence | Checked behavior |
| --- | --- | --- |
| ED E | ed-save-bcadn6_n | User-7 save, original backup, user-0 sentinel, output-DU exit |
| ED Q | ed-quit-xab4grdl | Discard preserves original, no backup/work file, caller-DU exit |
| ED H then E | ed-head-ifhlmh8x | Save/restart composition and final backup contents |
| CONFIG decline | config-startup-N-j68wv63f | Startup record unchanged |
| CONFIG save | config-startup-Y-iwuh_3e6 | Verified startup save; VER executes on next cold boot |

ED's first checker expected A0 after successful E. The current ED spec section
39 preserves output-DU exit behavior; the observed B7 prompt is correct. The
corrected checker requires B7 after E and A0 after Q, then explicitly returns
to A0 before shutdown. The earlier timeout/transcript is retained as an
instrument failure, not an OS failure.

ED input, backups and the user-0 sentinel are independently extracted and
compared; no CASE.$$$ remains. CONFIG saves do not immediately execute the
new command. An independent reserved-area comparison confirms that system
bytes outside the two startup records remain unchanged. All 30 shipped files
and final filesystems pass in every accepted scenario. Aggregate logs,
executed runners, transcripts and per-case results are retained.

Broader DUP/SYSGEN/media-operation regression, additional utility scenarios,
guarded-ROM and manual/device outcomes remain separate campaign work.
These successful subsets do not complete system-wide validation.


## V015 — resumed guarded ROM and lifecycle checks

PR 376 is merged according to the user. Build/tests run with normal sandbox
permissions; no execution escalation was needed. The full ROM media is rebuilt
at `/private/tmp/bettercpm-v015-rom-media/`. Its 3454-byte BDOS is byte-identical
to the qualified production integration (SHA-256
`8e2fabb75c84c95c573bc4d90b0d7a112f99e112a1b275c9df03b3c0479c222f`).
ROM image SHA-256:
`e294ea58af1c78300b4176246a06e5f6da24422d190cb67aa48b529609860052`.
Evidence/log copies and the explicit open status are in
`/private/tmp/bettercpm-v015-lifecycle/`; retained diagnostic source and media
are in `/private/tmp/bettercpm-v015-diagnostic/`.

### Guarded repeat — PASS, acceptance still OPEN

The guard primitive probes reject CPU writes, DMA writes, guest unlocking and
boundary changes, and verify reset protection and ordinary-mode behavior.
The first full campaign boots at A9 rather than A0, so its prompt gate fails.
An unmodified repeat passes protected execution at DF00h, cold/warm returns,
CPX load/list/reconstruction/unload and RSX load/list/unload. The 1024-byte
workspace lifetime check passes with the 907-byte CONFIG control overlay.
Measured stack high-water/reserve: system 24/32 (8 spare), BDOS 28/40 (12 spare),
loader 18/64 (46 spare). These measurements apply to the successful campaign.

A private emulator copy traces writes to the relocated user-state byte and
boots at A0 in that diagnostic run; this does not explain or dismiss the first
failure. After removing the write trace, three independent pristine-media cold
boots yield A0, A0, then A24 (initial display includes A<0). The last run fails
its A0 gate. Both wrong-user outcomes remain unresolved; passing repeats do
not close the ROM cold-start acceptance gate. The generated per-run XIP report
records the successful campaign only; campaign-status.json and this ledger
explicitly retain the unresolved failure. No release acceptance is claimed.

### Focused monitor/RSX relocation — PASS after fixture correction

Assembled-code lifecycle tests pass with both ANSISCRN and M4SCRN backends:
ADM3A parser/mode state, VT52 partial-address/queued-reply state, and production
ANSI parser/saved-rendition state survive movement. Tests also cover blocked
backend removal while bound, public service lookup, continuation and unload
back to the baseline/53K boundary. These are controlled CPU fixtures, not six
new native-emulator campaigns. Production ANSI is selected explicitly; an
initial private-candidate ANSI test is not substituted for it.

VT52 initially fails removing HELLO because its synthetic disk envelope at
C000 extends into the prospective live profile. Source metadata is overwritten
by the installation itself. Move synthetic disk bytes to the existing ANSI
fixture's safe addresses and assert complete file envelopes stay below the
prospective live allocation. The corrected test passes on both backend profiles.
This changes only the test fixture, not the manager or VT52 implementation.
Original failure/diagnostic and corrected logs are retained.

Next core work is to isolate the intermittent ROM cold-start wrong-user state.
Manual/device outcomes and later campaign stages remain open as before.


## V016 — ROM cold-start recovery flag fix

The V015 wrong-user failure is an OS initialization defect, not an emulator
latency or prompt-detection issue. Instrumenting CPU writes, DMA writes and
reads of relocated UB_USERNO (D6C1h) reproduces the failure. In one failed boot,
the first nonzero store is at EE05h in relocated CL_ABORT, writing EBh; the
prompt initially displays AG5 before subsequent context restoration masks
the user to 11. No DMA write causes the corruption.

CL_ABORT interprets page-zero 0048h bit 0 as an active interrupted lookup and
restores the saved user at 0046h. On a ROM cold start these bytes are
uninitialized; reconstruction reaches CL_ABORT before the CCP initializes
them. Clear the active flag in the ROM-only cold initializer. Warm entry
preserves genuine loader recovery. The change adds three ROM bytes, with no
resident RAM, BIOS or BDOS growth and no change to the 53K unloaded TPA.
The integrated ROM now has 457 spare bytes and entry FE15h.

Validation:

- Full z80pack development/ROM-media build passes, including independent
  packing, relocation and cold-initializer execution checks. The initializer
  test begins with poisoned A5h RAM, requires the recovery flag to be zero
  and leaves the inactive saved-user byte untouched.
- 32 separate untraced guarded-simulator cold boots on fresh disk copies all
  reach the unchanged strict A0 prompt gate and halt normally.
- Full protected-ROM campaign passes: guard primitives, cold/warm return,
  transient execution, CPX reconstruction/unload, RSX load/unload and 53K
  restoration. Workspace lifetime checks pass. Stack usage/reserve remains
  system 24/32 (8 spare), BDOS 28/40 (12 spare), loader 18/64 (46 spare).

Evidence: `/private/tmp/v016-rom-build.log`,
`/private/tmp/v016-cold-repeats.log`, `/private/tmp/v016-rom-xip.log`,
`/private/tmp/bettercpm-v016-rom-media/rom/` and retained diagnostic traces
`/private/tmp/bettercpm-v015-diagnostic/readtrace-*/transcript.bin`.
ROM SHA-256: `757d38cb0ccec92ccb3624501e45ad64b90cc0c3f79487b2c75695143535b918`.
The wrong-user gate is resolved; this does not close deferred manual/device
checks or declare whole-system validation complete.


## V017 — shipped cpmsim DUP/SYSGEN media workflows and disk cold-state fix

Continue stage 5 with the shipped DUP and SYSGEN binaries, without replacing
utilities with development binaries. `run_validation_cpmsim_media.py` retains
private source/target disks, transcripts, independent file extraction,
filesystem checks, all 30 shipped-file comparisons and per-case results.
The fixture saves `:VER /BANNER` as its startup command to avoid SUBMIT's
filesystem writes obscuring source-preservation comparisons; this changes
protected startup configuration only, not the shipped command files.

### Disk cold-start finding and fix

The first run passes DUP format/copy/check and reaches the SYSGEN restored
system's prompt, but fails its banner-count oracle: the fixture used resident
`VER /BANNER` instead of `:VER /BANNER`. The transcript also exposes an OS
initialization defect distinct from that fixture error: a cold A32 prompt
briefly precedes A0 redisplay. Preserve the original run at
`/private/tmp/bettercpm-v017-cpmsim-media/` and its log
`/private/tmp/v017-cpmsim-media.log`; it is not passing round-trip evidence.

The disk bootstrap leaves its own bytes at the same page-zero recovery
addresses implicated in V016. In the previous cpmsim boot record, 0048h is
7Dh (active bit set) and 0046h is 20h: CL_ABORT restores user 32 on cold
reconstruction. Command editing later masks it to zero. Fix both disk cold
loaders to clear the active flag before BIOS BOOT. Warm reconstruction remains
unchanged. The cpmsim clear happens after the final resident read because
page zero still holds executing bootstrap instructions. Keep its 128-byte
limit by retaining zero in D, reusing it for C, and removing the unreachable
restart after the interrupt-disabled terminal HALT. The Model 4 stage-one
loader uses the zero result of its final sector counter decrement.

`test_cold_boot_lookup_state.py` executes both emitted disk loaders with three
poisoned-RAM patterns. It checks the cpmsim flag, all 52 physical record
requests across track boundaries, destination addresses and the 128-byte limit;
it checks Model 4 flag clearing with controlled successful sector transport.
The old cpmsim loader fails this new regression; both corrected loaders pass.
The small CPU fixture now accepts DI/EI while delivering no interrupts; the
existing 17 BIOS-vector and disk-path contracts still pass. This controlled
Model 4 check does not substitute for native boot qualification.

### Corrected cpmsim workflows — PASS

- DUP FORMAT decline leaves every target byte unchanged. Formatting A is
  rejected as protected. Confirmed B format writes/verifies every raw byte as
  E5h; subsequent CHECK reports zero unreadable sectors.
- DUP COPY decline leaves both disks unchanged. Confirmed copy equals every
  source byte, source is unchanged, and subsequent CHECK reports zero
  unreadable sectors.
- SYSGEN exports the named BASE090.SYS package with exactly 161 records;
  its 160 payload records independently match the source's mapped system
  records, including saved startup. Export preserves source and output
  system area. Replacement decline preserves the entire output disk;
  confirmed replacement preserves package bytes and leaves no recovery names.
- Named installation decline preserves every target byte. Confirmed install
  preserves the entire target filesystem and an independently extracted
  user-7 sentinel, then the installed disk cold-boots and executes its saved
  startup and an explicit banner command. All observed prompts must be A0;
  a later valid redisplay cannot hide an invalid initial prompt.

All three cases verify all 30 shipped source files and check source/target
filesystems. Evidence: `/private/tmp/bettercpm-v017-fixed-cpmsim-media/` and
`/private/tmp/v017-fixed-cpmsim-media.log`. The tested cpmsim candidate SHA-256
is `8ea8a419901a1e6a62ef4f3d80af2e5635f851ac06bc8608fdeb7d5f6df2c4da`;
it matches the separately rebuilt second candidate byte-for-byte.

No permanent RAM increase: both platforms' BDOS (3454 bytes), BIOS (757),
gateway (248) and file loader (145) remain byte-identical to V010 production.
The Model 4 cold loader grows from 315 to 318 bytes inside its 512-byte slot;
cpmsim's first-record loader remains exactly 128 bytes. CONFIG's generated
fingerprint and cold-IOBYTE descriptor checks pass against the rebuilt media.

Fresh isolated distribution rebuild and real boot qualification pass on both
platforms. Both reports pass filesystem, included-file integrity, CONFIG
fingerprint and boot gates; no System Disk manifest omissions. cpmsim has
30 files/148 KiB free; Model 4 has 29 files/596 KiB free. Native Model 4 cold
startup, CPX LIST, VER and ED /VER complete normally.

Published evidence generation: `/private/tmp/bettercpm-v017-r2-distribution/release-17e28637d18c-b25e85846766`.
The first ordinary-permission native launcher attempt was blocked by macOS
LaunchServices; its log is `/private/tmp/v017-distribution.log`, not an OS
failure. The successful second build uses authorized native-launch permissions
and logs to `/private/tmp/v017-r2-distribution.log`. Native DUP/SYSGEN workflows,
broader utility recovery matrices, manual/device checks and final acceptance
remain open; these selected cpmsim results do not close stage 5.


## V018 — native named SYSGEN and controlled media-utility recovery

PR 378 contains V017. Continue against its independently built Model 4
System Disk, SHA-256
`58ef6d3e84ff367991d847f9939524785444ee7636bd4b38e1070d9f74f5b4f5`.
`run_validation_model4_media.py` keeps all shipped programs unchanged and
adds only a private SETBSYS helper using public disk-control calls to configure
B as a compatible SYSTEM destination. Source/target disks, command invocations,
screen captures and independently extracted packages are retained beneath
`/private/tmp/bettercpm-v018-native-media/`; aggregate log:
`/private/tmp/v018-native-media.log`.

### Controlled recovery and parser checks — PASS after stale test correction

Execute the existing emitted-code tests against the isolated V017 build, and
verify tested SYSGEN/DUP binaries match the manifest hashes. Provenance and
logs are retained in `/private/tmp/bettercpm-v018-controlled/`.

- SYSGEN's 24 export/package/failure cases pass: exact new/default/replacement
  output, decline, reserved recovery-name collisions, RO/SYS protection,
  read/create/write/close/verification/delete failures, partial and failed
  renames, final verification and retained backup, Ctrl-C, descriptor/pointer
  and geometry rejection, and the 36K boundary guard.
- SYSGEN's 32 command tails plus standalone/invalid combined version requests
  pass; invalid tails cannot enter either source loader.
- DUP's valid/invalid command parsing, direct engine dispatch, one-shot exit
  and standalone/invalid combined version requests pass.

The first parser runs fail only their hard-coded version expectations: they
expect SYSGEN Build 004 and DUP Build 003 while the manifest-qualified binaries
are Build 005 and Build 004. Replace those stale test literals with the shared
utility-version metadata. Retain both failed and corrected logs; no production
utility change is made. These controlled filesystem/BIOS fault fixtures do not
claim real physical fault injection or power-loss safety.

### Native named-package round trip — PASS

- Export BASE090.SYS on B: exact 161-record package, with all 160 payload
  records equal to the source system area. Output system area and every
  pre-existing output file/directory entry are unchanged.
- Install B:BASE090.SYS onto B itself after explicit Proceed confirmation.
  Package input is fully buffered; the containing disk's entire filesystem
  remains byte-identical. All installed payload bytes match the source except
  the documented binding normalization at offset 7030, E0h to A0h.
- The installed target cold-boots under native trs80gp and runs ED /VER.
  Independent audits preserve all 29 shipped files on both source and target;
  both filesystems check clean. The reference distribution hash is unchanged.
- Supplemental independent comparison confirms every source protected-system
  byte remains unchanged after export and installation; the sentinel also
  survives the installed-system cold boot. Evidence:
  `/private/tmp/v018-native-source-preservation.log`.

Successful result: `/private/tmp/bettercpm-v018-native-media/sysgen-r42k6jzl/result.json`.
There is no production OS change in V018. Broader native DUP, disk-source
SYSGEN, refusal/attribute/recovery matrices and deferred manual/device checks
remain open. These selected checks do not close utility validation.


## V019 — shipped native DUP physical-media workflows

PR 379 contains V018. Native DUP uses the unchanged V017 Model 4 System Disk,
SHA-256 `58ef6d3e84ff367991d847f9939524785444ee7636bd4b38e1070d9f74f5b4f5`.
`run_validation_model4_dup.py` preserves all shipped executables and adds only
a private public-API binding witness for bounded geometry/recovery fixtures.
Full-format coverage uses the default 80-cylinder, double-sided data binding;
copy/recovery coverage uses two cylinders and both sides, including a reserved
track, with a mismatched destination requiring temporary reconfiguration.

### Memory precondition / first attempt

The initial native run stops at the expected `DUP needs 51K of transient
memory.` diagnostic: the default monitor pair leaves only 50K. The native
screen was inspected; independent host comparisons confirm both disposable
B/C DMKs remain unchanged. Stop only the owned waiting test emulator and retain
this as an observation, not a passing disk-operation campaign. Evidence:
`/private/tmp/bettercpm-v019-native-dup/decline-eqcxg5tn/` and
`/private/tmp/v019-native-dup.log`.

The corrected runner unloads ADM3A, then M4SCRN, and explicitly captures
`No RSXs loaded` / `TPA available: 53K` before testing DUP. This follows the
engineering specification's 51K requirement; no OS or utility change is needed.
The intended cases are protected/declined operations, full interactive format
and direct CHECK, direct COPY with binding restoration, and a source CRC error
with unchanged destination and a one-error CHECK count. The subsections below record each completed native case and its independent
media checks; none of the preparatory or interrupted attempts is counted as a pass.

Documentation alignment note: the user guide's DUP `/VER` example still says
Build 002 and the consolidated engineering examples say Build 003; the
qualified utility is Build 004. Runtime memory requirements are
already documented correctly. Track this example for the separate documentation
alignment phase rather than changing executable version metadata to match it.

### Native refusal/decline — PASS

The corrected diagnostic run completes at
`/private/tmp/bettercpm-v019-r4-native-dup/decline-zvbc3u_8/`.
Its captures show 53K with no RSXs, physical-drive-zero protection, the FORMAT
B confirmation, the COPY B-to-C confirmation, and the final binding witness.
Both B/C DMKs compare byte-for-byte equal to their pre-operation images.
The entire A system area and all 29 shipped files are unchanged; the source
filesystem checks clean and the immutable baseline hash is unchanged.

Two intervening runner attempts were stopped while awaiting subsequent negative
case markers, and remain incomplete: `/private/tmp/bettercpm-v019-r2-native-dup/`
and `/private/tmp/bettercpm-v019-r3-native-dup/`. A short post-LIST interval did
not establish a completed warm return; increase that interval. The diagnostic
attempt also captures each negative confirmation before sending N, rather than
relying on a repeated generic `[Y/N]` marker that can remain on screen from an
earlier operation. Both expected prompts appear and the independent final
checks pass. These instrument attempts are not classified as OS failures or
passing disk-operation campaigns. Retain all aggregate logs in
`/private/tmp/v019*-native-dup.log`.

### Full default native format/check — PASS

`/private/tmp/bettercpm-v019-r4-native-dup/format-1dspirl5/` exercises the
interactive FORMAT menu, then direct `/CHECK B:` after normal menu exit.
DUP reports 160 surfaces written and verified. Independent decoding checks
all 1600 sector IDs (1–10 on each cylinder/side), 512-byte sizes, header CRCs,
data CRCs and every erased payload byte (E5h). CHECK reports zero unreadable
sectors. The unused C disk is unchanged. Source system area, all 29 shipped
files, filesystem integrity and immutable baseline hash are preserved.

### Native mismatched-format copy/check — PASS

`/private/tmp/bettercpm-v019-r4-native-dup/copy-rm0xw5s0/` runs direct COPY from
a two-cylinder, double-sided source onto a destination initially configured
single-sided. Patterned 128-byte portions detect stale/repeated cache data.
DUP reformats the required destination surfaces and verifies the copy.
Independent decoding checks all 40 copied physical-sector payloads and CRCs,
including the reserved track; destination bytes after those four surfaces
remain unchanged. The source DMK is byte-identical. The public-API witness
confirms the original destination binding is restored, CHECK reports zero
unreadable sectors, normal A0 return is captured, and source system area/all
29 shipped files/filesystem/reference hash remain unchanged.


### Native CRC failure and read-only CHECK — PASS

`/private/tmp/bettercpm-v019-r4-native-dup/crc-ovi54rwx/` corrupts only the data
CRC of physical sector ID 3 on the first source surface. COPY reports that CRC
error, does not claim completion, and stops before writing the destination.
The entire destination DMK remains unchanged, as does the source (including its
intentional bad CRC). The destination binding is restored. A subsequent CHECK
continues and reports exactly one unreadable sector, then returns normally.
Source system area, all 29 shipped files, filesystem integrity and immutable
baseline hash are preserved. This is a native emulator CRC-fault fixture, not
a claim about every real-floppy failure or power-loss scenario.

### Batch result and limits

All four selected native cases pass. Aggregate results:
`/private/tmp/bettercpm-v019-r4-native-dup/summary-all.json`; aggregate log:
`/private/tmp/v019-r4-native-dup.log`. Each result's runner identity matches
its retained executed source; every case preserves the 29 shipped files.
The first source-sector fixture is independently decoded before execution to
verify all 1600 ID/header/data CRCs and distinct sub-record payload patterns.
The damaged-source case then flips exactly one data-CRC byte.

No production OS/utility or permanent-memory change is made. The default 50K
monitor profile is insufficient for DUP by contract; all operation passes have
an explicit unloaded 53K witness. Remaining utility validation includes native
disk-source SYSGEN, broader protection/selector/interruption/recovery matrices,
other utilities and deferred manual/device work. Stage 5 is still partial.


## V020 — shipped native disk-source SYSGEN

PR 380 is merged according to the user. Continue with the unchanged V017
Model 4 System Disk, SHA-256
`58ef6d3e84ff367991d847f9939524785444ee7636bd4b38e1070d9f74f5b4f5`.
`run_validation_model4_sysgen_disk.py` retains the shipped SYSGEN and all other
release files; only private public-API helpers are added to configure B as
SYSTEM media and map logical C onto physical A/B for refusal checks.
The default monitor profile remains loaded; SYSGEN's 36K requirement fits it.
No runtime-source or permanent-memory change is made.

### Confirmation and physical alias safeguards — PASS

Native captures at
`/private/tmp/bettercpm-v020-native-sysgen-disk/sysgen-disk-odtam5mz/refusals/`
show the `SYSGEN A: B:` Proceed question, normal return after N, refusal when
B and C resolve to the same physical disk, and physical-drive-zero protection
when C aliases A. The complete destination DMK remains byte-for-byte unchanged;
the source's entire protected system area also remains unchanged.
These alias checks use distinct logical letters and real installed bindings,
not parser rejection of identical letters.

Confirmed installation and cold boot are reported separately below; these
refusal results are not counted as successful installation evidence.
Aggregate log: `/private/tmp/v020-native-sysgen-disk.log`.

### Confirmed disk-source installation — PASS

After the refusal checks, replace every destination system-area byte with A5h
while preserving its populated filesystem. `SYSGEN A: B:` still stops for
Proceed confirmation; only the following Y enables installation. The native
utility reports installation and verification complete. Independently compare
every installed system byte with the source: the only difference is the
specified boot-binding normalization at offset 7030, E0h to A0h.
The entire filesystem beyond 20,480 bytes is byte-preserved, including KEEP.TXT,
and the source protected system area is unchanged. Before/after raw images,
confirmation/completion captures and invocation are retained in the V020 work
directory. The final cold-boot/file-audit result follows below.


### Installed cold boot and file integrity — PASS

Boot a new native emulator instance directly from the installed B disk as
physical drive zero. Its saved startup loads the normal monitor pair, prints
the banner, and the installed ED /VER command completes at A0. The installed
protected area is unchanged by cold boot and KEEP.TXT survives. Independent
manifest/hash audits preserve all 29 shipped files on both source and target;
both filesystems check clean and the immutable baseline hash is unchanged.

Final result: `/private/tmp/bettercpm-v020-native-sysgen-disk/sysgen-disk-odtam5mz/result.json`.
The recorded runner hash matches the retained executed source. Refusal and
installation screens, exact before/after system bytes, file extractions, helper
listings and emulator invocations are retained with that result.

This completes the selected native explicit disk-source confirmation, alias
protection, payload/filesystem preservation and reboot workflow. It does not
claim fresh exhaustive interactive/cross-format/source-error/write-failure
coverage, real-floppy fault behavior or power-loss safety. Broader utility and
manual/device coverage remains open; system-wide validation is not complete.


## V021 — shipped cpmsim ERA selection, protection and destructive erase

Executed the unchanged V017 production System Disk with disposable secondary
media. The resident/transient runner completed 21 sessions: resident multi-user
selection and unconditional RO/SYS protection, unsupported-option `Use :ERA`
diagnostic, transient branch-specific explicit protection admission, negated
aliases, unattended RO skipping, one RO authorization with `/C`, quiet-mode
confirmation, cancellation, invalid input before mutation, duplicate DU scope,
per-file confirmation and exact-file confirmation. Independent directory reads
and surviving-file byte comparisons verified the results after each operation.

The destructive runner verified multi-extent allocated-block zeroing, exact
`E5 00 ... 00` directory scrubbing, cross-user shared-block preservation while
zeroing unshared blocks, explicitly admitted RO deletion with `/R`, empty-file
and batch deletion, cancellation with byte-identical media, and one combined RO
and destructive authorization. The shared-block fixture deliberately introduces
a cross-link before deletion; its surviving owner's block is checked byte for
byte. No modified ERA binary or injected BDOS wrapper is used in these runs.

Both runners audited all 30 shipped files against the manifest and immutable
baseline, and checked both System Disk and final secondary filesystems clean.
No production utility or OS change was required.

Evidence:
- `/private/tmp/bettercpm-v021-r2-era-protection/result.json`
- `/private/tmp/bettercpm-v021-era-destructive/result.json`

Each directory retains the executed runner, transcripts, fixture bytes, disks,
file audits and filesystem results. The initial ordinary run completed all
operation assertions but failed at the runner's final filesystem command because
`-n` followed the image argument; this was a harness error. The fresh r2 run
corrected option ordering and included the resident cases. It is the accepted
ordinary result.

Scope is selected shipped cpmsim utility workflows. Native Model 4 repetition,
injected I/O failures, raw-write recovery, physical devices and power-loss
behavior are not newly qualified here. Stages 4/5 remain partial; system-wide
validation is not complete.


## V023 — restored campaign and fresh shipped REN validation

After PR 382 merged, the temporary campaign checkout and retained evidence were
no longer present. Restored an isolated checkout at e1633a9 without modifying the
user's repository. The previously reported, unpushed V022 REN runner and evidence
were lost; the results below are fresh reruns, not recovered evidence. Historical
`/private/tmp` evidence links above should not be assumed to remain available.

Built and boot-qualified a fresh cpmsim System Disk from merged source:
`/private/tmp/bettercpm-v023-distribution/release-e1633a91c034-2bc6ff44e934/z80pack`. Image SHA-256: `8ea8a419901a1e6a62ef4f3d80af2e5635f851ac06bc8608fdeb7d5f6df2c4da`.
The manifest contains 30 files with 148K free. The build's boot, ED identity,
clock-provider and host-exit checks passed.

The unchanged disk passed 12 resident/transient REN sessions. Physical-directory
and extracted-payload checks verified all eight RO/SYS/ARC combinations,
multi-extent preservation, `/P`, safe default skips, byte-identical dry-run and
invalid-option media, collision help/invalid replacement/confirmation,
destination-ledger behavior, both operand orders and compound users. Resident
REN preserved multi-extent contents, skipped explicitly selected RO/SYS files
and reported `Use :REN` for `/P`. Unattended collisions preserved both files.
All 30 shipped files remain unchanged; all three final filesystems check clean.

Evidence: `/private/tmp/bettercpm-v023-ren-media/evidence.json`, including executed
runner, transcripts, images and extracted-file comparisons. Version checks use
utility metadata rather than the inherited test's stale Build 005 expectation.

Four controlled suites passed against the fresh isolated build after its
REN.COM hash was matched to the manifest: `test_ren_failure.py`,
`test_ren_protection.py`, `test_ren_workflow.py`, `test_ren_collision.py`.
They cover retry/help/skip/abort, target races, read-only drives, attribute repair
failures, mixed extents, policy precedence and collision input handling.
Logs: `/private/tmp/bettercpm-v023-ren-faults/`. These are BDOS fixtures, not
injected physical media failures. No production fix was needed. Native repetition
and broader media fault coverage remain open; validation is incomplete.


## V024 — shipped cpmsim COPY/MOVE media validation

Fifteen sessions on disposable copies of the fresh V023 System Disk passed:
resident source-first and assignment COPY; transient `/B /V` wildcard copy
including all eight RO/SYS/ARC combinations and a 33,280-byte multi-extent
binary; skip-existing immutability; verified writable replacement; read-only
target protection; self-copy refusal; compound ARC/not-SYS predicate; empty-file
verification; invalid trailing option, overlong destination and invalid drive
domain before mutation; successful resident MOVE; read-only source refusal;
and collision refusal. Independent extracted payloads and per-extent attributes
were checked. Successful MOVE removes its source only after producing the
expected destination; refused RO/collision moves leave both disks byte-identical.
All commands return to A0. No MOVE.COM is shipped; these MOVE checks exercise
the resident implementation.

All 30 shipped files remain unchanged against the manifest. The System Disk and
both final secondary filesystems check clean. Accepted evidence:
`/private/tmp/bettercpm-v024-r2-copy-move/result.json`, retaining executed runner,
commands, transcripts, fixtures, extracted files and disks. The first run stopped
on an obsolete test expectation that RO MOVE should copy then fail to delete;
the current resident contract instead rejects the source during preflight.
The fresh r2 run verifies complete media preservation for that refusal.

Against the manifest-matched fresh COPY binary, `test_copy_mapping.py` and
`test_copy_reporting.py` passed (positional mapping/conflicts, allocation maps
and unsigned decimal boundaries). Logs: `/private/tmp/bettercpm-v024-copy-core/`.
`test_copy_filespec.py` initially failed looking up BC_CVALID in resident RCP:
resident COPY now uses the shared selector and that private symbol is absent.
The test now explicitly covers only the transient validator/options; it passes
against the same fresh build. Resident shared-selector behavior is covered by
public media tests rather than pretending the removed private routine ran.

No production change was required. These checks do not newly qualify native
Model 4 repetition, injected read/write/close/verification failures, interactive
COPY recovery or power-loss behavior. Broader recovery coverage and remaining
utilities remain open; system-wide validation is incomplete.


## V025 — controlled cpmsim COPY verification and I/O failure recovery

Ran `test_z80pack_copy_verify_flow.py` and `test_z80pack_copy_errors.py` using
private copies of the fresh V023 release. Both tests used the isolated build at
`/private/tmp/bettercpm-v023-work/z80pack` after its unmodified COPY.COM SHA was
matched to the release manifest. Test-only binary changes inject failures;
this is not a claim that the unchanged shipped binary encountered physical
hardware errors. No production code was changed.

Verification flow passed normal multi-extent copies, rejected option combinations,
unattended comparison failure, help and invalid recovery input, skip, Ctrl-C
cleanup, ordinary copying without `/V`, batch continuation and successful retry.
Source contents survived and successful destinations retain the expected RO/SYS
attributes. Evidence: `/private/tmp/bettercpm-v025-verify-flow/evidence.json`.

Five one-shot I/O cases passed: source read failure, destination write failure,
close failure, disk-full stop and incomplete-destination cleanup failure.
Successful preceding files remain intact; failed partial outputs are removed
unless cleanup itself fails; later files continue for recoverable errors and
stop for disk-full/cleanup failure. Source ARC handling matches successful versus
failed/stopped files, failure accounting is correct, and execution returns A0.
Evidence: `/private/tmp/bettercpm-v025-r2-copy-errors/evidence.json`.

The error test now checks copy-out exit status only for expected surviving files,
and independently checks existence for absent ones. A preliminary assertion
incorrectly required cpmcp to return nonzero for a missing wildcard match; this
host version returns zero without creating a file. That trial stopped during
postcondition checking, not during guest recovery. The fresh r2 run is accepted.

Each accepted directory retains its executed test source, test binaries, media,
transcripts and evidence. To reproduce, stage release copies as drives a..d with
its diskdefs, import each test module from the current tools directory, set its
ROOT to the manifest-matched isolated build and invoke main with --image-dir
pointing at that runtime and --report pointing at a fresh directory.

Independent audit `/private/tmp/audit-v025.py` checked all other 29 shipped files
in all six test environments against manifest hashes; COPY.COM is explicitly
excluded because fault injection replaces it. All final disks check clean with
fsck.cpm and the immutable release image hash is unchanged. Audit summary:
`/private/tmp/bettercpm-v025-audit.json`. These controlled tests do not qualify
real-floppy faults, native Model 4 repetition or power-loss behavior. Validation
remains incomplete.


## V026 — shipped DIR/WHEREIS/STAT scopes, extents and attributes

Fifteen sessions on disposable copies of the V023 cpmsim System Disk passed.
Resident DIR rejects /WHEREIS with Use :DIR. Transient global search finds each
logical multi-extent file once across B0, B3 and C31. Drive-only qualification
inherits current user; B[-] expands users; SYS predicates filter correctly.
No-match output and invalid option combinations are distinguished. Resident and
transient ordinary DIR list both an empty and multi-extent file once. STAT
reports the latter as 260 records, 34K allocated and two physical entries.
All reporting leaves both secondary disks byte-identical.

STAT $R/O, $SYS, $R/W and $DIR changes match independently constructed full-disk
expectations: only the requested attribute bit changes across both selected
physical extents. Payload bytes, other users/files and the second disk remain
unchanged. All 30 System Disk files match the release manifest; its filesystem
and the ordinary secondary filesystem check clean. Accepted evidence:
`/private/tmp/bettercpm-v026-r3-dir-stat/result.json` with executed runner,
transcripts, media, file audits and filesystem checks.

Host fsck.cpm rejects valid BetterCP/M user 31 as CP/M 2.2 status 1F. The C31
fixture is independently proven unchanged; allocation/connectivity is checked
on a separate copy changing only its directory user byte from 31 to unused
user 15. The original is preserved. The JSON explicitly records this narrower
filesystem-check scope; this is not a claim that host fsck accepted user 31.

The first run used $RO (selector spelling) instead of STAT's $R/O update syntax;
STAT correctly rejected it. The corrected r2 passed operations but stopped on
that host fsck limitation. The fresh r3 run includes both harness corrections
and passed completely. No production behavior changed.

Two controlled tests also passed against manifest-matched fresh binaries:
`test_dir_whereis.py` covers scope, attributes, extent deduplication, ordering,
bounded memory and recoverable BIOS open/read errors with Search incomplete;
`test_z80pack_stat_files.capacity_probe()` covers EXM=0 extent collapsing,
384-summary capacity and overflow. Evidence:
`/private/tmp/bettercpm-v026-whereis-fixture/result.json` and
`/private/tmp/bettercpm-v026-stat-capacity/result.json`.
These are controlled fixtures, not physical hardware failures. Native repetition
and remaining utility/device recovery checks remain open; validation is incomplete.


## V027 — shipped TYPE navigation and controlled read recovery

Four private cpmsim sessions on the unchanged V023 System Disk passed long
cross-file paging, forward/backward file jumps, final-EOF bounds/bell, short
files with an empty middle file, tab expansion and resident ordinary output.
RO/SYS source fixtures remain readable. The complete secondary source image is
byte-identical after all sessions; all 30 shipped System Disk files match the
manifest and both final filesystems check clean. Evidence:
`/private/tmp/bettercpm-v027-type/result.json`, with executed runner, fixtures,
transcripts and disks. These stream-level checks supplement the earlier rendered
monitor/backend first-row checks; they do not newly claim visual screen placement.

Four controlled fixture suites passed against manifest-matched TYPE.COM and
RCP.CPX from the fresh isolated build: test_type_streaming, test_type_paging,
test_type_files and test_type_limits. Coverage includes shared selection,
transforms, EOF/record boundaries, open/read-error reporting and continuation,
bidirectional replay/history reconstruction, anchor-based file jumps, empty
files, cross-DU ordering, row arithmetic, 65,535-file selection bounds and
private stack guards (30/128 bytes observed). Evidence and retained test sources:
`/private/tmp/bettercpm-v027-type-fixtures/result.json`.

Two initial fixture failures were harness issues: streaming expected obsolete
Build 005 rather than metadata-owned Build 006; paging ignored the isolated build
root for its listing. Both tests were corrected and rerun successfully. No
production OS or TYPE change was required. Controlled BDOS fixtures do not
qualify real-media failure behavior.

Remaining stage-5 work includes filling the ED/CONFIG failure-recovery matrix,
remaining PIP/device and SUBMIT/TIME/VER/CPX/RSX utility cases, and explicit
cross-platform repetition/applicability decisions. Previously recorded manual
and hardware-only suite gaps remain deferred. This batch does not close core
acceptance: final clean rebuild/reruns and reviewed coverage closure remain.


## V028 — ED/CONFIG controlled failure recovery

Nine assembled-code suites passed through
`tools/run_validation_ed_config_recovery.py`. ED.COM and CONFIG.COM were first
matched to the V023 release manifest; EDDEV.COM was separately verified
byte-identical to shipped ED.COM. Fixtures execute those binaries with controlled
BDOS/BIOS return values. No OS or utility production code was changed.

ED checks cover setup ordering, existing destination and create failures,
source/output DU isolation, protected files, read/write failures, attempted
recovery close (including failed close), exact diagnostics and caller DU/DMA
restoration. Save-drain failures retain unaccepted text. Publication tests check
close-before-rename ordering and both rename-failure boundaries, preserving the
remaining original/backup/work files under the documented DRI-bug correction.
Transfer tests cover pending/deferred data, cleanup and write failure.

CONFIG checks cover startup save with failed first or second writes, successful
restoration and failed rollback warnings; saved IOBYTE decline, validation,
read/write/verification/rollback failures, supported-device gates and live
IOBYTE preservation. CRC-32 oracle vectors, masked editable fields, immutable
byte corruption, geometry/layout rejection and disk-read failures pass. Invalid
saved-image cases retain original rollback data and avoid writes/prompts where
specified. Failed rollback is not reported as successful restoration.

Accepted result: `/private/tmp/bettercpm-v028-r2-ed-config/result.json`.
The directory retains the executed runner and test sources, helper hashes,
manifest-matched program hashes and individual logs. Earlier exploratory logs
in `/private/tmp/bettercpm-v028-ed-config/` also pass, but r2 is the complete,
repeatable nine-suite batch. The runner takes --build-root, --baseline and a
fresh --output directory; it does not rebuild or replace release binaries.

This is controlled instruction-level recovery coverage, not native Model 4
fault injection, physical hardware failure or power-loss qualification. Native
combined CONFIG save/rollback and broader live ED recovery repetitions remain
explicitly unclosed. Remaining PIP/device and SUBMIT/TIME/VER/CPX/RSX coverage,
reviewed exclusions and final acceptance reruns also remain. System-wide
validation is incomplete.
