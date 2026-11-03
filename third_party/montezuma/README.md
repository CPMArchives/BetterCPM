# Montezuma Micro runtime utility

`MDIR.COM` is an unmodified 3,072-byte utility recovered from the user-supplied
Montezuma Micro CP/M boot disk `MMCPM.dmk`.

- SHA-256: `6ba323d6b9df4ef903cc8916e231f4d554e11cb01a016483969a4dda8e31488b`
- CP/M directory allocation: 16-bit blocks 37 and 38, 24 records
- Extraction: 512-byte sectors in Montezuma logical skew order

The binary is retained as third-party software and is not part of BetterCP/M's
original source. The retained [DRI CP/M permission](../dri-link/LICENSE)
covers CP/M and its derivatives. We have no record establishing that its grantor
controlled the rights to Montezuma's independently contributed MDIR utility.

## Disk format catalogue

`DISK.FDF` is the unmodified 10,752-byte Montezuma Micro format catalogue
extracted from the downloaded distribution during reconstruction. It is
third-party reference data, not original BetterCP/M source.

SHA-256: `9635fc0e93838f28c96aa274033fae1c8eb747db97fe4b2bd04337e39a286d66`.

The two System disks carry the same 108-entry BetterCP/M `DISK.FDB`.
Its editable source is BetterCP/M FDF v1 text in `metadata/DISK.FDF` and
`metadata/release-formats.fdf`. The 107 compatibility entries preserve their
IDs and order, including independent definitions for MMF017 and MMI008.
BCPM780 adds the native 780K Model 4 System layout.

All six packages and their nested source archives exclude the original
Montezuma DISK.FDF, utilities and disassemblies. The recorded “distribution
rights undetermined” notice concerns historical format data retained in
the native catalogue, including definitions recovered from CONFIG.COM.
See [1.0 format support](../../docs/platform/FORMAT-SUPPORT-1.0.md).

The retained 2001/2022 Digital Research correspondence does not establish a
grant of Montezuma's separate contributions. The supplied 2005 MMCPM232
disassembly README describes unsuccessful attempts to reach the original
author and expresses doubt about that archive's authorization.

[Computer News 80, archived by the Computer History Museum](https://archive.computerhistory.org/resources/access/text/2019/12/102794144-05-03-acc.pdf)
vol. 3, no. 11, p. 3, reports that Montezuma Micro president John Lancione
and CN80 agreed to exclusive CN80 distribution of the Model 4 CP/M system. This is a research lead about historical distribution. It establishes
neither present ownership nor downstream permission for this project.

Package freeze remains on hold pending the remaining release checks.

### Customer update service and format decisions

The March 1985 issue of [80 Micro](https://colorcomputerarchive.com/repo/Documents/Magazines/80%20Micro/1985/80%20Micro%20-%208503%20-%20March%201985.pdf)
describes a customer sending Montezuma a disk and format information and
receiving the disk back with an updated definition. The [TRS-80 Archives
index](https://electrickery.hosting.philpem.me.uk/comp/trs80-4p/trs80Archives_cpm/index.html)
lists DISK.FDF on cpm2, cpm15 and cpm16. Neither source states permission to
republish this particular catalogue or a compiled edition. Matching editions
and a notice from an authorized distributor or rights holder remain open.

The [format decision list](../../packaging/1.0/montezuma-formats.tsv) names all
112 historical entries by stable ID. The external file has 96 entries. The compiled catalogue uses
91 of them. Five rejected entries remain in the historical file and require
no runtime replacement. The 16 internal records have a different origin.

The [independent format trial](../../docs/engineering/evidence/2026-11-03-release-formats/README.md)
identified the actual release media as CCS 332K (MMF017), 800K data (MMI008)
and BetterCP/M's own 780K System layout. Historical MMI012 has 790K of
allocation space and puts the directory 10 KiB earlier than the release
System. The production builder uses the independent release definitions while retaining the historical compatibility catalogue and its notices. Research-only tests that
exercise original Montezuma binaries require a separate, privately supplied reference copy.

## DUP 2.01 working disassembly

[DUP-2.01-annotated.lst](DUP-2.01-annotated.lst) is an annotated disassembly
of selected format, copy, check, controller and catalogue routines from the
original MM DUP 2.01. It is a reference listing, not recovered original source
or a complete reassemblable program. Annotations are BetterCP/M research notes;
the disassembled instructions remain third-party reference material.

Original COM: 8,064 bytes; SHA-256
`71df2862c4a5f645353f9d07d8b97fc230737e712df5bd99609035e98d0aac31`.
Extracted identically from `CPMb231.dsk` and `MMCPM231.DSK`; independent
cpmtools extraction matched. See the
[analysis and routine map](../../docs/engineering/MM-DUP-REVERSE-ENGINEERING.md).

## CONFIG 3.10 / 3.01 reference binaries and disassembly

Original CONFIG.COM files were extracted from the retained MM 2.32 and 2.31
distributions respectively. `CONFIG-3.10-annotated.lst` traces the logical-drive
selection and format-assignment paths. The two `CONFIG-*-linear.lst` files are
raw linear disassemblies, including data decoded as instructions; they are
not reassemblable source. Hashes are in `CONFIG-extraction-manifest.json`.

See [CONFIG analysis](../../docs/engineering/MM-CONFIG-REVERSE-ENGINEERING.md)
for the A–D restriction, BIOS table evidence, provenance and limitations.
These are third-party reference materials, not original BetterCP/M code.

## Agreed project license boundary

Original BetterCP/M software and reusable code examples use GPL-2.0-or-later; original documentation prose and illustrations use CC BY 4.0. Neither grant relicenses the historical materials in this directory. See [project licensing](../../docs/LICENSING.md) and the [permission investigation](../../docs/engineering/Montezuma-Permission-Review-2026-11-03.md). Both sources of format data carry the notice above.
