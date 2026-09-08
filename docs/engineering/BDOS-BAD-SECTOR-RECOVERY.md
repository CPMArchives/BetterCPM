# BDOS Bad Sector Operator Recovery

Status: implemented and targeted qualification passed, 08-Sep-2026

## Result

The production BDOS now keeps logical file results separate from exhausted
physical BIOS errors.  The BIOS performs its controller retries first.  If a
read or write still fails, the BDOS prints `Bad Sector` and waits for the
operator:

- any ordinary key ignores the physical error and resumes the interrupted
  BDOS path, following CP/M 2.2 behavior;
- Control-C abandons the interrupted caller and enters BIOS warm boot;
- an abort clears the dirty-directory flag before warm boot, preventing a
  failed directory write from being flushed while the CCP is reconstructed.

All physical reads and writes use the same two wrappers.  This includes
sequential and random record I/O, zero filling, directory reads, and directory
writes.  Logical EOF, disk-full, read-only, and range results remain ordinary
BDOS return values and do not enter the operator path.

## Conformance cases

| Case | Requirement | Qualification |
|---|---|---|
| 0393 | Separate logical results from physical failures | logical paths retain their results; injected physical failures enter the operator handler |
| 0394 | Present the Bad Sector path | emulator capture stops at `Bad Sector` |
| 0395 | Ignore a physical error | read and write callers resume only after an ordinary key |
| 0396 | Abort a physical error | Control-C enters warm boot |
| 0397 | Define the restart destination | abort restarts at the CCP |
| 0405 | Preserve sequential-write logical results | disk-full remains a logical return; physical write failure uses the operator path |
| 0581 | Suspend the direct caller | a no-input emulator run never reaches the marker after the BDOS call |
| 0586 | Abandon the caller on abort | the post-call marker remains absent after Control-C |
| 0587 | Recover a usable command environment | `VER` executes after the warm boot |

The exact DRI diagnostic-presentation profile (0411) remains a separately
selected profile.  BetterCP/M currently supplies the required semantic text
without claiming byte-for-byte DRI wording.

## Verification

`tools/test_bdos_recovery.py` injects final read and write errors into the
assembled production BDOS.  It covers status values 0, 1, 2, and 255; normal,
Ignore, and Control-C choices; every filesystem and directory I/O path; caller
register preservation; dirty-directory abort handling; and private-stack use.
The complete matrix passed.  The private stack high-water mark was 26 bytes
inside its 40-byte allocation.

`tools/test_bdos_operator_recovery.py` builds a disposable current-system disk
and runs the one-shot read/write fault provider in trs80gp.  Its three runs
proved presentation and suspension, Ignore continuation, caller abandonment,
and a working CCP after abort.  The most recent evidence is retained beneath
`build/compatibility/bad-sector-*`.

The ordinary unified-BDOS foundation, all 112 BIOS retry cases, the complete
system build, and the media-change regression also pass with this handler.

## Memory charge

The handler and the extra stack safety margin require 64 bytes in the current
packed resident layout.  `LY_TPA` remains `D501h`, so the published 53 KiB TPA
and maximum COM boundary do not change.  The charge temporarily reduces the
persistent history reservation from 256 to 192 bytes, leaving 182 bytes for
packed command records after its ten-byte header and work area.  This is the
approved temporary trade-off; the history reservation must not be reduced
again while the longer-term memory layout is reconsidered.
