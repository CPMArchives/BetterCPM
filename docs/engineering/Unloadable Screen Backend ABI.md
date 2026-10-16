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
to `build/rsx/`. Provider 1.6 payloads: Model 4 1182 bytes, 1280 allocated; ANSI-host
1,091 bytes, 1,280 allocated. The allocation includes carrier/runtime overhead and
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


## Rendition and styled-glyph integration checkpoint

Provider 1.3 retains SCRN 1.0 and SCX 1.0. SCX discovery now reports operation
mask 001Bh: relative movement (17), position (18), rendition (20), and styled
glyph (21). Erasure (19) is still unimplemented and returns 255.

Operation 20 takes HL pointing to nine bytes: flags, foreground kind, three
foreground color bytes, background kind, three background color bytes. Kind 0
is default, 1 is a palette index in the first color byte, and 2 is RGB. Flags,
from bit 0 to 7, mean bold, faint, italic, underline, blink, reverse, conceal,
strike. Both color kinds are validated before any state/output change. Invalid
kinds return 255; success returns zero. The entire record is copied into the
backend, so the caller's buffer need not remain live after the call.

Model 4 retains the full record and renders reverse/conceal. Its advertised
rendition mask is 60h and color mask zero. Unsupported physical styles/colors
are inert rather than rejected, making the physical limit visible through
capability discovery. The ANSI-host rendition mask is FFh and color mask 7
(base palette, 256-color palette and RGB). This describes the controls the
backend encodes; physical host attribute/color support remains endpoint-dependent.
Its palette encoding uses CSI 38/48;5 and RGB uses CSI 38/48;2. The host does not
receive any raw application escape sequence through this interface.

Operation 21 takes printable ASCII C=32..126 and uses the stored rendition.
It returns zero; invalid glyphs return 255 without writing or changing pending
wrap. Unlike operation 7, this operation follows ANSI delayed wrapping: writing
the rightmost cell leaves a pending wrap, taken by the next glyph. Explicit
positioning or relative motion cancels pending wrap. At the bottom, writing the
next glyph scrolls and fills the new line in the current rendition. Host output
retains its actual dimensions; Model 4 uses 80x24. Private margins are not yet
part of this control slice.

The host caches styled mode, invalidates legacy rendition on a style change,
and restores canonical rendition after a legacy cell/fill. Legacy callers keep
their original normal/reverse behavior. Typed control callers still synchronize
with operation 6 before using the fixed-cell tracker. Model 4's pending-wrap
byte and canonical record survive manager movement. The host's temporary
internal color pointer is cleared before callback return, so no undeclared
runtime pointer survives relocation.

Qualified checkpoint payloads: M4SCRN 703 bytes/768 allocated/60 relocations; ANSISCRN
1,091 bytes/1,280 allocated/188 relocations. Model 4's allocation is unchanged
from provider 1.2; the host adds 256 loaded bytes. No permanent BIOS/BDOS or
manager code changes are needed in this increment.

`tools/test_screen_rendition.py` checks 3,072 attribute/palette cases across
both actual backends at two relocation addresses, plus RGB, atomic invalid
records/glyphs, cached rendering, legacy/styled switching, delayed wrap and
bottom scrolling. Host tests include 80x25 and 100x40 geometry. The independent
pyte model does not represent faint/conceal: those host encodings are checked
on the wire; Model 4 conceal is checked directly in video RAM.

`tools/test_adm3a_lifecycle.py` now retains nondefault canonical state and a
right-edge pending wrap across unrelated-module removal, then continues styled
output through the repaired callback. Both platform manager tests pass, along
with existing ADM3A/VT52 screen tests and native ZSM4/LINK parity.

`tools/qualify_screen_rendition_cpmsim.py --diskdefs <build>/diskdefs` generates a
private transient test, resolves SCRN through public Function 182, checks SCX
capabilities, renders RGB/reverse text, switches legacy/styled output, restores
normal rendition, and unloads to 53K. Its captured output is independently
rendered by pyte. The test is not a new distribution utility. Ordinary live
cpmsim passes; local evidence is `build/screen-rendition-live/cpmsim-6dzo4gfv/`.
Protected-ROM public lookup/rendering passes with the matching relocated
container and no ROM-write violations; evidence is
`build/screen-rendition-live/cpmsim-8j0gjvkz/`. Both clean System Disk builds/boots
pass (`/private/tmp/bettercpm-rendition-qualified-work/` locally). Actual Model 4
legacy command editing and unload/53K pass with the new backend;
`build/monitor-development/native-campaign/editing-95tsk5qs/`. This native campaign
checks compatibility, while direct SCX rendition semantics are covered by the
assembled-code/video-RAM tests rather than a native SCX visual exercise.
The production ANSI personality remains unchanged; parser integration, erasure,
margins, save/restore/index and release application qualification remain open.

Before activating a portable ANSI personality, admission must establish that its
backend supplies all required controls, not merely SCRN 1.0. Current optional
capability discovery does not by itself change the manager's dependency rules.
No existing ANSI carrier is switched to the new path in this checkpoint.


### SCX erasure integration (provider 1.4)

Operation 19 takes B=0 for the current line or B=1 for the screen, and
C=0 for cursor through end, C=1 for beginning through cursor, or C=2 for
all. Endpoints include the cursor cell. Other arguments return 255 before
changing state or output. Success returns zero. The cursor and delayed-wrap
state are preserved. With a pending wrap, suffix erasure starts logically after
the last-column cell: line suffix is empty and screen suffix begins on the next
row. Prefix and entire-line/screen forms still include the last-column cell.
This agrees with the ANSI-host endpoint model and is explicit in the Model 4
implementation; it does not consume the deferred wrap. Erased cells use the stored canonical rendition;
Model 4 physically implements reverse blanks and host output uses CSI J/K
under the canonical attributes. The host endpoint supplies its actual geometry.
The operation mask is now 001Fh. This adds no permanent BIOS/BDOS bytes.

`tools/test_screen_erasure.py` checks 288 cases across both relocated carriers,
including 80x24, 80x25 and 100x40 host geometries, inclusive ranges, reverse/RGB
blank attributes, cursor preservation and atomic invalid arguments. These are
CPU/terminal-model checks. Additional qualification passed through public SCRN
lookup on live cpmsim RAM and protected-ROM builds, with styled inclusive prefix
erasure verified from captured output. Both restore 53K after unload. Evidence:
`build/screen-rendition-live/cpmsim-mqn9kle9` (RAM) and
`build/screen-rendition-live/cpmsim-eli53q8s` (guarded ROM).
The manager lifecycle test also executes erasure through the rebound callback
after moving the backend, then confirms pending wrapping and 53K unload.
Native/cross assembly parity passes for both backends and the manager helpers.
Model 4 erasure is CPU/VRAM-qualified; this checkpoint does not claim a native
visual erasure exercise.

Provider 1.4 payloads are M4SCRN 810 bytes/1024 allocated/69 relocations and
ANSISCRN 1141 bytes/1280 allocated/196 relocations. Model 4 grows by one loaded
256-byte page; host allocation is unchanged. Unloaded permanent memory is
unchanged.


### SCX margins and index integration (provider 1.5)

The operation mask is 00BFh: operations 17–22 and 24, excluding 23.
Operation 23 remains unsupported; cursor save/restore is not yet implemented.
The callable descriptor remains SCRN 1.0 and discovery remains SCX 1.0.

Operation 22 sets scrolling margins. HL is the one-based top row and DE the
one-based bottom row; zero selects the screen default (top 1, bottom last row).
At least two rows are required. Setting margins homes the cursor at physical
row/column zero and clears pending wrapping. The Model 4 validates its physical
24-row bounds before mutation; host geometry remains endpoint-managed, as with
positioning. Both backends reject a nonzero bottom not greater than the effective
top before emitting or changing state. Success returns zero, rejection 255.
A host cannot report rejection based on unknown physical screen dimensions.

Operation 24 takes B=0 for index, B=1 for next line (index plus carriage return),
and B=2 for reverse index. Other values return 255 without state/output changes.
Index/reverse index preserve the column; next line selects column zero. All
three clear pending wrapping. At the corresponding margin they scroll only the
selected region, preserving rows outside it. Otherwise they move one physical
row, stopping at the physical screen edge. Model 4 styled wrapping also uses the
selected region, and paints newly exposed rows with canonical reverse blanks.
Legacy fixed-cell scrolling remains full-screen. ANSI-host output sends index
or reverse-index controls under the current canonical rendition; actual blank
attributes and movement outside margins follow the host terminal. The terminal
model used by tests supplies default attributes on newly exposed rows, so tests
verify Model 4 physical fills separately rather than claiming identical host
blank rendition. Next-line output is CR followed by ESC D, avoiding reliance on
the endpoint's newline-mode treatment of ESC E.

Margin bounds are initialized to the full Model 4 screen and retained through
RSX movement. Host margins live in the terminal and survive backend relocation;
the manager test verifies both forms alongside canonical rendition, deferred
wrapping, rebound service calls and 53K unload.

`tools/test_screen_margins.py` passes 640 region/index/wrap cases at two load
addresses, including 80x24, 80x25 and 100x40 host screens, plus default reset,
invalid arguments and Model 4 movement outside margins. Existing motion,
erasure and rendition tests pass, as does native assembly parity. A live cpmsim
public-service exercise verifies forward/reverse scrolling and unchanged outer
rows (`build/screen-rendition-live/cpmsim-6jpqfg8c`), with a matching protected-ROM
run at `build/screen-rendition-live/cpmsim-9a4s0xkt` (all seven ROM guards pass,
no ROM writes, clean unload/53K). Model 4 has CPU/VRAM evidence;
a native visual region exercise remains part of validation.

Payload/allocation/relocation counts: M4SCRN 1090/1280/106, ANSISCRN
1267/1280/216. Model 4 adds one loaded page over provider 1.4; host allocation is
unchanged. No permanent BIOS/BDOS bytes or TPA-boundary changes are introduced.


### SCX cursor/rendition save integration (provider 1.6)

SCX operation 23 takes B=0 to save and B=1 to restore. There is one reusable
slot: another save replaces it; restoring does not consume it. Restoring before
the first save, or an action other than 0/1, returns 255 without changing state
or output. Success returns zero. The operation mask is now 00FFh (all currently
assigned operations 17–24); SCRN and SCX descriptor versions remain 1.0.

The saved state contains cursor position and the entire nine-byte canonical
rendition, including physically unsupported Model 4 attributes/colors. Margins
are independent and are neither saved nor restored. Restore cancels deferred
wrapping, so the next glyph overwrites the saved cell rather than wrapping from
a saved right-edge position. Saving does not consume an existing pending wrap.
Cursor visibility is not part of this slot.

Model 4 stores the physical cursor/column and rendition in backend state. The
saved video address is an external hardware address, not a self-pointer to be
relocated. ANSI-host uses the endpoint's DECSC/DECRC cursor slot and keeps its
own copy of canonical rendition; it reapplies the copied rendition on restore
and retains the endpoint slot for repeated restoration. The backend owns that
endpoint slot while active. A client must not independently overwrite it through
raw ESC 7/8 and then expect SCX restoration to retain its previous position.
Host restoration follows the endpoint's current bounds/margins; changing those
bounds can constrain a previously saved position. Saving/restoring arbitrary
external terminal state is not part of this API.

Saved state survives manager compaction. The lifecycle test saves at a pending
right-edge wrap before moving backend/personality, then restores and writes
through the rebound callback twice, checks canonical state, and unloads to 53K.
`tools/test_screen_cursor_save.py` passes 288 continuation cases at two relocated
addresses and 80x24/80x25/100x40 host sizes, plus unset-slot, replacement,
repeated-restore, margin-independence and atomic invalid-action checks. Existing
legacy screen, motion, erasure, rendition and margin suites pass. The legacy
invalid-operation fixture now uses 255 rather than the already supported erase
operation 19. Native/cross assembly parity passes for both backends.

Live public-service lookup and repeated restoration pass on cpmsim RAM
(`build/screen-rendition-live/cpmsim-mqlfeza0`) and protected ROM
(`build/screen-rendition-live/cpmsim-l6wxuqaa`). All seven ROM guards pass, no ROM
writes occur, and unloading restores 53K. Model 4 remains CPU/VRAM-qualified for
these typed controls; native visual validation remains pending.

Payload/allocation/relocation counts: M4SCRN 1182/1280/120 and ANSISCRN
1357/1536/232. Host allocation grows by one loaded 256-byte page; Model 4
allocation is unchanged. No permanent BIOS/BDOS bytes change. Portable ANSI
parser conversion and complete backend capability admission remain necessary;
this checkpoint alone does not switch the production ANSI personality.
