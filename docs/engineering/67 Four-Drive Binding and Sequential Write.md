# Engineering Specification 67: Four-Drive Binding and Sequential Write

## Milestone

BetterCP/M's Model 4 binding now exposes all four physical floppy selectors as
logical A: through D:. This enables FILETEST's explicit C: Make/Write case and
completes the returning sequential-write group without failures.

## Resident layout

The immutable four-drive DPH table and shared MM 790K DPB occupy
`C080h..C0CEh`, inside the previously unused gap between the system gateway and
the BDOS at `C100h`. Directory Services now uses the conventional BIOS DPH
directory buffer at `F300h` directly.

The freed `BF00h..BFFFh` page contains independent CSV and ALV workspaces for
B:, C:, and D:. Drive A retains its existing high-memory workspace. The build
therefore supports four independent logged-drive contexts without extending
the BIOS into its `F300h` buffer.

The Model 4 physical selector maps logical drives to controller masks 1, 2, 4,
and 8. The existing drive-change settling and Restore rule applies to every
transition.

## Conformance images

The compatibility builder additionally creates
`BetterCPM-Conformance-Drive-C.dmk`. It contains the canonical one-record
`BTBFILE.DAT` cross-drive fixture, whose repeated marker begins `BFILE-000`.
The command runner accepts `--drive-c` and mounts it as physical drive 2.

## Verification

The isolated explicit-drive case reports:

```text
FILETEST /0278:REPORT
RESULT PASS
OBSERVED prerequisite/Open return 02; operation/state 00
```

The complete returning Write group reports:

```text
FILETEST /GROUP:WRITE
Summary: 16 pass, 0 fail, 0 error, 5 observations, 3 not-run
```

The observations are the suite's NOT GUARANTEED characterization rows; the
not-run rows are explicitly outside FILETEST's executable scope. All required
returning cases pass.

BIOS, Directory Services, BDOS, CCP, and system regressions pass. Native CP/M
and cross builds are byte-identical for BIOS, Directory Services, BDOS, CCP,
and the expanded gateway.
