# Engineering Specification 83: DIRTEST Search Continuation Diagnostics

## Status

All non-guaranteed DIRTEST Search Continuation diagnostics have been physically
observed on the TRS-80 Model 4 target.

## Result

Each diagnostic ran independently under `trs80gp` using private writable A:
and B: disk copies:

```text
0541  O  N  Post-RET/no oracle=00; next=FF
0544  O  N  Lowercase FCB search=FF; next=00
0547  O  N  Lifecycle/no oracle=00; next=FF
0548  O  N  Physical order slots=00; next=01
0549  O  N  Invalid search/no oracle=10; next=FF
```

Every run completed with one pass, zero failures, zero errors, and one
observation. The cases characterize continuation after program return,
application-built lowercase FCB matching, continuation across a program
lifecycle boundary, physical enumeration order, and the invalid-drive Search
First result.

These results are implementation evidence, not portable CP/M 2.2 guarantees.
They do not add requirements to the four required Search Continuation passes
recorded in Engineering Specification 82.

## Search Continuation accounting

The DIRTEST Search Continuation group is now closed:

- 4 required cases pass.
- 5 diagnostic cases have been observed.
- No applicable cases remain untested.

