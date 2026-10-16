# Unloadable screen backend ABI 1.0

Status: backend implementation checkpoint, 2026-10-16. The standalone build
produces `M4SCRN.RSX` and `ANSISCRN.RSX`; each platform's System Disk now includes
its backend for portable VT52. See [VT52 integration](VT52%20Portable%20Backend%20Integration.md)
for native/live/ROM/distribution checks. ADM3A and ANSI personality conversion
and full release qualification remain in progress.

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
| 7 | Write cell | C=literal display byte, bit 7 selecting reverse; advance within row, clamped at column 79 |
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

`M4SCRN` writes the literal display byte to Model 4 video RAM, with bit 7 as
reverse. Cell output accepts all byte values; the personality interprets terminal
controls before making a cell call. Printable ASCII glyphs (low seven bits
32..126) are portable. Other glyphs are backend-specific: Model 4 preserves the
video byte exactly, while the ANSI-host backend substitutes `?`, retaining bit
7's reverse attribute and advancing once. It never emits a cell's control-code
value as a host terminal control. This widens operation 7's original accepted
range without changing valid ASCII calls or the SCRN 1.0 descriptor. It imports the current
BIOS's M4CURSOR and M4COLUMN addresses at build time. It must be distributed with that matching BIOS build;
it is not a portable hardware driver. Its cursor is presented by the
personality's private-cursor operation; the personality must honor its own
visibility state. Bell uses the existing Model 4 port-90 tone sequence.

`ANSISCRN` emits ANSI controls through cpmsim's basic console transport. It
assumes an ANSI-capable host endpoint with at least 80x24 cells and the normal
full-screen scrolling region. It uses addressing, SGR normal/reverse, erase,
insert/delete line, reverse index and cursor visibility. Line operations reset
the host's scrolling region to the full screen; private application margins
are not retained. Newly introduced lines and reverse EOL/EOS blanks are painted explicitly because
host terminals differ in their treatment of reverse-video blank fills. Physical
host terminal modes remain outside this ABI.

These hardware/transport choices belong to the backend. A portable personality
must contain neither Model 4 addresses nor host ANSI output strings.

## Build and evidence

Run `python3 tools/build_screen_backends.py` after building the Model 4 BIOS.
Payloads and listings go in `build/screen-backends/`; carriers are also copied
to `build/rsx/`. Provider 1.2 payloads: Model 4 545 bytes, 768 allocated; ANSI-host
831 bytes, 1,024 allocated. The allocation includes carrier/runtime overhead and
alignment. These are optional loaded costs, with zero permanent growth.

Run `tools/test_screen_backends.py` with the environment described in
`tools/requirements-monitor-tests.txt`; `--cpmsim-bios` selects an alternate
cpmsim BIOS build (default `build/z80pack`). It executes assembled machine code at
6000h and 8101h using Model 4 video RAM and an independent pyte ANSI screen.
It checks descriptor bytes, full-screen writes, right-edge clamping, reverse
cells/fills, erase, scrolling, insert/delete line and invalid-argument rejection.
This is CPU-level evidence, not live emulator, native-assembler parity or full
portable-personality lifecycle qualification.


## Optional SCX control integration candidate

Status: this control checkpoint passes CPU, native-assembler, actual manager,
live and protected-ROM cpmsim, native Model 4 editing/unload, and both clean
System Disk build/boot checks. This does not complete ANSI conversion.
Provider versions are 1.2; the callable SCRN service and original descriptor
remain 1.0. The original operations 0..15 retain their existing contracts.

Operation 16 probes the optional control family. On success A=0 and HL points
to twelve bytes: `SCX`, major 1, minor 0, length 12, rows, columns, a little-endian
operation mask, rendition flag mask and color capability mask. A legacy backend
returns A=255 instead. The masks must be checked; discovery does not promise
unimplemented operations. The current mask is 0003h, with rendition/color masks
zero. Model 4 reports 24 rows/80 columns. Zero rows/columns on the host mean
host-managed geometry, not a zero-sized screen or a detected terminal size.

- Operation 17: B=0 up, 1 down, 2 right, 3 left; HL=16-bit count.
- Operation 18: HL=one-based row, DE=one-based column.

Zero arguments use one. Model 4 clamps to its physical bounds. The host emits
its own control sequences and lets the endpoint apply its actual screen bounds,
without querying terminal input. Invalid operations/directions return 255 without
screen mutation; successful controls return zero. Other registers are scratch.

This control family is separate from the fixed 80x24 legacy cell tracker. A
caller switching back to legacy cell operations after control/raw screen output
must explicitly synchronize using operation 6, just as after raw output. Existing
ADM3A/VT52 personalities do not call SCX controls and continue using their own
fixed-screen coordinates.

`tools/test_screen_controls.py` checks 560 cases on both actual relocated
carriers, including host 80x24/80x25/100x40 geometry, full-width values, discovery,
invalid operations and explicit legacy resynchronization. Existing screen,
ADM3A and VT52 renderer checks pass. Native ZSM4/LINK matches all four monitor
and backend payloads. Candidate sizes: M4SCRN 545 bytes/768 allocated/43
relocations; ANSISCRN 831 bytes/1,024 allocated/144 relocations. Each loaded
allocation grows by 256 bytes, with zero permanent BIOS/BDOS growth.

Actual-manager relocation/unload passes on both platforms, as does live cpmsim
movement, the full ADM3A exercise and unload/53K. The larger host carrier exposed
8-bit overflow in conversion of >=128 repair words to byte counts. Preparation,
finalizer capacity and scheduler validation/copying now preserve the carry.
Scheduler regression cases include 0/1/127/128/144/255 repair words, exact and
undersized scratch capacity, and guarded destination boundaries. Zero-count
copying now avoids Z80 LDIR's 64K interpretation of BC=0.

The finalizer is 968 bytes and retained preparer 900 bytes; both stay within
existing slots. Scheduler remains 496 bytes through local instruction savings.
No permanent core image, descriptor size or interface grows. Native ZSM4/LINK
parity covers all three changed overlays as well as both backends and portable
personalities. See [repair-count qualification](RSX%20Repair%20Word%20Count%20Qualification.md).
ANSI rendition and remaining typed screen operations still need integration;
this does not complete the portable ANSI personality.

Final local evidence: `/private/tmp/bettercpm-scx-qualified-work/` for both clean
System Disks; `build/monitor-development/native-campaign/editing-hoyvix42/`
for actual Model 4 command editing and unload/53K; and
`build/monitor-development/live/cpmsim-o3hlii3d/` for guarded-ROM cpmsim with
fresh matching relocated overlays and no ROM-write violations. The Model 4
loaded backend/ADM3A pair now reports 50K; unloading both restores 53K.
