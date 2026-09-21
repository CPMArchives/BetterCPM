# Engineering Specification 141: Stateful RSX In-Memory Commit

## Status

Phase 3 increment 7 is implemented and qualified outside Function 202. It
defines the short, disk-free commit phase for a prepared resident transaction.

## Commit inputs

The preparation phase supplies a validated prospective plan, STATEFUL pointer
unions, and one descriptor per provider. A retained `STATEFUL` or unchanged
`COLD_ONLY` provider needs no snapshot. Every fresh or `STATELESS` provider has
a complete, pre-relocated live allocation in temporary TPA memory. Its snapshot
therefore includes zeroed allocation tail and materialized service descriptors.

This staging rule removes disk I/O, carrier parsing, relocation, initialization,
and every other fallible external operation from commit. The planner's minimum
base must reserve enough TPA for the caller and these snapshots.

## Commit sequence

Before touching live memory, the commit engine validates all record classes,
the tightly packed prospective map, allocation and dispatch bounds, snapshot
sizes, and snapshot disjointness from both live sources and prospective
destinations. It then:

1. invokes the validated STATEFUL move scheduler;
2. copies prepared fresh and STATELESS images to their final allocations;
3. rewrites every loader-owned dispatch and next-chain word; and
4. publishes the low boundary, TPA ceiling, page-zero ceiling, chain head, and
   finally the resident-layout generation.

The completion count is written only after publication. Once the scheduler is
entered, the remaining operations are bounded memory operations with no error
return. A failure discovered by validation leaves live images and publication
state unchanged.

## Qualification

The focused Z80 test removes the leading member of a profile, moves a retained
STATEFUL image upward, installs a prepared STATELESS snapshot, repairs an
internal pointer while preserving a fixed pointer, rebuilds both runtime
headers, and verifies every publication field and the generation increment.
Bad snapshot size and destination overlap are rejected before movement.
Removing the final provider also verifies the explicit discard path and empty
profile publication.

The next increment must make the Function 202 preparation phase construct the
snapshot descriptors and temporary images, then invoke this disk-free commit
engine on both supported targets.
