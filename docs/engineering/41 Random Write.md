# Engineering Specification 41: Random Write

## Milestone

BetterCP/M now implements BDOS function 34 (Write Random). It writes one
128-byte DMA record at the CP/M random-record position and automatically
allocates a missing data block or directory extent.

## CP/M 2.2 contract

Function 34 receives a 36-byte FCB in `DE`. As with Read Random, CP/M 2.2 uses
`R0` and `R1` as a 16-bit record number and requires `R2` to be zero.

The call does not change `R0-R2`. On success, `EX`, `S2`, and `CR` identify the
record just written, so a following sequential read or write addresses that
same record again. A program must Open the file's base extent, or Make an empty
file, before using random writes.

## Allocation and failure behavior

An existing target extent is activated through exact Open. If the requested
extent does not yet exist, BetterCP/M creates a canonical empty extent before
entering the established Sequential Write path. That path performs DPB-driven
record mapping, free-block selection, physical write, allocation-vector
publication, and FCB metadata updates.

The public results distinguish the CP/M random-write conditions:

- 0: write completed;
- 2: no free data block;
- 5: no directory entry available for a new extent;
- 6: nonzero `R2`, outside the CP/M 2.2 range;
- 9: invalid drive or wildcard FCB; and
- FFh: software/file protection or physical storage failure.

The existing write-protection checks remain in force. A newly selected data
block is not published in the allocation vector or FCB unless the BIOS accepts
the physical write.

## Placement

Random Write is the twenty-first fixed System Services entry at `D83Ch`. The
BDOS dispatcher supplies the current DMA address, user, and transient drive
protection state.

## Verification

Executable tests cover overwriting an allocated record, creating and writing a
missing extent, preserving `R0-R2`, sequential-position side effects, data-block
exhaustion, directory overflow, nonzero-`R2` rejection, and application access
through `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services, BDOS, and resident-system binaries.

## Next increment

Implement BDOS function 40 (Write Random with Zero Fill). This can reuse Random
Write while initializing the unwritten portion of a newly allocated block to
zero, as required by CP/M 2.2.
