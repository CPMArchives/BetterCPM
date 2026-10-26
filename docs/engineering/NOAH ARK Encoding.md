# NOAH ARC encoding foundation

Status: method-4 SQ adapter and method-8 encoder phase; production loader and
callback routes pass the full Z80 core; the isolated method-8 harness passes on
z80pack and TRS-80 Model 4, 2026-10-26. The ARC writer entries now share the
production `NHARK` overlay and pass the resident layout check for the existing
12,800-byte arena. The current padded NHARK image ends at `A780h`; a 6,144-byte
ordinary source-plan table can follow it and end at `BF80h`, below the arena end
at `C400h`. The build and host regression now assert this non-overlap. No NOAH
command invokes those writer entries yet: this is a memory-layout proof, not an
archive update feature. The
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

## ARC member stream writer foundation

`src/archive/arkwrite.inc` and `arkwrite.mac` provide `ARK_BUILD_HEADER`,
`ARK_WRITE_MEMBER`, and `ARK_WRITE_END`. The serializer validates canonical
padded CP/M 8.3 names and writes the new-format 29-byte header for methods 2
(stored), 4 (SQ) or 8 (CR), including exact stored/logical lengths, raw DOS
date/time words and CRC. `ARK_WRITE_MEMBER` streams that header and exactly
the stored payload length through caller-provided input and output callbacks;
the caller's 128-byte buffer supports bounded chunks without adding physical
record padding to member data. `ARK_WRITE_END` emits ARC's `1Ah 00h` marker.
The caller still owns physical record packing/padding, retained-member order,
opaque trailer handling, staged readback and NOAH's publication transaction.
The API uses static scratch and is not reentrant.

`tools/test_ark.py` assembles these routines beside the production ARC reader.
It checks method-2/4/8 header bytes and metadata round trips, malformed-name
rejection, a 522-byte member across 128-byte boundaries, an empty member, the
end marker, source I/O failure, short reads and failed output. This remains an
isolated library proof, not NOAH command integration. `/ADD`, replacement,
`/REMOVE`, `/COMPACT`, trailer preservation, staged readback and
publication/recovery remain open.

`tools/qualify_ark_writer_cpm.py` adds one native CP/M method-2 write check.
On z80pack, unmodified ZSM4/LINK build the proof, and the program writes a
522-byte deterministic member plus the ARC end marker. The extracted 640-byte
CP/M file matches the independent 553-byte ARC oracle followed only by `1Ah`
record padding. The linked proof ends at `13ACh` against the measured `C501h`
active TPA ceiling. Its [receipt](NOAH-ARK-Writer-Native.json) records the
input-system and output hashes. This is an isolated library/runtime check; it
does not exercise NOAH archive staging, retained members, recovery, or
publication.

The same run has not completed on the Model 4. The local trs80gp 2.5.8 process
aborted during startup on macOS 27.2, and LaunchServices could not launch the
temporary test bundle. Treat Model 4 writer qualification as pending; the
z80pack result does not close the cross-platform gate.

## Writer entry points in the production overlay

`tools/noah_overlays.py` now assembles the shared ARC framing library and
`ARK_BUILD_HEADER`, `ARK_WRITE_MEMBER`, and `ARK_WRITE_END` into the reloadable
`NHARK` phase. `tools/test_noah.py` checks that each exported entry falls inside
the assembled phase and that its record-padded image remains within the
existing 12,800-byte inactive arena. This adds no resident TPA allocation and
preserves the original nine reader/controller slots. Three stable writer
dispatch slots now follow those entries; the host layout test pins their
addresses and target labels. The existing `tools/test_ark.py` vectors continue
to exercise the writer implementation in isolation.

The entries are not yet connected to `/ADD`, `/REMOVE`, or `/COMPACT`. The
current overlap has a bounded memory solution for ordinary source plans:
derive the plan-table start from the record-padded NHARK size and place the table
after the loaded overlay. The deterministic host build asserts the table fits
inside the existing arena. The future command path still has to preserve that
relocated table while loading and calling the overlay, supply read/write
callbacks, reconcile ARC member enumeration and source-plan metadata,
independently reopen and verify the staged archive, recheck source stability,
and only then use NOAH's existing safe publication/rollback path. Neither a
native CP/M transaction nor Model 4 writer qualification is claimed by this
layout proof.

## Remaining encoding and update work

- Wire the production method-4/8 encoders and method-2 copy path to `/ADD`,
  including length/CRC accounting, source-stability checks, staged verification
  and publication/recovery. Standalone CR output is not an ARC method-8 stream.
- Add ARC creation, replacement, REMOVE and COMPACT with exact retained member,
  raw metadata, opaque suffix and trailer preservation rules.
- Qualify the integrated writer with native ZSM4/LINK and runtime transactions
  on z80pack and the Model 4 before advertising ARC writes.
