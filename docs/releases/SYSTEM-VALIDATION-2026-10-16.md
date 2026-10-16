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
| 2. Fresh conformance suite | Partial groups pass on both platforms | Fresh ENTRYTST, CPUTEST, ECOTEST, BDOSTEST required, DIRTEST safe, FILETEST required and RANDTEST safe results below. Selected console, disk/BIOS/error and native Model 4 checks also pass below; remaining cases and CCP procedures are still pending; V004 is open below. |
| 3. CPX/RSX lifecycle, relocation, ROM protection | Protected ROM candidate campaigns pass | Fresh V002/V003 guarded ROM, lifecycle, workspace and stack results below; wider RAM/native lifecycle coverage remains. |
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

### V004 — open: cross-user command loads stop at a physical extent

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

V004 remains an unresolved validation blocker. The correction must retain the
lookup user for every extent read while still restoring the caller before
program entry, on failure and for lifecycle callbacks. Load-abort context and
the fixed resident-memory/stack budgets must also be checked; moving restoration
without qualifying those paths would be insufficient. No production change for
V004 has been made in this tranche. Fresh conformance remains incomplete.
