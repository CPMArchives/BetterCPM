# Engineering Specification 148: Stage 3 Retained Profile Planning

## Status

This increment extends the Function 202 transaction coordinator from an empty
profile to a bounded append plan for a nonempty profile. It introduces
`R3PROF.RSX`, a separate manager-slot phase, so carrier streaming and retained
profile planning remain independently bounded below one kilobyte. Production
Function 202 still does not select this transaction path, and no live or
persistent profile state changes.

## Safe phase handoff

After `R3COORD.RSX` validates and normalizes the candidate carrier, it writes a
six-byte context containing the public request, candidate facts, and workspace
high bound after the maximum normalized descriptor reservation. It then loads
`R3MOVE.RSX` and jumps to that image's existing handoff routine. The handoff
replaces the manager slot with `R3PROF.RSX` and passes the context address in
DE. A jump rather than a call removes the coordinator frame, so the replacement
phase returns directly through the original Function 202 call frame.

## Retained profile facts

The persistent reconstruction table records names and services but not the
allocation sizes or reconstruction classes required by `R3PLAN.RSX`.
`R3PROF.RSX` therefore reopens each retained carrier and validates the fixed
header fields that determine planning:

- BRSX signature, format, and ABI;
- filename identity;
- supported reconstruction class;
- nonzero code size; and
- page-rounded allocation greater than the code size.

The builder rejects a candidate already present in the retained profile. It
places each retained allocation in both the old and prospective vectors,
appends the candidate's already normalized allocation and class, and invokes
the existing planner. Payload checksum, relocation, pointer-list, and callable
metadata validation remain part of the subsequent snapshot-preparation phase;
the fixed-header pass does not replace them.

## Workspace and failure behavior

The durable area after the candidate facts contains the complete movement
records, old and prospective allocation vectors, class vector, and planner
request. A nonempty profile additionally requires one reusable 512-byte sector
after that area for header inspection. The disposable sector is excluded from
the returned next-scratch pointer and can be reused by later preparation.

Every range is proved against the caller's exclusive high bound before a
retained file is opened. Missing or malformed carriers, duplicate names,
insufficient workspace, overlay failure, and planner failure leave the public
service result, reconstruction table, and live profile unchanged.

## Qualification

The focused Z80 integration test executes the real coordinator, handoff,
profile builder, and planner overlays. It proves both the empty-profile case
and a nonempty append containing a retained legacy carrier plus a fresh
stateful carrier. It checks both plan records, exact workspace acceptance and
one-byte-short rejection, duplicate rejection, unchanged persistent state,
and unchanged live memory. Existing candidate corruption and unsupported
operation checks remain active.

Both platform image builders install `R3PROF.RSX` with the other private Stage
3 overlays. The next increment can consume the complete general plan while it
constructs pointer unions and prepared snapshots for every prospective member.
