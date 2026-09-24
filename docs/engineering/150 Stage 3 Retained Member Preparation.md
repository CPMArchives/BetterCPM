# Engineering Specification 150: Stage 3 Retained Member Preparation

## Status

This increment completes the preparation inputs required by the existing
disk-free commit engine. It reopens and fully validates every retained carrier,
constructs durable pointer-slot unions for retained STATEFUL members, and
constructs commit-ready snapshots for retained STATELESS members. COLD_ONLY
members retain their validated live allocation and require neither artifact.

No live RSX allocation, persistent reconstruction entry, generation value, or
TPA boundary changes during this increment. Production Function 202 still does
not select the transaction path.

## Overlay sequence

The existing `R3PROF.RSX` manager slot is full, so retained preparation is
divided among three private overlays:

- `R3KCTX.RSX` expands the post-candidate handoff seed, reconstructs the durable
  plan and descriptor addresses, clears every descriptor, and publishes the
  already prepared candidate descriptor;
- `R3KEEP.RSX` streams one retained carrier into bounded scratch, derives its
  exact length, and invokes `R3CARR.RSX` and `R3META.RSX`; and
- `R3KPRE.RSX` reconciles the normalized facts with the prospective plan and
  constructs the class-appropriate retained artifact.

Each manager-slot transition uses the existing `R3MOVE.RSX` safe handoff. The
three new files therefore obey the same 1 KiB private-overlay contract as the
earlier Stage 3 phases.

## Durable transaction layout

The complete prospective profile has parallel descriptor vectors:

- six bytes per member for snapshot source, allocation size, and dispatch
  offset; and
- three bytes per member for pointer-union source and entry count.

All descriptors begin as zero. The fresh candidate receives its snapshot
descriptor. Each retained STATELESS member receives a snapshot descriptor, and
each retained STATEFUL member receives a pointer-union descriptor. Retained
COLD_ONLY members and the fresh candidate retain zero union descriptors.

Carrier streams, normalized facts, and constructor requests occupy reusable
scratch above the durable cursor. A completed retained snapshot or union is
copied downward to the cursor before the next carrier is opened. Only that
compact artifact survives the iteration. Every temporary and durable extent is
bounded by the caller's exclusive workspace high address.

## Validation and failure behavior

Every retained carrier passes the same complete checksum, relocation,
metadata, callable-service, and runtime-pointer validation as a fresh
candidate. Its allocation and reconstruction class must also match its plan
record before an artifact is published.

Any missing or renamed carrier, malformed stream, plan mismatch, overlay
failure, or insufficient workspace aborts preparation. Scratch may have
changed, but the public result remains unpublished and all live and persistent
state remains unchanged.

## Qualification

The focused Z80 integration test exercises the actual file-backed overlay
sequence and proves:

- empty-profile candidate preparation still succeeds at its exact workspace
  boundary;
- a retained BRSX-v2 STATELESS module is fully revalidated and reconstructed
  as a commit-ready snapshot;
- a retained STATEFUL module receives the sorted, duplicate-free union of its
  static relocation and runtime-pointer slots;
- descriptor vectors remain zero for classes that do not consume them;
- exact retained-snapshot workspace succeeds and a one-byte-short workspace is
  rejected; and
- success and every tested failure leave live and persistent profile state
  unchanged.

The next increment may construct the commit request from these complete plan,
snapshot, and pointer-union vectors and invoke the already qualified disk-free
commit engine. Publication must remain the final operation.
