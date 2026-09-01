# Engineering Specification 51: Print String

## Milestone

BetterCP/M now implements BDOS function 9 (Print String).

## Contract

Function 9 accepts a string address in `DE` and emits successive bytes until,
but not including, the first dollar sign (`24h`). BetterCP/M returns zero through
the standard `A=L` and `B=H` aliases, although CP/M-compatible programs must not
depend on a result from this output operation.

The terminator remains in application memory and is not emitted. Function 9
does not impose a separate length limit; as in CP/M 2.2, the caller is
responsible for supplying a reachable terminator.

## Shared cooked-output path

Every emitted byte passes through the same cooked character routine used by
Function 2. Print String therefore inherits tab expansion, console-column
tracking, flow-control polling, printer echo, and type-ahead preservation rather
than developing subtly different console behavior.

The string scan pointer is preserved across that routine because tab expansion
uses working registers of its own.

## Verification

Direct and application `CALL 0005h` tests print `A`, a tab, and `B` from an
`A<tab>B$Z` fixture. They verify cooked expansion to column nine, confirm that
`B` is the final emitted byte, prove that neither the dollar sign nor trailing
`Z` is emitted, and ensure that the source string remains unchanged.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implement function 10 (Read Console Buffer), completing the CP/M 2.2 console
service group.
