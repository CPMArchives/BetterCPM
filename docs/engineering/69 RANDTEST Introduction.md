# Engineering Specification 69: RANDTEST Introduction

## Status

Implemented and physically introduced on the TRS-80 Model 4 target.

## Decision

The reproducible conformance system disk shall carry `RANDTEST.COM` alongside
the earlier compatibility executables. Random-I/O work will proceed in numbered
slices so that a stalled physical run identifies one exact CP/M contract.

## Evidence

`RANDTEST /VER` loads and returns to the BetterCP/M CCP under `trs80gp`.
The first eight physical cases pass independently:

```text
0317  P  R  Prereq/Open=03; random-I/O=00
0318  P  R  Prereq/Open=03; random-I/O=00
0319  P  R  Prereq/Open=03; random-I/O=00
0320  P  R  Prereq/Open=03; random-I/O=00
0321  P  R  Prereq/Open=03; random-I/O=00
0322  P  R  Prereq/Open=03; random-I/O=00
0323  P  R  Prereq/Open=03; random-I/O=00
0324  P  R  Prereq/Open=00; random-I/O=00
```

Case 0319's exact Function 36 boundary is also covered locally: S2=15, EX=31,
CR=127 produces little-endian random record `FF FF 00`, or record 65535. All
39 defined CP/M 2.2 BDOS functions continue to pass the local regression.

## Test-infrastructure note

The first aggregate `RANDTEST /GROUP:RANDOM` attempt left multiple batch
emulator processes using the same writable image. Those processes were stopped
without disturbing the user's interactive emulator. The command runner now
copies every mounted image into its private temporary directory by default;
`--in-place` is required when a test intentionally needs persistent media.
Numbered runs of cases 0319 through 0324 on isolated media confirmed that the
earlier blank capture was test-process interference, not a BetterCP/M failure.
