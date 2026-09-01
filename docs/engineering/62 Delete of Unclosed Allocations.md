# Engineering Specification 62: Delete of Unclosed Allocations

## Milestone

BetterCP/M now permits Delete to retire allocations journalled by the same FCB
without requiring an intervening Close. This allows repeated create, Function
40, read, and delete lifecycles while retaining protection against unrelated
dirty files.

## Defect

The first corrected Function 40 compatibility case passed, but its cleanup
Delete was rejected because the allocation journal was nonempty. The suite did
not Close the scratch file or inspect the cleanup result. Its next two identical
cases therefore encountered the leftover `ENT40.$$$` and failed.

## Contract

Delete preflights the pending journal. It may proceed only when every live
entry belongs to the FCB being deleted. Journal entries are removed only after
all matching directory extents have been deleted successfully. An unrelated
pending FCB still prevents Delete, and a failed deletion retains the journal.

## Verification

The BDOS regression performs two consecutive Make, Function 40 record-2 write,
same-FCB Random Read, and Delete cycles. Each cycle verifies zero records 0 and
1, caller data in record 2, successful deletion, and reuse of the scratch name.

The regenerated compatibility disk completes the full physical
`ENTRYTST /SAFE` sequence under `trs80gp` with 25 passes, zero failures, zero
errors, and zero observations, then returns normally to the CCP prompt.

Native CP/M and cross builds must remain byte-identical.
