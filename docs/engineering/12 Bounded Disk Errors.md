# Engineering Specification 12: Bounded Disk Errors

Status: Implemented and verified
Date: 2026-09-01

## Result

The Model 4 physical-sector reader and writer no longer wait forever for the
floppy controller.  Every wait for controller idle, seek completion, data
request, and command completion has a finite 16-bit polling budget.

Exhausting a budget returns `A=1` with the zero flag clear.  Controller-reported
errors retain their masked nonzero status.  The BIOS passes either result back
to its caller and does not retry automatically.

The polling budget is a deterministic execution bound, not a calibrated time
interval.  A later hardware specification may replace it with timer-based
deadlines and a deliberately defined retry/recalibration policy.

## Failure contract

- A failed logical `READ` does not copy scratch data to the caller's DMA area.
- A failed write pre-read does not call the physical writer.
- A failed physical write returns its nonzero status.
- BIOS disk operations do not modify the caller's DMA area on failure.
- The 512-byte BIOS scratch buffer is unspecified after any failed operation
  and must not be treated as cached valid data.
- After a physical-write failure, the on-disk sector is indeterminate because
  the controller may have written part of it before reporting failure.

This deliberately describes only guarantees that the current implementation
can uphold.  Recovery, retries, bad-sector handling, and user-facing error
reporting remain later policy decisions.

## Verification

The binary-level BIOS fixture injects distinct physical-read and physical-write
errors.  It verifies status propagation, DMA preservation, and suppression of
the physical write when its prerequisite read fails.  Existing exhaustive
tests still cover all 80 logical mappings and all three CP/M write types.

The real-controller-path diagnostics continue to pass under `trs80gp` for
cylinder 2, side 1, sector 10.  Native CP/M and cross builds remain
byte-identical:

- physical-read diagnostic: 462 bytes;
- physical-write diagnostic: 446 bytes; and
- production BIOS: 1040 bytes.

## Next increment

Load the first filesystem-facing directory sector through the BIOS and define
the minimum directory-search behavior needed for the initial BetterCP/M BDOS.

