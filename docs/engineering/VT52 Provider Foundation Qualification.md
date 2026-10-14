# VT52 provider foundation qualification

## Status and build

The first VT52 development stage targets cpmsim with an ANSI host terminal.
It is not distributed or loaded by startup. ADM3A's Model 4 release is unchanged.

`tools/build_vt52.py` emits VT52.RSX, VT52TST.COM and listings under
`build/vt52-development`. The carrier is STATEFUL, module version 0.1, with an
MCON 1.0 callable service and backend bit 0002h. The ordinary RSX entry passes
unclaimed BDOS calls through the next link. Payload is 456 bytes, with 80 static
relocation slots and a 512-byte allocation including the runtime descriptor.
Its cursor/parser storage contains bytes, not internal runtime pointers.

The entry uses the existing MONRAW hook derived from the running WBOOT vector.
No cpmsim change or built-in emulator VT52 translation is required: the RSX
translates VT52 output into ANSI bytes. Input/status currently pass through;
identification replies and terminal key modes are not implemented yet.

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

The foundation assumes an ANSI host configured for 80 columns and 24 rows with
ordinary full-screen scrolling and LF semantics. Larger windows, altered host
scroll regions, terminal mode normalization and resize behavior are live
qualification/design gates. In particular, byte-stream tests cannot establish
that host LF scrolls at logical row 23 in a taller window.

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

The assembled VT52TST utility is exercised with controlled BDOS service lookup
and keyboard input: missing-provider preflight, all three pauses, raw addressed
output, erasure and parser reset. Its raw-output strings avoid both BDOS TAB
expansion and dollar-termination of encoded coordinate bytes.

## Remaining work

Implement identification/reply queues, graphics, keypad and required input
semantics; resolve outstanding parser cases from the selected historical
reference. Qualify real RSX installation/movement/unload and host rendering,
then test real VT52-configured software (a local WordStar VT52 disk is available).
Add /VER, normal build/distribution entries and startup only when qualified.
VT52TST looks up MCON, not a personality name; use it only with the VT52 provider.
