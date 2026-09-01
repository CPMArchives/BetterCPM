# Engineering Specification 64: Model 4 Two-Drive Conformance

## Decision

The TRS-80 Model 4 development platform exposes logical drives A: and B: as
physical floppy drives 0 and 1. Both temporarily use the Montezuma Micro
Extended 790K geometry, while retaining independent DPH scratch, check-vector,
and allocation-vector state.

This is a platform binding, not a restriction on BetterCP/M's portable drive
model or its future native disk formats.

## BDOS behavior

- Function 14 accepts zero-based drives 0 and 1 and commits the default drive
  only after a successful directory login.
- Function 24 accumulates A:/B: login bits.
- FCB drive byte zero uses the current drive; bytes 1 and 2 explicitly select
  A: and B: without changing the default drive.
- File operations select the appropriate directory context before access.
- Software write-protection and selective-reset bits are evaluated per drive.

## Model 4 physical rule

Port `F4h` selects drives with masks 1, 2, 4, and 8. Because the WD controller
track register is shared while each drive has an independent head position, a
physical drive change must allow motor settling and issue Restore before the
requested Seek. Omitting Restore can make a new drive appear to be on the old
drive's track and causes otherwise valid directory login to fail.

## Workspace

Drive B's CSV and ALV occupy the reserved `BF80h..BFD1h` gap after the
directory transfer buffer and before the `C000h` gateway. They must not overlap
the growing BIOS image or drive A's vectors.

## Generated fixtures

`tools/build_compatibility_disk.py` now creates:

- `BetterCPM-Conformance-First-Pass.dmk` for drive A, containing the test tools;
- `BetterCPM-Conformance-Drive-B.dmk` for drive B, containing `BDSA.TMP` and
  `BDSB.TMP` under their required CP/M names.

The command runner accepts `--drive-b` and resolves both image paths before it
changes to its temporary capture directory.

## Verification

The paired images booted under `trs80gp` and completed:

```text
BDOSTEST /SAFE
Summary: 56 pass, 0 fail, 0 error, 0 observations
```

The focused Function 14 physical test also completed with one pass and no
failures, confirming that B: is selected and logged through the real BIOS path.
