# Engineering Specification 77: DIRTEST Delete

## Status

The DIRTEST Delete group is physically qualified on the TRS-80 Model 4 target.

## Required results

Each destructive case ran independently under `trs80gp` using private disk
copies. All nine required cases pass:

```text
0285  P  R  Delete=00; next=FF
0286  P  R  Delete/non-target=00; next=01
0287  P  R  Wildcard/nonmatch=00; next=02
0288  P  R  Matches before/after=02; next=00
0289  P  R  Delete result/remaining=00; next=00
0290  P  R  Absent delete=FF; next=00
0291  P  R  Delete/search=00; next=FF
0294  P  R  Drive before/after=00; next=00
0295  P  R  User0 delete/user1 search=00; next=01
```

This verifies Function 19's convention, exact and wildcard identity, deletion
of every match, success and no-match results, immediate search visibility,
explicit-drive operation without changing the default drive, and user-area
isolation. Case 0294 requires a writable B: disk; its initial run without B:
was a setup error and was replaced by the passing correctly mounted run.

## Diagnostic observation

```text
0296  O  N  Open/delete/close=00; next=FF
```

The behavior of an already-open FCB after Delete is not guaranteed by CP/M
2.2 and has no conformance effect. Item 0297, Digital Research's physical
`E5h` deletion mechanism, is an implementation detail and remains out of
scope.

