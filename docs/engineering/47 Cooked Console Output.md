# Engineering Specification 47: Cooked Console Output

## Milestone

BetterCP/M now implements BDOS function 2 (Console Output) on the shared CP/M
cooked-console core.

## Contract

Function 2 writes the byte in register `E`. Tab expands to spaces through the
next eight-column stop. Carriage return resets the tracked column, backspace
retreats without underflow, and line feed preserves the column. Other bytes are
passed to the console and advance the column.

Cooked output observes the traditional controls found while polling input:

- `Ctrl-S` pauses output until `Ctrl-Q`;
- `Ctrl-P` toggles printer echo;
- `Ctrl-C` enters warm boot; and
- stray `Ctrl-Q` is consumed.

## Preserving typed input

Output polling can encounter an ordinary keystroke. Discarding it would create
an observable compatibility failure, so BetterCP/M retains one cooked-console
lookahead byte. Function 11 reports that byte as ready, and the next Function 1
or Function 6 input operation returns it before consulting BIOS `CONIN`.

This lookahead belongs to the portable BDOS console layer; the BIOS remains a
simple device transport.

## Verification

Direct and `CALL 0005h` tests verify graphic output, tab expansion, deterministic
return, and preservation of an ordinary key encountered during output polling.
The direct suite confirms the saved byte first appears through Console Status
and is then returned and echoed by Console Input.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implemented by [Engineering Specification 48](48%20Logical%20Character%20Devices.md).
Reader Input, Punch Output, and List Output are thin services over the standard
BIOS vectors and complete the single-character logical-device group.
