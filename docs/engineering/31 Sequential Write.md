# Engineering Specification 31: Sequential Write

## Milestone

BetterCP/M now implements BDOS function 21 (Write Sequential). An application
can write a 128-byte record through its current DMA address, overwrite a record
in an existing allocation block, or acquire the first free block for an empty
allocation entry.

## Call and result contract

Function 21 receives an activated FCB in `DE` and uses the DMA address selected
by function 26. `A=00h` reports a complete write. `A=01h` currently reports
that no record can be represented in the active extent, including `CR=128` or
allocation exhaustion. Protection and physical-storage failures remain mapped
to the provisional `FFh` result at the BDOS boundary.

The fourteenth System Services vector at `D827h` owns the implementation. BDOS
passes current-user, DMA, and software write-protection state without exposing
the resident layout to applications.

## Translation and allocation

Write Sequential uses the same DPB-driven translation as Read Sequential. It
derives the allocation entry and record-within-block from `EX`, `EXM`, `CR`,
`BSH`, and `BLM`, supports both 8-bit and 16-bit allocation entries according
to `DSM`, and translates the selected block through `SPT` and `OFF` before
calling BIOS `SETTRK`, `SETSEC`, `SETDMA`, and `WRITE`.

When an allocation entry is zero, System Services scans the reconstructed ALV
for its first clear bit. Directory-reserved and file-owned blocks are already
marked during login, so selection is independent of the MM 790K geometry.

## Transaction boundary

Software drive protection and the FCB T1 read-only attribute are checked before
any disk or in-memory mutation. For a new block, the candidate remains private
until BIOS reports a successful data write. Only then does BetterCP/M mark the
ALV, publish the block in the caller's FCB, advance `CR`, and extend `RC` when
necessary. A failed physical write therefore leaves the FCB and ALV unchanged.

This ordering can leave unreachable data in a block that was selected but not
published if the machine loses power after the physical write. It cannot make
the directory point at unwritten data, which is the safer failure direction.
Crash-recovery policy remains future work.

## Verification

Executable BDOS tests verify an existing-block overwrite, changed DMA content,
first-free-block allocation, 16-bit FCB allocation encoding, ALV publication,
`CR` and `RC` advancement, software protection, FCB read-only protection, and
physical-write failure without FCB or ALV mutation. The test BIOS routes data
and directory sectors to distinct fixtures so a data write cannot masquerade
as directory writeback.

Native CP/M ZSM4/Digital Research LINK and the host assembler must continue to
produce byte-identical components.

## Deliberate boundary and next increment

Write Sequential does not yet create a new directory extent at `CR=128`.
Engineering Specification 32 now extends Close with a pending-allocation
journal and transactional allocation-map commit. Automatic extent creation is
therefore the next remaining sequential-write boundary.
