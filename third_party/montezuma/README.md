# Montezuma Micro runtime utility

`MDIR.COM` is an unmodified 3,072-byte utility recovered from the user-supplied
Montezuma Micro CP/M boot disk `MMCPM.dmk`.

- SHA-256: `6ba323d6b9df4ef903cc8916e231f4d554e11cb01a016483969a4dda8e31488b`
- CP/M directory allocation: 16-bit blocks 37 and 38, 24 records
- Extraction: 512-byte sectors in Montezuma logical skew order

The binary is retained as third-party software and is not part of BetterCP/M's
original source. Its CP/M redistribution status follows the Digital Research
CP/M open-source distribution permission reaffirmed in 2022; it is not
relicensed under BetterCP/M's project license.

## Disk format catalogue

`DISK.FDF` is the unmodified 10,752-byte Montezuma Micro format catalogue
extracted from the downloaded distribution during reconstruction. It is
third-party reference data, not original BetterCP/M source.

SHA-256: `9635fc0e93838f28c96aa274033fae1c8eb747db97fe4b2bd04337e39a286d66`.

CONFIG reads the text catalogue at run time. No diskdefs conversion is used.

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
