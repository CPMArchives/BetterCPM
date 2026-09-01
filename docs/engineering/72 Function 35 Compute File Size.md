# Engineering Specification 72: Function 35 Compute File Size

## Status

Implemented and physically qualified on the TRS-80 Model 4 target.

## Scope

RANDTEST cases 0347 through 0351 exercise the required CP/M 2.2 Compute File
Size contract. Each case ran serially under `trs80gp` using a private copy of
the reproducible conformance disk.

## Result

```text
0347  P  R  Prereq/Open=03; random-I/O=00
0348  P  R  Prereq/Open=03; random-I/O=00
0349  P  R  Prereq/Open=03; random-I/O=00
0350  P  R  Prereq/Open=03; random-I/O=00
0351  P  R  Prereq/Open=02; random-I/O=00
```

All five required cases passed with zero errors. The slice verifies Function
35's calling convention, placement of the result in FCB bytes 33 through 35,
128-byte record units, maximum extent handling, and sparse virtual file size.

Case 0352 concerns the non-guaranteed accumulator value and is not part of this
required slice. Case 0353 describes Digital Research's private seek machinery
and remains deliberately out of scope.

