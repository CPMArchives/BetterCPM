# Engineering Specification 78: DIRTEST Rename Required

## Status

All required DIRTEST Rename cases are physically qualified on the TRS-80
Model 4 target.

## Result

Each case ran independently under `trs80gp` using private writable A: and B:
disk copies:

```text
0298  P  R  Rename/search=00; next=00
0299  P  R  Rename/old search=00; next=FF
0300  P  R  Same-drive rename/search=00; next=00
0301  P  R  Rename/size records=00; next=81
0302  P  R  Rename result=00; next=00
0303  P  R  Missing-source rename=FF; next=00
0304  P  R  Old/new search=FF; next=00
0305  P  R  Rename/read=00; next=00
0306  P  R  User1 rename/user0 search=00; next=FF
0307  P  R  Default drive before/after=00; next=00
```

All ten required cases pass with zero errors. The slice verifies Function 23's
calling convention and two-name FCB layout, same-drive destination semantics,
renaming all extents, success and missing-source results, old/new identity
transition, preservation of file data and user ownership, and explicit-drive
operation without changing the default drive.

Rename diagnostics 0308, 0310, 0311, and 0315 remain to be observed. Items
0309, 0312, 0313, and 0316 describe wildcard, timestamp, private-algorithm, or
directory-compaction behavior outside the required CP/M 2.2 contract.

