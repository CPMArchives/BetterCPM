# Engineering Specification 50: Set I/O Byte

## Milestone

BetterCP/M now implements BDOS function 8 (Set I/O Byte).

## Contract

Function 8 stores the byte supplied in `E` at conventional CP/M page-zero
address `0003h`. BetterCP/M returns zero through the standard `A=L` and `B=H`
aliases, although compatible programs must not depend on a return value from
this output operation.

The byte is written directly rather than copied into private BDOS state. Direct
inspection of `0003h`, Function 7, and Function 8 therefore share one coherent
IOBYTE value.

## Architecture boundary

Function 8 changes the standard logical-device selection byte only. Interpreting
its bit fields and routing console, reader, punch, and list operations remains a
BIOS and configuration responsibility. This preserves the portable BDOS
interface without embedding platform-specific device choices in the BDOS.

## Verification

Direct and application `CALL 0005h` tests set IOBYTE to `5Ah`, verify the exact
page-zero mutation and deterministic return, then call Function 7 to prove that
the paired interface observes the new value.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implemented by [`Engineering Specification 51`](51%20Print%20String.md).
