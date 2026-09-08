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
