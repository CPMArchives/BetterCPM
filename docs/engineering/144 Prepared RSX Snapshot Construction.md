# Engineering Specification 144: Prepared RSX Snapshot Construction

## Status

Stage 3 increment 10 implements and qualifies the bounded snapshot constructor
needed by the Function 202 transaction coordinator. It prepares fresh and
`STATELESS` allocations without changing the live RSX profile.

## Input contract

`R3SNAP.RSX` runs in the shared CONFIG overlay and accepts a request containing:

- a validated carrier payload, its size, and its page-rounded allocation;
- the carrier's linked base and the provider's prospective live base;
- the validated static relocation directory;
- zero, one, or two packed callable-service descriptors;
- the validated BRSX carrier format;
- a caller-owned snapshot destination; and
- the validated dispatch offset.

The coordinator remains responsible for carrier and metadata parsing. This
component receives the compact facts produced by that parsing and refuses
invalid sizes, overflowing address ranges, malformed relocation ordering,
incomplete relocation words, excessive descriptor counts, inadequate
descriptor space, overlapping payload and snapshot ranges, and invalid
formats or dispatch offsets. The request, relocation list, and packed
descriptors remain distinct coordinator-owned inputs outside the snapshot
allocation.

## Prepared image

All validation completes before the first destination write. On success, the
constructor copies the payload, clears the entire allocation tail, applies
static relocation for the **prospective live base**, materializes callable
descriptors downward from the allocation top for BRSX-v2, and creates the
eight-byte loader-owned runtime header. The
resulting allocation can therefore be copied byte-for-byte by the disk-free
commit engine.

Relocation targets the eventual live address rather than the temporary
snapshot address. Runtime-pointer slots are not adjusted for a fresh or
stateless reconstruction; their initial values come from the carrier and may
later be established by the provider itself. Runtime-pointer slots matter when
moving an existing `STATEFUL` allocation and are handled by the pointer-union
and mover path.

The completion byte is written only after the complete snapshot is ready. A
failure leaves both the completion byte and destination memory unchanged.

## Qualification

The focused Z80 test verifies relocation to an address different from both the
linked and snapshot addresses, fixed-pointer preservation, zero-filled tail,
descriptor order and runtime-header contents. It also proves that malformed
relocation order, a partial relocation word, an invalid dispatch, and
insufficient descriptor capacity are rejected before any snapshot byte is
written. Public BRSX-v2 input receives its eight-byte header and may
materialize callable descriptors. The constructor's version-1 branch is
transitional implementation residue, not a supported input contract.

Both target image builders package `R3SNAP.RSX`. Engineering Specification 149
connects carrier parsing, prospective-profile construction, the existing
planner, and this snapshot constructor for the new candidate. Engineering
Specification 150 completes preparation by constructing retained-member
pointer unions and snapshots. Commit coordination and publication remain the
next Stage 3 increment.
