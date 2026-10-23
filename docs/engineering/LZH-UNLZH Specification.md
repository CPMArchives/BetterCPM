# LZH/UNLZH Engineering Specification

This is an implemented-baseline specification dated 2026-10-23. The
[common engineering specification](Compression%20Utilities%20Common%20Specification.md)
defines the Z80 ABI, callbacks, statuses, file adapter and safe publication.
Offsets below are decimal. Allocation size is public; working fields are private
and must not be changed during processing. The `.inc` files remain the exact
assembly definitions. These documents do not add unimplemented command options.

## Sources and entries

[LZH definitions](../../src/codec/lzh.inc), [LZH code](../../src/codec/lzh.mac),
[UNLZH definitions](../../src/codec/unlzh.inc), [UNLZH code](../../src/codec/unlzh.mac).
Commands: [lzh.mac](../../src/utilities/lzh.mac), [unlzh.mac](../../src/utilities/unlzh.mac).
User pages: [LZH](../user/LZH.md), [UNLZH](../user/UNLZH.md).

`LZH_INIT` validates READ/WRITE, context and bounded `LZH_NAME`, initializes the
ring, tree and match chains, then enters READY without I/O. `LZH_RUN` performs
one input pass and emits a `20h` stream to DONE. REWIND is unused; no encoder
GET/END is supplied. A missing bounded name terminator is `CS_CONFIG`/80h;
32-bit input-count overflow is `CS_SPACE`/81h; internal tree/path failure is
`CS_CORRUPT`/1. Common repeat-completion and latched-failure rules apply.

`UNLZH_INIT` requires READ and enters READY without I/O. `UNLZH_HEAD` validates
the header and initializes the ring/tree, entering DATA without output.
`UNLZH_GET` returns a byte or verified C/CS_END. `UNLZH_RUN` additionally requires
WRITE; `UNLZH_END` discards/verifies. Both finish NC/DONE. No operation requires
the compressed or expanded file to fit in memory.

## CrLZH format variants

This is CP/M CrLZH, not a general `.LZH`/LHA archive reader. The filename does not
identify its format conclusively. UNLZH accepts significant revisions `10h` and
`20h` with checking selector zero; LZH writes `20h` only. Both variants use a
2048-byte space-initialized history ring and literal-byte LZ77; there is no RLE90
stage. Old `10h` uses six low position bits, permitting distances 1..4096 that
wrap through that same ring. New `20h` uses five, permitting distances 1..2048.
Reference and spare fields are retained without extra revision gates.

| Order | Encoding |
| --- | --- |
| Signature | `76 FD` |
| Name/metadata | NUL-terminated, at most 127 non-NUL bytes |
| Four fields | Reference, significant revision, checking selector, spare |
| Symbols/positions | Adaptive Huffman and fixed canonical position prefixes, MSB-first |
| Trailer | Byte alignment, then little-endian additive original-byte checksum |

LZH emits reference `20h`, significant `20h`, checking 0 and spare 5. It emits
stop symbol 256, zero-fills a partial byte, then writes the checksum. CP/M record
padding is outside the library. UNLZH consumes no byte beyond its checksum;
physical EOF before completion is truncation. A checksum error is not successful
GET end. Trailing file records/bytes are not a concatenated-member interface.

There are 315 symbols: literals 0..255, stop 256, match symbols 257..314 for
lengths 3..60 (`length = symbol - 254`). The adaptive tree has 629 nodes plus a
frequency sentinel, 315 leaf references and 944 parent slots. Initial leaf
weights are one. Update ordering preserves exact equal-weight behavior; rebuild
occurs before a symbol update when the root weight reaches `8000h`, halving
rounded-up leaf weights and rebuilding branches in place. Encoding traces the
current leaf-to-root path before updating the tree. The stop symbol updates the
tree too, so exact EOF reconstruction boundaries matter.

For a distance d, encode d-1 as an upper index and variant-specific low bits.
The upper index's canonical prefix lengths for indices 0..63 are 3 (one),
4 (three), 5 (eight), 6 (twelve), 7 (twenty-four), 8 (sixteen). UNLZH uses
immutable decode tables. Copies proceed byte by byte, supporting overlap,
seeded spaces and ring wrap; bulk nonoverlapping-copy semantics are incorrect.

## LZH match search and bounded memory

LZH holds 60 bytes of lookahead, checks matching first-byte positions in the
2048-byte ring, and chooses the longest match of at least three bytes. Nearest
distance wins equal-length ties. Overlapping comparisons use earlier lookahead
bytes after reaching the distance. Consumed bytes enter the ring before refill.

A 256-word first-byte head table and 2048-word next-link table avoid scanning
impossible first bytes. Chains traverse from recent to old positions. An
incorrect first byte or nonincreasing distance identifies an overwritten link;
all older original links are obsolete. Strictly increasing distances bound a
search to 2048 candidates even if old links form a cycle. Seeded-space chains
are initialized nearest-first. No dictionary pruning based on compression ratio
or historical encoder byte identity is promised. Worst-case match search still
visits the full ring; this is not a measured throughput guarantee.

Tree path scratch is 629 bytes, with bounds checks rather than recursive calls
or assumptions about a 16-bit Huffman code. UNLZH has no encoder lookahead,
match-search links or path buffer. Its corruption details 1/2 mean tree/symbol;
header overflow is `CS_SPACE`/3. Unsupported significant/checking bytes produce
`CS_VARIANT`, with the rejected byte as detail; checksum mismatch is `CS_CHECK`.

## Command-specific naming

LZH follows the inspected CrLZH 2.0 naming sequence:

| Condition | Result |
| --- | --- |
| No extension | `.YYY` |
| Middle slot is not Y | Replace middle slot with Y (`ABC` -> `AYC`) |
| Middle is Y, last is not Y | Replace last slot with Y (`AYC` -> `AYY`) |
| Last two are YY, first is not Y | `.YYY` (`AYY` -> `YYY`) |
| Already `.YYY` | Refuse, including with another destination drive |

A one-letter `.A` or two-letter `.AB` becomes `.AY`; `.YY` becomes `.YYY`.
LZH embeds the original stem, dot and three extension slots, including blanks.
UNLZH uses the first three extension slots, trims trailing blanks and ignores
later historical metadata before validating the destination. Unsafe/high-bit
filename characters are refused rather than stripped. UNLZH does not require
Y in the compressed extension and restores no timestamps or attributes.

Both commands use the common safe temporary lifecycle. Decoding old `10h` does
not require a command switch. LZH does not offer an old-variant output option.

## Workspace layout

### LZH — 11943 bytes

| Field/block | Decimal offset | Meaning |
| --- | ---: | --- |
| `LZH_LEN` | 16 | live lookahead bytes, 0..60 |
| `LZH_EOF` | 17 | physical EOF observed |
| `LZH_BEST` | 18 | Private working state. |
| `LZH_TAKE` | 19 | Private working state. |
| `LZH_SUM` | 20 | physical input checksum modulo 65536 |
| `LZH_DISTANCE` | 22 | candidate distance, 1..2048 |
| `LZH_COUNT` | 24 | 32-bit physical input byte count |
| `LZH_WRITEPOS` | 28 | Private working state. |
| `LZH_SCANPOS` | 30 | Private working state. |
| `LZH_POSLOW` | 32 | low five position bits |
| `LZH_BYTE` | 33 | packed output accumulator |
| `LZH_BITS` | 34 | accumulated bits, 0..7 |
| `LZH_NAMLEN` | 35 | Private working state. |
| `LZH_PATHLEN` | 36 | Private working state. |
| `LZH_SYMBOL` | 38 | Private working state. |
| `LZH_CUR` | 40 | Private working state. |
| `LZH_I` | 42 | Private working state. |
| `LZH_J` | 44 | Private working state. |
| `LZH_K` | 46 | Private working state. |
| `LZH_F` | 48 | Private working state. |
| `LZH_LEFT` | 50 | Private working state. |
| `LZH_RIGHT` | 52 | Private working state. |
| `LZH_TEMP` | 54 | Private working state. |
| `LZH_HOPS` | 56 | Private working state. |
| `LZH_REBUILDS` | 58 | diagnostic count modulo 65536 |
| `LZH_BESTDIST` | 60 | Private working state. |
| `LZH_LASTDIST` | 62 | monotonic chain distance bound |
| `LZH_NAME` | 64 | caller sets before INIT; preserved |
| `LZH_RING` | 192 | 2048 bytes, initially spaces |
| `LZH_FREQ` | 2240 | 630 words, including FFFFh sentinel |
| `LZH_SON` | 3500 | 629 words |
| `LZH_PARENT` | 4758 | 944 words |
| `LZH_LOOK` | 6646 | 60 bytes of lookahead |
| `LZH_PATH` | 6706 | 629 bytes, bounded reversed tree path |
| `LZH_HEADS` | 7335 | 256 first-byte chain heads, words |
| `LZH_NEXT` | 7847 | 2048 ring-node links, words |

### UNLZH — 6646 bytes

| Field/block | Decimal offset | Meaning |
| --- | ---: | --- |
| `ULZ_REF` | 16 | Private working state. |
| `ULZ_SIG` | 17 | Private working state. |
| `ULZ_CHECK` | 18 | Private working state. |
| `ULZ_SPARE` | 19 | Private working state. |
| `ULZ_SUM` | 20 | Private working state. |
| `ULZ_EXPECT` | 22 | Private working state. |
| `ULZ_COUNT` | 24 | 32-bit decoded-byte count |
| `ULZ_WRITEPOS` | 28 | Private working state. |
| `ULZ_COPYPOS` | 30 | Private working state. |
| `ULZ_COPYLEFT` | 32 | Private working state. |
| `ULZ_BYTE` | 33 | Private working state. |
| `ULZ_BITS` | 34 | Private working state. |
| `ULZ_HDRLEN` | 35 | Private working state. |
| `ULZ_POSBITS` | 36 | 6 for 10h, 5 for 20h |
| `ULZ_VALUE` | 37 | pending output byte |
| `ULZ_SYMBOL` | 38 | Private working state. |
| `ULZ_CUR` | 40 | Private working state. |
| `ULZ_I` | 42 | Private working state. |
| `ULZ_J` | 44 | Private working state. |
| `ULZ_K` | 46 | Private working state. |
| `ULZ_F` | 48 | Private working state. |
| `ULZ_LEFT` | 50 | Private working state. |
| `ULZ_RIGHT` | 52 | Private working state. |
| `ULZ_TEMP` | 54 | Private working state. |
| `ULZ_HOPS` | 56 | Private working state. |
| `ULZ_REBUILDS` | 58 | diagnostic count, modulo 65536 |
| `ULZ_HEADER` | 64 | raw filename/metadata, 127 bytes + NUL |
| `ULZ_RING` | 192 | 2048 bytes, initially spaces |
| `ULZ_FREQ` | 2240 | 630 words, including FFFFh sentinel |
| `ULZ_SON` | 3500 | 629 words; sibling at SON index + 1 |
| `ULZ_PARENT` | 4758 | 944 words, including leaf locations |

## Reproduction and evidence

```sh
python3 tools/test_lzh.py
python3 tools/test_unlzh.py
python3 tools/test_lzh_com.py
python3 tools/test_unlzh_com.py
python3 tools/test_lzh_com_cpm.py
python3 tools/test_unlzh_com_cpm.py
```

Historical tests require unmodified `crlzh11.lbr` and `crlzh20.lbr` in
`build/test-fixtures/crlzh/`, or `--archives PATH11 PATH20`. SHA-256 pins and
original download location are in [test_unlzh.py](../../tools/test_unlzh.py).
All 47 historical compressed members exercise the library; command tests
explicitly refuse unsafe embedded names instead of claiming all members are
published successfully. Historical decoder tests cover both variants; the
encoder round trips produce `20h` and are not tests of `10h` encoding.

Baseline library evidence: 45 assembled UNLZH round trips, all 2048 new-format
position encodings, random/repetitive/binary/empty data, >64 KiB input, overlaps,
ring wrap, maximum distance, stale search links and exact reconstruction
boundaries. Independent host match and Huffman models check wire output.
ABI/canary/code-immutability tests include callback failures, configuration
errors, count overflow, failure recovery, cyclic-tree rejection and separate
contexts. The command campaign adds 47 encoder fault-injection cases and 15
complete LZH.COM -> UNLZH.COM round trips under stock CP/M 2.2, including extents,
headers, drives, collisions and cleanup. Rebuilds qualify their exact artifacts;
these counts are baseline evidence, not a forever-fixed test interface.
