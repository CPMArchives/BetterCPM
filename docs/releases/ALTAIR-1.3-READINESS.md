# BetterCP/M 1.3 Altair release integration

This is an additional platform for OS 1.3. It does not replace the eight
published 1.3 archives or change their frozen source choice and hashes.
The Altair package has its own exact source commit, selected-source manifest,
media ledger and source offer. The exact artifact and acceptance records are retained in
[evidence/altair-1.3-banner](evidence/altair-1.3-banner/README.md). Its status is
**published emulator platform on 28 November 2026**.
See the [publication record](evidence/altair-1.3-publication/README.md) for live
downloads, verified asset digests and the unchanged original release assets.
Frozen product source: `6bfb621b6348e1f3782e2f12be4512fe37197306`
(tree `9eac4485b52c47d77b1a44bbf121774e923a9a92`).

The target is Z80 / 64 KiB / 88-2SIO / Tarbell 1011D under the pinned serial-only
z80pack emulator. No physical hardware, 8080, graphics or modem claim is made.
See [installation](../platform/ALTAIR-INSTALLATION.md) and
[adapter details](../../src/platform/altair/README.md).

| Gate | Current evidence |
| --- | --- |
| Four complete media volumes | Fresh manifest build, filesystem checks, independent file-by-file readback |
| Boot and memory | Actual release cold startup, 57,344-byte default COM |
| Shared core | Identical BDOS/CCP/RCP/file-loader bodies against the matching flat-RAM build; unchanged 1.3 core inputs |
| Installation | SYSGEN preserves populated destination filesystem; independent installed cold boot |
| Configuration | Saved STARTUP/IOBYTE and MCL/VAR cold settings; transient return, NDR and PATH |
| Disk management | Full 77-track erase/read-check and whole-disk copy/readback equality |
| Error handling | Missing/wrong-sized/read-only media; failed reads preserve DMA, failed writes preserve media; media-change/reset |
| Console routing | All 256 IOBYTE values on the emitted BIOS |
| Compatibility | 269 independent automatic assertions, zero failures/errors; separate from manual/external cards |
| Utility integration | PASS: 45 final-media identity queries, all three integrated screen personalities, HELP/NOAH and native ZSM4/LINK |
| Offline source | PASS: pinned emulator/assembler sources; offline first launch and exported Source ZIP rebuild |
| Final packages | PASS: source/notices, deterministic archives and exact-artifact verification; all four images reproduce |
| Publication | PASS: PR #696 merged; four additive files published with verified digests; existing assets unchanged |

The independent suite is pinned at
`a9a878fcd2e36698c7e856654a85847a004fdd20`. Automatic groups cover CPU, ecosystem,
disk, CCP, entry, BIOS, error, directory, BDOS, file and random-record behavior.
They do not establish 627 newly executed passes. Existing 1.3 shared-core
functional evidence is reused only for matching sources and executable bodies;
the Altair BIOS, controller, geometry, cold start and media errors have their
own direct checks. Physical-device and interactive terminal applicability is
bounded by the declared emulator configuration.

The source/build and package ledgers record exact input and artifact hashes.
Maintainer publication authorization was received after review; the merged
platform and verified download assets are now published. Historical locks and receipts remain unchanged.
