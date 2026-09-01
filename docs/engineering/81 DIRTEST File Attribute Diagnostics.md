# Engineering Specification 81: DIRTEST File Attribute Diagnostics

## Status

The two non-guaranteed DIRTEST file-attribute diagnostics have been physically
observed on the TRS-80 Model 4 target.

## Result

Each diagnostic ran independently under `trs80gp` using private writable A:
and B: disk copies:

```text
0359  O  N  Reserved t3/result=D0; next=00
0365  O  N  Exact Function30 slot=00; next=00
```

Each run completed with one pass, zero failures, zero errors, and one
observation. Case 0359 records BetterCP/M's handling of reserved bits in the
third type character. Case 0365 records the directory slot returned for an
exact Function 30 match.

These results characterize implementation behavior that CP/M 2.2 does not
guarantee. They do not add requirements to the twelve required File Attributes
passes recorded in Engineering Specification 80.

## File Attributes accounting

The DIRTEST File Attributes group is now closed:

- 12 required cases pass.
- 2 diagnostic cases have been observed.
- No applicable cases remain untested.

