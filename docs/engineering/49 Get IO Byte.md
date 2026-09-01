# Engineering Specification 49: Get I/O Byte

## Milestone

BetterCP/M now implements BDOS function 7 (Get I/O Byte).

## Contract

Function 7 takes no parameter and returns the byte stored at conventional CP/M
page-zero address `0003h`. The result uses the standard BDOS aliases `A=L` and
`B=H`.

There is deliberately no private BDOS copy. Programs that inspect address
`0003h` directly and programs that call Function 7 therefore observe the same
state.

## Initialization and architecture

Resident-system initialization installs the warm-boot vector at `0000h` and the
BDOS vector at `0005h` without changing `IOBYTE` at `0003h`. Logical-device
routing remains a BIOS/configuration responsibility; Function 7 only exposes
the standard CP/M state byte.

## Verification

Direct and application `CALL 0005h` tests seed `0003h` with `A5h`, verify that
resident initialization preserves it, and verify the exact return value without
memory mutation.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implement function 8 (Set I/O Byte), completing the paired page-zero interface.
