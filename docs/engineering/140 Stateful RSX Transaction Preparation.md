# Engineering Specification 140: Stateful RSX Transaction Preparation

## Status

Phase 3 increment 6 is implemented and qualified outside Function 202. It
combines prospective profile planning with the pointer-slot preparation needed
by the existing move scheduler. The live commit remains a separate increment.

## Prepared transaction

The preparer invokes the validated layout planner, then builds one pointer-union
descriptor for every prospective provider. Each descriptor identifies the
sorted, duplicate-free union of the carrier's static relocation slots and its
declared runtime-pointer slots.

Before producing unions, it checks the complete prospective layout, descriptor
capacity, and the aggregate worst-case union capacity. Each provider's lists
are then checked by the pointer-union preparer. The returned prepared-record
count is written only after every provider succeeds. A failure may leave bytes
in transaction scratch, but it cannot make that scratch eligible for commit
and it does not alter a live RSX allocation.

## Qualification

The focused Z80 test removes the leading member of a three-provider profile,
produces two upward STATEFUL moves, and verifies the two independent pointer
unions and their descriptors. It also proves that a malformed later provider,
inadequate union capacity, and a no-fit prospective layout leave the completion
byte unpublished and the live-profile memory unchanged.

The next increment connects this prepared transaction to the move scheduler,
reconstructs fresh and STATELESS entries, rewrites loader-owned headers and
descriptors, and publishes the new profile only after commit succeeds.
