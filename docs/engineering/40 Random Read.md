# Engineering Specification 40: Random Read

## Milestone

BetterCP/M now implements BDOS function 33 (Read Random). It decodes a CP/M
2.2 random-record number, activates the corresponding directory extent, and
reads one 128-byte record through the existing DPB-driven sequential mapper.

## CP/M 2.2 contract

Function 33 receives a 36-byte FCB in `DE` and uses the current DMA address.
CP/M 2.2 defines the random record as a 16-bit value in `R0` and `R1`; `R2`
must be zero. BetterCP/M deliberately reports status 6 for a nonzero `R2`
rather than introducing a private 24-bit extension at this compatibility
boundary.

The decoded position is:

```text
CR = R0 & 7Fh
EX = ((R1 & 0Fh) << 1) | (R0 >> 7)
S2 = R1 >> 4
```

On success, `EX`, `S2`, and `CR` identify the record just read. This is the
documented CP/M side effect: a following sequential read addresses that same
record. `R0`, `R1`, and `R2` remain unchanged.

## Results

- 0: record read successfully;
- 1: unwritten record within an existing extent;
- 4: requested extent has not been written;
- 6: random record number is outside the CP/M 2.2 range;
- 9: invalid drive or wildcard FCB; and
- FFh: provisional BetterCP/M presentation of a physical storage failure.

## Implementation

Random Read is a System Services operation reached through a new fixed vector
at `D839h`. It validates and decodes the random fields, reuses exact extent
Open, then calls the established Read Sequential mapper. After a successful
transfer it reverses Read Sequential's `CR` increment, preserving the CP/M
random-I/O positioning rule without duplicating disk geometry logic.

## Verification

Executable tests verify record 1 data and positioning, unchanged `R0-R2`, an
unwritten record, a missing extent, nonzero-`R2` overflow, wildcard rejection,
and the complete path through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services, BDOS, and resident-system binaries.

The compatibility behavior follows the CP/M 2.2 Interface Guide's Read Random
contract and error definitions.

## Next increment

Implemented by [Engineering Specification 41](41%20Random%20Write.md), including
automatic extent and block allocation, distinct exhaustion results, protection,
and the CP/M random-write FCB positioning rules.
