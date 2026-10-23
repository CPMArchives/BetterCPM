# Archive read library — initial LBR implementation

This is the first NOAH implementation increment, not the complete archive API
or a release qualification. The normative behavior remains in the
[NOAH specification](../engineering/NOAH%20Specification.md).

The library is original Z80 code derived from the published
[LUDEF5 format definition](https://www.seasip.info/Cpm/ludef5.html), not copied
from LU/NULU source. There are no external code or historical binaries bundled
with this increment. Historical fixture/tool interoperability remains pending.

## Assembly and ownership

Include `src/archive/archive.inc` and `src/archive/lbr.mac`, then emit `LBR_CODE`
once. The include is the authoritative register/layout/status contract, shared
by the library, command, adapter and tests. All public entries preserve IX/IY,
the alternate register bank and stack balance. AF/BC/DE/HL are scratch unless
an entry explicitly returns them. This is a provisional read ABI, version 1;
writer, overlay and capability interfaces remain engineering gates.

A caller owns a nonwrapping allocation of at least `AS_CONTEXT_SIZE` (138) bytes.
The first 12 bytes are configuration; the rest belong to the library. Before
OPEN, initialize ABI=1, RESERVED=0, READ, USER, FILE_SIZE and SIZE. READ is an
absolute-byte-offset callback; USER is an opaque caller context pointer.
FILE_SIZE is a known 32-bit physical length. The declared SIZE must describe
accessible memory; the library can check arithmetic, not actual ownership.
Even invalid allocations must have an accessible, nonwrapping 12-byte prefix.

The callback reads AS_OFFSET/AS_BUFFER/AS_COUNT and writes AS_ACTUAL. It returns
NC for a transfer, or C with an adapter-specific reason in A. Every request must
be satisfied exactly; NC with a short/overlong transfer is AS_TRUNC. A callback
may destroy the primary scratch registers but must preserve IX/IY, alternate
registers, SP and context bytes other than AS_ACTUAL and the requested buffer.
Output buffers must be accessible and must not overlap the archive context,
adapter workspace or executing code. The library rejects wrapping ranges; it
cannot discover actual memory ownership.
No recursive invocation on the same context is allowed. Separate contexts may
share the emitted code; the library has no mutable global state.

| Entry | Contract |
| --- | --- |
| `LBR_OPEN` | Initialize library state and validate the control entry and directory extent against physical length. Does not audit all members or check CRCs. |
| `LBR_NEXT` | Enumerate one active member in directory order. Skip deleted entries without interpreting their undefined fields. Skip unused entries and reject later occupied entries. Return C/AS_END at directory end. Abandons unread data of the previous member. |
| `LBR_READ` | DE=output buffer, BC=capacity. Read up to the member's remaining logical length; return NC and BC=actual count. Capacity zero performs no I/O. A nonzero read at member end returns C/AS_END, BC=0. No read crosses the member boundary. |
| `LBR_CLOSE` | End the library state with no I/O. Does not close caller-owned streams. |

All non-END operational errors are sticky until CLOSE or a new OPEN. OPEN
configuration failures return AS_CONFIG without changing library state; callers
must not continue an operation after failed configuration. The callback's I/O
reason is retained in AS_DETAIL when AS_IO is returned. Error-return BC is
unspecified except for the documented normal member-end case.

The 64-byte member record at AS_MEMBER belongs to the caller allocation and is
valid until NEXT, OPEN or CLOSE. Copy it if longer lifetime is needed. It holds
the normalized padded 8.3 name, stable directory-byte-offset ID, physical start,
stored bytes, logical bytes, pad count, CRC advertisement and raw timestamp words.
Lengths/offsets are checked 32-bit bytes, including record endpoints above
65535. Empty member indices are meaningless and normalized to zero. Bytes 1Ah
are ordinary data; only the explicit LUDEF pad count shortens logical length.

Method zero denotes opaque LBR storage, not an assertion that the member's
contents are uncompressed. Nonzero advertised CRC sets the availability flag;
no CRC is claimed verified. Zero CRC may mean unavailable and is not taken as
proof of corruption. Timestamp words are exposed unchanged; date conversion,
effective inherited change dates and availability belong to the forthcoming
metadata layer. Unknown control-entry metadata is ignored as LUDEF requires.

## Standard CP/M binding

Include `cpmfile.inc` / `cpmfile.mac` and emit `ARCHIVE_CPM_CODE` once after the
LBR code. AS_USER points at a zero-initialized AP_SIZE (176) byte allocation.
Build AP_FCB as an ordinary exact CP/M FCB (drive 0 means logged drive). The
caller owns name/DU parsing; it need not parse LBR structures or wire callbacks.

`AC_OPEN` opens the FCB, obtains physical record count, supplies the read callback
and calls LBR_OPEN. Call `AC_CLOSE` even after OPEN returns an error: a successful
FCB open followed by size/header failure still owns a handle. Opening an already
owned handle returns AS_STATE without losing it. A close failure returns AS_IO
and retains the opened marker so the caller can report/retry cleanup. AC_CLOSE
also closes the LBR state after successful FCB cleanup.

```asm
        ; IX -> configured archive context
        ; AS_USER -> zeroed adapter workspace with AP_FCB already prepared
        CALL AC_OPEN
        JR C,FAILED_WITH_CLEANUP
NEXT_MEMBER:
        CALL LBR_NEXT
        JR C,END_OR_ERROR       ; AS_END is distinct from a read/format error
        ; Consume/copy AS_MEMBER metadata here; then optionally read data.
        LD DE,MY_BUFFER
        LD BC,128
        CALL LBR_READ
        ; Continue reads until AS_END, or move directly to NEXT_MEMBER.
```

Adapter reads translate absolute offsets into bounded random-record reads and
copy only requested bytes from its private DMA record. It never changes drive
or user, creates output, writes data, renames or erases files. CP/M random-record
numbers must fit 24 bits; unsupported media/read failures remain AS_IO, never a
clean EOF. The adapter changes BDOS DMA to AP_DMA; the caller must restore its
own DMA after the operation (the NOAH command restores 0080h).

## Current command and verification

Build with `python3 tools/build_noah.py`. Development commands are:

```text
NOAH [/LIST] [drive:]file
NOAH /VER
NOAH /HELP
```

This first command accepts one exact ordinary filename in the current user
area. It prints active member names and logical byte lengths in hexadecimal,
then explicitly states that CRCs/content were not tested. Partial read failures
and close failures do not print a completed listing. No write path exists.
It is not yet added to the Utilities Disk; its full filespec grammar, sorting,
batch selection, member filtering, CRC/overlap/duplicate audits, extraction,
ARK, updates, common timestamp metadata and NOAH.OVL are still pending.
Unsupported command forms are rejected before any archive open.

Reproduce the first-increment checks with:

```text
python3 tools/test_lbr.py
python3 tools/test_noah.py
```

Both assemble the actual code and execute it on a temporary full z80pack Z80
core. Fixtures are independently constructed in Python from LUDEF fields.
The command harness intercepts BDOS with deliberately clobbered scratch
registers and injected open/size/random-read/close failures. It forbids write
services. Checks retain original input bytes, private-stack discipline,
registers, context guards, immutable code and deterministic builds.

Measured first increment: 948 bytes of LBR library code, 138-byte library
context, 176-byte CP/M adapter workspace, and 3,374-byte NOAH.COM. The command
reserves a 256-byte stack (lower 128 bytes temporarily hold normalized version
query text); maximum observed stack use is 28 bytes with BDOS intercepted.
This is not a native BDOS/BIOS stack bound, minimum-TPA claim, native-assembler
qualification or historical interoperability qualification. Those remain open.
