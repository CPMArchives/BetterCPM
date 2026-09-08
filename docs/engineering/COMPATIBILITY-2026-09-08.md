# BIOS/BDOS and command-environment qualification — 7–8 September 2026

Follow-up: [media-change protection](MEDIA-CHANGE-PROTECTION.md) repairs 0143 on a later image. The results below remain the historical campaign snapshot.

Further focused follow-up closes 0509 and 0471.  The full campaign table below
remains a historical snapshot until the requested clean consolidated rerun:

- `tools/test_ret_termination.py` proves that entry RET bypasses a temporary
  page-zero WBOOT hook and restores a usable CCP, closing 0509.
- `tools/test_z80pack_reader.py` runs BIOSTEST 0471 under z80pack.  Its first
  stage reads `R` from cpmsim's host-fed READER stream; its second stage, on a
  fresh emulator process with no sender, returns immediate Ctrl-Z.  BIOSTEST
  reports `0471 P R READER returned R; absent READER returned Ctrl-Z`.

This supersedes the outstanding-test inventory in [the initial September 7 report](COMPATIBILITY-2026-09-07.md). It is a development qualification campaign, not a release certificate. The remaining required cases have now been investigated: 413 pass, 11 fail, and 6 are blocked by missing supporting functionality. No REQUIRED case remains merely unrecorded or awaiting routine operator input.

The catalog has 627 entries, including 430 REQUIRED entries. These numbers count distinct requirements, not executions or assertions. The prior inventory had 273 REQUIRED passes; this campaign adds 140 passing requirements. Passing narrow checks does not cancel a failing broader requirement.

## Results and reproduction

- [Complete 627-entry ledger](COMPATIBILITY-2026-09-08.tsv): per-item classification, verdict, rationale, and local evidence location.
- [Manifest](COMPATIBILITY-2026-09-08-manifest.json): source, probe, COM, image and evidence SHA-256 identities.
- [Retained evidence archive](COMPATIBILITY-2026-09-08-evidence.tar.gz): reviewed textual observations and result records. Disk images remain under `build/compatibility/`; the archive does not contain all mutable disk images.
- Final qualification image: `build/compatibility/BetterCPM-Compatibility-Qualification.dmk`, SHA-256 `98568349d0c8865b3e37522d4e3985283b2a96bc14eae5585dae5b0753ce3348`.
- BetterCP/M base commit `5889fdc4be3473bd2ae4b954608ae25bfa3404a9`; compatibility-suite base `1443bc12cc9a55c9a117ea2be71777998aa4fd2d`. Both have uncommitted development changes, including changes predating this campaign.
- Target: trs80gp Model 4, private batch/turbo processes with disposable media. These results do not qualify the z80pack or RomWBW hardware adapters, ROMability, real floppy timing, or physical peripherals.

The suite was rebuilt with ZSM4 and DRI LINK under z80pack. All thirteen programs assembled without errors. The companion suite repository records reporting and cleanup repairs in `docs/REPORTING-FIXES-2026-09-07.md`. ERRTEST's Close oracle was corrected from zero-only to the documented success range 0–3; the corrected 0408 and 0582 cases pass.

`tools/run_compatibility_capture.py` runs suite cases. The CCP, console, BIOS-boundary, media-change, load-boundary, and provider tools retain additional observations. The two review scripts and summarizer merge executed evidence without treating a not-run row as a pass. Review scripts reference retained historical campaign directories; reproducing the exact merge requires that evidence. A new campaign must review its own new observations rather than copy the old verdicts.

## Repairs demonstrated and retested

- BIOS backspace now moves left without erasing or crossing the left margin.
- Cold BOOT resets the drive/default disk state before warm reconstruction. Spoiled page-zero gateways and nondefault DMA were exercised.
- BDOS write-protected drive operations now take the Disk R/O warm-start path. Six mutation cases left their protected images unchanged.
- Directory-cache flushing preserves the requested next record number. A wildcard erase that formerly skipped entries now erases all selected user-0 files across directory records, preserving user-1 files.
- Blank and SPACE-only command lines return to the prompt without a spurious error.
- BASIC.CPX DIR reports the actual selected drive, rather than a filename letter mistaken for a drive.
- COM loading uses a staging record and checks its destination before copying. Oversized and failed loads do not execute or prepare default transient FCBs. Successful EOF prepares the FCBs/tail and executes the complete image.

Focused BIOS tests pass all 17 vectors, character transport, 80 logical-record reads/writes, error returns and translation. The unified BDOS regression passes, including independent directory-full/allocation-full cases; its measured private stack high-water is 22 bytes. Final CCP parsing/dispatch and full-TPA overwrite/reconstruction tests pass. File, directory, random-I/O, console, reset, and automatic logical-error suite reruns are retained in the ledger.

## Memory and load capacity: an unresolved release blocker

The memory map still exposes 54,273 bytes from 0100h to its advertised upper TPA boundary, and the full overwrite/warm-reconstruction test passes, including a loaded RSX. Resident BDOS uses 3,390/3,390 bytes; BIOS uses 638/638 bytes. Neither has spare bytes in its present allocation.

**This does not mean that the ordinary COM loader can safely load a 53 KiB file.** With BASIC.CPX loaded, its running CCP begins at C001h. The guarded loader accepts 382 records (48,896 bytes, 47.75 KiB), and rejects a 383-record image. Before the repair, the latter overwrote the CCP and still began executing. The test now demonstrates safe rejection, not restored full-size loading.

A loader that remains executable while the CCP/CPX area is overwritten, with a safe failure/reconstruction path, is still needed to realize the full advertised COM loading capacity. Do not describe the core as finalized or the 53 KiB loading target as achieved on this evidence. This engineering gap is additional to the counted failed predicates: the narrow resident-protection predicate passes because an unsafe load is rejected.

## Non-passing REQUIRED cases

| Items | Result | Finding / prerequisite |
|---|---|---|
| 0143 | Fail | A logged removable drive with nonzero DPB CKS accepted a different healthy directory and remained writable. Media-change read-only handling is missing. |
| 0392 | Fail | Assembled read and write engines return after one declared recoverable seek failure. They do not implement the required retry policy. This instrument tests control flow, not real controller timing. |
| 0393, 0394, 0405, 0581 | Fail | Final BIOS physical failures return to the BDOS caller instead of presenting the Bad Sector operator path and suspending the interrupted operation. Logical error results pass separately. |
| 0395, 0396, 0397, 0586, 0587 | Blocked | Ignore/abort/restart choices cannot be exercised until the physical-error operator path exists. |
| 0471 | Blocked | Absent-reader EOF is tested; a normal assigned reader device/provider is unavailable in this target profile. Logical device-vector instruments are not claimed as normal-reader hardware qualification. |
| 0509 | Fail | Instrumented entry RET invokes the public WBOOT gateway. All three termination mechanisms restore a usable prompt, but stock RET-without-WBOOT semantics are not met. |
| 0578 | Fail | USER accepts 16–31. This is an intentional BetterCP/M extension; it was preserved rather than removed to satisfy the stock range predicate. |
| 0612 | Fail | STAT device-assignment utility is absent from the distribution. |
| 0620, 0621 | Fail | SUBMIT and XSUB are absent from the distribution. |

No routine manual console testing is being handed back to the user. Normal reader qualification needs a suitable target device/provider; the other blockers require engineering work or an explicit compatibility-profile decision. The core release work should address disk recovery/media-change handling and full-size loading before treating BIOS/BDOS as finished. Distribution utilities remain a separate milestone.

## Evidence limitations and excluded trials

The ledger combines baseline and later affected-case retests; not every case was rerun on the final image. Changes were followed by focused and relevant broader regressions. It is not a clean-tree, single-image certification run.

Screen snapshots are sampled rather than a lossless serial transcript. Some checks use declared public-vector or service-result providers; their scope is recorded rather than presented as physical-device testing. Controlled read/write status tests complement these with actual emulator media operations.

Early media-removal trials omitted trs80gp's eject confirmation flag and did not remove the disk; they are excluded. Initial mixed-case input fixtures exceeded assembler line length and were rebuilt with bounded data lines. The first SAVE fixture incorrectly assumed TPA content survived warm reconstruction; its replacement primes the memory immediately before SAVE. The initial media-change probe had uninitialized FCB fields; the corrected probe verifies both original and replacement directories. The earlier oversized-COM run is retained as a demonstrated pre-repair failure. These invalid/intermediate trials do not contribute passing verdicts.

## Subsequent COM-loader repair

The historical 47.75 KiB limit above is superseded by the
[full-TPA COM loader](FULL-TPA-COM-LOADING.md). Historical campaign results are
retained unchanged; see the follow-up for new tests and their scope.
