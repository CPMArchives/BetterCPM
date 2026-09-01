# Engineering Specification 70: Function 33 Random Read

## Status

Implemented and physically qualified on the TRS-80 Model 4 target.

## Scope

RANDTEST cases 0326 through 0333 exercise the required CP/M 2.2 Random Read
contract. Each case ran independently under `trs80gp` using a private copy of
the reproducible conformance disk.

## Result

```text
0326  P  R  Prereq/Open=03; random-I/O=00
0327  P  R  Prereq/Open=03; random-I/O=00
0328  P  R  Prereq/Open=03; random-I/O=00
0329  P  R  Prereq/Open=03; random-I/O=00
0330  P  R  Prereq/Open=03; random-I/O=00
0331  P  R  Prereq/Open=03; random-I/O=01
0332  P  R  Prereq/Open=03; random-I/O=04
0333  P  R  Prereq/Open=03; random-I/O=06
```

All eight required cases passed with zero errors. This verifies the Function
33 calling convention, DMA destination, successful data transfer, preservation
of the random position across repeated reads, unwritten-record behavior,
missing-extent status `04h`, and out-of-range status `06h`.

Case 0334 is diagnostic and not guaranteed by CP/M 2.2; it is not part of this
required slice.

