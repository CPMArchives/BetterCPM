# CP/M Tools binary snapshot

This directory contains the general CP/M utilities bundled on BetterCP/M
system disks. Their source is intentionally maintained in the separate
[`CPMArchives/cpm-tools`](https://github.com/CPMArchives/cpm-tools) project.

The files here are a pinned distribution snapshot, not a source-code fork.
`manifest.json` records the upstream revision and verifies every file before a
system image is created. Adopt a later upstream revision by rebuilding that
project, replacing these artifacts, and updating the manifest and checksums
together.

BetterCP/M's stock-compatible `STAT.COM` remains part of BetterCP/M. The pinned
general-tool collection does not provide a competing `STAT.COM`.

## Matching source companion

`source/` retains the pinned source, build scripts, tests and documentation
under their original GPL-2.0-or-later terms. `source-manifest.json` records
every selected upstream Git blob and SHA-256, plus the mapping from all seven
unchanged COM snapshot hashes to the same upstream revision's build products.
Prebuilt COM and DMK files are excluded from this source-only subtree; the
original COM snapshot above remains unchanged. Retain this entire companion
wherever those binaries are redistributed, including nested source archives.

The upstream source is verbatim, including its historical path defaults.
Use a private work copy. SYSINFO uses Z80ASM (`Z80ASM=/path/to/z80asm sh
source/sysinfo/build.sh`). The other six native builders accept explicit
`--cpmsim`, `--system-disk`, `--boot-template`, `--tools` and `--output` paths;
for example run `python3 source/cominfo/tools/build_cominfo.py --help` before
supplying the pinned CP/M boot media and ZSM4/LINK tool directory. See each
upstream README and BUILD.SUB for its native commands. Python 3, cpmtools,
Expect, the CP/M tools and emulator are external build prerequisites, not
newly bundled host programs. The source hash mapping establishes which pinned
source accompanies each binary; it is not a claim of a fresh seven-program
native rebuild or current BetterCP/M runtime qualification.

`python3 tools/cpm_tools_source.py` from the BetterCP/M root verifies the
source manifest and binary mapping without building or changing programs.
The package and Utilities-source builders perform this check before assembly.
