# Engineering Specification 05: Initial BIOS Scaffold

Status: Implemented and structurally verified  
Date: 2026-09-01

## Result

BetterCP/M now produces an independently assembled CP/M 2.2 compatibility
BIOS artifact. It is not yet loaded by the diagnostic boot path and its
`F000h` origin is a test placement, not a resident-memory decision.

The artifact is 131 bytes and exposes all 17 required three-byte `JP` entries:

| Index | Offset | Entry |
|---:|---:|---|
| 0 | 00h | BOOT |
| 1 | 03h | WBOOT |
| 2 | 06h | CONST |
| 3 | 09h | CONIN |
| 4 | 0Ch | CONOUT |
| 5 | 0Fh | LIST |
| 6 | 12h | PUNCH |
| 7 | 15h | READER |
| 8 | 18h | HOME |
| 9 | 1Bh | SELDSK |
| 10 | 1Eh | SETTRK |
| 11 | 21h | SETSEC |
| 12 | 24h | SETDMA |
| 13 | 27h | READ |
| 14 | 2Ah | WRITE |
| 15 | 2Dh | LISTST |
| 16 | 30h | SECTRAN |

The source retains a dated patch comment explaining why incomplete services
must not cause removal or reordering of the historical vector.

## Implemented compatibility behavior

- `BOOT` and `WBOOT` are explicitly non-returning. Until CCP/BDOS integration,
  they stop safely rather than return to an invalid caller.
- `CONST` normalizes platform status to exactly `00h` or `FFh` without
  consuming input.
- `CONIN` clears the returned parity bit.
- `CONOUT` passes the byte in C directly to the platform operation.
- Unassigned `LIST` and `PUNCH` operations are null outputs.
- Unassigned `READER` immediately returns Ctrl-Z.
- `HOME`, `SETTRK`, `SETSEC`, and `SETDMA` maintain the required persistent,
  single-context disk state.
- `SELDSK` records the request but returns HL=0 because no DPH exists yet.
- `READ` and `WRITE` return nonzero because no logical-sector implementation
  exists yet.
- `SECTRAN` implements identity translation for a null XLT and table lookup
  for a non-null XLT.
- `LISTST` returns not-ready for the unassigned list device. Its general result
  encoding remains policy-pending.

Returning explicit absence or failure is important: a scaffold must not claim
that a drive or transfer succeeded before the corresponding DPH, DPB, and
128-byte logical-sector implementation exist.

## Platform fixture

`biosplat.inc` currently supplies build-only console stubs. It makes the BIOS
artifact independently reproducible without duplicating the stage-one Model 4
driver. A later TRS-80 resident-platform module will replace this fixture and
share the proven physical console implementation.

The compatibility-visible CP/M BIOS and BetterCP/M's internal hardware
boundary may share implementation; they need not become two complete driver
stacks.

## Verification

```sh
python3 tools/build_bios.py
python3 tools/test_bios.py
python3 tools/build_native_bios.py
```

The structural test verifies all 17 opcodes, spacing, and in-image targets.
The native build uses ZSM4 and Digital Research LINK 1.3 under CP/M and is
byte-identical to the host cross-build.

```text
00332dd5105a061288c329e8024358d32db38264f77a7af25c2a9be8ea04e7d5  bios.bin
```

## Next increment

Build a direct-call BIOS conformance fixture that executes the character and
sector-translation entries and observes raw registers. This will test behavior,
not merely vector structure, before any CCP or BDOS depends upon the artifact.
