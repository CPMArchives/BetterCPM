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
| 2. Fresh conformance suite | Partial cpmsim groups pass | Fresh ENTRYTST, CPUTEST, ECOTEST, BDOSTEST required, DIRTEST safe, FILETEST required and RANDTEST safe results below. Console, disk/BIOS/error/CCP procedures and Model 4 suite runs remain. |
| 3. CPX/RSX lifecycle, relocation, ROM protection | Protected ROM candidate campaign passes | Fresh V002 guarded ROM, lifecycle, workspace and stack results below; wider RAM/native lifecycle coverage remains. |
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
