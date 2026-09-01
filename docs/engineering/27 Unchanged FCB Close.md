# Engineering Specification 27: Unchanged FCB Close

## Milestone

BetterCP/M now implements the first deliberately bounded slice of BDOS
function 16 (Close File): closing an activated FCB whose directory state has
not changed since Open. This establishes the public Close boundary and its
result codes without performing a premature or unsafe directory write.

## Current contract

Function 16 receives an activated FCB address in `DE`. System Services saves
FCB bytes 1 through 31, locates and reactivates the corresponding directory
extent through the existing Open engine, then compares the resulting state
with the saved FCB.

If all compatibility-visible directory fields are unchanged, Close:

- returns the matching directory slot code 0 through 3;
- preserves all 33 bytes of the caller's sequential FCB; and
- performs no physical or logical disk write.

If the filename or requested extent cannot be found, Close returns `FFh`.

## Deliberate dirty-FCB rejection

If reactivation would change any saved byte from filename through allocation
map, this milestone treats the FCB as requiring a dirty close. It restores the
caller's exact saved fields, returns `FFh`, and leaves media unchanged.

This rejection is scaffolding, not the final function-16 contract. CP/M 2.2
requires Close after writes to persist compatible new directory information.
That path needs validated allocation-map merging, read-only enforcement,
directory writeback, and bounded failure recovery. Silently discarding dirty
metadata would be worse than rejecting it while those mechanisms are absent.

The implementation does not adopt DRI's private high-`S2` dirty flag or its
exact unnecessary-close result. Those representations are explicitly outside
the BetterCP/M compatibility requirement.

## System Services boundary

The twelfth provisional vector at `E821h` exposes unchanged Close. Its private
31-byte snapshot allows the current Open implementation to serve as a lookup
and canonical-state oracle without allowing a comparison attempt to modify the
caller's FCB.

Internal storage failure remains distinguished by carry and is mapped by BDOS
to the current provisional `FFh` disk failure.

## Verification

The executable tests Open the file in directory slot 1, snapshot its activated
FCB and the entire physical-sector fixture, and then Close it. They verify slot
1, exact FCB preservation, and byte-for-byte media preservation.

A second test changes `RC`, invokes Close, and verifies deliberate `FFh`
rejection, restoration of the dirty caller state, and no media change. Closing
a missing filename also returns `FFh`. The unchanged path is repeated through
an application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical components: 1,242 bytes for directory/System Services and 403
bytes for BDOS.

## Next increment

Implement the directory-record write service and dirty Close commit as one
transactional increment: verify the matching on-disk identity, enforce the
software read-only vector, merge the compatible FCB fields, write the complete
128-byte directory record, and invalidate/reconstruct affected cached state on
failure or success.
