# DUP direct operation entry points

DUP Build 002 introduced (retained in current Build 003) the [1.0 command-line contract](DUP%20Specification.md):

```text
DUP /FORMAT drive:
DUP /COPY source: destination:
DUP /CHECK drive:
```

The complete command tail is parsed before initialization. Operation keywords
are case-insensitive and must be complete. FORMAT/CHECK accept A-D; COPY accepts
A-D source and B-D destination. Only a drive letter and colon are accepted;
DU selectors, filenames, extra operands and unknown options are errors.
`/VER` retains the existing standalone gate.

A single dispatch gate and supplied-drive adapter enter the existing engines.
All media validation and destructive confirmations remain in those engines.
Direct results skip ordinary completion pauses and return to the CCP through
binding cleanup. Restoration failure retains the interactive retry; it cannot
be bypassed by direct invocation. There is no confirmation-bypass option.

Current Build 003 DUP is 8,267 bytes. The original Build 002 command-line
change added 378 transient bytes; that historical delta is not the current
binary size.
BIOS, BDOS, RCP and permanent RAM allocations are unchanged. No new disk backend
service or command-tail extension is introduced.

## Focused checks

`test_dup_command_line.py` checks accepted and rejected syntax, supplied drive
values, dispatch into the correct existing engine, one-shot return behavior,
and standalone/invalid-combined version queries.

`test_z80pack_dup_command_line.py` uses disposable disks to exercise declined
FORMAT and COPY confirmation, protected-system FORMAT refusal, full represented payload
copy equality, source preservation and read-only CHECK. It waits for the CCP
prompt before entering subsequent commands.

`test_z80pack_dup_format.py --direct` checks full uniform formatting and
verification; `--unsupported --direct` checks mixed-sector rejection with no
target modification. The existing interactive uniform formatting case also
passes with the new binary.

`test_dup_operations.py copy --direct` retains the Model 4 observation points
and media comparisons while bypassing the operation/drive menus. It covers
confirmation refusal, temporary binding restoration, source/system preservation,
payload equality, subsequent direct CHECK and return to the command environment.

`test_dup_operations.py abort --direct` also passes on the final binary:
Ctrl-C interruption preserves source/system media, restores the destination
binding and returns to the command environment.

These are focused conformance checks; final distribution/release qualification
remains separate.
