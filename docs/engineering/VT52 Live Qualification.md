# VT52 live and lifecycle qualification

**Historical ANSI-adapter evidence.** The native VT52 correction supersedes
these output-format and host-rendering claims. See [current correction and
remaining gates](VT52%20Native%20Correction%20Qualification.md). Retained test
results below describe the earlier artifact, not the corrected native carrier.

## Changes uncovered by qualification

Direct addressing now commits its row only when the column completes the
sequence. Previously a partial row changed internal tracking before ANSI output
moved the real cursor. Reset now preserves the committed cursor.

Boundary LF and reverse-LF use a temporary ANSI scrolling area for rows 1..24,
then restore the host's full margins and explicitly restore the tracked cursor.
This prevents a taller host window from scrolling at its own bottom rather than
VT52 row 23. The provider remains 80x24 logically; the host needs at least that
size and normal ANSI origin/LF modes. Run CLS after manually loading VT52 to
establish cursor coherence; load has no terminal-position query or rendering
callback. Existing custom host margins are not preserved across a scroll.

Payload is 653 bytes, 116 static relocations, with a 768-byte allocation including
the runtime descriptor. Permanent BIOS size and unloaded 53K TPA are unchanged.

## Independent rendering

Install the isolated test dependency from tools/requirements-monitor-tests.txt
and run tools/test_vt52_rendering.py, passing --bios for the actual cpmsim BIOS
build if necessary. pyte 0.8.2 renders the assembled provider's real ANSI output;
it is not used by production code.

Both 80x24 and 100x40 screens pass margin replacement, pending-address reset,
bottom LF versus clamped cursor-down, top reverse-LF, erasure, cursor positions
and restored full margins. Provider screen/control, reply-ring and utility
checks remain in tools/test_vt52_foundation.py. Unknown-final sweeps establish
bounded recovery and no spurious reply, not original-VT52 historical behavior.

## Production lifecycle

Tools/test_vt52_lifecycle.py loads the actual carrier through production RSX
preparation/commit. Removing an earlier HELLO allocation moves VT52 upward while
preserving a partial cursor address, its pending row and an unread reply suffix.
The moved entry completes the address and returns the remaining reply bytes.
Function 182 resolves the new entry. Final unload restores the basic monitor,
an empty RSX profile and 53K TPA.

## Actual cpmsim execution

Tools/qualify_vt52_cpmsim.py uses fresh private media. It loads HELLO and VT52,
removes HELLO, then runs VT52TST through identification and all three interaction
phases. It unloads VT52, verifies the empty registry and 53K TPA, and exits with
BYE. The campaign passes. --diskdefs selects the matching distribution disk
format definition; originals are never modified. Transcripts remain under
build/vt52-development/live.

## Original application

Tools/qualify_vt52_wordstar.py extracts the unchanged WS.COM, WSMSGS.OVR and
WSOVLY1.OVR from the local WordStar_VT52.dsk reference (IBM-3740 filesystem),
installs them on a fresh private BetterCP/M disk, loads VT52, clears the screen,
and opens a disposable VT52TEST.TXT document. It types VT52 EDIT CHECK, saves
and exits with WordStar's control-K/control-X command, then verifies the saved
file contains the marker. Provider unload and BYE also pass.

The qualified binary hashes are:

```
WS.COM       65761d8aba0991e22eaed9b2692c3ff7862b5e0310d4a6aa44302c9b5b20747e
WSMSGS.OVR   e1792b75e3851e631017b7760c36e457a81627a3723aed341b2e9154a564d63d
WSOVLY1.OVR  4af3480aa62514e33045b55dacc97051867dc7320f2b4549d4da2a4a74bc6d2a
```

Binary hashes and the complete transcript are recorded in each fresh run
under build/vt52-development/wordstar. No WordStar binary is redistributed.
This qualifies the tested open/edit/save path, not every WordStar feature or
other software installed for VT52.

## Remaining scope

Graphics and alternate/auxiliary keypad support are optional in the accepted
1.0 contract; they are currently harmless no-ops. Hold-screen and copier are
unsupported, and identification remains ESC / K. Abstract arrow/keypad events
are a backend concern: the provider does not invent them from arbitrary host
bytes. Unresolved historical parser cases remain research-only with bounded
recovery. Release integration now supplies module version 1.0 and VT52TST 1.0 Build 001.
Both files are included on the cpmsim disk; startup selection remains unchanged.
Protected-ROM execution passed as recorded below.

## Protected-ROM cpmsim qualification

The same live VT52 campaign also passed with the current integrated ROM image
and the qualification simulator enforcing write protection from DF00h through
FFFFh. The campaign loads HELLO then VT52, unloads HELLO to move the retained
provider, exercises identification and all three VT52TST phases, unloads VT52,
and confirms an empty registry and 53K TPA. No ROM-write violation occurred.

Before the campaign, the simulator guard passed its execution, CPU-write,
guest-unlock, boundary-change, DMA-write, reset-protection, and ordinary-mode
checks. This qualifies the cpmsim ROM backend; it does not qualify a separate
Model 4 ROM configuration.

Reproduce using `tools/qualify_vt52_cpmsim.py --rom-build <platform-build>
--diskdefs <platform-build>/diskdefs`. The tool builds a private guarded
simulator, copies the ROM media, and removes only development test fixtures
from that disposable copy to make directory space. Original media are untouched.
The source checkout for the simulator can be selected with `--z80pack-source`.

Evidence: `build/vt52-development/live/cpmsim-oetl2jp2/transcript.bin`.
The release-identity campaign also passed against fresh distribution media,
including `/VER` before loading a monitor and the protected-ROM lifecycle.
The cpmsim system disk contains 24 files with 174K free; ED.COM remains planned.
Automatic startup selection remains separate work.
