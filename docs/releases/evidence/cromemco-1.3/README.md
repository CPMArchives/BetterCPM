# Cromemco 1.3 focused acceptance — 28 November 2026

All eight focused gates passed on the four exact media hashes in `summary.json`.
`receipts-and-transcripts.tar.gz` retains per-gate machine-readable results and
guest transcripts. Package/source-export proof and publication are subsequent
steps; these original execution receipts are not rewritten to imply publication.

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
