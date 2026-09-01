# Engineering Specification 48: Logical Character Devices

## Milestone

BetterCP/M now implements BDOS functions 3 through 5, completing the CP/M
single-character logical-device calls.

## Services

- Function 3, Reader Input, blocks in BIOS `READER` and returns its byte.
- Function 4, Punch Output, passes the byte in `E` to BIOS `PUNCH`.
- Function 5, List Output, passes the byte in `E` to BIOS `LIST`.

The two output functions have no specified CP/M result; BetterCP/M returns zero
deterministically. Reader Input uses the ordinary `A=L`, `B=H` return aliases.

## Architectural boundary

These are deliberately thin services. BDOS contains no knowledge of serial
ports, printers, paper tape, redirection, or whether a logical device is
assigned. Those decisions remain in the BIOS and, eventually, the system
configuration facility.

The provisional TRS-80 BIOS currently treats List and Punch as unassigned and
returns CP/M end-of-file (`1Ah`) from Reader. That platform policy does not
change the public BDOS implementation.

## Verification

Tests temporarily substitute instrumented BIOS vectors and verify exact input
and output bytes at both the direct BDOS boundary and application `CALL 0005h`.
The original resident BIOS vectors are restored before filesystem tests.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Function 7 is implemented by [Engineering Specification 49](49%20Get%20IO%20Byte.md),
preserving the conventional page-zero `IOBYTE` at address `0003h`. Function 8
remains the next increment.
