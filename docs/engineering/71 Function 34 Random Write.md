# Engineering Specification 71: Function 34 Random Write

## Status

Implemented and physically qualified on the TRS-80 Model 4 target.

## Scope

RANDTEST cases 0335 through 0346 exercise the required CP/M 2.2 Random Write
contract. Each case ran serially under `trs80gp` using its own private copy of
the reproducible conformance disk.

## Result

```text
0335  P  R  Prereq/Open=02; random-I/O=00
0336  P  R  Prereq/Open=02; random-I/O=00
0337  P  R  Prereq/Open=02; random-I/O=00
0338  P  R  Prereq/Open=02; random-I/O=00
0339  P  R  Prereq/Open=02; random-I/O=00
0340  P  R  Prereq/Open=02; random-I/O=00
0341  P  R  Prereq/Open=02; random-I/O=00
0342  P  R  Prereq/Open=02; random-I/O=00
0343  P  R  Prereq/Open=02; random-I/O=00
0344  P  R  Prereq/Open=02; random-I/O=00
0345  P  R  Prereq/Open=02; random-I/O=06
0346  P  R  Prereq/Open=02; random-I/O=02
```

All twelve required cases passed with zero errors. The slice verifies Function
34's calling convention, data transfer, successful allocation, sparse holes,
virtual file length, working FCB fields, preservation of the random-record
position, absence of an automatic extent switch, and close/reopen persistence.
It also verifies exact status `06h` for an invalid random extent and `02h` when
the disk allocation space is full.

