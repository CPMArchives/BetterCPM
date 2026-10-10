# DIR.COM qualification — complete 2026-10-10

The retained 1.0 DIR implementation is complete. `/Z=E` is adopted as physical
directory entries used by each selected file. Automatic resident-to-transient
handoff and additional console geometry remain separate facilities; `:DIR` and
`.DIR` explicitly invoke this self-contained utility.

Final DIR.COM: version 1.0, Build 002, 8,495 bytes, SHA-256
`a846074dd2d9e4315f0a0f52caf307fafc7ec97dc2697c6f715e0e751a5348bb`.
The E-unit closure adds 12 executable bytes to Build 001. RCP, BIOS and BDOS
allocation/code are unchanged. Native ZSM4/LINK matches cross assembly exactly.

## Final physical-entry closure

Ten public cases pass on z80pack and Model 4 with RCP unloaded. Independent
raw-directory counts verify an empty file occupies 1E, the 40,000-byte fixture
occupies 2E on z80pack and 3E on Model 4, and another user's small file occupies
1E. These different results distinguish physical entries from logical 16 KiB
extents. Cases combine E units with selectors, predicates, attributes, columns,
paging and sorting; check totals, invalid options, repeated-switch precedence,
no matches, free space remaining in KiB, and next-command reset to K. Fixture
contents and attributes are preserved.

Evidence:

- `/private/tmp/dir-extents-z80pack-20261010c`
- `/private/tmp/dir-extents-model4-20261010`

The separate 60-file, two-column paging campaign includes `/P /P /A /Z=E`:
each empty file occupies 1E and the total is 60E. Space/Enter, ignored keys,
Ctrl-C restoration and next-command reset retain their existing behavior.

- `/private/tmp/dir-extents-paging-z80pack-20261010`
- `/private/tmp/dir-extents-paging-model4-20261010`

Focused checks cover 31 valid/40 invalid command forms, 264 rendered-column
cases (including independent E DWORD values), physical-entry carry/aggregation,
and allocated-space sorting with E display selected. `/VER` identifies Build
002 and existing version-query checks pass. The full 63-case public campaign passes on z80pack with final Build 002:
`/private/tmp/dir-final-build002-z80pack-20261010`. It includes the ten extent
cases alongside the previously qualified 53-case campaign.

The following historical campaign used the pre-version-query 7,585-byte binary,
SHA-256 `8547e20f9ab2581d7f43625e034e0387b4f01b7a1f5c1317ea04f44c59f4eab0`.
Its evidence is retained. The final full z80pack rerun is recorded above;
Model 4 closure adds the ten extent and four paging cases rather than rerunning
the historical 53-case campaign.

## Public combined campaign

`tools/test_dir_transient_select.py` now includes ten additional combined edge
cases in its full 53-case campaign. They combine compound selectors, duplicate
users and leading zeros, repeated terminal stars, attribute predicates/display,
record units, columns, paging and sorting. Invalid filespecs and superseded-but-
invalid options must reject the invocation rather than partially list files.
Contradictory predicates select no files. The final ordinary invocation confirms
that options reset to defaults.

All 53 cases pass on both z80pack and Model 4. Evidence:

- `/private/tmp/dir-final-combined-z80pack-20261010`
- `/private/tmp/dir-final-combined-model4-20261010`

The full Model 4 campaign runs sequentially through SUBMIT with RCP unloaded;
z80pack checks each public command with RCP unloaded. Exact selected sizes,
ordering, hidden SYS behavior, error diagnostics, column fit and output fields
are checked. Model 4 fixture contents/attributes remain intact; z80pack images
must remain byte-identical. The tested binary is preserved with the evidence.

## Paging with columns

`tools/test_dir_paging_native.py --two-columns` uses sixty empty files from a
caller DU different from the selected DU. Two columns place 42 files on the first
23-output-line page, including the heading and blank line. The first page ends
at PG041; PG042 must wait for continuation. Space/Enter continue, other keys are
ignored, and Ctrl-C aborts and restores caller DU. Attribute/record display is
combined with repeated `/P`. The next ordinary invocation resets paging,
attributes, units and columns. All media contents/attributes remain intact.

Both z80pack and Model 4 pass this four-command paging campaign. Evidence:

- `/private/tmp/dir-final-paging-z80pack-20261010`
- `/private/tmp/dir-final-paging-model4-20261010`

## Supporting qualification

The existing focused checks cover transaction failure atomicity; shared DU and
attribute semantics; multi-extent grouping; bounded buffer exhaustion; all eight
attribute masks; 246 sort cases; 450 metric cases; 176 column-width/fit cases;
165 free-space cases; and paging stack restoration/final-boundary behavior.

The earlier four-case drive-summary campaign passes on both platforms with
independent exact free-space oracles. It checks one footer per selected drive,
multiple users, multiple drives and no matches. Model 4 media match the bindings:
SYSTEM on A, DATA on B. Free-space output stays in KiB independently of `/Z=S`.

## Closure status

No retained DIR command feature remains pending. Other console widths/heights
and automatic handoff are outside this 80-column/24-row utility qualification.
