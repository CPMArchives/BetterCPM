# Engineering Specification 44: Console Status

## Milestone

BetterCP/M now implements BDOS function 11 (Get Console Status), beginning the
remaining CP/M 2.2 character and system-call group.

## Contract

Function 11 takes no parameter and returns:

- `00h` when no console character is ready; or
- `FFh` when a character can be read.

The status check must not consume the pending character. The normal BDOS return
aliases remain in force, so `A=L` and `B=H`.

## Implementation

The BDOS dispatcher calls the standard BIOS `CONST` vector at `F006h`. The BIOS
already converts any platform-specific ready indication into exactly `00h` or
`FFh`, keeping keyboard hardware knowledge below the portable BDOS boundary.

## Verification

Direct BDOS and application `CALL 0005h` tests provide empty and ready platform
states. They verify exact result normalization and repeat the ready query to
prove that no character was consumed.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implemented by [Engineering Specification 45](45%20Direct%20Console%20IO.md).
Function 6 builds on BIOS `CONST`, `CONIN`, and `CONOUT` while preserving its
special nonblocking and uncooked behavior.
