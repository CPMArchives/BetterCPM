# Engineering Specification 79: DIRTEST Rename Diagnostics

## Status

The applicable non-guaranteed DIRTEST Rename diagnostics have been physically
observed on the TRS-80 Model 4 target.

## Result

Each diagnostic ran independently under `trs80gp` using private writable A:
and B: disk copies:

```text
0308  O  N  Collision result/matches=FF; next=01
0310  O  N  Open/renamed-close=00; next=FF
0311  O  N  Physical search slots=00; next=01
0315  O  N  Invalid drive/no oracle=10; next=FF
```

Every run completed with one pass, zero failures, zero errors, and one
observation. These cases characterize behavior that CP/M 2.2 does not fully
guarantee: destination collision handling, closing an FCB after its file has
been renamed, physical directory-slot placement, and the exact invalid-drive
result.

The results are evidence, not additional compatibility requirements. They do
not change the ten required Rename passes recorded in Engineering
Specification 78.

## Rename accounting

The DIRTEST Rename group is now closed:

- 10 required cases pass.
- 4 diagnostic cases have been observed.
- 4 cases remain outside the BetterCP/M CP/M 2.2 conformance scope: wildcard
  Rename (0309), timestamps (0312), the private DRI in-place algorithm (0313),
  and directory compaction (0316).

