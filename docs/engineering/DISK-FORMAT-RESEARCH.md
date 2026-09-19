# Disk Format Research Notes

> **Status: Historical research — non-normative**
>
> This document records research that contributed to the BetterCP/M
> disk-format design. Some terminology, interpretations, and architectural
> conclusions have been superseded by later analysis.
>
> The authoritative current specification is
> `DISK-FORMAT-DEFINITION-SPECIFICATION.md`.
>
> This document is retained as supporting research and should not be used
> as an implementation specification.

## Purpose

This note records source and methodology findings for BetterCP/M's disk-format support research. It is supporting engineering research, not the canonical disk-format specification.

The working architectural goal is to distinguish CP/M filesystem organization, recorded-media organization, logical-to-physical mapping, exceptional track layouts, and host image serialization. No existing format database is assumed to be authoritative or complete.

## Source corpus

### Montezuma Micro DISK.FDF

DISK.FDF remains the practical starting point for BetterCP/M. It combines CP/M filesystem parameters with physical-media information needed by the Montezuma Micro Model 4 BIOS. Its limitation is equally important: it describes the needs and capabilities of one BIOS/controller environment rather than a universal CP/M disk model.

### cpmtools diskdefs

cpmtools diskdefs appears to be the strongest candidate for the broadest inventory of named CP/M filesystem formats. It should therefore be used as a breadth baseline and candidate-format registry.

Its definitions are comparatively weak as physical-media descriptions. Typical cpmtools fields describe sector length, total tracks, sectors per track, allocation block size, directory size, skew, reserved tracks, and CP/M version. Information required to reproduce the recorded medium may be absent.

Research rule: use cpmtools for breadth, but enrich/verify formats from physically richer sources.

### Sydex 22DISK

The released 22DISK 1.44 package contains an indexed CPMDISKS.DEF with 187 format definitions. The database identifies itself internally as the database for 22DISK version 1.40.

22DISK's definition language is substantially richer in recorded-media information than cpmtools. Public examples and recovered definitions use fields including:

- DENSITY
- CYLINDERS
- SIDES
- SECTORS and physical sector size
- SKEW
- explicit SIDE1 and SIDE2 sector sequences
- ORDER
- CP/M DPB/allocation parameters
- OFS or SOFS
- COMPLEMENT
- special ordering modifiers where applicable

The distributed STRIPIDX utility is documented as removing the index from an indexed definition file to produce an editable form. The released indexed database therefore contains recoverable definition information rather than an opaque compiled geometry table.

For research purposes the 187 released definitions form a useful historical physical-format corpus.

### EURO1.DEF

EURO1.DEF is a public 22DISK-format supplement for European/foreign formats. Its header attributes most definitions and testing to H. Jungkunz, with XF2D and SF2D additions by F. van Empel.

It is especially useful because it exposes the 22DISK source syntax directly and includes examples with non-1-based sector IDs, explicit per-side sector sequences, special ordering, and extended Joyce formats.

Treat it as a supplemental corpus with its own provenance rather than silently merging it into the Sydex baseline.

### LibDsk

LibDsk contributes a different set of physical/formatting concepts. Its geometry model includes cylinders, heads, sectors, sector base, sector size, data rate, FM/MFM selection, sidedness/traversal modes, read/write gap, format gap, multitrack behavior, and deleted-data handling.

Some of these may be controller or formatting concerns rather than canonical BetterCP/M format properties. Their presence makes them candidates for the capability survey; they should enter the canonical model only where historical formats demonstrate a need.

### CPM-Floppy-Definitions / NEWDEFS1

The CPM-Floppy-Definitions collection is useful as a modern cross-reference and conversion corpus, not as an authoritative historical source. It contains cpmtools, LibDsk, FlashFloppy/GOTEK, and related representations and includes provisional/defaulted values in places.

NEWDEFS1.pdf documents a methodology for constructing disk definitions from a running CP/M system or an unknown disk. It explicitly treats 22DISK parameters as sufficiently rich to derive many LibDsk and cpmtools fields, while also showing that some LibDsk values (for example gap values and some controller behavior) may be provisional rather than derivable from 22DISK.

The document also makes the logical/physical distinction explicit: CP/M records per track may differ from physical sectors per track when physical sectors are larger than 128 bytes.

## Important semantic distinctions

### CP/M translation versus physical interleave

A DPH XLT table describes the BIOS's logical-sector translation used by CP/M. It must not automatically be interpreted as the physical rotational interleave of sector IDs on the recorded track.

22DISK SIDE1/SIDE2 sequences and physical disk-analysis tools may describe information that cannot be recovered merely from a CP/M DPB or cpmtools diskdef.

### Disk format versus image serialization

A disk format describes the CP/M organization and recorded medium. A raw/DMK/IMD/DSK/etc. representation describes how that disk is serialized in a host file. More than one image representation may encode the same disk format, and "raw" alone does not establish sector ordering.

## Evidence strategy

Use the sources for different purposes rather than attempting to select one universal database:

- cpmtools: breadth/master candidate inventory
- 22DISK: large historical corpus with richer physical layout
- Montezuma DISK.FDF: independent historical BIOS-oriented format source
- LibDsk: additional geometry/formatting capabilities
- EURO1.DEF: public 22DISK-language examples and European supplement
- CPM-Floppy-Definitions: cross-reference and candidate discovery
- DRI/OEM documentation: primary evidence for specific systems
- surviving disk images: empirical verification and conflict resolution

The next research deliverable should be a capability matrix followed by a master format registry. Syntax for a permanent BetterCP/M canonical definition should follow demonstrated semantic requirements rather than precede them.
