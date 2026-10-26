# NOAH ARC encoding foundation

Status: method-4 SQ adapter and method-8 encoder phase; production loader and
callback routes pass the full Z80 core; the isolated method-8 harness passes on
z80pack and TRS-80 Model 4, 2026-10-26. These are format-codec foundations only.
They do not enable `/ADD` to create or update ARC archives. The
[NOAH specification](NOAH%20Specification.md) remains normative.

## Method 4 from the owned SQ encoder

ARC method 4 uses the Huffman tree, least-significant-bit-first code stream and
RLE token stream already produced by BetterCP/M's two-pass SQ encoder. The
standalone SQ wrapper adds exactly five leading bytes before that body: magic,
additive checksum and an empty original-name terminator. The ARC member header
provides its own method number, decoded length and CRC, so those five bytes must
be omitted when the stream is used as a method-4 member.

`noahark-sq-bridge.inc` supplies `NASQ_DISPATCH` and `NASQ_RUN`. The production
SQ overlay calls the dispatcher: normal calls go straight to `SQ_RUN`, while
the resident ARC mode selects the body path. The bridge clears its temporary
context mode on both success and failure. `SQ_INIT`, `SQ_SCAN`, source-stability
checks, tree construction, output callbacks and error handling are shared with
the standalone encoder. A successful method-4 member still requires the
archive writer to place its method-4 header and compute the final decoded-byte
CRC; this component does neither.

`tools/test_ark_sq_bridge.py` executes the assembled encoder on the full Z80
core. Eight binary, empty, escape, long-run, all-byte and deterministic-random
inputs are checked with the independent SQ tree/bitstream parser. It also checks
that standard SQ framing is unchanged, that an out-of-state call is rejected,
and that a failed output callback clears the temporary mode. A generated body
passes the production method-4 TEST path under both previously measured TPA
ceilings. These are controlled full-Z80 harness results, not native CP/M runtime
qualification on z80pack or the Model 4. The production resident/overlay route
is covered separately below; archive transactions remain open.

## Isolated method-8 encoder phase

`noahark-crencode.inc` adds `N8_RUN`, an isolated ARC method-8 body encoder. It
uses CR's existing checked input, RLE tokenization, and collision-safe phrase
lookup/insertion routines, but initializes ARC's dynamic dictionary at code
257 and emits the `0Ch` twelve-bit-compress marker. It packs nine-to-twelve-bit
codes least-significant-bit first in groups of eight, pads a short group at a
width change, and leaves the final group short as ARC readers expect. It does
not emit an ARC member header, decoded-length/CRC fields, member trailer, or
archive update. The writer must still account for those values and stage and
verify the completed archive before publication.

The phase is present as `NCAR8` in the checked NOAH overlay but is not called by
the command controller. It shares CR's 25,207-byte context and required end
address (`B3F7h` with the current overlay window), so it needs no extra buffer
and ends below the existing method-5–9 LZW phase (`B980h`). Its memory use fits
both measured TPA ceilings. The phase image is 1,648 bytes, within the 2 KiB
overlay window.

`tools/test_noah_ark_crencode.py` runs 23 input vectors on the full Z80 core.
The emitted bytes match the independent dynamic-LZW/RLE model, including empty
input, DLE escaping, RLE count boundaries, width transitions, incompressible
20 KiB input, and read/write callback failure latching. Eight representative
streams were wrapped in ARC member headers and passed through production NOAH
TEST/EXTRACT under both measured ceilings, plus the original ARC utility and
the pinned Deark decoder. ZSM4/LINK output for `NCAR8` matched the cross-build
on z80pack and the Model 4. `tools/qualify_noah_ark_encoder_cpm.py` now runs the
linked encoder as an actual CP/M program on both systems. It reads a 20 KiB
binary through BDOS file callbacks, writes the method-8 body to a CP/M file and
compares every byte to the independent model. Both runs emitted 27,036 bytes
with SHA-256 `8cdf60fa1f9a3023a78b3874790b8ed6e6bce8bc434671486ed89654f7d8f440`.
The measured loaded-system ceilings were `C501h` on z80pack and `CA01h` on the
Model 4; the 25,207-byte CR context plus the harness's 1,024-byte private stack
fits below both. This qualifies only the isolated encoder's native file
callbacks and memory use. ARC headers, archive transactions and publication
remain unimplemented.

## Production resident dispatch proof

`NR_LOAD` accepts overlay module 8, and `NR_CODEC` can run it through the same
resident file callbacks used by NOAH's other codec phases. The SQ phase's third
entry is `NASQ_DISPATCH`, controlled by resident `NR_ARC_MODE`; with the flag
clear, the normal standalone SQ path retains its framing. With the flag set,
the shared SQ implementation emits only the method-4 body. The focused
`overlay_encoder_tests` case in `tools/test_noah.py` drives both module 2 and
module 8 through production `NR_CODEC`, opens simulated CP/M files, and checks
method-4 decoding and method-8 output against independent models. It also
verifies the overlay loader installs module 8 and rejects module 9 without
opening the overlay.

This closes encoder phase loading and resident callback integration under the
full Z80 core. Native CP/M execution on both platforms remains isolated to the
method-8 entry harness; no `/ADD` command sets ARC mode, emits ARC member
headers, stages or verifies an archive, or publishes an ARC update yet.

The current production modules also pass native ZSM4/LINK parity on z80pack and
the Model 4. The [qualification receipt](NOAH-ARK-Encoder-Dispatch.json) records
the focused tests, native outputs and remaining write scope; its
[evidence bundle](NOAH-ARK-Encoder-Dispatch-evidence.tar.gz) contains console,
execution and linked-file results without emulator disk images.

## Remaining encoding and update work

- Wire `NCAR8` to `/ADD /CR`, including ARC member header creation,
  length/CRC accounting, source-stability checks, staged verification and
  publication/recovery. Standalone CR output is not an ARC method-8 stream.
- Add ARC creation, replacement, REMOVE and COMPACT with exact retained member,
  raw metadata, opaque suffix and trailer preservation rules.
- Qualify the integrated writer with native ZSM4/LINK and runtime transactions
  on z80pack and the Model 4 before advertising ARC writes.
