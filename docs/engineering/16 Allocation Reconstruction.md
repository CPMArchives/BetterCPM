# Engineering Specification 16: Allocation Reconstruction

Status: Implemented and verified
Date: 2026-09-01

## Result

Drive login now reconstructs the complete CP/M allocation vector before the
login-valid flag is set. After clearing the DPB-sized vector and installing
`AL0`/`AL1`, System Services reads every directory record and marks every
nonzero allocation block referenced by an ordinary user extent.

Deleted entries and reserved metadata entries are ignored. Repeated references
to the same block are idempotent at the bitmap level. A live entry containing a
block number greater than `DSM` fails login, leaving drive state invalid and
preventing an out-of-bounds allocation-vector write.

## Allocation-entry widths

The scanner implements both standard CP/M 2.2 directory layouts:

- `DSM <= 255`: sixteen 8-bit allocation block numbers per extent; and
- `DSM > 255`: eight little-endian 16-bit allocation block numbers per extent.

Zero remains the unused allocation-slot value. The current MM 790K carrier has
`DSM=394` and therefore uses the 16-bit form.

## Login ordering and failure behavior

The allocation scan uses the same DPH/DPB-derived directory bounds and logical
track/sector mapping as directory search, but calls an internal raw loader
while login state is still invalid. Only this complete sequence makes the
drive valid:

1. parse and validate DPH/DPB state;
2. size and clear the allocation vector;
3. install reserved-directory masks;
4. scan all live extents and mark their blocks; and
5. set login valid.

Any BIOS read failure or corrupt out-of-range block exits before step 5.

## Verification

The binary fixture constructs a live 16-bit extent referencing blocks 5 and
257, including a duplicate reference to block 5. It also places impossible
block numbers in a deleted entry and a reserved metadata entry. Login succeeds
after exactly 32 directory-record reads and the resulting 50-byte vector has
only the reserved blocks, block 5, and block 257 marked.

The test then changes the DPB to `DSM=127` and verifies reconstruction of a
live 8-bit block entry. A live `FFFFh`/`FFh` block is separately verified to
fail login. Existing invalidation, dynamic `DRM`/`OFF`, exact-name, BIOS, boot,
and physical disk tests continue to pass.

Native CP/M ZSM4/Digital Research LINK and the host cross assembler produce
the same 592-byte component.

## Preserved implementation history

The private DMA buffer moved from its specification-15 address `EA00h` to
`EC00h` so allocation reconstruction could grow without overlapping it. The
source comment continues to record the earlier `E900h` and `EA00h` placements.
All remain provisional until the resident-memory layout is fixed.

## Next increment

Interpret CP/M extent fields (`EX`, `S1`, `S2`, and `RC`) and define the first
FCB-open result. This will connect exact directory search and the reconstructed
allocation map to the CP/M-visible file interface without enabling mutation.

Engineering Specification 17 completed the first exact, read-only FCB Open
service for the current `EXM=0` carrier. Grouped extents, wildcards, and the
public BDOS function-15 dispatch remain subsequent compatibility increments.
