# Disk-format proposal: completed assessment

19 September 2026. Assessed the current `BetterCPM-Disk-Format-Definition-Proposal.md`, including its questions A–F. Repository evidence is from BetterCP/M commit `196a992f4558dae306291881b07da3613717f0c7`. This is a design review with executable checks, not a claim that FDFCOMP or the new CONFIG reader has been implemented.

## Verdict

Retain the architecture and the 16-byte header / 64-byte descriptor design, with the completed rules in `BetterCPM-Disk-Format-Definition-Proposal-Reviewed.md`. The original proposal is preserved. Two claims originating in the previous assistant assessment were incorrect: all non-default EXMs are not invalid, and original MM DUP does not use the logical translation list as its rotational formatting order.

## A. BLM and EXM

Use different policies for these fields.

- **BLM:** derive `(1 << BSH) - 1`. An explicit value is an assertion and must match. The DRI `atran` algorithm combines a block number shifted by BSH with `vrecord & BLM`; changing the significant mask bits breaks the intended allocation-block addressing. No supported historical case justifies changing this relationship. This is a v1 validity requirement, not a claim about every possible degenerate or modified BDOS.
- **EXM:** the usual derivation is the *maximum/default*, not the only valid value. Permit any contiguous low-bit mask `2^k - 1` no larger than that maximum. Emit an informational diagnostic for a reduced value and preserve it. Reject oversized or noncontiguous masks.

For BSH=4, DSM=191, the default EXM is 1. EXM=0 is also valid: each directory entry describes one 16 KiB extent and uses eight of its sixteen byte-sized allocation slots. The next extent gets another directory entry. Unused slots remain zero. DRI `dm$position`, extent matching, and `open$reel` support this directly.

Six recovered catalogue entries use this reduced mask: BMC if800/20, Heath H8/Trionyx H-C8, Lobo MAX-80 DS, Lobo MAX-80 CP/M 3 DS, Pied Piper Executive, and Televideo 802. Pied Piper has a separate directory-bitmap inconsistency; its EXM value itself is not the error. BetterCP/M's existing TRS-80 validator already admits smaller contiguous masks (`src/bios/config.mac`, DC_EXMDONE).

The independent algorithm check covers 512 logical extents and all 128 record positions for every accepted BSH/EXM combination at each allocation-pointer width. It checks unique addresses and allocation-slot bounds. This models the inspected DRI algorithms; it does not substitute for a future end-to-end native BDOS file test.

## B. Mixed sectors

Accept `SECTOR_SIZES` in v1. This is established behavior, not a speculative feature. MM CONFIG's four built-in SUPER formats use SPT=44, six sectors, maximum size 1024, and IDs `1,3,5,2,4,6`. Original DUP at 06BAh–06C9h assigns sector ID 6 a 512-byte size. Thus the ordered list is `1024,1024,1024,1024,1024,512` and totals 44 CP/M records per surface track.

BetterCP/M intentionally implements normalization, explicit size maps, formatting and adjacent-record verification for these formats. Existing source includes `src/rsx/fdf.mac`, `tools/test_fdf_rsx.py`, and `tools/test_fdf_workflow.py`. This review rebuilt the current mapper into an isolated directory and executed its machine-code tests successfully: 1,536 catalogue boundary mappings at two relocation addresses, plus its mixed-size, rejection and unload checks. The live trs80gp workflow was inspected, not rerun in this review.

`SECTOR_SIZES` is sufficient for this demonstrated case: one value per sector ID in logical mapping order, with SPT equal to the total records per logical track. It is not a representation of arbitrary special boot tracks or varying geometry across the disk.

## C. MEDIA and DATA_RATE

Keep both out of v1. The recovered catalogue includes 5¼-inch formats and 77-cylinder 8-inch DRI formats, but their need for different controller timing does not by itself prove a need for a new portable field: the physical-drive binding already supplies the drive/controller context. MM's DCB records explicitly separate drive type, timing and selection from format properties.

No inspected member of the scoped corpus establishes two otherwise indistinguishable recordings that require the portable definition to supply a rate discriminator on the same configured drive. This is an evidence-bounded decision, not proof that encoding and geometry determine rate universally. A future dual-rate format on the same drive would be a valid reason for a required extension. Do not infer rate universally from cylinder count or `FM/MFM`; a BIOS must establish support from its implemented profile and binding or refuse the assignment.

## D. Provenance

Keep provenance and historical aliases in comments and the companion catalogue. The current software displays names, loads geometry and compares bindings. It does not consume structured provenance or verification-status fields. Stable IDs remain machine-readable. Renaming a display description must not change an ID; an incompatible format mapping must receive another ID.

## E. Binary stress test

The layout is practical after closing four omissions:

1. Define CRC parameters and CP/M padding. Use CRC-16/CCITT-FALSE, polynomial 1021h, initial FFFFh, no reflection, xorout 0; `123456789` gives 29B1h. Include the complete zero-padded CP/M record stream, with header CRC bytes zeroed.
2. Give TLVs required/optional semantics. Bit 7 of the type marks a required capability; bits 0–6 identify it. Unknown required semantics make that descriptor unsupported. Unknown optional metadata is skipped. Known semantic extensions cannot be mislabeled optional.
3. Define absolute file offsets, bounds, overlap, terminator and version rules. Structural corruption invalidates the database; an unsupported capability invalidates only use of the affected descriptor.
4. Align the descriptor array at offset 128. The header remains 16 bytes, followed by 112 zero bytes, so two 64-byte descriptors fit exactly in each CP/M disk record.

Measurements from the independent encoder/reader:

| Case | Result |
|---|---:|
| All 112 input entries, layout sizing only | 8,704 bytes |
| 107 entries passing the stated structural checks | 8,320 bytes |
| Sector-ID bytes in all 112 entries | 1,350 |
| 680 synthetic 32-sector descriptors, without extensions | 65,408 bytes: accepted |
| 681 of the same | Exceeds v1 limit: rejected |

The 16-bit address space is ample for this release. Define the v1 maximum as 65,408 bytes (FF80h), including padding, to avoid a special 65,536-byte length representation on the Z80. Larger catalogues require explicit subsets or a future wider format; never wrap or truncate offsets. CONFIG can stream the file and needs only bounded buffers, not a 64 KiB database allocation.

`PSECTORS <= 32` is the current backend's implementation limit. The proposed byte fields permit 1–255; the structural reader successfully accepts 33- and 255-sector synthetic descriptors. This does not claim the current BIOS can bind them.

The 16 test groups also cover repaired-CRC malformed pointers, duplicate/reserved extension types, required-capability rejection, optional skipping, padded EOF, nonzero pool gaps, record-address and recorded-ID overflow, every single-byte one-bit corruption in the 8,320-byte test database, truncation at each record boundary, and optional header/descriptor growth.

## F. Extensibility

Keep the first 16 header bytes and first 64 descriptor bytes stable within major version 1. New optional header/descriptor tails may be ignored using the advertised sizes. Required semantic changes must be conveyed through required TLVs, not hidden in ignored tails.

Future track-range layouts, per-track IDs and mixed encoding can use required extensions that override explicitly defined default fields. Older readers reject those descriptors. Separate formatting order can likewise be a required extension. This is compatible evolution of the file parser, not a promise that older BIOSes gain the capability.

One-byte TLV lengths limit each future inline payload to 255 bytes. That accommodates compact track-range rules and small per-track maps, but not arbitrary full-disk tables. Under the strict v1 pool-ownership and zero-padding rules, an unknown extension cannot simply reference an unframed external table: an older reader would mistake that table for invalid padding. Larger objects therefore require a major revision with generic object framing, unless a separately specified representation fits the existing inline rules. No future types are assigned now. The extension mechanism is useful, but not unlimited.

A change to existing field meanings, DPB layout, offset width, checksum framing or required/optional interpretation requires a major version. New optional metadata alone does not.

## Additional demonstrated corrections

### Original MM formatting order

Original MM DUP's 0673h formatter initializes C from its first-ID parameter, stores C into each sector ID field at 06B7h, and increments C at 06BAh. It does not index the DPH translation table there. The table is used for logical access in MM BIOS `SETSEC`; MM `SECTRN` returns the input unchanged. BetterCP/M's current formatter chooses its own list order, but that behavior must not be attributed to original MM.

Consequently, v1 `SECTOR_IDS` defines logical access order only. The formatter may choose rotational placement while preserving the IDs, sizes and contents. Exact historical rotational reproduction is outside v1. A future demonstrated requirement can add a separate required formatting-order extension.

### Logical track unit

Micro-Abacus already demonstrates a missing distinction: SPT=64, eight 512-byte sectors per side, two sides. One surface supplies only 32 records. BetterCP/M deliberately normalizes this as a cylinder-wide CP/M track. Add `LOGICAL_TRACK SURFACE|CYLINDER`, default SURFACE, with a required FDB extension for CYLINDER. The old reserved bit 5 must not be copied into the canonical flags for this purpose; MM used it for double stepping.

For CYLINDER, records on side 0 precede side 1 within each logical track. Require two sides and default topology for the initial supported case. `OFF` counts cylinders in this mode. The Micro-Abacus OFF=2 therefore reserves 16,384 bytes (2 × 64 × 128).

### Corpus acceptance is not historical verification

Five entries fail arithmetic checks under their supplied values:

| Entry | Problem |
|---|---|
| Acorn 80T SS SD | Declared allocation exceeds available media bytes |
| Eagle 80T SS DD | Directory bitmap does not reserve its full directory |
| Omikron Mapper II | Declared allocation exceeds available media bytes |
| Pied Piper Executive | Directory bitmap does not reserve its full directory |
| Zenith H89 SD | Declared allocation exceeds available media bytes |

Do not silently repair them or publish them as supported. Keep their exact reference data and diagnostics in the research corpus; omit them explicitly from a qualified runtime database until independent evidence supplies a correction. The five findings match the categories excluded by the repository's existing catalogue-audit expectations. Smaller CKS values seen elsewhere describe limited directory checksumming and are not automatically grounds for rejecting the filesystem.

## Evidence and reproducibility

- Original DRI CP/M 2.2 `OS3BDOS.ASM`, local reference under `cpm-compatibility/investigations/036 ... /reference/`; archive provenance: [Digital Research original sources](https://www.cpm.z80.de/source.html).
- Original MM CONFIG and DUP instruction listings in BetterCP/M `third_party/montezuma/`, particularly CONFIG 08CDh–0934h and DUP 0673h–073Eh, 0885h–08E4h.
- [MM 2.32 recovered source archive](https://oldcpusrus.xepb.org/mmcpm232.zip), retained under `evidence/`; BIOS `setsec` lines 1358–1405, seek lines 1832–1889, and the documented EXBIOS patch at 2551–2583. This is recovered source/disassembly, not a new binary equivalence proof. Some comments mislabel side/type bits; the executable instructions and independent listings take precedence.
- [MM 2.20 annotated BIOS](https://oldcpusrus.xepb.org/montbios.asm) independently corroborates SETSEC and double stepping.
- `evidence/corpus-audit.json` records input hashes, reduced EXMs, exclusions and measured database sizes.
- `stress_test.py` is an independent design prototype, not a shipped compiler. Its FDB fixture uses synthetic IDs/descriptions and is not a release catalogue.
- `evidence/stress-test-results.txt` records 16 passing test groups; `evidence/mapper-test-results.txt` records the isolated rebuilt mapper test.

Run `python3 stress_test.py` in this directory to repeat the design checks. It reads the existing repository and writes only this assessment directory. No user disk image, original proposal, repository source, or Git branch was modified for this review.

The remaining engineering work is implementation and qualification: production FDFCOMP, CONFIG's FDB reader, migration of runtime bindings, and disk-level tests on both platforms. Those are implementation tasks, not unanswered design questions A–F. Correcting the five historical reference entries is a separate evidence task; they are explicitly excluded rather than guessed into validity.
