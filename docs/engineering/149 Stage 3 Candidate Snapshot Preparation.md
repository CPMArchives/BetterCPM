# Engineering Specification 149: Stage 3 Candidate Snapshot Preparation

## Status

This increment connects the general append plan to `R3SNAP.RSX` and prepares
the new candidate's commit-ready allocation. It reserves a snapshot descriptor
for every prospective profile member but deliberately leaves retained entries
empty. No live or persistent profile state changes, and production Function
202 still does not select the transaction path.

## Bounded preparation layout

After `R3PROF.RSX` receives the complete plan, it reserves six bytes of
snapshot descriptor space for every prospective member, one 23-byte snapshot
request, and one complete candidate allocation. The candidate snapshot begins
after all planning records and request data, remains disjoint from the carrier
payload, and must end at or below the caller's exclusive workspace high bound.

The candidate descriptor records the prepared source, complete allocation
size, and dispatch offset. Every retained descriptor remains zero until a
later increment reopens and completely prepares that retained member. The
normalized facts' next-scratch pointer advances past the candidate allocation
only after snapshot construction succeeds.

## Runtime headers

The snapshot request carries the already validated carrier format. Public
BRSX-v2 modules have an eight-byte loader-owned header and may advertise
callable descriptors. A transitional version-1 branch remains in the isolated
constructor until the old production manager is removed, but it is not part of
the BetterCP/M 1.0 input contract:

- version 1 accepts no callable descriptors, permits dispatch at offset 4,
  and clears only the four loader-owned header bytes; and
- version 2 retains the eight-byte header, offset-8 dispatch floor, and
  callable-descriptor materialization.

Unknown formats and callable descriptors on a version-1 request are rejected
before destination memory changes.

## Publication and failure behavior

`R3PROF.RSX` publishes the candidate snapshot descriptor, next-scratch pointer,
and public primary-service result only after `R3SNAP.RSX` reports complete
success. Insufficient workspace, overlay failure, malformed snapshot input, or
constructor failure may alter caller-owned scratch but leaves the public
result, persistent reconstruction table, live RSX profile, generation, and TPA
ceiling unchanged.

## Qualification

The focused Z80 integration test executes the real coordinator, carrier and
metadata normalizers, retained-profile builder, planner, handoff, and snapshot
constructor. It proves:

- an empty-profile STATEFUL append produces a complete relocated snapshot and
  candidate descriptor;
- exact workspace acceptance and one-byte-short rejection;
- a converted stateless BRSX-v2 candidate receives the eight-byte runtime
  header without callable descriptors;
- a nonempty append reserves descriptors for the complete prospective profile,
  leaves the retained descriptor empty, and prepares the candidate entry;
- malformed carriers and unsupported operations still fail; and
- every success and failure leaves live and persistent profile state unchanged.

Engineering Specification 150 prepares every retained member. It fully
validates each retained carrier and metadata stream, constructs pointer unions
for retained STATEFUL modules, constructs snapshots for retained STATELESS
modules, and completes the descriptor arrays without publishing live state.
