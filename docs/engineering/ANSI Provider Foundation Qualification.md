# ANSI/VT100 host provider foundation

## Scope

ANSI.RSX is the bounded cpmsim host personality for the third 1.0 monitor
target. This development stage is not included on distribution disks or loaded
at startup. It forwards supported ANSI controls to a compatible host terminal;
it does not claim full VT100 or xterm emulation. Host geometry and wrapping
apply, rather than the VT52 provider's fixed 80 by 24 logical screen.

Supported output in this stage:

- Printable text and ordinary console controls pass through. DEL is ignored.
- CSI A/B/C/D, H/f: relative and absolute cursor movement.
- CSI J/K: screen and line erasure.
- CSI m: host text attributes, including reverse and normal video.
- CSI r: host scrolling region; CSI s/u and ESC 7/8: save/restore cursor.
- ESC D/E/M: index, next line and reverse index.
- CSI ?25h/?25l: show/hide cursor.

CSI parameters accept decimal digits and semicolons. Omitted parameters and
parameter interpretation follow the host terminal. A leading question mark
is accepted only for the exact cursor-visibility forms above. Unknown commands,
other private modes and terminal queries are consumed without forwarding.
There are no synthetic identification or cursor-position replies in this stage.
OSC and DCS strings are discarded until BEL or ST. Eight-bit control forms,
character-set selection, keypad modes and VT52-mode switching are outside the
supported subset. Raw input/status preserve host keyboard bytes; this stage
does not translate host arrow sequences or provide abstract key events.

## Parser and lifecycle contract

Output sequences remain private until a supported final byte arrives. The
32-byte buffer accepts sequences of at most 31 bytes; longer or malformed CSI
sequences are discarded through their final byte. ESC restarts an unfinished
ordinary sequence. CAN and SUB cancel pending state, including strings. Parser
reset discards pending bytes without screen output. Explicit clear resets the
parser and emits CSI 2J plus CSI H. It does not reset host attributes or margins.
Applications must restore changed attributes, margins and cursor visibility.

This ensures warm-boot parser reset cannot leave the host awaiting the remainder
of a forwarded escape sequence. No callback calls BDOS, allocates memory, or
performs disk I/O. All buffered state is retained in the module allocation;
relocation uses static operand relocation rather than runtime buffer pointers.

## Build and qualification

`tools/build_ansi.py` emits development ANSI.RSX 0.1, ANSITST.COM and listings
under `build/ansi-development`. The provider exposes MCON 1.0 with host backend
bit 0002h and STATEFUL reconstruction. Current payload: 460 bytes and 83 static
relocations, with a 512-byte runtime allocation including the service descriptor.
No permanent BIOS or BDOS growth is required.

`tools/test_ansi_foundation.py --bios <host-build>` executes the assembled
provider at 6000h and 8101h using the actual host BIOS. It checks supported
sequences, cancellation/reset, buffer boundaries and long overflow, suppressed
queries and strings, unchanged input/status, and independent pyte rendering of
positioning, reverse video and erasure. Dependencies are in
`tools/requirements-monitor-tests.txt`.

ANSITST is an initial interactive positioning/attribute/erase/reset exercise.
Actual manager relocation and protected-ROM lifecycle now pass. Application
qualification, expanded utility coverage and release integration remain next
stages. No historical terminal compatibility beyond this subset is
implied by the development module.

## Live qualification

`tools/test_ansi_lifecycle.py --bios <host-build>` exercises the actual RSX
manager: install HELLO then ANSI, begin CSI 12;, unload HELLO to move ANSI,
verify all pending bytes and counters survived, complete the sequence, reset
another partial sequence, resolve MCON through function 182, and unload ANSI.
The public binding returns to the basic monitor and TPA returns to 53K.

`tools/qualify_ansi_cpmsim.py --diskdefs <host-build>/diskdefs` copies the
distribution to private media and runs the same load/movement ordering with
ANSITST's two interactive phases. An independent pyte screen decodes real
cpmsim output and checks positioning, reverse-video attributes and line erasure.
Evidence: `build/ansi-development/live/cpmsim-872ex1m9/transcript.bin`.

Adding `--rom-build <host-build>` builds and proves the guarded simulator and
runs the campaign against copied ROM media. The CPU-write, DMA-write, guest
protection-change and reset guard tests pass, with DF00h through FFFFh protected.
ANSI loads, moves, renders both utility phases and unloads without a ROM-write
violation. Evidence: `build/ansi-development/live/cpmsim-ppwgk32r/transcript.bin`.

These campaigns qualify ordinary and protected-ROM cpmsim behavior and screen
rendering through the independent terminal model. They do not certify every
macOS/Linux terminal configuration or a separate Model 4 ROM target. The local
WordStar collection currently contains VT52 and Hazeltine installations, so
application qualification must use a separately configured ANSI/VT100 program.
No existing application binary has been silently repatched.
