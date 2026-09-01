# Engineering Specification 23: Disk Reset and Login Vector

## Milestone

BetterCP/M now implements BDOS function 13 (Reset Disk System) and function 24
(Return Login Vector). Together they establish an observable disk-state reset
boundary through the public `CALL 0005h` interface.

## Function 13

Reset Disk System follows the required CP/M 2.2 compatibility-ledger effects:

- drive A is logged in and becomes the current/default drive;
- the login vector is reset so that only bit 0 (drive A) is set;
- the DMA address returns to `0080h`; and
- the current BDOS user number is preserved.

CP/M defines no function-specific result for function 13. BetterCP/M currently
returns zero after a successful reset, but applications must not depend upon
that value.

The compatibility contract also requires reset to clear the software read-only
drive vector. BetterCP/M has not implemented function 28 or read-only state, so
that vector is presently zero by construction. The requirement remains binding
when protection state is introduced.

If drive-A login fails, reset returns the existing provisional disk failure and
does not publish newly reset BDOS state. Directory login remains invalid so a
later operation can retry after the storage fault is corrected.

## Function 24

Return Login Vector supplies a 16-bit value in `HL`; bits 0 through 15
correspond to drives A through P. The current system exposes only drive A, so
the observable value is `0001h` after initialization, drive-A selection, and
disk reset.

The common 16-bit return path also supplies the conventional aliases `A=L` and
`B=H`. This differs from the existing one-byte return path, which constructs
`HL` from an 8-bit result.

Adding the 16-bit return path exposed a potential fallthrough from Open's
provisional storage-error result. A dated patch comment now records the
explicit branch that preserves the original 8-bit error return instead of
allowing it to enter function 24's return path.

## State ownership

The BDOS dispatcher now owns the login vector alongside current drive, current
user, and DMA address. Its initial value is drive A because the page-zero
gateway is published only after drive-A login succeeds.

Function 14 marks A logged only after successful selection. Unavailable drive
requests do not modify the vector. Future multiple-drive support must set a
drive's bit after successful first login and retain other logged-drive bits
until reset or another defined invalidation event.

## Verification

Direct and page-zero tests verify:

- `HL=0001h` from function 24;
- function 13 restores drive A, DMA `0080h`, and login vector `0001h`;
- function 13 preserves a nonzero modulo-32 user number;
- failed drive selection does not change login membership; and
- Open storage errors remain `FFh` after introduction of the 16-bit return
  path.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce the
same 260-byte BDOS binary.

## Next increment

Implement function 28 (Write Protect Disk) and function 29 (Return Read-Only
Vector), completing the disk-state pair that function 13 is already required
to clear. Actual write operations can then consult coherent protection state.
