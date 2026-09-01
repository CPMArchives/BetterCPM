# Engineering Specification 08: MM 790K Drive Definition

Status: Implemented and verified
Date: 2026-09-01

## Result

The compatibility BIOS now exposes drive A as the temporary Montezuma Micro
Extended 790K development format. Other drives remain unavailable, and disk
reads and writes still return failure until physical transfer support exists.

This is a new BetterCP/M DPH/DPB implementation. It incorporates no Montezuma
Micro BIOS code.

## Logical geometry

One CP/M logical track spans a complete two-sided physical cylinder:

```text
2 sides * 10 physical sectors * 512 bytes / 128 bytes = SPT 80
```

Consequently `OFF=2` reserves two cylinders, or 20,480 bytes. Treating a side
as a CP/M track would reserve only half the documented system area and is
therefore incorrect for this format.

The DPB is:

| Field | Value |
|---|---:|
| SPT | 80 |
| BSH | 4 |
| BLM | 15 |
| EXM | 0 |
| DSM | 394 |
| DRM | 127 |
| AL0/AL1 | C0h/00h |
| CKS | 32 |
| OFF | 2 |

The DPH uses identity `SECTRAN`, a shared 128-byte directory buffer, a
32-byte checksum vector, and a 50-byte allocation vector. Its three scratch
words are present in the historical order required by BDOS.

## Compatibility behavior

- `SELDSK` with C=0 returns the drive-A DPH in HL.
- `SELDSK` for every other drive returns HL=0.
- The requested drive remains recorded in the BIOS single disk context.
- `READ` and `WRITE` continue to return nonzero rather than claim unsupported
  transfers succeeded.

The direct-call fixture follows the returned DPH pointer and verifies every
DPB value from the assembled binary. Native CP/M and cross builds produce the
same 571-byte BIOS artifact.

```text
4515a51cf66fb73b334aa5d2721daca66587f891542b7e79cfa69cbf963f3014  bios.bin
```

## Preserved implementation history

The source contains a dated patch comment at the DPH explaining the
whole-cylinder track interpretation. Workspace was initially expressed using
a host-assembler `DS size,fill` extension; native ZSM4 rejected it. The active
source uses canonical repeated `DB 0`, preserving deterministic identical
output without retaining nonportable syntax.

## Next increment

Define and verify the Model 4 physical-read operation for arbitrary cylinder,
side, and sector. Then map each CP/M sector number 0-79 to one quarter of the
corresponding 512-byte physical sector and copy that 128-byte quarter to the
selected DMA address. Writes remain deferred until read-modify-write behavior
and error recovery are specified.
