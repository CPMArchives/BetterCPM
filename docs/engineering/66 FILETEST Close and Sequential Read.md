# Engineering Specification 66: FILETEST Close and Sequential Read

## Milestone

After the complete Function 15/Open slice, BetterCP/M advances through the
independent FILETEST groups for Function 16/Close File and Function 20/Read
Sequential on the physical Model 4 boot path.

## Results

```text
FILETEST /GROUP:FN:16
Summary: 2 pass, 0 fail, 0 error, 0 observations, 0 not-run

FILETEST /GROUP:FN:20
Summary: 22 pass, 0 fail, 0 error, 0 observations, 1 not-run
```

The single sequential-read not-run case requires the optional explicit C:
cross-drive fixture. It is unavailable in the current A:/B: Model 4 binding
and is classified by FILETEST rather than counted as a failure.

## Coverage

The physical tests independently exercise unchanged and incompatible Close
behavior and the sequential-read contracts for record transfer, return state,
DMA replacement, EOF, FCB position advancement, and multi-record/extent
fixtures. All applicable required cases pass through the public BDOS gateway,
directory services, BIOS, and generated DMK image under `trs80gp`.

No implementation correction was required by these slices. Their value is
external confirmation that the previously implemented file path behaves as
specified when loaded as an ordinary CP/M transient program.
