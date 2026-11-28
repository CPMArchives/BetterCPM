# Cromemco 1.3 focused acceptance — 28 November 2026

All eight focused gates passed on the four exact media hashes in `summary.json`.
`receipts-and-transcripts.tar.gz` retains per-gate machine-readable results and
guest transcripts. Final package/source-export proof also passed; publication is recorded in `publication.json`.
These execution receipts do not imply publication.

The gates cover loader/56 KiB TPA/reconstruction, populated-media installation,
saved settings and MCL/VAR/NDR/PATH, complete erase/check/copy, physical faults
and media resets, all IOBYTE routes, 45 shipped utility queries, three integrated
display personalities with HELP, NOAH overlays, native ZSM4/LINK, 269 independent
compatibility assertions, and delayed-UART display transport/footprint checks.
Shared BDOS/CCP/RCP/file-loader bodies match the established flat-RAM build.

`collect_cromemco_acceptance.py` may reuse these executed gates only after a
frozen-source build reproduces every complete media volume and the checked
shared/display executable bodies. `verify_cromemco_package.py` separately
requires exported-source emulator/media rebuild equality and actual execution
of the unpacked native launcher. Hard disks and other hardware remain deferred.

Final archives use frozen source commit `b417ff8591239d2c4f61cb0048efbdadfeb52b06`.
`package-verification.json` records the successful offline source rebuild and
actual unpacked native launch. `packaged-console.txt` retains that guest session.
`artifact-ledger.json.gz` contains the exact package member ledger, source and
media identities; `SHA256SUMS-Cromemco-1.3.txt` identifies the distributable files.
This evidence-only follow-up does not change the frozen package source.
