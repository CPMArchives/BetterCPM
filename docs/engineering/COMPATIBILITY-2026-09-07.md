# BetterCP/M compatibility pass — 2026-09-07

Current follow-up results are in [the September 8 qualification report](COMPATIBILITY-2026-09-08.md). The original baseline is retained below. See **Repair and regression pass** at the end for the corrected build.

This is a development baseline, not release certification. All 12 executables were exercised on disposable trs80gp Model 4 media. No BIOS, BDOS, or suite binaries were changed during testing. The pristine boot image hash was checked unchanged after the runs.

## Reproducibility

- BetterCP/M base: `5889fdc4be3473bd2ae4b954608ae25bfa3404a9`, with the existing uncommitted CONFIG H work in the image; this was not a clean release build.
- Suite: `1443bc12cc9a55c9a117ea2be71777998aa4fd2d`; published source/COM checksums verified when building the image.
- Emulator: local trs80gp, Model 4, batch/turbo; original mounted user disks were not touched.
- A: 80-track DS 780 KiB allocation system format. B/C/D: matching 800 KiB DATA geometry. B includes BDOSTEST.COM and BDSA/BDSB; C has BTBFILE.DAT.
- D is empty normally; full-data and full-directory cases use separate appropriate fixtures. Those fixtures are not interchangeable.
- Evidence: `build/compatibility/{captured,followup}/`, including intermediate raw screens, decoded screens, final screens, and run outcomes. These are sampled screen captures, not guaranteed lossless serial transcripts.
- `build/compatibility/ledger-results.json` preserves counted rows and evidence references. `test-manifest.json` records input identity.
- Repeatable harness: `tools/run_compatibility_capture.py`. New runs receive separate timestamped directories.

## Captured results

The retained evidence resolves 466 distinct ledger entries: 254 pass, 9 fail, 95 observations, 101 explicitly not run/out of scope/profile, 5 mixed batch/isolated results, 1 blocked, and 1 inconclusive. This is not a claim that the other ledger entries passed or were executed. The 627-item catalog includes manual and profile requirements; screen sampling also missed some fast output. Suite summary totals are not used.

| Utility | Pass | Fail | Observation | Not run | Mixed/blocked/inconclusive |
|---|---:|---:|---:|---:|---:|
| BDOSTEST | 56 | 0 | 14 | 16 | 0 |
| BIOSTEST | 16 | 1 | 11 | 14 | 0 |
| CCPTEST | 3 | 0 | 3 | 15 | 0 |
| CONSTEST | 2 | 0 | 0 | 0 | 1 |
| CPUTEST | 2 | 0 | 1 | 2 | 0 |
| DIRTEST | 44 | 0 | 15 | 8 | 5 |
| DISKTEST | 9 | 2 | 1 | 4 | 0 |
| ECOTEST | 1 | 0 | 3 | 4 | 0 |
| ENTRYTST | 18 | 3 | 15 | 15 | 0 |
| ERRTEST | 3 | 2 | 12 | 23 | 0 |
| FILETEST | 68 | 0 | 16 | 0 | 0 |
| RANDTEST | 32 | 1 | 4 | 0 | 1 |

## Findings requiring engineering work

- **0345:** out-of-range random write returned success (00). Reproduced with the isolated detailed report. **0346** then makes no visible progress both in the random-I/O batch and in isolation; timeout is not a failure verdict.
- **0407, 0582:** logical random-write range refusal and the dependent recovery/meta-check fail in ERRTEST.
- **0602, 0603, 0605:** Function 40 scratch-FCB/write-zero-fill/result checks fail individually.
- **0275, 0276:** full-data-disk growth/result oracles fail with prepared full media.
- **0458:** BIOS WRITE type-code lifecycle fails in the controlled batch and isolated check.
- **0545, 0546, 0559, 0561, 0566:** directory batch-state failures; all five pass on clean images individually. Preserve both results and investigate the batch transitions.
- **0106:** observed buffered input was correct (count 02, AB), but the later confirmation returned before scripted Y. Do not treat that operator-result row as a proven buffer defect.

## Fixture corrections and suite reporting problems

- The initial no-secondary-disk pass produced spurious drive/login failures. The corrected B/C/D run passes these checks.
- BDOSTEST 0194 expects a COM match on B. Adding BDOSTEST.COM to that fixture removes the failure; corrected BDOSTEST has 56 required passes, 14 observations, and 16 unperformed/scope/profile rows.
- FILETEST 0253 and RANDTEST 0556/0557 pass with their required directory-full D disk. Initial failures on empty D are excluded.
- Failure-list routines in ENTRYTST, BDOSTEST, DISKTEST and related utilities retain B across BDOS output calls. B is a documented return alias (B=H), so it cannot serve as an unprotected loop counter. The result is garbage after valid failure numbers. Example: ENTRYTST PRINTFAILS loads B before calling PUTS, which calls BDOS 9 without preserving BC. No suite code was patched in this run.
- BDOSTEST also prints 70 passes where its rows contain 56 required passes plus 14 observations. Count the rows, not that summary.

## Additional controlled checks completed

- 0464: cold BOOT restored the public environment and CCP on A.
- 0465: warm BOOT resumed at the requested drive.
- 0466: warm BOOT repaired deliberately damaged page-zero gateways.
- 0468/0469: real console readiness/nonconsumption and controlled K input.
- 0470: logical CONOUT/LIST/PUNCH argument behavior through the suite intercepts. This does not certify physical printer/punch output.
- 0473: raw BIOS TAB versus formatted BDOS TAB.
- 0456: traced application/directory DMA addresses.
- CONSTEST 0052/0082: observed output A and nonblocking no-input return 00, followed by affirmative confirmation.

## What the user still needs to complete

Do not repeat the automated failures manually yet. Fix the core failures and suite reporting/batch issues first, then rerun the baseline. The remaining operator work is:

1. **Console and editing:** run CONSTEST selected items with its printed keystrokes, checking echo, cursor placement, TAB/backspace/DEL, line editing, pause/resume, Ctrl-C, and printer echo. In particular repeat 0106 with real keyboard input and confirm the AB/count-02 result. Record actual observations before answering Y.
2. **Write protection and recovery:** BIOSTEST /0457 on a disposable blank disk; choose its drive and consent, turn emulator write protection on only at the fault prompt, then off when requested. This verifies a genuine failed BIOS write and subsequent recovery.
3. **READER providers:** BIOSTEST /0471 requires a provider returning R and a separately verified immediate-EOF provider. Do not use an unverified blocking provider or assume MM STAT assignments exist in BetterCP/M. Remains blocked until those providers are available.
4. **Physical output:** printer/punch/reader routing and captures for CONSTEST, with declared devices; logical-vector interception alone is insufficient.
5. **Resident-command transcripts:** CCPTEST and ECOTEST manual command/termination procedures, including LOAD/SAVE/TYPE and batch submission semantics, once the CCP milestone is ready. BASIC.CPX supplies standard commands. These are not all BIOS/BDOS release blockers.

## Work still belonging to engineering, not the user

- Finish fault-provider coverage for ERRTEST read/write/retry/abort/recovery. Do not ask the user to simulate these by merely causing a logical file error.
- Test BIOSTEST 0453 on a blank medium configured with a SYSTEM DPB having nonzero OFF; the DATA scratch disk used here cannot establish it.
- Complete unobserved ledger rows with reliable continuous capture, rerun random-I/O cases after fixes, and resolve directory batch-state differences.
- Qualify z80pack separately. This pass covered trs80gp only. RomWBW remains unported/untested.
- ROM write-protection, RSX lifecycle and persistent-DATA qualification remain separate core engineering checks.

The boot disk and every test working image remain in build/compatibility. Use fresh copies for further tests.

## Repair and regression pass

The nine reproducible failures are fixed: 0345, 0407, 0582, 0602, 0603, 0605,
0275, 0276 and 0458 all pass. The five mixed DIRTEST rows (0545, 0546, 0559,
0561, 0566) also pass in the complete batch after repairing suite cleanup.
0346 passes with a nearly full system disk and a longer capture allowance.
Its silent write-until-full run took about 149 seconds even with just two
allocation blocks initially free; the previous 60-second unchanged-screen
cutoff was insufficient. This is a harness timeout, not evidence of a hang.

### Core changes

- Reject nonzero R2 with random-I/O result 06h before modifying the FCB.
- Preserve dirty random-write extents before decoding/reopening another
  position; unclosed writes and Function 40 data must not disappear.
- Initialize a new extent at the shared creation point, so random
  and sequential paths both start with an empty allocation map.
- Return allocation-full result 02h and avoid publishing an empty new extent
  when no data block is available; failed growth preserves the old file size.
- Normalize successful record positioning to zero, including the Function 40
  zero-fill path.
- Supply BIOS WRITE type 2 for the first record in a newly allocated block,
  including zero-fill initialization; retain type 0 for ordinary data and
  type 1 for directory writes.

The BDOS is **3,386 bytes**, four bytes smaller than the baseline, and still
fits its original 3,390-byte region. No memory boundaries moved. The advertised
TPA remains **54,273 bytes (53 KiB plus one byte)**. The full TPA overwrite test
passed, including BDOS survival, warm boot, CPX reconstruction and resident RSX
survival. The production-code unit harness now reads the actual production
BDOS binary; its stack high-water check observed 20 of the reserved 32 bytes
with the fixture platform leaves.

### Independent suite repairs

The suite now preserves failure-list counts and pointers across console calls,
and separates observations from required-pass totals. DIRTEST 0294 and 0307
restore the incoming default drive instead of selecting B on exit. This was
the cause of later batch-only fixture failures. No test oracle was relaxed.
The eight changed COMs and their source checksums were rebuilt with ZSM4 and
DRI LINK under z80pack. The companion repository documents these changes in
`docs/REPORTING-FIXES-2026-09-07.md`.

### Regression evidence and repeat procedure

The corrected image is `build/compatibility/BetterCPM-Compatibility-Final.dmk`.
Its identity and retained build logs are in
`build/compatibility/fix-validation/manifest.json`. All runs used private copies.
Final emulator captures are in `run-20260907-211115` and
`run-20260907-211227` under `build/compatibility`.

The extra `tools/test_random_io.py` regression checks complete zero records,
the requested payload, unclosed writes across extent boundaries, subsequent
reads, close/reopen persistence and file size on a real emulator disk. It
passed. Its FCB templates explicitly initialize all bytes; assembler DEFS
space is not assumed to contain zeroes.

To repeat: rebuild the suite with its documented ZSM4 builder; run
`tools/build_complete_system.py`, then `tools/build_compatibility_disk.py
--system-only --output build/compatibility/BetterCPM-Compatibility-Final.dmk`.
Run `tools/test_unified_bdos.py`, `tools/test_random_io.py` and
`tools/test_packed_tpa.py`. Set BETTERCPM_TEST_IMAGE to the corrected image when
using `tools/run_compatibility_capture.py` for the independent suite.

This closes the observed core failures, not the complete 627-item release
qualification. The console 0106 operator confirmation remains inconclusive;
the manual console/device and controlled fault-provider work listed above
still applies. No ROM, date/time, RomWBW or full z80pack-port qualification is
implied by this pass.

Final selected-run totals (required passes; observations reported separately):

| Run | Pass | Fail | Observations |
|---|---:|---:|---:|
| BDOSTEST /ALL | 56 | 0 | 14 |
| ENTRYTST /ALL | 25 | 0 | 16 |
| DIRTEST /ALL | 49 | 0 | 15 |
| FILETEST /ALL | 68 | 0 | 16 |
| RANDTEST /GROUP:LIFECYCLE | 6 | 0 | 4 |
| RANDTEST /0345 and /0346 | 2 | 0 | 0 |
| DISKTEST /ALL, prepared D | 11 | 0 | 1 |
| BIOSTEST /0458, controlled D | 1 | 0 | 0 |
| ERRTEST /GROUP:AUTOMATIC | 5 | 0 | 0 |

Manual, profile and out-of-scope rows are omitted from this compact table.
`build/compatibility/fix-validation/fixed-items.json` links each repaired or
resolved item to its final evidence. The corrected disk SHA-256 is
`9521f154e9803246a7b611cd6bc69bb54ffb5e431e024157141f99162f5398b6`.
