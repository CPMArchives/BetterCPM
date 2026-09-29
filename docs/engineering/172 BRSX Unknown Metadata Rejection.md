# BRSX unknown metadata rejection

## Decision

BRSX metadata version 1.0 defines record types 1, 2 and 3 and has no optional
record types. The production metadata normalizer rejects every other type. A
future metadata version may introduce explicit forward-compatible semantics;
version 1.0 never infers them by skipping an unknown record.

This is the first bounded Implementation Item 3 correction. It changes no
carrier layout, resident ABI, allocation, or accepted metadata record.

## Correction

`R3META.RSX` previously validated the framing and length of an unknown record,
then advanced to the next record. It now returns the existing transaction
failure result immediately. Publication already occurs only after the complete
metadata stream succeeds, so the correction uses the established rollback
path and requires no new state.

The added conditional branch contributes one address word to the generated ROM
overlay inventory. Its accepted total is therefore 704 rather than 703; the
18-artifact set and every other ROM ownership or placement decision remain
unchanged.

## Qualification

The focused fixture changes the first valid metadata record type to `7Fh` while
leaving its length, payload and envelope internally consistent. This isolates
record-type handling from framing failures.

`tools/test_rsxcarrier.py` proves that the normalizer returns failure, leaves
the completion byte untouched, preserves all 26 previously published fact
bytes, and leaves explicit sentinels in both the live RSX region and the
active-profile table byte-for-byte unchanged. The production coordinator
already treats every nonzero normalizer return as transaction failure before
invoking the profile planner or any publication phase.
