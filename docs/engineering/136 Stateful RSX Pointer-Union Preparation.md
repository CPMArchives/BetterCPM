# Engineering Specification 136: Stateful RSX Pointer-Union Preparation

## Status

Phase 3 increment 3 is implemented and qualified outside the live Function 202
pipeline.  Production `STATEFUL` loading remains blocked pending complete
profile planning and publication.

## Slot preparation

The preparer accepts one provider's allocation size, sorted static relocation
list, sorted runtime-pointer list, and a bounded output area.  It validates both
input lists completely before producing their sorted, duplicate-free union.

Validation rejects:

- zero allocations;
- wrapped counts or inadequate output capacity;
- nonzero reserved request fields;
- unsorted or duplicate entries in either source list; and
- offsets that do not identify a complete word in the allocation.

Failure leaves both the output area and returned count unchanged.

## Composed qualification

The integration test reads the real static relocation directory and type-3
runtime-pointer record from `STATEFUL.RSX`, creates their union with the Z80
preparer, initializes and mutates the live provider, and passes that union to
the overlap-safe mover from Specification 135.  It then invokes the service at
its new address and proves:

- the counter and buffer retained their mutated values;
- the linked and runtime-created pointers both identify the relocated buffer;
- neither pointer still identifies the old allocation; and
- fixed 0005h, null and FFFFh values were not adjusted.

This is the core state transformation required by the resident transaction.
The remaining work is to calculate every old and prospective allocation before
commit, invoke the transformation in a safe order, rebuild loader-owned links
and service descriptors, and publish the new generation atomically.
