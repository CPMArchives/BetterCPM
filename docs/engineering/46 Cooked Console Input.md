# Engineering Specification 46: Cooked Console Input

## Milestone

BetterCP/M now implements BDOS function 1 (Console Input), including CP/M's
cooked single-character echo and control behavior.

## Contract

Function 1 blocks until a non-intercepted console character is available and
returns it in the normal BDOS aliases. Echo behavior is:

- graphic characters are echoed;
- carriage return, line feed, and backspace are echoed;
- tab expands to spaces through the next eight-column stop; and
- other control characters are returned without echo.

Carriage return resets the tracked console column. Backspace retreats one
column without underflow. Direct Console I/O remains entirely outside these
cooked rules.

## CP/M controls

The cooked input loop also recognizes the traditional CP/M controls:

- `Ctrl-S` pauses and consumes input until `Ctrl-Q`;
- `Ctrl-P` toggles printer echo;
- `Ctrl-C` enters BIOS warm boot; and
- stray `Ctrl-Q` and `Ctrl-P` do not reach the application.

Unexpected characters while paused produce a bell and leave the system paused.
When printer echo is active, echoed characters also pass through BIOS `LIST`.

## Implementation

The BDOS now owns a small reusable cooked-console core: current column,
printer-echo state, character classification, tab expansion, and a shared
console/list output helper. All actual device transport remains behind BIOS
`CONIN`, `CONOUT`, `LIST`, and `WBOOT` vectors.

## Verification

Direct BDOS tests verify graphic echo and return aliases, invisible ordinary
controls, tab expansion from column one through column eight, and carriage
return column reset. Application `CALL 0005h` tests verify graphic and control
paths through the resident gateway.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implement BDOS function 2 (Console Output) on the shared cooked-console core,
including tab expansion and console flow-control polling.
