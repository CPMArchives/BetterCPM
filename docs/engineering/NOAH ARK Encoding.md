# NOAH ARC encoding foundation

Status: isolated native method-4 adapter and method-8 encoder phase proofs,
2026-10-26. These are format-codec foundations only. They do not enable `/ADD`
to create or update ARC archives. The
[NOAH specification](NOAH%20Specification.md) remains normative.

## Method 4 from the owned SQ encoder

ARC method 4 uses the Huffman tree, least-significant-bit-first code stream and
RLE token stream already produced by BetterCP/M's two-pass SQ encoder. The
standalone SQ wrapper adds exactly five leading bytes before that body: magic,
additive checksum and an empty original-name terminator. The ARC member header
provides its own method number, decoded length and CRC, so those five bytes must
be omitted when the stream is used as a method-4 member.

`noahark-sq-bridge.inc` supplies `NASQ_RUN`, which temporarily selects the
context-owned method-4 header path while calling the existing `SQ_RUN`. It clears
the mode on both success and failure. `SQ_INIT`, `SQ_SCAN`, source-stability
checks, tree construction, output callbacks and error handling are shared with
the standalone encoder. The ordinary SQ entry remains unchanged. A successful
method-4 member still requires the archive writer to place its method-4 header
and compute the final decoded-byte CRC; this component does neither.

`tools/test_ark_sq_bridge.py` executes the assembled encoder on the full Z80
core. Eight binary, empty, escape, long-run, all-byte and deterministic-random
inputs are checked with the independent SQ tree/bitstream parser. It also checks
that standard SQ framing is unchanged, that an out-of-state call is rejected,
and that a failed output callback clears the temporary mode. A generated body
passes the production method-4 TEST path under both previously measured TPA
ceilings. These are controlled full-Z80 harness results, not native CP/M runtime
qualification on z80pack or the Model 4. Archive transactions and production
overlay integration remain open.

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
on z80pack and the Model 4. The broad Model 4 runtime regression was stopped
during its pre-existing 20 KiB decoder case; the encoder phase itself has not
yet been invoked from CP/M on either platform.

## Remaining encoding and update work

- Add a small native CP/M runtime harness for invoking `NCAR8` on both targets.
- Wire `NCAR8` to `/ADD /CR`, including ARC member header creation,
  length/CRC accounting, source-stability checks, staged verification and
  publication/recovery. Standalone CR output is not an ARC method-8 stream.
- Add ARC creation, replacement, REMOVE and COMPACT with exact retained member,
  raw metadata, opaque suffix and trailer preservation rules.
- Qualify the integrated writer with native ZSM4/LINK and runtime transactions
  on z80pack and the Model 4 before advertising ARC writes.
