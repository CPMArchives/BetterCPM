# BetterCP/M Disk Format Definition Proposal — reviewed version 1

Assessment revision, 19 September 2026. Supersedes the open decisions in the supplied proposal for purposes of review; it is not an assertion that the compiler and runtime reader have been implemented or that the user has approved every recommendation. Evidence, corrections to earlier advice, and test results are in `ASSESSMENT.md`.

## 1. Scope and boundary

`DISK.FDF` describes the format-dependent information an independent BetterCP/M BIOS needs to provide the CP/M disk interface. Controller commands, ports, drive selection, timing, buffering, retry policy and derived drive-binding state remain BIOS responsibilities. Image containers and host-file serialization remain separate adapter concerns.

Version 1 targets the recovered 96-entry MM catalogue as a reference corpus, the 16 recovered MM built-in definitions, and the demonstrated BetterCP/M mappings intentionally retained here. Catalogue membership is not proof of validity or compatibility. Five entries currently fail capacity or directory-allocation checks and must remain excluded from a qualified runtime database pending independent correction.

Implement only demonstrated requirements. New formats may justify future required extensions. No universal controller API, general archival track language, MEDIA field, DATA_RATE field, or parsed provenance vocabulary is introduced here.

## 2. Source and runtime pipeline

```text
DISK.FDF -> FDFCOMP -> DISK.FDB -> CONFIG -> BIOS / drive binding
```

FDF is authoritative text. FDB is generated and versioned. CONFIG reads FDB; it does not parse the new text language. The canonical format and the BIOS's private in-memory binding need not have identical byte layouts.

The FDB descriptor is a source for constructing a self-contained normalized
BIOS binding; it is not a runtime indirection required for disk I/O or cold
boot. The installed binding remains operational authority if the catalogue is
missing or later contains different semantics under the same ID. CONFIG may
record the eight-byte ID and a canonical per-descriptor fingerprint as
provenance, report a mismatch, and offer explicit migration. It must never
silently reinterpret an installed binding. The whole-file FDB CRC is not a
per-descriptor fingerprint because unrelated catalogue changes affect it. See
Architecture Specification 28.

The new language reuses the historical filename but is not compatible with the old MM numeric grammar. A migration tool must recognize the old grammar explicitly, preserve reference values, and report errors; current CONFIG must not be handed the new source until its reader is upgraded. Keep the old reference file unchanged.

## 3. FDF source grammar

- ASCII; LF and CRLF line endings accepted. A CP/M 1Ah EOF byte ends meaningful source; subsequent record padding is ignored.
- First meaningful statement: `FDF_VERSION 1`. This distinguishes the new grammar and allows future major revisions to be rejected clearly.
- One statement per line; keywords and enumerated values case-insensitive.
- `#` starts a comment outside a quoted string. Blank lines are ignored.
- `FORMAT` begins a definition; `END` terminates it. Nesting and missing END are errors.
- Other statements use `KEYWORD value`.
- Numbers are unsigned decimal or `0x` hexadecimal. Lists are comma-separated; each element must be present.
- Strings use double quotes. Version 1 permits printable ASCII except an embedded double quote; no escape syntax is defined. Whitespace inside the string is retained.
- Unknown fields and duplicate fields are errors, including duplicate IDs after case normalization. Provenance, aliases and qualification notes remain comments or companion documentation.
- Source errors identify the format ID, source line and invalid relationship. No silent truncation, wraparound or catalogue-entry omission.

Mandatory fields: ID; explicit DPB fields listed below; PSECTORS, SECSIZE, CYLINDERS, SIDES, ENCODING, SECTOR_IDS. Optional fields and defaults are specified below.

## 4. Identity

`ID`: 1–8 ASCII letters/digits; normalize to uppercase and store as 8 space-padded bytes. Unique within the database. Preserve it across display-name changes; an incompatible disk mapping requires a distinct ID.

`DESCRIPTION`: optional, 1–32 printable ASCII characters. Compile to 32 space-padded bytes; absent means the ID is copied and padded. A long historical name may be retained in a comment and given a deliberately shorter display description. Never silently truncate it.

## 5. CP/M DPB

Explicit fields: `SPT`, `BSH`, `DSM`, `DRM`, `AL0`, `AL1`, `CKS`, `OFF`.

- SPT is the number of 128-byte logical records per **CP/M track**.
- OFF counts those CP/M tracks, whose unit is established by LOGICAL_TRACK below.
- DSM and DRM are highest allocation-block and directory-entry numbers, not counts.
- Standard DPB byte fields must fit 8 bits; word fields must fit 16 bits. BSH is 3–7 for this CP/M 2.2 contract.
- Allocation data must fit both the exposed geometry and the CP/M 2.2 record-address range. The directory's occupied blocks must be reserved by AL0/AL1. Additional explicitly reserved bitmap blocks are permitted.
- CKS controls directory checksumming. Zero or partial checking is not by itself a filesystem-layout contradiction; backend checksum-buffer limits are checked at binding.

BLM is derived:

```text
BLM = (1 << BSH) - 1
```

An explicit BLM is an assertion and must equal this value.

EXM has a derived maximum/default:

```text
DSM < 256:  EXM_MAX = (1 << (BSH - 3)) - 1
DSM >= 256: EXM_MAX = (1 << (BSH - 4)) - 1
```

Reject DSM >= 256 with BSH=3: eight word-sized allocation pointers cannot describe even one 16 KiB logical extent with 1 KiB blocks.

Absent EXM means EXM_MAX. Explicit EXM is valid when:

```text
0 <= EXM <= EXM_MAX
(EXM & (EXM + 1)) == 0
```

A smaller valid mask uses fewer allocation slots per directory entry. Preserve it and report an informational diagnostic. It is not a corrupt override. Noncontiguous or oversized masks are errors. Valid reduced EXMs do not excuse other inconsistencies in the same definition.

## 6. Recorded-sector description

| Field | Version-1 meaning |
|---|---|
| PSECTORS | 1–255 physical sectors on one recording surface at one cylinder |
| SECSIZE | 128, 256, 512 or 1024 bytes; uniform size, or maximum when SECTOR_SIZES is present |
| CYLINDERS | 1–255 cylinders described by the format |
| SIDES | 1 or 2 |
| ENCODING | FM or MFM; historically described as SD or DD in the scoped MM corpus |
| INVERT | YES or NO; default NO; complement payload bytes on physical I/O |
| SECTOR_IDS | Exactly PSECTORS distinct byte-valued IDs, ordered by logical physical-sector position |
| SECTOR_SIZES | Optional list, one allowed byte size per SECTOR_IDS entry |

Sector ID zero is valid. IDs need not be consecutive or start at a particular value. Sector-size list entries correspond to the ID at the same list position, not to the ID's numeric value.

Without SECTOR_SIZES, every sector has SECSIZE bytes. With the list, SECSIZE must equal its maximum. The compiler may omit a redundant uniform size extension after validation. Mixed sizes are included specifically for MM SUPER and the demonstrated existing mapper.

Example of SUPER logical order:

```text
SPT          44
PSECTORS     6
SECSIZE      1024
SECTOR_IDS   1,3,5,2,4,6
SECTOR_SIZES 1024,1024,1024,1024,1024,512
```

The current 32-sector runtime arrays are a BIOS/implementation limit, not the FDB language limit. CONFIG reports unsupported bindings for definitions exceeding those arrays. Representing a larger definition does not imply that current hardware can use it.

## 7. Logical track unit

`LOGICAL_TRACK SURFACE|CYLINDER`, default SURFACE.

SURFACE: one CP/M track covers one physical surface track. Let `R` be `sum(SECTOR_SIZES)/128`, or `PSECTORS * SECSIZE / 128` for uniform media. Require SPT=R.

CYLINDER: one CP/M track covers both sides of a cylinder, side 0 before side 1. Require SIDES=2, SPT=2R, and the default topology values below. This restriction covers the demonstrated Micro-Abacus and existing BetterCP/M cylinder-based bindings without defining new combinations speculatively. OFF counts cylinders in this mode.

The Micro-Abacus reference has SPT=64, eight 512-byte sectors per side, two sides and OFF=2. It therefore needs CYLINDER: its reserved area is `2 * 64 * 128 = 16,384` bytes. FDB marks this mapping with a required extension, so an old reader cannot silently interpret it as SURFACE.

## 8. Topology

| Field | Default | Alternative |
|---|---|---|
| SIDE_ORDER | ALTERNATING | SIDE_MAJOR |
| SIDE1_DIRECTION | FORWARD | REVERSE |
| TRACK_ID_MODE | PER_CYLINDER | CONTINUOUS |
| SECTOR_ID_MODE | RESTART | CONTINUOUS |

For SURFACE with two sides and logical track `t`:

- ALTERNATING: cylinder=`t // 2`, side=`t % 2`.
- SIDE_MAJOR: side=`t // CYLINDERS`; first-side cylinder=`t`; second-side forward cylinder=`t - CYLINDERS`.
- SIDE_MAJOR with REVERSE: second-side cylinder=`CYLINDERS - 1 - (t - CYLINDERS)`.

REVERSE with ALTERNATING is invalid. Single-sided definitions require all four defaults. Out-of-range tracks are rejected before mapping.

TRACK_ID_MODE controls the recorded track ID, not mechanical seek position:

- PER_CYLINDER: ID equals the cylinder.
- CONTINUOUS: ID equals `2 * cylinder + side`.

SECTOR_ID_MODE controls IDs on side 1:

- RESTART: use the listed ID.
- CONTINUOUS: add PSECTORS to the listed ID on side 1.

Reject any resulting sector or track ID greater than 255; do not wrap. This byte-valued constraint concerns recorded ID fields, not the DPB's word-valued logical track count.

## 9. Logical-record mapping

For SURFACE, map the CP/M track using Section 8, then locate its logical record within the ordered sectors.

For CYLINDER, the CP/M track is the cylinder. If record `r >= R`, select side 1 and subtract R; otherwise select side 0. Then locate the remaining record within that side's sectors.

For uniform sizes:

```text
records_per_sector = SECSIZE / 128
index              = r // records_per_sector
subrecord          = r % records_per_sector
sector_id          = SECTOR_IDS[index]
```

For mixed sizes, walk cumulative `SECTOR_SIZES[i] / 128` counts to find the containing sector and the remaining subrecord. Apply the track- and sector-ID transformations after cylinder/side selection. Return mechanical cylinder, side, recorded track ID, sector ID, physical size and subrecord. The BIOS handles controller addressing and deblocking.

The serialized list is not a generic SPT-entry DPH XLT. The original MM BIOS performs deblocking and this lookup in SETSEC; SECTRN returns its input. Other BIOS implementations may organize their internal tables differently while preserving the same mapping.

## 10. Double stepping and formatter policy

MM OPTIONS bit 5 is derived double-stepping state. Exclude it from the canonical flags. CONFIG/BIOS derives drive stepping from the selected format and physical drive. The current BetterCP/M reuse of bit 5 to mark cylinder-based SPT is a separate internal convention and must be translated explicitly during migration, never copied as a canonical flag.

SECTOR_IDS defines logical access order. Original MM DUP 2.01 writes consecutive IDs in its examined formatting loop; the earlier assertion that it uses the translation table as rotational order was incorrect. BetterCP/M currently uses its own list order, which is an implementation policy.

Version 1 does not require reproduction of a particular rotational placement. A formatter must preserve required IDs, sizes, encoding, inversion and logical contents. It may choose a compatible physical order. Exact historical format-order preservation needs a future separately specified required extension if a verified format demands it.

## 11. Excluded fields and evidence scope

MEDIA and DATA_RATE are omitted. No examined member of the scoped corpus demonstrates that these must be passed as additional format fields to an independent BIOS with its physical-drive binding available. FM/MFM alone does not universally determine data rate; a BIOS must establish compatible timing from its implemented support and binding or refuse the format. A demonstrated ambiguity on the same configured drive can justify a future required extension.

Provenance, historical names and qualification notes remain comments/companion documentation. No current consumer needs formal SOURCE, STATUS, ALIAS or NOTES statements.

Track-range layouts, differing sector-ID maps by track, mixed FM/MFM and a separate required rotational order remain future work. Their absence is a bounded v1 scope, not a declaration that such disks cannot exist.

## 12. FDB file framing

All integer words are unsigned little-endian. All offsets are **absolute byte offsets from file start**, never memory pointers. Zero means absent only where explicitly specified.

Version 1 files consist of complete 128-byte CP/M records. Maximum serialized size is 65,408 bytes (FF80h), including padding. All offset/count arithmetic must be checked without 16-bit wraparound. A compiler rejects overflow and reports the need for an explicit subset. It must not truncate the catalogue automatically.

### Header: 16 bytes

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 4 | ASCII `BFDB` |
| 4 | 1 | Major version: 1 |
| 5 | 1 | Minor version: 0 |
| 6 | 1 | Header size: 16 |
| 7 | 1 | Descriptor stride: 64 |
| 8 | 2 | Descriptor count; zero is an empty catalogue |
| 10 | 2 | First descriptor offset: 128 |
| 12 | 2 | Pool offset: `128 + count * 64` |
| 14 | 2 | CRC-16, little-endian |

Bytes 16–127 are zero. Starting at 128 puts two descriptors in each CP/M record; descriptors do not straddle records in v1 output. Fixed ID and description sizes are preserved.

### Descriptor: 64 bytes

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 8 | Uppercase, space-padded ID |
| 8 | 32 | Space-padded display description |
| 40 | 15 | Standard CP/M 2.2 DPB |
| 55 | 1 | PSECTORS |
| 56 | 1 | SECSIZE code: 0=128, 1=256, 2=512, 3=1024 |
| 57 | 1 | CYLINDERS |
| 58 | 1 | Normalized flags |
| 59 | 1 | Sector-ID count; must equal PSECTORS |
| 60 | 2 | Sector-ID list offset |
| 62 | 2 | Extension-list offset, or zero |

The duplicated ID count is retained as an invariant check, not an independent geometry field. A future extension cannot reinterpret it silently.

### Flags

| Bit | Set meaning |
|---:|---|
| 0 | Two sides |
| 1 | MFM; clear means FM |
| 2 | Inverted payload data |
| 3 | SIDE_MAJOR |
| 4 | REVERSE side-1 direction |
| 5 | CONTINUOUS track IDs |
| 6 | CONTINUOUS sector IDs |
| 7 | Extension-list offset is nonzero |

Flag 7 and the extension offset must agree. These are new normalized flags, not an unchanged MM OPTIONS byte.

### Pool and extensions

Each descriptor references exactly PSECTORS ID bytes. There is no identity-table shortcut and no table deduplication in v1 output. Objects may not overlap or point into the header/descriptor area. Unused pool gaps and final padding are zero. The file ends at the next 128-byte boundary after the last referenced object; arbitrary extra record padding is invalid.

An extension list contains:

```text
type:     1 byte
length:   1 byte
payload:  length bytes
```

`0,0` terminates the list. Type 0 with nonzero length, type 80h, repeated kind values, and unterminated/out-of-bounds lists are malformed.

- Type bit 7 means **required for correct interpretation/use**.
- Type bits 0–6 are the kind, 1–127.
- Unknown optional kind: skip its payload.
- Unknown required kind: mark that descriptor unsupported and refuse binding, while retaining other usable entries.
- All disk-mapping or required recording changes must be required. Optional means safe to ignore without changing disk interpretation.

Assigned v1 semantic extensions:

| Type | Length | Meaning |
|---:|---:|---|
| 81h | PSECTORS | One size code per SECTOR_IDS entry; all codes 0–3, maximum agrees with descriptor SECSIZE |
| 82h | 1 | Logical-track unit; sole v1 payload value 1 means CYLINDER |

Absence of 81h means uniform sizes. Absence of 82h means SURFACE. Encoding either known semantic kind with its required bit clear is an error. No unrelated speculative types are assigned.

### CRC

CRC-16/CCITT-FALSE: polynomial 1021h, initial FFFFh, no reflection, xorout 0000h. Check vector: ASCII `123456789` gives 29B1h.

Calculate over the complete serialized file, including zero padding, with header bytes 14–15 treated as zero. Record/file length is obtained from the host file or CP/M record count; no text EOF interpretation applies to FDB.

FDFCOMP validates its semantic input, emits a temporary file, and checks the completed output before installing it. CONFIG validates header, file structure and CRC when opening the catalogue, before making a binding. A small implementation can stream 128-byte records and re-read the selected descriptor; loading the entire database into resident memory is unnecessary. The BIOS still independently validates the proposed binding.

## 13. Versioning and future extensions

Readers reject unknown major versions. They may accept newer minor versions when the fixed prefix and required-extension rules remain supported. `header_size` and `descriptor_stride` must be at least 16 and 64, fit their advertised byte fields, and produce valid nonoverlapping file regions.

The current writer emits exactly the sizes in Section 12. Future same-major tails are ignorable optional information only. Required semantics belong in required TLVs; they must never be placed solely in an ignored header/descriptor tail.

Default fields retain their existing meaning. A future required layout extension may explicitly override defaults on stated track ranges or define different per-track ID/encoding maps. Older readers reject its descriptor. This is file-format evolution, not automatic support by old BIOSes.

A one-byte TLV length bounds each inline payload to 255 bytes. Compact track-range rules and small per-track maps can be required extensions within that bound. V1 does not provide generic framing for additional referenced pool objects: unknown extensions pointing to such objects would conflict with an older reader's ownership and zero-padding validation. Large external tables therefore require a major revision introducing appropriate framing, unless their representation fits the existing inline rules. Do not claim unrestricted future table support from the presence of a TLV mechanism alone.

Reinterpreting existing base fields, changing the DPB, widening offsets, changing checksum framing, or changing required/optional semantics requires a new major version. A database exceeding the 16-bit envelope needs explicit subsets or a wider future format.

## 14. Validation and qualification

FDFCOMP rejects malformed text, duplicated IDs, out-of-range values, inconsistent BLM, invalid EXM masks, unreserved directory blocks, over-capacity allocation, impossible SPT mapping, invalid topology, ID overflow and malformed extension construction. It reports reduced valid EXM values informationally. No source value is silently repaired.

The FDB reader separates:

1. **Malformed database:** bad version framing, CRC, bounds, overlaps, invalid record relationships or malformed TLVs. Reject the file.
2. **Structurally valid but unsupported required semantics:** show the entry as unsupported; refuse binding it.
3. **Supported semantics but incompatible drive/backend:** refuse that assignment with a precise reason.

The initial corpus has 112 reference entries. The review's structural checks admit 107 after the demonstrated SUPER and cylinder-track normalizations. Acorn SS, Eagle SS, Omikron Mapper II, Pied Piper and Zenith H89 SD need independent historical correction and are excluded from qualified compilation. Preserve their original data and diagnostics in the reference corpus.

Successful parsing and mapping tests are not proof that 107 historical media formats work on every machine. Release claims require named platform and image-representation tests. Preserve the cpmtools/BetterCPM same-file bidirectional tests; add mixed-sector and cylinder-track fixtures when the new runtime path is implemented.

## 15. Complete example

```text
# California Computer Systems: recovered MM catalogue, entry at line 49.
# Historical full name and verification notes belong in comments.
FDF_VERSION 1

FORMAT
ID            CCS40DS
DESCRIPTION   "CCS 40T DS DD 332K"
SPT           36
BSH           4
# BLM 15 is an optional assertion. EXM defaults to 1 here.
DSM           165
DRM           63
AL0           0x80
AL1           0
CKS           16
OFF           6
PSECTORS      18
SECSIZE       256
CYLINDERS     40
SIDES         2
ENCODING      MFM
INVERT        NO
LOGICAL_TRACK SURFACE
SIDE_ORDER    ALTERNATING
SIDE1_DIRECTION FORWARD
TRACK_ID_MODE PER_CYLINDER
SECTOR_ID_MODE RESTART
SECTOR_IDS    1,5,9,13,17,3,7,11,15,2,6,10,14,18,4,8,12,16
END
```

Use this as the commented stock template after implementation; placeholder values are not valid source. For a historically reduced extent mask, explicitly add EXM and document its source rather than accepting the default blindly.

## 16. Assessment closure and implementation handoff

Questions A–F are answered in `ASSESSMENT.md`; the independent binary/algorithm prototype and results are included with it. The measured qualified test database is 8,320 bytes, and the rebuilt mapper passed its existing machine-code checks. These results support proceeding to implementation of this design.

Production FDFCOMP, CONFIG integration, private-binding migration and platform end-to-end qualification remain separate implementation work. The review prototype is intentionally not presented as those production components. In particular, the test database uses synthetic IDs and short descriptions and must not replace a user's DISK.FDB.
