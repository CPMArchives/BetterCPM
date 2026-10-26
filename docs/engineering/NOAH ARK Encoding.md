# NOAH ARC encoding and writer integration

Status: production command integration implemented, 2026-10-26. Native ZSM4/LINK parity, ARC transactions and
NOAH companion-volume execution pass on z80pack and Model 4. See [the integration record](NOAH%20ARC%20Write%20Integration.md) for
transaction, workspace and qualification details. The
[NOAH specification](NOAH%20Specification.md) remains normative.

## Native encodings

`/ADD` emits ARC stored method 2. `/ADD /SQ` emits method 4 using the owned
SQ encoder's Huffman/RLE body, without the standalone magic, checksum or filename
prefix. `/ADD /CR` emits native ARC method 8: dynamic 9-to-12-bit LZW with the
`0Ch` marker and ARC's code-group packing. It uses the owned CR input/RLE/hash
primitives, rather than embedding or relabeling a standalone Crunch stream.
All three retain the original member name. Explicit compression is honored even
when the result grows. Historical methods 1–9 remain readable; newly compressed
members are decoded and checked before publication.

The SQ overlay's `NASQ_DISPATCH` selects `NASQ_RUN` only while the resident ARC
mode is set. Ordinary standalone SQ retains its framing. The `NCAR8` phase
exposes `N8_RUN`, sharing CR's checked callbacks and dictionary workspace.
`NR_CODEC` runs both encoders through resident file callbacks and restores the
controller. ARC preparation finishes before any source-plan rows are live.

## Shared writer API

`src/archive/arkwrite.inc` and `arkwrite.mac` export `ARK_BUILD_HEADER`,
`ARK_WRITE_MEMBER`, `ARK_WRITE_END` and `ARK_COPY_MEMBER`. The serializer validates
canonical 8.3 names and writes method-2/4/8 29-byte headers with exact stored and
logical lengths, raw DOS date/time words and CRC-16/ARC. Callers supply bounded
read/write callbacks and a 128-byte buffer; the library emits no physical padding
inside a member. `ARK_COPY_MEMBER` copies original legacy/extended headers and
stored payloads byte-for-byte, preserving names, order, methods and raw metadata.
Short reads, short writes and offset overflow fail without successful cursor
advancement. Static scratch makes the API non-reentrant.

`NHARK` retains its original nine reader/controller slots, followed by writer
slots at +27/+30/+33/+36. The private transaction audit is at +39. Generated
`layout.json` records their targets, phase lengths, rounded load extent and
separate source-plan addresses. `NW_OVERLAY`, `NW_PLANS` and `NW_ARC_PLANS` are
distinct generated symbols.

## Prior component evidence

The [encoder dispatch receipt](NOAH-ARK-Encoder-Dispatch.json) and its
[evidence bundle](NOAH-ARK-Encoder-Dispatch-evidence.tar.gz) qualify the earlier
isolated encoder routes. `tools/test_ark_sq_bridge.py` checks method-4 bodies
against an independent Huffman/RLE parser. `tools/test_noah_ark_crencode.py`
checks 23 method-8 vectors, callback errors, original ARC and Deark decoding.
The [isolated writer receipt](NOAH-ARK-Writer-Native.json) records method-2
creation and exact retained-member copying on both systems. These receipts are
historical component evidence; their old load addresses and sizes do not replace
the current integrated layout or production transaction campaign.

The current command path stages and verifies complete ARC archives and uses
NOAH's existing publication/rollback machinery. The interactive browser, ZIP
and LZH/CrLZH selectors remain deferred.
