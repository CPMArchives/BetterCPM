# ANSI/VT100 host provider foundation

This records the historical host-only foundation. Production ANSI now uses the
portable parser/backend path; see [current qualification](ANSI%20Portable%20Backend%20Audit.md#production-activation-and-qualification).

## Scope

ANSI.RSX is the bounded cpmsim host personality for the third 1.0 monitor
target. The release integration includes it on the cpmsim distribution disk; it is not loaded
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

`tools/build_ansi.py` emits ANSI.RSX 1.0, ANSITST.COM and listings
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
qualification now passes for the TE VT100 editor as recorded below; expanded
utility coverage remains available for later qualification. No historical
terminal compatibility beyond this subset is
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
macOS/Linux terminal configuration or a separate Model 4 ROM target. The local WordStar collection contains VT52 and Hazeltine installations.
Application qualification instead uses the unchanged upstream TE VT100 build;
no existing application binary has been silently repatched.

Release integration supplies ANSITST 1.0 Build 001 with standalone `/VER`, normal complete-build generation and cpmsim-only distribution entries. Pure version and invalid-usage checks pass without monitor lookup. Core callback code and its 512-byte allocation are unchanged. Startup remains banner-only.

The fresh release disk boot-qualified with 26 files and 170K free. Release
ANSITST version reporting, screen rendering, live movement and unload passed
on ordinary cpmsim (`build/ansi-development/live/cpmsim-cq00c7lp`) and with
enforced ROM protection (`build/ansi-development/live/cpmsim-famg9syp`).

## Independent application qualification: TE

The upstream [TE editor](https://github.com/MiguelVis/te) provides a ready-built
VT100/WordStar-key adaptation. Its `te_ws100.c` uses BIOS console calls, decimal
CSI cursor addressing, CSI J/K erasure and SGR reverse/normal video.
The tested reference commit is `95d1d33be82513825bd7d455f0f5af06539a6b9f`.

Unmodified reference files, SHA-256:

```text
TE_WS100.COM  8e5d56d8a645c4e725992af4540573a7229d7aab8491d509b70c27538fd42d6f
TE_WS100.CF   22f3f316e84c66bd3d3a929b7076a12a1368501745f5e3400984c88e02f43841
```

`tools/qualify_ansi_te.py --reference <local-te-checkout> --diskdefs
<host-build>/diskdefs` stages the binary as TE.COM and its configuration as
TE.CF on copied media. It loads ANSI, clears the screen, opens ANSITEST.TXT,
inserts `ANSI EDIT CHECK`, selects Save and Exit from the editor's own menu,
and verifies the changed file by reading it back from the disk image. It then
unloads ANSI and confirms an empty registry and 53K TPA.

Independent pyte rendering of the actual application output checks the initial
filename header and document text on 80 by 25 and 100 by 40 host screens.
The unchanged upstream configuration requests 25 rows; this application campaign
therefore requires at least 80 columns by 25 rows.
Evidence: `build/ansi-development/te/run-qf7acbgv`, containing the transcript,
reference identities, saved document and decoded screen text.

This qualifies an ordinary cpmsim open/edit/save/exit workflow with this binary.
It does not claim all TE commands, every terminal implementation, or a
protected-ROM application run. Protected-ROM qualification above covers the
provider lifecycle and ANSITST. Neither the upstream binary nor configuration
is added to the BetterCP/M distribution or repository.
