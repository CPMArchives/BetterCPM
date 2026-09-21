# Engineering Specification 145: Stage 3 Carrier Preparation

## Status

This Stage 3 increment prepares a BRSX carrier for the Function 202
transaction without changing live protected memory.  It supplies two bounded
CONFIG-slot overlays and a normalized facts record consumed by the existing
snapshot constructor.  Function 202 does not yet select this path.

## Split validation

`R3CARR.RSX` validates the fixed BRSX envelope, name, checksum, allocation,
entry point, and sorted static-relocation directory.  It accepts the existing
v1 carrier and the typed v2 carrier.  On success it publishes the fixed fields
of a 26-byte facts record.

`R3META.RSX` then validates the version-specific metadata.  For v2 it checks
the typed envelope, runtime-pointer list, callable-service records, entry
bounds, uniqueness, and descriptor capacity.  Runtime pointer slots must be
sorted, unique, word-sized, inside the payload, and outside the loader-owned
first eight bytes.  At most two callable descriptors are packed into caller
scratch space.  A v1 carrier has no typed reconstruction metadata and leaves
these counts at zero.

The coordinator must provide distinct carrier, request, facts, and scratch
ranges.  It also supplies the scratch limit; the metadata phase refuses to
publish facts when normalized descriptors would cross that limit.

## Normalized facts

The record contains payload address, code size, allocation, linked base,
dispatch offset, static relocation list and count, runtime pointer list and
count, packed callable descriptor address and count, reconstruction class,
carrier version, primary numeric service, and the next free scratch address.
It contains no implicit pointers into either overlay.

Both phases use a completion byte in their request.  They update the facts
record and mark completion only after the complete phase succeeds.  A failure
therefore cannot expose partially validated facts to the coordinator.  Caller
scratch is disposable until metadata completion.

## Qualification

The focused Z80 qualification uses the real `STATEFUL.RSX` v2 carrier, passes
its normalized facts directly to `R3SNAP.RSX`, and verifies a relocated fresh
snapshot.  It also exercises the v1 `HELLO.RSX` path and rejects corrupted
checksums, wrong names, malformed metadata, duplicate callable identifiers,
and runtime pointers in the loader-owned header.

Both supported platform image builders install the two overlays with the
other private Stage 3 files.  The next increment is the coordinator that opens
the requested carrier, invokes these preparation phases, and continues into
plan, slot-union, snapshot, move, and commit processing.
