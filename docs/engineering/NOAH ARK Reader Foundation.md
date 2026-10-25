# NOAH ARK reader foundation

Status: first ARK implementation increment, 2026-10-26. Isolated library/proof,
not a production NOAH command. The [behavioral specification](NOAH%20Specification.md)
remains normative. NOAH 1.0 revision 13 and its companion remain byte-identical to
the qualified LBR/codec build. No Utilities Disk member, command or writer is added.

The subsequent [ARK CLI increment](NOAH%20ARK%20CLI%20Integration.md) integrates
this unchanged reader into NOAH 1.0 revision 14. The scope and measurements below
record the isolated foundation at revision 13.

## Implemented boundary

`src/archive/ark.inc` and `ark.mac` implement the existing 138-byte, caller-owned
archive read ABI with private ARK entry points. There is no global mutable iterator
state. Scratch registers may be destroyed by source callbacks; IX/IY, alternate
registers and balanced SP follow the existing contract. The caller supplies a
known physical byte length and a bounded random-access byte callback.

- `ARK_OPEN` validates configuration and the initial signature/method.
- `ARK_NEXT` validates the next header, canonical CP/M name and complete stored
  extent, returning metadata and advancing the next-header position. It abandons
  unread stored bytes without interpreting them as another header.
- `ARK_RAW` returns stored bytes bounded to this member. Zero capacity performs
  no callback. Its destination must not overlap live context/adapter/code storage;
  internal CRC/trailer operations intentionally use the handler's entry scratch.
- `ARK_TEST_STORED` rewinds and CRC-tests methods 1/2, leaving the member consumed.
  Other methods return sticky `AS_UNSUPPORTED`; callers must consult the method
  before requesting a test. A CRC of zero is present and checked, not unavailable.
- `ARK_CLOSE` closes library state; adapter handle closure remains caller-owned.

Each callback request is checked against physical size before the callback.
Header/data offset overflow, truncated extents, malformed names, missing end
markers, short reads and I/O errors have distinct explicit failure paths. Errors
are sticky until CLOSE/OPEN. Callback cancellation remains `AS_CANCEL`, rather
than being hidden as a successful short stream. Invalid configuration does not
write library-owned state. Header changes between the two header reads cannot
silently switch 25/29-byte layouts.

## Method and metadata matrix

The machine-readable [matrix](../../tests/fixtures/noah/ark-methods.json) pins the
boundary against the existing [reference hashes](../../tests/fixtures/noah/references.json).

| Methods | Framing/raw read now | Decoded bytes and CRC test now | Encode now |
| --- | --- | --- | --- |
| 1, old stored | 25-byte header | Yes, identity/stored bytes | No |
| 2, stored | 29-byte header | Yes, identity/stored bytes | No |
| 3, packed RLE | 29-byte header | Unsupported | No |
| 4, squeezed | 29-byte header | Unsupported | No |
| 5/6/7, historical crunched variants | 29-byte header | Unsupported | No |
| 8, dynamic crunched | 29-byte header | Unsupported | No |
| 9, squashed | 29-byte header | Unsupported | No |
| Other/high-bit/extended methods | Explicit unsupported; no guessed boundaries | Unsupported | No |

For future native ARK encoding, `/SQ` maps to method 4 and `/CR` to method 8.
These selectors are **not implemented for ARK in this increment**. Existing
standalone CP/M Crunch files cannot be relabelled as native ARC method 8, and an
explicit selector must not silently fall back to a different method or stored
output. Compression decoding, encoder provenance and realistic workspace limits
remain separate gates, especially the historical variants and 13-bit method 9.

`AM_ID` is the header offset; `AM_OFFSET` is the stored payload offset;
`AM_STORED` is stored length; `AM_LENGTH` is declared decoded length. Methods 1/2
require stored and decoded lengths to agree. The name is normalized to padded
8+3 with one optional dot and a required NUL inside the 13-byte source field.
Path/drive syntax, wildcards, controls, high-bit bytes and overlong components
are rejected. Padding after the first filename NUL is not treated as another name.

The raw DOS date/time words are copied without conversion. Member byte 41 is the
ARK-local `ARK_DOS_DATE` format tag; old consumers must not interpret these as
LUDEF dates. No date validity/conversion, timestamp restoration, duplicate-name
audit, encryption, self-extracting prefix scan or damaged-header resynchronization
is claimed. Future CLI integration must retain those distinctions and must not
present an opaque compressed member as tested.

## End marker and historical trailers

`1Ah,00h` is the authoritative archive end marker. On EOF, `AS_DIR_END` holds the
byte after it and `AS_UNUSED_SEEN` classifies the physical suffix:

- 0: no physical suffix;
- 1: every suffix byte is `00h` or `1Ah` padding;
- 2: an opaque suffix was observed; its contents remain unvalidated.

This distinction is required by the pinned `de-lbr.arc`: it has 146 non-padding
trailing bytes. The reader exposes that limitation instead of pretending the
suffix is padding or an integrity pass. The end marker bounds the recognized
container; opaque trailer preservation/authorization during updates is **not**
implemented. A future command must report the limitation and must not silently
rewrite/discard such data. No payload byte is treated as CP/M EOF during RAW or
CRC testing; only the declared member extent governs data reads.

## Source provenance and independent evidence

The implementation is original BetterCP/M assembly. It reuses BetterCP/M's owned
LBR ABI transfer/state primitives with private ARK names; no SEA ARC or Deark
implementation code is copied, linked or distributed as NOAH code. Published
format facts come from the pinned `Arcinfo` (Robert A. Freed's CP/M UNARC format
notes, preserved by Keith Petersen), with pinned SEA ARC and Deark sources used
as reference/oracle material. The SEA reference distribution contains GPL notices;
Deark has its own pinned COPYING notice. Public source availability is not used
as a claim of permission to copy it into BetterCP/M.

`tools/noah_compatibility.py` re-verifies every pinned reference and uses the
pinned Deark executable to independently decode historical method-8/9 fixtures
and generated method-1/2/3/4 vectors, checking reported/calculated CRCs and output
hashes. This validates the fixtures/oracle, not compressed decoding by our reader.
The original historical archives remain reference-only inputs; portable evidence
retains their URLs/hashes and oracle logs/output hashes, not third-party contents.

## Qualification and measured limits

`tools/test_ark.py` executes the assembled library on the full Z80 core with
clobbering callbacks. Its 53 cases cover empty/old/new stored members, binary and
zero-CRC data, a stored member crossing 64 KiB, methods 3–9 raw framing, unread
member abandonment, filename validation, exact/padded/opaque EOF, truncation,
32-bit overflow, destination wrap, invalid configuration, CRC/I/O/short-read/
cancellation failures, sticky errors and interleaved contexts. The inherited
checks preserve configuration, IX/IY/alternate banks/SP and context/code canaries.
Three additional pinned historical inventories match an independent host parser:
`crc32a.arc` (three method-8 members), `de-lbr.arc` (two method-8 members and opaque
trailer), `nulu15.arc` (two method-8/9 members). No compressed CRC claim is made.
The unchanged LBR tests still pass after making the shared test harness's
instruction budget configurable for the 64-KiB-crossing CRC case.

`tools/qualify_ark_reader.py` builds the isolated `ARKPRF` with unmodified native
ZSM4/LINK on z80pack and Model 4, requiring exact machine-code parity. With
terminal providers loaded, it checks old/new stored CRCs, all three historical
inventories, opaque trailers, a bad stored CRC and an unsupported method. The
proof reports verified-stored versus opaque counts separately. Source disks and
inputs remain unchanged and disposable media are filesystem-checked. See the
[receipt](NOAH-ARK-Reader.json) and portable evidence. Physical hardware and
production NOAH/ARK coexistence qualification are not claimed.

Measured library: **1,295 bytes**, context **138 bytes**. Reader plus the existing
CP/M adapter: **1,846 bytes**. Isolated proof: **3,106 bytes**, including adapter,
driver, data and a 512-byte private stack; required exclusive ceiling `0D22h`.
Native loaded-provider ceilings are `C501h` and `CA01h`. These are isolated-proof
measurements, not permission to append the reader to production NOAH, whose
lowest-profile spare space is only 513 bytes.

A promising integration is a sixth checked phase containing reader plus adapter
and a small entry dispatcher: 1,846 bytes leaves 202 within the current 2-KiB
window. The index has room for a sixth 16-byte descriptor before its CRC field.
That design is **not yet qualified**. Resident dispatch must restore the controller
before returning to its code, retain iterator/adapter state outside the window,
and never leave a handler callback on the stack while loading a decoder. Native
compressed bytes also need a bounded source adapter and native ARC codecs; the
existing CP/M stream codecs cannot simply be called on every ARC method.

## Remaining bounded increments

1. Integrate the checked ARK phase and production format dispatch; qualify
   LIST plus stored TEST/EXTRACT, including reporting, safe publication and the
   lowest loaded-provider TPA. Production code must reject unsupported formats
   honestly throughout the transition.
2. Add native ARC decoding/CRC qualification method by method, with historical
   fixtures and measured dictionary/stack bounds. Then add native encoding for
   the pinned selectors; no automatic fallback.
3. Add staged ARK creation/ADD/replacement/REMOVE/COMPACT with opaque-data and
   trailer preservation rules, source stability and fault qualification.
4. Complete command/format interoperability, documentation and Utilities Disk
   release acceptance/packaging. The browser remains deferred.
