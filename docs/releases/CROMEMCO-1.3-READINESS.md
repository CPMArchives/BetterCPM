# BetterCP/M 1.3 Cromemco release integration

Status: **release candidate complete; review, merge and publication pending**. This adds a platform for OS 1.3 and does not replace
the existing platform archives or alter their frozen identities.

Target: pinned serial z80pack Cromemco Z-1, Z80, bank-zero 64 KiB RAM, FDC UART,
16FDC and four fixed 8-inch SSSD drives. Default unloaded COM capacity is
57,344 bytes. See [installation](../platform/CROMEMCO-INSTALLATION.md) and
the [adapter target sheet](../../src/platform/cromemco/README.md).

| Gate | Executed acceptance |
| --- | --- |
| Complete media | Manifest-selected System and three Utilities disks, filesystem checks and independent file-by-file readback |
| Loader/memory | Release System boot, destructive 56 KiB TPA test, warm reconstruction and checked-carrier refusal |
| Shared core | BDOS, CCP, RCP and protected file-loader bodies identical to the matching flat-RAM build; released core sources unchanged |
| Installation | Native SYSGEN preserves a populated filesystem; independent installed cold boot |
| Saved settings | STARTUP, IOBYTE, PDS/MCL/VAR cold persistence; NDR and PATH across transient returns |
| Disk management | Full erase/check/copy with whole-image readback equality |
| Errors and routing | Missing/malformed/read-only media, caller DMA and media preservation, media change/reset and all 256 IOBYTE values |
| Utilities | 45 shipped version queries, HELP through all three integrated personalities, NOAH overlay add/test/extract, native ZSM4/LINK |
| Compatibility | 269 independent automatic assertions, zero failures/errors |
| Display transport | Delayed transmit-ready polling and preserved register/flag state; all three complete paths fit their existing footprint limits |
| Offline emulator | Pinned source archive builds without a network or graphics libraries; native binary matches the tested build |
| Final archives | PASS: frozen-source build and exported-source rebuild reproduce all four accepted images and the exact emulator; unpacked native launcher, banner and HELP pass |
| Publication | Branch/review, merge and additive asset publication remain separate from candidate qualification |

TCAP modules use MCON backend bit 16 and the exact private BIOS binding. Their
leaf calls poll the timed UART without monitor recursion. The complete ANSI
display path is 1,759 bytes, within the existing 1,792-byte limit; ADM3A and
VT52 remain within 1,280 bytes. No permanent display reservation is added.

The upstream host UART input correction is retained and tested separately.
Firmware, emulator sources and original notices accompany the offline kit.
The first release explicitly defers hard disks, other floppy geometries,
banked services, graphics, auxiliary serial and physical hardware.

The independent suite is pinned at
`a9a878fcd2e36698c7e856654a85847a004fdd20`. This is focused platform acceptance,
not a claim of 627 newly executed cards. Shared-core evidence is reused only
where the executable bodies and source boundaries match.
