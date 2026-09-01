# Engineering Specification 45: Direct Console I/O

## Milestone

BetterCP/M now implements BDOS function 6 (Direct Console I/O), providing the
CP/M nonblocking, uncooked console path.

## Contract

Function 6 interprets register `E` as follows:

- `E=FFh`: poll for input. Return zero immediately if no character is ready;
  otherwise read and return one character.
- any other value: write that byte directly to the console.

Direct input is not echoed. Direct input and output do not perform CP/M
control-character interpretation. The BIOS console-input service continues to
apply the system's established seven-bit input convention.

The output form has no specified CP/M result; BetterCP/M returns zero
deterministically. The input result uses the ordinary BDOS aliases.

## Implementation

The dispatcher composes the conventional BIOS services without platform
knowledge:

```text
input:  CONST -> empty return or CONIN
output: CONOUT
```

`CONST` makes the input form nonblocking. Calling `CONIN` only after a ready
result avoids depending on platform-specific keyboard polling behavior.

## Verification

Direct BDOS and application `CALL 0005h` tests verify:

- an empty input poll returns zero and produces no output;
- a ready input byte is returned without echo and with parity removed; and
- a direct output byte reaches BIOS `CONOUT` unchanged.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implement BDOS function 1 (Console Input), adding the first cooked-console
operation: blocking input with echo through the portable BIOS vectors.
