# Engineering Specification 39: Set Random Record

## Milestone

BetterCP/M now implements BDOS function 36 (Set Random Record). It converts an
FCB's current sequential position into the 24-bit random-record number used by
CP/M random I/O.

## Call and result contract

Function 36 receives a 36-byte FCB in `DE` and performs no disk access. It
writes FCB offsets 33 through 35 (`R0`, `R1`, `R2`) and returns zero. The
sequential fields and all other FCB bytes remain unchanged.

The conversion is:

```text
extent = ((S2 & 3Fh) << 5) | (EX & 1Fh)
random record = extent * 128 + CR
```

`CR=128` is accepted and carried into the next logical extent boundary, which
matches BetterCP/M's stable sequential end position.

## Placement

Set Random Record lives in the BDOS dispatcher rather than System Services. It
needs no directory, DPB, allocation vector, or BIOS state. The implementation
uses the same three-byte arithmetic contract documented for Compute File Size.

## Verification

Executable tests verify:

- `S2=1`, `EX=2`, `CR=5` becomes record 4,357, encoded `05 11 00`;
- `S2=0`, `EX=31`, `CR=128` carries to record 4,096, encoded `00 10 00`;
- the complete sequential portion of the FCB is unchanged; and
- the same conversion works through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS binaries.

## Next increment

Implemented by [Engineering Specification 40](40%20Random%20Read.md). Function
33 uses the strict CP/M 2.2 16-bit random-read range, activates the requested
extent, and preserves both the random fields and documented sequential
positioning side effect.
