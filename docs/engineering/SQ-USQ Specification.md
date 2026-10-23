# SQ/USQ Engineering Specification

This is an implemented-baseline specification dated 2026-10-23. The
[common engineering specification](Compression%20Utilities%20Common%20Specification.md)
defines the Z80 ABI, callbacks, statuses, file adapter and safe publication.
Offsets below are decimal. Allocation size is public; working fields are private
and must not be changed during processing. The `.inc` files remain the exact
assembly definitions. These documents do not add unimplemented command options.

## Sources and entries

[SQ definitions](../../src/codec/sq.inc), [SQ code](../../src/codec/sq.mac),
[USQ definitions](../../src/codec/usq.inc), [USQ code](../../src/codec/usq.mac).
Commands: [sq.mac](../../src/utilities/sq.mac), [usq.mac](../../src/utilities/usq.mac).
User pages: [SQ](../user/SQ.md), [USQ](../user/USQ.md).

| Entry | Required phase/capabilities | Result |
| --- | --- | --- |
| `SQ_INIT` | Configured prefix, READ/WRITE/REWIND, bounded SQ_NAME | READY; no I/O |
| `SQ_SCAN` | READY; input initially at start | Read first pass, build tree, rewind once; DATA; no output |
| `SQ_RUN` | DATA | Header and second pass, count/sum comparison, encoded EOF; DONE |
| `USQ_INIT` | Configured prefix, READ | READY; no I/O |
| `USQ_HEAD` | READY | Signature/name/tree read and validated; DATA; no output |
| `USQ_GET` | DATA | NC/A=decoded byte; C/CS_END after checksum verification |
| `USQ_RUN` | DATA, WRITE | Decode/write to verified DONE |
| `USQ_END` | DATA | Discard remaining decoded bytes and verify; DONE |

Repeated completed processing calls and latched failures follow the common ABI.
HEAD/SCAN are not repeatable completion probes. Encoder has no GET/END interface.

## Squeezed wire format

| Order | Encoding |
| --- | --- |
| Signature | Bytes `76 FF` |
| Checksum | 16-bit little-endian additive sum of original bytes |
| Name | Raw NUL-terminated field, at most 127 non-NUL bytes |
| Node count | Little-endian word, 0..256 internal nodes |
| Tree | Each internal node: two signed little-endian child words |
| Body | Huffman bits, least-significant bit first within each byte |

Node zero is the root. Nonnegative children identify an internal node; a negative
child `-(symbol+1)` identifies literal 0..255 or stop symbol 256 (`-257`). USQ
validates child ranges and rejects cycles, shared subtrees, unreachable nodes
and trees without an EOF leaf. A zero-node tree is the historical empty-stream
special case; its decoded checksum must still match. Physical EOF is never a
substitute for an encoded end, except that zero-node representation needs no
body bits. For empty input SQ emits that zero-node representation; otherwise it encodes
stop symbol 256 through the generated tree.

RLE is applied before Huffman encoding: literal `90h` uses `90 00`; after a
history byte, `90 n` repeats it to a total run count n. A nonzero count below 2,
missing history or an encoded EOF while awaiting a count is corrupt. All output
bytes, including literal `90h` and `1Ah`, contribute to the original-byte sum.
The checksum is in the header, not a trailer. Any partial final compressed byte
is zero-padded by SQ; command-level disk padding is separately 1Ah.

## SQ algorithm and input stability

SCAN computes RLE-symbol frequencies, checksum and a 32-bit byte count, builds
a binary Huffman tree, then rewinds. Frequency rescaling keeps weights within
16 bits while retaining every used symbol. There are 257 possible leaves and
at most 256 internal nodes. Parent paths permit up to 256 bits; there is no
16-bit code-length restriction, recursion or full-file buffer.

RUN repeats RLE and walks the saved tree. It compares second-pass count and sum,
and rejects a symbol absent from pass one before emitting encoded EOF. Failure
is `CS_CHECK`, detail `SD_CHANGED=2`; counter overflow is `CS_SPACE`, detail 3.
A name without a NUL in 128 slots is `CS_CONFIG`, detail 80h. These checks do not
prove an unchanged file: the caller must hold a stable snapshot through both
passes. SQ.COM closes/reopens the source, restores its original 12-byte FCB name
and clears all extent/current-record state and input buffering for pass two.
The reopen is not a locking mechanism. Temporary output is created after SCAN.

USQ corruption details 1..5 identify node count, child range, tree structure,
RLE and overlong name respectively. Its 128th non-NUL header byte is
`CS_CORRUPT`/5, unlike UNCR/UNLZH's `CS_SPACE` header diagnostic. Library names
are raw data; filename policy belongs to the command.

## Command-specific behavior

`SQ [drive:]file [destination-drive:]` replaces the second extension slot with
Q. No extension becomes `.QQQ`; short extensions retain the other slots, so
`.A` and `.AB` both become `.AQ`. A source with Q already in the second slot is
refused even when another destination drive is selected. Examples:

| Source | Squeezed name |
| --- | --- |
| `REPORT.TXT` | `REPORT.TQT` |
| `CODE.ABC` | `CODE.AQC` |
| `SHORT.A` | `SHORT.AQ` |
| `NOEXT` | `NOEXT.QQQ` |

SQ embeds the original uppercase name without drive or trailing extension blanks.
USQ validates that entire embedded field as a plain 8.3 name; header metadata,
padded spaces and high-bit names are not accepted by USQ.COM. USQ does not require
Q in the input extension. It uses `USQ_HEAD` before MAKE and never publishes a
checksum failure. Its format/header errors share the `invalid or truncated
squeezed file` message. SQ separately reports second-pass reopen and changed-input
failures. Neither command replaces an existing output or deletes its source.

## Workspace layout

### SQ — 3524 bytes

| Field/block | Decimal offset | Meaning |
| --- | ---: | --- |
| `SQ_SUM` | 16 | current pass sum modulo 65536 |
| `SQ_EXPECT` | 18 | first-pass original-byte checksum |
| `SQ_TOTAL` | 20 | scaled symbol-frequency total |
| `SQ_ROOT` | 22 | Full node index of generated tree root. |
| `SQ_NEXT` | 24 | next internal index (257..513) |
| `SQ_NAMLEN` | 26 | Private working state. |
| `SQ_RLE_STATE` | 27 | Private working state. |
| `SQ_LAST` | 28 | Private working state. |
| `SQ_RUNLEN` | 29 | Private working state. |
| `SQ_PENDING` | 30 | Private working state. |
| `SQ_RLE_FLAGS` | 31 | Private working state. |
| `SQ_COUNT` | 32 | current pass original-byte count |
| `SQ_EXPECT_COUNT` | 36 | first pass count, 32-bit LE |
| `SQ_OUTBYTE` | 40 | Private working state. |
| `SQ_OUTMASK` | 41 | Private working state. |
| `SQ_PATHLEN` | 42 | word, up to 256 bits |
| `SQ_MIN_INDEX` | 44 | Private working state. |
| `SQ_MIN_WEIGHT` | 46 | Private working state. |
| `SQ_FIRST_INDEX` | 48 | Private working state. |
| `SQ_FIRST_WEIGHT` | 50 | Private working state. |
| `SQ_RESERVED` | 52 | twelve private bytes |
| `SQ_TREE_NODES` | 60 | Private working state. |
| `SQ_NAME` | 64 | caller fills before INIT; preserved |
| `SQ_WEIGHTS` | 192 | 513 unsigned 16-bit node weights |
| `SQ_PARENTS` | 1218 | 513 parent words, bit15=right edge |
| `SQ_CHILDREN` | 2244 | 256 pairs of full child indices |
| `SQ_PATH` | 3268 | reverse path: 256 one-byte bits |

### USQ — 1440 bytes

| Field/block | Decimal offset | Meaning |
| --- | ---: | --- |
| `UQ_EXPECT` | 16 | Private working state. |
| `UQ_SUM` | 18 | Private working state. |
| `UQ_NODES` | 20 | Private working state. |
| `UQ_BITBYTE` | 22 | Private working state. |
| `UQ_BITSLEFT` | 23 | Private working state. |
| `UQ_LAST` | 24 | Private working state. |
| `UQ_REPEAT` | 25 | Private working state. |
| `UQ_FLAGS` | 26 | Private working state. |
| `UQ_NAMLEN` | 27 | Private working state. |
| `UQ_COUNT` | 28 | 32-bit original-byte count, LE |
| `UQ_NAME` | 32 | 127 bytes plus NUL; bytes preserved |
| `UQ_TREE` | 160 | 256 pairs of signed child words |
| `UQ_MARKS` | 1184 | 256 validation marks: 0/1/2 |

## Reproduction and qualification scope

```sh
python3 tools/test_codec.py
python3 tools/test_sq.py
python3 tools/test_usq.py
python3 tools/test_sq_com.py
python3 tools/test_usq_com.py
python3 tools/test_sq_com_cpm.py
python3 tools/test_usq_com_cpm.py
```

Library tests cover malformed trees/RLE, truncation, checksum, long paths,
rescaling, pass changes, callbacks, status latching, register preservation and
bounds. Command fault injection checks destructive BDOS semantics are guarded,
FCB reset after close, temporary ownership and source preservation. Stock CP/M
2.2 tests exercise actual SQ.COM -> USQ.COM record round trips, binary/empty
files, extent boundaries, destinations and collisions on disposable disks.
Wire compatibility does not imply an identical historical tree or output file.
