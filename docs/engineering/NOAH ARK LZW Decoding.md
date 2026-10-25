# NOAH ARC LZW decoding and workspace proof

Status: NOAH 1.0 revision 17, ARC methods 5–9 decoding, 2026-10-26. The
[specification](NOAH%20Specification.md) remains normative. Native qualification
and portable evidence are recorded in [NOAH-ARK-LZW.json](NOAH-ARK-LZW.json).

## Supported methods

NOAH now decodes methods 5–9 for selected ARC members during TEST and EXTRACT.
LIST continues to report header metadata without reading member contents. Each
decode checks the exact decoded length and ARC CRC-16, including zero CRC, and
uses the existing staged output, comparison and recovery flow. A malformed
stream, output longer than declared, short output, bad CRC or source error cannot
be reported as verified or published. The generic ARK reader's raw-byte ABI and
stored-only test entry remain unchanged.

Methods 5–7 use a 4,096-slot static dictionary and fixed-width 12-bit
most-significant-bit-first codes. Methods 5 and 6 use the historical squared
hash with chained collision slots; method 7 uses ARC 4.6's multiplier hash.
Methods 6 and 7 pass their LZW output through the ARC run-length stage. Methods
8 and 9 use dynamic LZW dictionaries and least-significant-bit-first code
packing. Method 8 starts with the 0Ch twelve-bit-compress header, grows from
nine to twelve bits and applies RLE. Method 9 is the 13-bit squashed variant.
Both dynamic methods honor CLEAR code 256 and restart their dictionary and code
width. Width changes and CLEAR codes discard the unused remainder of the
current eight-code packing group. The final short group may end with fewer than
eight padding bits.

The run-length stage expands LZW bytes before final output accounting. It keeps
the established ARC escape and repeat semantics, rejects a repeat without prior
history, and rejects an unfinished escape. Length and CRC apply to final file
bytes. Every TEST, extraction, staged comparison and retry opens the member at
its recorded stored offset and resets the LZW dictionary, bit reader, RLE state,
length and CRC. A Retry therefore starts from the original stream position.

The decoder uses fixed-width arithmetic, an explicit phrase-path bound and no
recursive calls or per-phrase stack growth. Invalid codes and broken prefix
chains fail as format errors; physical input exhaustion in an incomplete code
is truncation. Output is capped at the member's declared decoded length. The
existing source-bound and cancellation callbacks remain in the resident module.

## Compatibility evidence

The owned implementation was checked against generated streams with independent
ARC and Deark decoders, then against the pinned historical archives
`crc32a.arc`, `de-lbr.arc` and `nulu15.arc`. The historical set exercises methods
8 and 9, including the 13-bit path. Their reference hashes are in
[`references.json`](../../tests/fixtures/noah/references.json); the payloads
remain in the local reference cache and are not copied into the evidence bundle.
No external decoder source is copied or linked into NOAH.

The focused production checks cover all methods, empty dynamic members, all
byte values, long repeated runs, 128-byte record boundaries, 20 KiB
incompressible streams, dictionary-width growth, CLEAR resets, invalid first
codes, impossible dynamic codes, short/excess output, bad CRC, Retry/Skip state
reset, source close failure, cancellation and unchanged pre-existing targets.
Host-side oracle runs compare method 5–9 fixtures to the original ARC decoder;
Deark independently checks methods 5, 6, 8 and 9. Method 7's oracle is the
pinned original ARC decoder.

Native qualification on z80pack and the TRS-80 Model 4 assembled and linked the
new LZW phase with the repository's unchanged ZSM4 and LINK tools. Native runtime
tests extracted generated members for all five methods, rejected corrupt CRC
and malformed static/dynamic streams, and tested the 20 KiB method 8/9 streams
through the full decoder and CRC path. The three historical archives passed
native LIST/TEST; `de-lbr.arc` retains its expected partial warning because its
opaque trailer is not interpreted. Host production tests also extracted every
historical member and compared bytes with the pinned oracle output. Filesystem
checks and retained-source hashes passed on both platforms.

## Transient-memory boundary

The decoder runs as a temporary whole-member phase. Its 1,705-byte code image
loads at `4980h` and ends before the live 2 KiB NOAH context at `5180h`. The
24,576-byte dictionary and hash workspace starts at `5980h` and ends at `B980h`.
The phase never keeps a CLI or ARK callback return address inside the replaced
window: resident callbacks handle bounded input and output, and the bridge
reloads the CLI and ARK modules before returning.

| Measurement | Address / size |
| --- | ---: |
| LZW phase code | `4980h`, 1,705 bytes |
| Preserved NOAH context | begins `5180h` |
| Dictionary/workspace | `5980h`–`B980h`, 24,576 bytes |
| LZW phase required end | `B980h` |
| Lowest loaded z80pack TPA ceiling | `C501h` |
| z80pack space above LZW workspace | 2,945 bytes |
| Lowest loaded Model 4 TPA ceiling | `CA01h` |
| Model 4 space above LZW workspace | 4,225 bytes |
| Existing whole-NOAH maximum required end | `C400h` |

The overlay descriptor declares the `B980h` required end, and the resident loader
checks it against BDOS's current transient-memory ceiling on every phase load.
The overall program still needs `C400h` for its existing writer plans and
transformed-identity area; that leaves 257 bytes at the z80pack ceiling and
1,537 bytes on the Model 4. LZW itself fits both ceilings, while the whole
program's existing `C400h` boundary remains the tighter limit.

## Remaining work

Methods 1–9 can now be read, tested and extracted. Compatible ARC encoding,
staged ARC creation and updates, opaque metadata/trailer preservation, broader
interoperability, release acceptance and Utilities Disk packaging remain open.
The interactive browser, ZIP and LZH/LZ remain deferred.
