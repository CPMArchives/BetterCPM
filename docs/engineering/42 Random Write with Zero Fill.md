# Engineering Specification 42: Random Write with Zero Fill

## Milestone

BetterCP/M now implements BDOS function 40 (Write Random with Zero Fill), the
final CP/M 2.2 random-file operation.

## Contract

Function 40 has the same call, random-record decoding, FCB side effects, return
codes, allocation behavior, and protection rules as Function 34. The sole
difference is required when the target record needs a new CP/M allocation
block: every 128-byte record in that block is initialized to zero before the
caller's record is written.

This is block initialization, not merely gap filling. It makes every unwritten
record within an allocated block deterministic while leaving writes to an
already allocated block unchanged.

## Implementation

Function 40 enters the Random Write service through a separate fixed vector at
`D83Fh`, setting a per-call zero-fill mode. When Sequential Write selects a free
block, the zero-fill helper:

1. constructs a 128-byte zero DMA buffer in the expendable directory cache;
2. maps each logical record of the new block using the live DPB;
3. writes all `BLM+1` records through the BIOS;
4. invalidates the displaced directory cache; and
5. returns to the ordinary write path to install the caller's record.

The first zero write uses BIOS write type 2, identifying the first logical
sector of a new allocation block. Remaining initialization and caller-data
writes use ordinary type 0.

If initialization fails, the selected block is not published in the allocation
vector or FCB. Physical sectors in an otherwise free block may already have
been cleared, but no file can observe or claim a partial allocation.

## Verification

Tests begin with nonzero backing data, write record 16 into a newly selected
block, and verify that the requested 128-byte record contains caller data while
the other records are zero. They also verify unchanged random fields and the
required sequential position, both at the direct BDOS boundary and through an
application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services, BDOS, and resident-system binaries.

The behavior follows Digital Research's CP/M 2.2 Function 40 specification:
a previously unallocated block is filled with zeros before the data is written.

## Next increment

Implemented by [Engineering Specification 43](43%20Selective%20Drive%20Reset.md),
completing the remaining CP/M 2.2 disk-state operation before functions 0
through 11 and the CCP.
