# Engineering Specification 43: Selective Drive Reset

## Milestone

BetterCP/M now implements BDOS function 37 (Reset Drive), completing the CP/M
2.2 disk-state and filesystem function set.

## Contract

Function 37 receives a 16-bit drive vector in `DE`. Bit 0 selects A:, bit 1
selects B:, and so on through bit 15 for P:. Every selected drive returns to
the reset state:

- it is no longer logged in;
- its transient software read-only status is cleared; and
- cached filesystem state for it is invalidated.

The current/default drive, current user, and DMA address do not change. CP/M
2.2 returns zero for compatibility with MP/M.

## Present platform scope

The provisional TRS-80 BIOS currently exposes only drive A:. Consequently,
Function 37 acts on bit 0 and safely ignores the other vector bits. The BDOS
implementation still accepts the full 16-bit interface, so adding drives does
not require an ABI change.

Selecting A: after a reset performs a fresh directory scan and allocation-vector
reconstruction before restoring its login-vector bit. This is the intended path
after changing media.

## Verification

Executable tests verify that:

- a mask selecting only unavailable B: leaves A: logged and protected;
- selecting A: removes it from the login and read-only vectors;
- the current drive remains A:;
- selecting A: afterward rebuilds and republishes its login state; and
- all behavior is available through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implemented by [Engineering Specification 44](44%20Console%20Status.md).
Function 11 uses the existing BIOS `CONST` service as the first bridge from the
completed disk-focused BDOS to functions 0 through 10.
