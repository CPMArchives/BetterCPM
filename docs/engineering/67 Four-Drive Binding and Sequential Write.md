# Engineering Specification 67: Four-Drive Binding and Sequential Write

## Milestone

BetterCP/M's Model 4 binding now exposes all four physical floppy selectors as
logical A: through D:. This enables FILETEST's explicit C: Make/Write case and
completes the returning sequential-write group without failures.

## Resident layout

The four-drive DPH table and shared MM 790K DPB originally occupied
`C080h..C0CEh`. Specification 90 corrects that provisional choice: addresses
below the BDOS entry are TPA, not protected gateway space. The tables now live
at `C900h..C94Eh`. Directory Services continues to use the conventional BIOS
DPH directory buffer (now at `EC80h`) directly.

Independent CSV and ALV workspaces for all four drives now follow the DPB at
`C950h..CA97h`. The build therefore supports four independent logged-drive
contexts without placing mutable disk state in the TPA or extending the BIOS
into its directory buffer.

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
