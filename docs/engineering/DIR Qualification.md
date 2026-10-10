# DIR.COM combined qualification — 2026-10-10

This campaign qualifies the implemented transient DIR feature set together.
It does not admit `/Z=E`: the physical-entry versus logical-16-KiB definition
still needs a decision and implementation. Automatic resident-to-transient
handoff is separate; `:DIR` and `.DIR` explicitly invoke the transient.

Tested DIR.COM: 7,585 bytes, SHA-256
`8547e20f9ab2581d7f43625e034e0387b4f01b7a1f5c1317ea04f44c59f4eab0`.
This increment changes tests/documentation only. The previously qualified native
ZSM4/LINK binary is byte-identical to host assembly; no resident allocation changes.

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

## Remaining closure

- Decide and implement `/Z=E`, then qualify its formatting, totals, column widths
  and interactions. Existing `/S=Z` remains allocated-space sorting.
- Other console widths/heights and automatic handoff are separate from this
  80-column/24-row DIR qualification.
