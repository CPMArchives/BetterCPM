# 163 — z80pack ROM Cold Initializer

Date: 2026-09-27  
Status: isolated executable initializer implemented; immutable image pending

## Purpose

This increment turns the accepted RAM initialization representation into
executable Z80 code without prematurely fixing the final immutable-code layout.
The z80pack build emits `rom/cold-init.bin` and a hash-bearing
`rom/cold-init.json`, then executes the routine in the focused Z80 runner.

## Internal entry contract

The initializer is position independent. Its future ROM entry supplies:

- `HL`: address of the immutable 2,412-byte RAM template;
- `IX`: final immutable BDOS entry address; and
- `SP`: a valid stack outside the destination RAM image.

The routine copies the template to `D501h..DE6Ch`, publishes `JP` plus the
supplied BDOS address at the fixed three-byte RAM gateway, invalidates the first
history-signature byte, and returns. It does not know or constrain where the
immutable resident components will be packed.

This contract is internal to ROM construction. It is not a public BetterCP/M
ABI and may be replaced when the final immutable entry path is assembled.

## Focused evidence

The executable test begins with nonzero RAM, runs the initializer with two
different BDOS entry addresses, and proves that:

- every byte of the accepted template reaches its assigned RAM location;
- the three-byte gateway contains the requested BDOS target;
- history is invalid on true cold entry;
- the immutable source template is unchanged; and
- neither byte adjacent to the accepted RAM image is written.

The builder also subtracts the emitted routine from the 671-byte allowance
established by Engineering Specification 162 and rejects an overflow.

This is deliberately not an XIP boot claim. The next bounded step is to pack
the immutable resident bytes, template and initializer into one ROM image and
resolve the initializer's two input addresses from that measured layout.
