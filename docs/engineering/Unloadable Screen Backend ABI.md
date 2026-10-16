# Unloadable screen backend ABI 1.0

Status: backend implementation checkpoint, 2026-10-16. The standalone build
produces `M4SCRN.RSX` and `ANSISCRN.RSX`. They are not yet installed on the
System Disks. Personality conversion and full release qualification remain in
progress; existing shipping personalities retain their current behavior.

A backend advertises STATEFUL callable service `SCRN` 1.0, with capability 1
for Model 4 or 2 for cpmsim. Selection and the manager-owned MCON 1.1 reference
are defined in [production integration](Monitor%20Backend%20Production%20Integration.md).
There is one backend per active profile. Load it before a dependent personality;
unload the personality before the backend. Loaded allocations reduce TPA;
these modules add no permanent BIOS or BDOS code.

## Calling convention

A is the operation; B/C contain arguments below. Registers and flags are
scratch, the stack is balanced. Invalid screen operations/arguments return
A=255 without output or screen mutation. Other results are unspecified except
where listed. Coordinates are zero-based in a fixed 80-column, 24-row screen.
Calls must be serialized and cannot reenter the backend.

| A | Operation | Input/result |
| --- | --- | --- |
| 0..5 | Basic console operations | Existing MONRAW convention; 0 is basic output, 1 status, 2 input, 3 private cursor, 4 clear, 5 reset |
| 6 | Position | B=row 0..23, C=column 0..79 |
| 7 | Write cell | C=ASCII 32..126, optionally OR 80h for reverse; advance within row, clamped at column 79 |
| 8 | Erase to end of line | C=20h normal blank or A0h reverse blank; cursor unchanged |
| 9 | Erase to end of screen | Same fill and cursor rules |
| 10 | Scroll screen up one line | Same fill and cursor rules; fill bottom line |
| 11 | Scroll screen down one line | Same fill and cursor rules; fill top line |
| 12 | Query | HL points to nine bytes: `SCR`, 1, 0, 24, 80, FFFFh (little-endian operation mask) |
| 13 | Insert current line | Move current and following rows down, discard bottom, fill current row; same fill/cursor rules |
| 14 | Delete current line | Move following rows up, fill bottom; same fill/cursor rules |
| 15 | Cursor visibility | C=0 hidden, 1 visible |

The prototype's write-and-hold primitive is superseded by operation 7's
write-and-advance contract. It avoids cursor-address output for each ordinary
character. This production contract has not previously shipped.

Operations 0..5 expose the basic transport for status/input and bell. A
personality uses typed operations for screen changes and owns its screen cursor
state. After using basic clear/output to change the screen, synchronize with
operation 6 before typed rendering; raw terminal escape sequences must not
bypass the backend's tracked position/rendition. No terminal grammar is parsed
by a backend.

## Implementations

`M4SCRN` writes Model 4 video RAM, with bit 7 as reverse. It imports the current
BIOS's M4CURSOR and M4COLUMN addresses at build time, as the existing ADM3A
implementation does. It must be distributed with that matching BIOS build;
it is not a portable hardware driver. Its cursor is presented by the
personality's private-cursor operation; the personality must honor its own
visibility state. Bell uses the existing Model 4 port-90 tone sequence.

`ANSISCRN` emits ANSI controls through cpmsim's basic console transport. It
assumes an ANSI-capable host endpoint with at least 80x24 cells and the normal
full-screen scrolling region. It uses addressing, SGR normal/reverse, erase,
insert/delete line, reverse index and cursor visibility. Line operations reset
the host's scrolling region to the full screen; private application margins
are not retained. Newly introduced lines are painted explicitly because host
terminals differ in their treatment of reverse-video blank fills. Physical
host terminal modes remain outside this ABI.

These hardware/transport choices belong to the backend. A portable personality
must contain neither Model 4 addresses nor host ANSI output strings.

## Build and evidence

Run `python3 tools/build_screen_backends.py` after building the Model 4 BIOS.
Payloads and listings go in `build/screen-backends/`; carriers are also copied
to `build/rsx/`. Model 4 payload: 372 bytes, 512 allocated; ANSI-host payload:
523 bytes, 768 allocated. The allocation includes carrier/runtime overhead and
alignment. These are optional loaded costs, with zero permanent growth.

Run `tools/test_screen_backends.py` with the environment described in
`tools/requirements-monitor-tests.txt`; `--cpmsim-bios` selects an alternate
cpmsim BIOS build (default `build/z80pack`). It executes assembled machine code at
6000h and 8101h using Model 4 video RAM and an independent pyte ANSI screen.
It checks descriptor bytes, full-screen writes, right-edge clamping, reverse
cells/fills, erase, scrolling, insert/delete line and invalid-argument rejection.
This is CPU-level evidence, not live emulator, native-assembler parity or full
portable-personality lifecycle qualification.
