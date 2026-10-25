# NOAH ARK Huffman/RLE decoding

Status: NOAH 1.0 revision 16, method-4 decoding increment, 2026-10-26.
The [specification](NOAH%20Specification.md) remains normative. This extends the
[packed decoder](NOAH%20ARK%20Packed%20Decoding.md), without adding encoding,
archive updates or browser features. Qualification receipts and portable evidence
are in [NOAH-ARK-Huffman.json](NOAH-ARK-Huffman.json).

## Method and integration boundary

Production NOAH now supports ARC methods 1/2 (stored), 3 (packed RLE) and
4 (explicit Huffman tree followed by RLE). LIST continues to enumerate metadata
without testing contents. TEST/EXTRACT decode selected method-4 members, check
exact decoded length and CRC-16/ARC (including zero), and use existing archive
selection, overwrite authorization, staged output, reopened comparison and
recovery behavior. Methods 5–9 remain explicit unsupported warnings/skips.
The reusable ARK_RAW and stored-only integrity API remain unchanged.

The implementation uses owned code and the existing USQ tree-validation strategy;
no external decoder source is copied or linked. An ARC method-4 body begins with
a little-endian tree count and child pairs. It has no standalone Squeeze magic,
filename or additive checksum: the ARC member header supplies filename, decoded
length and CRC. Only Huffman symbols feed the shared method-3 RLE stage. CRC and
length accounting apply to final decoded file bytes, not Huffman/RLE tokens.

## Tree, bitstream and failure policy

- Counts are 0–256 internal nodes, with two signed 16-bit children per node.
  Root index is zero. Nonnegative children must be in the declared node range;
  negative leaves must be -1 through -257, representing symbols 0–256.
- Validation uses a fixed 256-byte mark array and repeated iterative sweeps.
  It rejects cycles, shared internal children, unreachable stored nodes and
  nonempty trees without an EOF leaf. Arbitrary node ordering is accepted.
  Leaf values may repeat. Neither validation nor symbol traversal recurses.
- A zero-node tree represents empty input. A nonempty tree decodes bits least
  significant first; symbol 256 ends the Huffman stream. Physical stored EOF
  before the tree or required symbol completes is truncation. Huffman EOF during
  a pending RLE escape is also truncation.
- Unused bits in the final compressed byte are tolerated. Whole stored bytes
  after Huffman EOF are rejected, including bytes already buffered. This policy
  concerns compressed-member contents; the existing separate policy for physical
  padding or opaque trailers after the archive end marker is unchanged.
- RLE history, decoded bounds and CRC follow method 3's documented behavior.
  Excess/short decoded length, invalid trees, I/O errors and bad CRCs cannot
  produce a successful file. Reader/decoder errors remain sticky.

Every integrity, extraction, staged-comparison and safe-retry pass resets the
raw stored cursor, input buffer, Huffman readiness/bit/EOF state, RLE state,
decoded count and CRC. Each pass rereads and validates its tree; it does not reuse
a tree from an earlier member or failed output attempt. Source callbacks stay in
the loaded controller. Cancellation is polled during tree validation and the
existing compressed-input/test/extraction paths.

The selected-member audit checks names/framing before output. Unselected member
trees are not decoded, and no verified-CRC credit is assigned to them. Existing
input exclusion, frozen batches, destination users, DOS timestamp warnings and
opaque-container-trailer warnings retain their previous meanings.

## Memory and qualification

All new state remains in the supplemental NHARK module within the inactive LBR
writer arena: 1,024 bytes for child pairs, 256 validation marks and small scalar
state. The input/output buffers and RLE/CRC machinery are shared with method 3.
No additional resident buffer or transient-memory allowance is assumed.

| Measurement | Revision 16 |
| --- | --- |
| Resident bytes | 18,433 |
| Controller/codec window | 4980h |
| NHARK address / bytes | 9200h / 4,306 |
| Rounded NHARK load end | A300h |
| Largest required end | C400h, unchanged |
| Loaded z80pack ceiling / spare | C501h / 257 bytes |
| Loaded Model 4 ceiling / spare | CA01h / 1,537 bytes |

The focused full-Z80 checks include shuffled node numbering, all byte values,
input/output record boundaries, a maximum-depth 256-node tree, empty data, zero
CRC, invalid counts/leaves/links, cycles, shared/unreachable nodes, missing EOF,
truncated trees/bitstreams, dangling RLE escape, extra stored bytes, decoded
length/CRC mismatch, filtered corrupt members, cancellation, stage tampering and
Retry/Skip state resets. Host-intercepted stack high-water is 56 bytes within the
existing private stack; this is not a native BDOS stack measurement.

The valid generated fixture independently matches pinned Deark output. Native
qualification uses unchanged ZSM4/LINK on both platforms, compares phase bytes,
reconstructs the companion from native products, and runs LIST/TEST/EXTRACT with
terminal providers loaded. Native cases cover valid/empty method-4 output, bad
CRC, bad link, cycle, missing EOF, truncated tree, invalid leaf, short/excess
decoded length and extra stored bytes. Outputs and source archives are compared
byte-for-byte, and disposable filesystems checked. Unchanged codec builds may be
reused only after byte parity. Maximum-depth, injected save failures and other
host-only cases are not claimed as native runtime cases.

Existing method-3, stored-ARK/historical, LBR read/write, codec and reporting
regressions are retained. The pinned historical archives contain methods 8/9;
their continued enumeration/unsupported outcomes do not establish historical
method-4 interoperability. This increment's method-4 compatibility evidence is
the generated independent fixture/oracle and native qualification stated above.

## Remaining work

Methods 5–7 (historical static LZW variants) and 8/9 (dynamic LZW) still require
compatibility and dictionary/workspace proofs. Their memory use must not be
assumed to fit the present narrow controller margin. Compatible encoding,
staged ARK writes and metadata/trailer preservation, broader interoperability
and release acceptance, and disk packaging remain open. Interactive browsing,
ZIP and LZH/LZ remain deferred.
