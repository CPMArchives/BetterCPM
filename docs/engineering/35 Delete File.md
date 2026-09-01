# Engineering Specification 35: Delete File

## Milestone

BetterCP/M now implements BDOS function 19 (Delete File). Applications may
delete an exact filename or use CP/M `?` wildcards across the eight-byte name
and three-byte type. Every matching extent for the current user is removed.

## Call and result contract

Function 19 receives an FCB in `DE`. Drive byte zero selects the current drive
and one selects drive A in FCB notation. `A=00h` reports that at least one
extent was deleted. `FFh` reports no match, invalid drive, software or file
protection, or a live pending-allocation conflict. Internal storage failure is
carried separately and currently maps to `FFh` at the BDOS boundary.

Filename and directory attribute bits are masked during matching. Extent fields
in the caller FCB do not restrict deletion: all matching extents are targets.

## Read-only preflight

Delete uses two complete directory passes. The first finds every matching
extent without changing media. If any match has its T1 read-only attribute set,
the complete operation is rejected. This prevents a wildcard or multi-extent
request from deleting writable extents before discovering a protected one.

Software drive protection is rejected before directory access. Delete also
refuses to run while the pending-allocation journal contains entries; otherwise
it could invalidate the ownership proof needed to Close an unrelated dirty
FCB. This restriction can be narrowed after full open-file lifecycle tracking
exists.

## Mutation and allocation coherence

The second pass changes the user byte of each matching directory entry to
`E5h`. A directory record is written only when it contained a match. After all
writes, cached login state is invalidated; the next filesystem operation
reconstructs the ALV from surviving extents, thereby releasing every block
owned only by the deleted file.

Deletion spanning multiple directory records cannot be globally atomic on a
CP/M disk. If a later physical write fails, earlier record writes may already
be durable. BetterCP/M reports storage failure and invalidates its cache so the
next operation reconstructs coherent state from the actual medium rather than
assuming either complete success or complete rollback.

## Verification

Executable tests create two wildcard-matching extents with distinct allocated
blocks, delete both, and verify ALV reconstruction releases those blocks. A
second two-extent fixture marks one extent read-only and proves that neither
entry changes. Tests also cover software protection, the live allocation-
journal guard, and dispatch through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services and BDOS binaries.

## Next increment

Implement BDOS function 23 (Rename File) with the same two-pass protection and
wildcard discipline, duplicate-target rejection, and multi-extent handling.
