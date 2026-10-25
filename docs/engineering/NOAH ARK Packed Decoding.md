# NOAH ARK packed decoding

Status: NOAH 1.0 revision 15, method-3 decoding increment, 2026-10-26.
Build/runtime evidence is recorded in [NOAH-ARK-Packed.json](NOAH-ARK-Packed.json).
The [specification](NOAH%20Specification.md) remains normative. This extends the
[stored ARK integration](NOAH%20ARK%20CLI%20Integration.md); it adds no encoder,
archive update, browser or new command.

## Implemented behavior

ARC method 3 is now supported by LIST/TEST/EXTRACT. LIST reports metadata without
reading or claiming to verify contents. TEST decodes selected members and verifies
both exact declared decoded length and CRC-16/ARC, including a present zero CRC.
EXTRACT uses the same decoder and existing safe-save machinery. Methods 1/2 retain
their stored behavior. Methods 4–9 remain explicit unsupported skips/warnings.

The original Z80 implementation is internal to NOAH's supplemental module. The
reusable ARK framing library and its stored-only integrity entry point are
unchanged: ARK_RAW still means stored bytes. The method matrix now explicitly
records production NOAH capabilities rather than the earlier isolated reader.
No external codec source is copied or linked. Pinned format/reference sources
and the independently built Deark oracle remain reference/test material.

Packed data uses 90h followed by a count to repeat the preceding decoded byte,
with the preceding occurrence included in the count. Count zero emits literal
90h; count one emits no additional byte. An escaped 90h becomes the preceding
byte for subsequent repeats, matching Deark. A nonzero repeat without a preceding
byte is rejected. A marker without its count is truncated input. The fixture
encoder emits literal 90h runs as escapes, avoiding historical decoder differences
in the interpretation of repeats immediately following an escaped marker.

Stored input is buffered in 128-byte chunks. Pending repeats, input position,
decoded 32-bit count and CRC survive output-chunk boundaries. The decoded length
is checked before emitting each byte; EOF must match both the declared length
and CRC. Excess or insufficient decoded length, dangling markers, malformed
repeat history, I/O failure and CRC mismatch are errors, not successful short
files. Failed reader/decoder state remains sticky. Selected-member bounds prevent
consumption of a following header as compressed input.

Every test/extraction/retry pass resets the decoder and restores the **stored**
input extent from immutable member metadata. The existing staged verification
pass now resets decoder state too; rewinding only the byte cursor would be
incorrect for a streaming codec. Reopened candidate bytes are compared against a
fresh decode before publication. Failed stages follow the existing cleanup and
Retry/Skip rules, preserving an existing destination. Cancel polling occurs during
test chunks and the existing extraction/read paths. No inner CP/M expansion is
implied by decoding the ARK storage method.

Duplicate-name audit, member filters, frozen archive queues, destination DU,
input exclusion, protection/overwrite prompts, raw DOS timestamp warnings and
opaque-trailer warnings retain their existing meanings. Integrity coverage counts
method 3 as verified only after successful length/CRC validation. Unselected
members are not decoded or credited with verified CRCs.

## Memory and qualification

The decoder's buffers and state live with NHARK in the inactive writer arena;
no additional resident buffer, stack allocation or TPA is assumed.

| Measurement | Revision 15 |
| --- | --- |
| Resident bytes | 18,433 |
| Controller/codec window | 4980h |
| NHARK address / bytes | 9200h / 2,629 |
| Rounded NHARK load end | 9C80h |
| Largest required end | C400h, unchanged |
| Loaded z80pack ceiling / spare | C501h / 257 bytes |
| Loaded Model 4 ceiling / spare | CA01h / 1,537 bytes |

Focused full-Z80 checks cover repeated runs across output records, literals across
input records, escaped marker bytes, embedded zero/1Ah, empty data, a present zero
CRC, count-one behavior, decoded counts beyond 65535, malformed/truncated streams,
length mismatch, CRC mismatch, filtered corrupt members, stage tampering and
Retry/Skip decoder resets. The main generated fixture's decoded bytes also match
pinned Deark output. Existing stored-ARK/historical, LBR write, codec, coverage and
read/adapter checks remain in place.

Native qualification uses the unchanged ZSM4/LINK tools on both platforms,
compares all phase products, reconstructs the companion from native bytes, and
runs LIST/TEST/EXTRACT with terminal providers loaded. Native runtime includes
valid and empty packed members plus bad CRC, dangling marker, excess/short decoded
length and orphan-repeat refusal. Extracted files and source archives are compared
byte-for-byte and disposable filesystems checked. Large decoded-count and injected
save-failure checks are host Z80 checks, not claimed as native runtime cases.
Unchanged codec modules may reuse retained native builds only after byte parity.

## Remaining decoding work

Next is method 4 (Huffman plus this RLE stage), with independent fixtures and
measured tree/workspace bounds. Methods 5–7 and dynamic LZW methods 8/9 require
separate compatibility and workspace proofs; the current controller leaves only
a small memory margin, so their dictionary storage must not be assumed to fit.
Compatible encoding, staged ARK writes and preservation, broader historical
interoperability/release qualification and disk packaging remain open. The
interactive browser, ZIP and LZH/LZ remain deferred.
