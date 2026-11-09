# NDR embedded-default checks

Approved syntax is `NDR /DEFAULT [DU:]file[.RSX]`, requiring a filename.
`/SAVE` and `/LOAD` retain their existing separate BNDR-set meanings.

`tools/test_ndr_defaults.py` executes the assembled transient against a
record-oriented BDOS fixture. All 86 cases pass for the default Model 4,
checked cpmsim-fullram and checked Model II-fullram layouts. They cover both
public BRSX v2/v3 forms, repeated updates, empty defaults, conventional tails,
DU restoration, source code/metadata/checksum/length rejection, invalid live
snapshots, read-only protection, staging/backup collisions, read/write/close
failures, readback corruption, failed renames, rollback and retained recovery
files. Tests verify that record data changes only in the table/checksum and
that file attributes and live state are preserved. The rewritten provider's
actual relocated service sees its embedded table. Existing `test_ndr.py`
management/shell/PATH checks also pass on all three layouts.

[Profile receipts](profiles.json) record matching NDR.COM binaries and unchanged
512-byte provider allocations. NDR.COM is now 7,216 transient bytes; this feature
adds no resident code, CCP growth or PDS storage. Component registry (9 tests),
selected inputs (13 tests), and the existing NDR budget check pass.

`tools/qualify_ndr_defaults.py` boots privately assembled checked cpmsim media
and checks 24 commands against actual disk I/O. It saves defaults to B2 while
preserving A0 as caller, edits the live set, unloads/reloads the B2 carrier,
updates those defaults a second time, saves and reloads an empty set, and checks
a read-only copy. Host extraction compares carrier record data and actual
directory attribute bits (F1/F3, SYS and archive). The independent .NDR set is
removed before a fresh cold boot, where `RSX LOAD NDR` alone restores names.
The [booted guest receipt](booted-cpmsim.json) records the input hashes/results.

Run the guest checker from a prepared checked cpmsim source workspace, with
its BETTERCPM_BUILD_CONTEXT environment selected. Provide a fresh `--output`
directory and a patched `--simulator`; host cpmtools must be on PATH. This is
feature qualification on private development media, not release-media or
physical-hardware acceptance.
