# Engineering Specification 38: Compute File Size

## Milestone

BetterCP/M now implements BDOS function 35 (Compute File Size), beginning the
CP/M random-record function cluster. It scans every exact-name extent and
writes the file's end position as a 24-bit count of 128-byte records into FCB
bytes `R0`, `R1`, and `R2` (offsets 33 through 35).

## Call and result contract

Function 35 receives a 36-byte FCB in `DE` and uses the current BDOS user.
Drive byte zero or one selects the current drive A. The filename must be exact;
`?` is rejected because a size result for multiple filenames is undefined.

`A=00h` reports success. `FFh` reports an invalid FCB or missing file. A missing
file leaves the caller's existing `R0–R2` bytes unchanged. Internal storage
failure is carried separately and currently maps to `FFh` at the BDOS boundary.

## Extent arithmetic

For each matching directory extent, System Services computes:

```text
extent = ((S2 & 3Fh) << 5) | (EX & 1Fh)
end record = extent * 128 + RC
```

The maximum end record across all extents is the file size. The calculation is
performed directly as three bytes, including carry from `RC=128`, rather than
being truncated through a 16-bit host representation. Filename/type attribute
bits do not participate in matching.

Function 35 does not Open the file or modify `EX`, `S1`, `S2`, `RC`, allocation
entries, or `CR`.

## Verification

The executable fixture presents three extents of one file:

- `EX=0, S2=0, RC=128`;
- `EX=2, S2=0, RC=5`; and
- `EX=0, S2=1, RC=1`.

The third boundary is record 4,097 and must produce `R0–R2 = 01 10 00`. This
tests both extent selection and carry from `S2` into the second result byte.
A missing-file test proves that pre-existing random-record bytes are preserved,
including through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services and BDOS binaries.

## Resident growth note

System Services now crosses `E800h` while remaining within its documented
`D800h–EDFFh` region. Direct unit-test stacks were moved to `ED00h`; production
BDOS already uses its private stack and required no change.

## Next increment

Engineering Specification 39 implements function 36 (Set Random Record) using
this arithmetic contract. The next increment is function 33 (Read Random).
