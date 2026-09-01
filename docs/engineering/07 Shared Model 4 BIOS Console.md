# Engineering Specification 07: Shared Model 4 BIOS Console

Status: Implemented and verified
Date: 2026-09-01

## Result

The compatibility BIOS is now bound to the real TRS-80 Model 4 video and
matrix-keyboard implementation. Stage one and the BIOS include one shared
`m4cons.inc`; there are no parallel console-driver copies.

The shared module owns initialization, screen clearing, cursor state, character
output, keyboard status, blocking input, release debounce, matrix scanning,
and the initial ASCII table. The bring-up HAL aliases its console calls to
these routines. The BIOS platform binding aliases `CONST`, `CONIN`, and
`CONOUT` physical operations to the same routines.

## Layered verification

The existing `trs80gp` boot test continues to execute the shared hardware code
and verifies screen output plus a matrix-level `K` press and release. The BIOS
direct-call test executes the assembled BIOS adapter and substitutes isolated
device responses to verify exact compatibility-boundary register semantics.
The production BIOS build includes the shared Model 4 code.

This provides composition evidence without loading the BIOS into the current
one-sector diagnostic boot path. A combined resident-system boot remains a
separate future integration milestone.

## Sizes and hashes

Stage one is now 508 bytes; the three-byte increase is the tail transfer from
HAL initialization to shared console initialization. The BIOS is 323 bytes.

```text
4bd24100e1d621162e8390277bee7dea71eb8a2f50b70f3c31440c99059202e8  stage1.bin
0747e26c52dc0278a8e88cdf481d8699f1e66d4666949955f17525fe3dbd1e98  bios.bin
```

Both remain byte-identical between native CP/M ZSM4/Digital Research LINK and
the host cross assembler.

## Next increment

Define the first real logical drive's DPH and DPB and implement a 128-byte
logical-sector read path over the Model 4's 512-byte physical sectors. This
begins CP/M disk semantics without selecting BetterCP/M's eventual native
filesystem format.
