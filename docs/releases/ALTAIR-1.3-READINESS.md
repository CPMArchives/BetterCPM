# BetterCP/M 1.3 Altair release integration

This is an additional platform for OS 1.3. It does not replace the eight
published 1.3 archives or change their frozen source choice and hashes.
The Altair package has its own exact source commit, selected-source manifest,
media ledger and source offer. Until the final artifact ledger and publication
record are retained, its status is **candidate; not published**.

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
| Utility integration | Final-media queries, screen/overlay loading and native toolchain smoke in progress |
| Offline source | Pinned emulator/assembler source archive; offline emulator build passes |
| Final packages | Source/notices, deterministic archives and exact-artifact verification pending |
| Publication | Pending validated packages and release integration |

The independent suite is pinned at
`a9a878fcd2e36698c7e856654a85847a004fdd20`. Automatic groups cover CPU, ecosystem,
disk, CCP, entry, BIOS, error, directory, BDOS, file and random-record behavior.
They do not establish 627 newly executed passes. Existing 1.3 shared-core
functional evidence is reused only for matching sources and executable bodies;
the Altair BIOS, controller, geometry, cold start and media errors have their
own direct checks. Physical-device and interactive terminal applicability is
bounded by the declared emulator configuration.

The source/build and package ledgers record exact input and artifact hashes.
Maintainer review and publication are separate from an assembled or bootable
image. Historical locks and receipts remain unchanged.
