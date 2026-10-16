# VT52 provider foundation qualification

**Historical ANSI-adapter evidence.** The native VT52 correction supersedes
these output-format and host-rendering claims. See [current correction and
remaining gates](VT52%20Native%20Correction%20Qualification.md). Retained test
results below describe the earlier artifact, not the corrected native carrier.

## Status and build

VT52 targets cpmsim with an ANSI host terminal.
It is included on the cpmsim distribution disk but is not loaded by startup. ADM3A's Model 4 release is unchanged.

`tools/build_vt52.py` emits VT52.RSX, VT52TST.COM and listings under
`build/vt52-development`. The carrier is STATEFUL, module version 1.0, with an
MCON 1.0 callable service and backend bit 0002h. The ordinary RSX entry passes
unclaimed BDOS calls through the next link. Payload is 653 bytes, with 116 static
relocation slots and a 768-byte allocation including the runtime descriptor.
Its cursor/parser and queue-index storage contains bytes, not internal runtime pointers.

The entry uses the existing MONRAW hook derived from the running WBOOT vector.
No cpmsim change or built-in emulator VT52 translation is required: the RSX
translates VT52 output into ANSI bytes. Input/status now merge keyboard bytes and identification replies in a bounded
queue; terminal key modes remain unimplemented.

## Implemented output

- ESC Y addressing in the normal 24-by-80 range, high invalid row retaining
  the previous row and high column clipping to 79.
- ESC A/B/C/D movement with edge clamping, and ESC H home.
- Printable output advances through column 78 and remains at column 79.
  An explicit ANSI address after margin output cancels ANSI delayed wrapping.
- Backspace clamps at column 0. TAB goes to fixed 8-column stops up to 72,
  then advances one column at a time to 79.
- Line feed scrolls at the bottom; ESC B at the bottom does nothing.
- ESC I moves up, or emits ANSI reverse index at the top.
- ESC J/K emit ANSI erase-to-end operations; CR moves to column 0.
- NUL and DEL are ignored; BEL is passed to the host.
- Explicit clear resets parser/cursor and emits ANSI clear/home; parser reset
  alone preserves the cursor and emits no host bytes.

Unassigned controls and unknown escape selectors are consumed for development
containment. This does not settle the specification's outstanding historical
parser questions. Low invalid coordinate parameters currently retain the
corresponding coordinate; that is provisional and not a compatibility claim.

The host must provide at least 80 columns and 24 rows, ANSI cursor addressing,
erasure and scrolling margins, and ordinary origin/LF modes. Boundary LF and
reverse-LF temporarily set rows 1..24 as the scrolling area and explicitly
restore full host margins and cursor position afterward. Independent rendering
checks now cover 80x24 and 100x40 hosts. Arbitrary pre-existing host modes,
smaller windows and resizing during a sequence are not qualified.

Cursor address rows remain pending until the column arrives. Resetting a partial
address therefore leaves both the host cursor and committed provider coordinates
unchanged. Clear or explicit home/address establishes initial host/provider
cursor coherence after a load; manual use should run CLS before screen work.

## Identification and input queue

ESC Z enqueues ESC / K without changing display coordinates or emitting host
output. A 16-byte ring has byte-sized head/tail/count fields and reserves all
three reply bytes before writing. Insufficient capacity drops the entire newest
reply. Existing keyboard/reply bytes and their order are preserved.

When the logical queue is empty, status polls MONRAW and may enqueue one observed
keyboard byte. A nonempty queue returns ready without further backend reads.
Repeated status calls never remove logical bytes. Input pops the oldest queued
byte or uses raw blocking input when empty. Thus provider-observed keyboard
bytes stay ahead of later replies; unread backend bytes need not precede a reply
that was already generated. Parser reset and clear preserve the input queue.

No polling is added to identification generation, and no attempt is made to infer
abstract arrow/keypad events from arbitrary host character bytes.

## Checks

Build an actual cpmsim BIOS with `tools/build_z80pack_image.py`, then run
`tools/test_vt52_foundation.py` (default BIOS directory build/z80pack), or pass
`--bios` with the desired build directory containing bios.bin and bios.lst.
The fixture executes the real host BIOS, with controlled console ports, and
relocates the provider to 6000h and 8101h.

There are 49,920 cursor/control cases covering thirteen operations at every
screen coordinate at both load addresses, plus normal-range cursor addressing,
high clipping, interrupted-sequence reset, clear, ignored controls, bell and
raw input/status bypass. Expected ANSI byte streams and provider coordinates
are checked independently. These are not rendered-terminal screenshots.

The queue campaign runs at both load addresses and checks all 16 ring phases
and all 17 occupancy boundaries: keyboard A before five complete replies,
keyboard B afterward, repeated non-consuming status, atomic overflow and
preservation across reset/clear. It also verifies that identification produces
no screen output. The utility generates an ID request, resets its output parser,
and reads the three reply bytes through raw non-echoing console input.

The assembled VT52TST utility is exercised with controlled BDOS service lookup
and keyboard input: missing-provider preflight, all three pauses, raw addressed
output, erasure and parser reset. Its raw-output strings avoid both BDOS TAB
expansion and dollar-termination of encoded coordinate bytes.

## Remaining work

Complete release build/version/manifest integration and document optional
graphics/keypad omission; preserve research-only parser cases from the selected historical
reference. The actual carrier now passes production relocation/lookup/unload, live
cpmsim utility checks and an unchanged VT52 WordStar edit/save run. See
[VT52 live qualification](VT52%20Live%20Qualification.md) for evidence and limits.
Add /VER, normal build/distribution entries and startup only when qualified.
VT52TST looks up MCON, not a personality name; use it only with the VT52 provider.
