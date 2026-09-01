# Engineering Specification 80: DIRTEST File Attributes Required

## Status

All required DIRTEST file-attribute cases are physically qualified on the
TRS-80 Model 4 target.

## Result

Each case ran independently under `trs80gp` using private writable A: and B:
disk copies:

```text
0356  P  R  Read-only type byte=D4; next=4D
0357  P  R  System type bytes=54; next=CD
0358  P  R  Coexisting type bytes=D4; next=CD
0360  P  R  Function30/search slot=00; next=00
0361  P  R  Set/clear type byte=D4; next=54
0362  P  R  All-extents result/type=00; next=D4
0363  P  R  Function30 result=00; next=00
0364  P  R  Missing attribute result=FF; next=00
0366  P  R  Open/type indicator=00; next=D4
0367  P  R  Make/type indicator=00; next=D4
0370  P  R  RO delete/search=FF; next=00
0371  P  R  RO rename/search=FF; next=00
```

All twelve required cases pass with zero failures or errors. The slice
verifies the conventional high-bit representation of read-only and system
attributes, coexistence and clearing of those bits, Function 30 result and
all-extent behavior, missing-file handling, attribute reporting through Open
and Make, and read-only protection against Delete and Rename.

The latter two cases also verify that the protected directory entries remain
searchable after the rejected mutation.

Engineering Specification 81 records diagnostics 0359 and 0365. They
characterize non-guaranteed reserved-bit and exact-match behavior rather than
adding requirements to the CP/M 2.2 contract.
