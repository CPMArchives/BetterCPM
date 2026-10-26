# NOAH ARC encoding foundation

Status: isolated native method-4 encoder adapter proof, 2026-10-26. This is a
format-codec foundation only. It does not enable `/ADD` to create or update ARC
archives. The [NOAH specification](NOAH%20Specification.md) remains normative.

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

## Remaining encoding and update work

- Integrate this entry into NOAH's checked production overlay and archive ADD
  path, including ARC member header creation, length/CRC accounting, source
  stability, staged verification and publication/recovery.
- Implement and independently qualify native method-8 encoding for `/CR`;
  standalone CR output is not an ARC method-8 stream.
- Add ARC creation, replacement, REMOVE and COMPACT with exact retained member,
  raw metadata, opaque suffix and trailer preservation rules.
- Qualify the integrated writer with native ZSM4/LINK and runtime transactions
  on z80pack and the Model 4 before advertising ARC writes.
