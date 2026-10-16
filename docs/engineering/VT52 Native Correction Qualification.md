# VT52 native wire correction and portability audit

Historical record: the portable MCON/SCRN implementation supersedes this native-wire
checkpoint. See [portable backend integration](VT52%20Portable%20Backend%20Integration.md)
for current architecture and qualification.

Status: 2026-10-16. Native wire correction implemented and focused-qualified.
The full portable-backend requirement remains open. This is not final release
or physical-terminal display qualification.

## Corrected behavior

The former provider decoded VT52 application output and emitted ANSI controls.
The corrected provider emits native VT52 output: ESC Y with encoded row/column,
ESC H / ESC J for clear/home, ESC J/K for erasure, LF for bottom scrolling,
and ESC I for reverse scrolling. It contains no ANSI renderer or direct video
memory references. Existing bounded parsing, complete-address buffering,
identification replies, queue ordering, reset and relocation behavior remain.

A native VT52-capable 80x24 endpoint is required. Loading this provider does not
make an ANSI-only host understand VT52. ANSI.RSX remains unchanged for ordinary
ANSI terminal use. No automatic host mode switching is attempted. Run CLS after
loading to establish a common cursor position.

The current carrier's provider version is 1.1; its MCON service remains 1.0.
VT52TST is utility Build 002. Its version query remains standalone.

## Measured cost

| Item | Former adapter | Native wire correction |
| --- | ---: | ---: |
| Payload | 653 bytes | 570 bytes |
| Static relocation slots | 116 | 102 |
| Runtime allocation including callable descriptor | 768 bytes | 768 bytes |

The payload saves 83 bytes; page rounding leaves allocation unchanged. Carrier
file size is 1,106 bytes. BIOS, BDOS, manager, descriptor layout and permanent
resident code are unchanged. The installed/uninstalled memory policy is the
existing RSX policy; live and CPU lifecycle tests restore 53K unloaded TPA.

Exact artifacts:

- VT52.RSX SHA-256: `0d992dc63362c9bc7dd7a7308bb53a5583d30d9b0ded73be18ed74ee4ca196d7`
- VT52TST.COM: 1,010 bytes; SHA-256 `cccda6061bc4c363df774481833ac11436b43cb5d709f1f0029fe22cfdc46f68`

## Focused evidence

- `tools/test_vt52_foundation.py --bios build/audit/release-090-z80pack`:
  49,920 relocated coordinate/control cases at two load addresses; native wire
  bytes, clipping, partial reset, clear, utility execution, raw input and unknown
  selector containment. Queue tests cover all 16 ring phases and 17 capacity
  boundaries, atomic reply overflow and reset/clear preservation.
- `tools/test_vt52_rendering.py --bios build/audit/release-090-z80pack`:
  an independent fixed 80x24 native wire model checks screen cells, right margin,
  scrolling in both directions, erasure, committed coordinates and interrupted
  addressing at two relocation bases. The model has no ANSI parser.
- `tools/test_vt52_lifecycle.py --bios build/audit/release-090-z80pack`:
  production manager install, relocation of an active parser and partial reply,
  continuation, service lookup, unload and 53K recovery.
- `tools/test_utility_versions.py`: 166 version/dispatch/purity checks pass.
- `tools/qualify_vt52_cpmsim.py` using a disposable copy of the retained
  `/private/tmp/dup-current-conformance/disks/drivea.dsk` fixture:
  load, movement after removing another RSX, identification, all three utility
  phases, native positioning/erasure wire checks, no ANSI CSI in the exercise,
  unload/53K and simulator shutdown pass. Transcript:
  `build/vt52-development/live/cpmsim-1qpu8s2y/transcript.bin`.
- `tools/qualify_vt52_wordstar.py` on another disposable copy of that fixture:
  unchanged VT52-configured WordStar opens, edits and saves a document, returns
  and permits unload. Captured application output contains native addressing
  and no ANSI CSI. Transcript and local reference hashes:
  `build/vt52-development/wordstar/run-gehp21zh/`.

The retained live disk fixture is not a newly rebuilt 0.90 release image. The
CPU tests use the 0.90 cpmsim BIOS audit artifact. These are focused functional
checks, not exact-artifact release distribution qualification. No original or
third-party disk image was modified. The first WordStar fixture attempt stopped
because an old VT52.RSX already existed; the harness now replaces named files
only on its disposable copy before testing.

## Remaining portable-backend boundary

The current private MCON ABI is explicitly platform-bound:

- capability bit 0 selects the Model 4 backend;
- capability bit 1 selects cpmsim;
- the manager rejects other combinations and mismatches;
- MONRAW supplies basic character I/O, cursor presentation, clear and reset;
  it does not expose portable positioning, erase or scrolling primitives.

Consequently, source portability is not yet carrier/backend universality. The
corrected VT52 carrier still uses bit 1 and is rejected on Model 4. Model 4's
MONRAW writes characters through its basic video console; it does not interpret
native VT52 sequences. ADM3A currently renders using Model 4-specific exported
cursor addresses and video memory, which cannot be copied into a universal
VT52 provider without violating the intended separation.

A common portable parser can operate on a native VT52 byte-stream endpoint, as
this correction demonstrates. Making the same carrier support a non-VT52 local
screen additionally requires backend screen operations or another explicit
backend adaptation boundary. Changing capability bits alone cannot provide it.
The current hook audit therefore does not justify claiming Model 4 support or
silently accepting this carrier on every platform.

Before closing the roadmap requirement:

1. Settle and qualify a portable backend-binding/screen-operation contract if
   non-native local screens are included. Audit any permanent code cost before
   changing BIOS/BDOS; preserve 53K unloaded TPA. Do not embed separate machine
   renderers in VT52.RSX or quietly restore ANSI translation.
2. Qualify actual display behavior on a native VT52-capable endpoint, including
   ordinary keyboard input and terminal-generated replies. The independent
   model and captured cpmsim stream do not prove a real terminal's behavior.
3. Rebuild and qualify the exact distribution artifacts, including ROM ownership
   and application/display evidence for every claimed backend.

Historical ANSI-adapter reports remain evidence for their original artifacts;
they do not close these gates. General TCAP and simultaneous monitor providers
remain outside this bounded correction.
