# Engineering Specification 65: FILETEST Open Slice

## Milestone

BetterCP/M's generated A: conformance image now includes `FILETEST.COM` and
the canonical `BT*.DAT` runtime fixtures from the independent compatibility
suite. This begins file-lifecycle validation above the already completed BDOS
call/state checks.

The first selected slice is Function 15, Open File:

```text
FILETEST /GROUP:FN:15
Summary: 26 pass, 0 fail, 0 error, 0 observations, 2 not-run
```

The two not-run cases require the suite's optional explicit C:
`BTBFILE.DAT` cross-drive fixture. BetterCP/M's current Model 4 binding exposes
A: and B:, so their omission is expected and is reported by FILETEST rather
than treated as a failure. The other 26 Open cases pass through the physical
boot disk under `trs80gp`.

## Image construction

`tools/build_compatibility_disk.py` installs the current `FILETEST.COM` and all
canonical `BT*.DAT` payload files alongside ENTRYTST, BDOSTEST, MDIR, and the
ordinary BetterCP/M transient fixture. The files are installed by the same
DPB-driven image builder used for the rest of the development disk.

## Scope

This milestone deliberately does not run FILETEST's destructive or
terminal-outcome profiles. Subsequent work can advance through Close,
sequential read/write, Make, Delete, Rename, attributes, and lifecycle slices
with their required scratch-media preparation.
