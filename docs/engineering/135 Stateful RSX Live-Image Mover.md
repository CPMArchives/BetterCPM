# Engineering Specification 135: Stateful RSX Live-Image Mover

## Status

Phase 3 increment 2 is implemented and qualified in isolation.  The live-image
mover is not yet connected to Function 202; production `STATEFUL` loading
therefore remains rejected until profile preparation can supply the validated
union of static and runtime-pointer slots.

## Interface

The mover accepts a manager-owned request containing the old base, new base,
allocation size, and a sorted unique vector of pointer-slot offsets.  The
request and slot vector reside outside both allocations and remain valid for
the duration of the operation.

Before changing memory, the mover validates:

- a nonzero allocation whose old and new half-open ranges do not wrap;
- a zero reserved request byte;
- every slot as a complete two-byte word inside the allocation; and
- strict ascending order, which also excludes duplicates.

Validation failure returns FFh without modifying either range.

## Movement and repair

The mover provides memmove semantics.  Downward movement copies from the low
end and upward movement copies from the high end, so overlapping allocations
remain intact.

After copying, each declared slot is read from the new allocation.  Its value
is changed only when it lies in `[old_base, old_base + allocation_size)`.  The
replacement is the corresponding address relative to `new_base`.  Fixed
addresses, nulls, sentinels, and external pointers are left unchanged.

The focused execution test covers overlapping movement in both directions,
an internal pointer, fixed 0005h, null, FFFFh, byte-for-byte image preservation,
stack balance, and atomic rejection of an invalid final-byte slot.

## Next integration step

The reconstruction preparer must merge the carrier's static relocation slots
with its type-3 runtime-pointer slots, remove duplicates, calculate every old
and prospective allocation, and invoke this mover only after the complete
profile succeeds validation.  The rebuilder must then restore loader-owned
chain words and descriptor publication before advancing the registry
generation and TPA boundary.
