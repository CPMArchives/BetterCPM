# Enhanced DUMP qualification

This is the historical Build 002 qualification and unchanged-byte extraction
record. Current exact-range behavior and revision 006 evidence are recorded in
[DUMP Range Qualification](DUMP%20Range%20Qualification.md).

DUMP 1.0 Build 002 implements the consolidated
[DUMP specification](DUMP%20Specification.md). The initial Build 001 record
remains historical; enhanced behavior is no longer described as merely proposed.

## Artifact and changes

- Native Z80/ZSM4 source: `src/utilities/dump.mac` and the five `dump*.inc`
  modules under `src/utilities/common/`.
- `DUMP.COM`: 14,154 bytes, SHA-256
  `1d1f260172e5d4cea26d32965b30f524a044a206aa659695f6c1f483f467e5c8`.
  This includes two bounded 4,064-byte page buffers and the private stack.
- No BIOS, BDOS, CCP or resident allocation changes. DUMP uses the existing
  DU lexer, exact filename validator and callable SCRN service lookup.
- The assembler expands shared source for both cross and native builds.
  Explicit reserved-byte fill in the native harness resolves assemblers'
  differing DS defaults; the final programs are byte-identical.
- The original DRI output loop remains separate under `/BARE`. The enhanced
  parser reconstructs its FCB so options may precede the operand.
- Raw prompt input uses unechoed direct console reads. Cooked input would echo
  through an unrelated personality cursor after typed screen rendering.

## Compiled-code checks — passed

`tools/test_dump_enhanced.py` executes the compiled program against a hostile
public BDOS fixture and independent screen-cell model. All 80 cases pass.
Coverage includes both exact row formats; option validation/precedence; shared
DU inheritance and restoration; empty files; numeric syntax and offsets beyond
64 KiB; backend capability/geometry rejection; different heights; forward and
backward paging; Go To correction/cancellation; prompt insertion and all four
WordStar controls; horizontally scrolled 95-character input; exact 32-byte
patterns; case, spaces and H/A choices; overlapping and record-crossing matches;
search retention/anchors; no-wrap/no-match results; cancellation; and initial,
replacement, streaming and search read failures with preserved state.

`tools/test_dump.py` passes 19 DRI/version cases. Its sealed `/BARE` output,
record consumption and row-boundary status checks are compared with the retained
DRI executable, including 64K wrap, final-record padding and the unconsumed
interruption character. The enhanced parser necessarily adds setup services;
service-list identity with DRI is not claimed. `/VER` remains standalone,
visually styled and free of file activity.

These fixture checks are machine-code behavior evidence, not physical-device
or live terminal certification. The fixtures reject write services and verify
stack-balanced direct return and caller DU restoration.

## Native assembly and live cpmsim — passed

`tools/build_native_dump.py` assembles with ZSM4 and links with LINK under an
isolated CP/M emulator. All 14,154 bytes match the cross-built candidate.

`tools/test_dump_live.py` checks real BDOS streaming display, version, empty and
missing input, and A0:DUMP invoked from A3. Record data and the immutable source
image remain unchanged and independent filesystem checking passes.

`tools/test_dump_view_live.py` runs the candidate with shipped ANSISCRN and ANSI
on a private copy of accepted V052 cpmsim media, baseline SHA-256
`6823e809d2e52ab978bd37646b9f201ff3a074fc910fdd0ec1df780030e8fae2`.
Independent pyte screens verify wide and compact rows, Page Down, Go To,
record-crossing Find, next/previous matches, ESC cancellation and direct CCP
return. Fixture data is read back independently and fsck passes. The test
runner bounds emulator shutdown rather than waiting indefinitely for SIGTERM.

The legacy SCRN descriptor reports an 80-by-24 typed screen. Host-managed SCX
geometry does not constitute host terminal size detection. The host endpoint
must support that viewport; tests do not claim automatic physical resize or
terminal-size discovery.

## Native Model 4

`tools/test_dump_model4.py` passes all ten captured stages on actual trs80gp:
wide rows, Ctrl-C Page Down, Go To with all four WordStar editing keys and
a visible software insertion cursor, a record-crossing match, next/previous
matches, physical CLEAR cancellation, compact rows and the following queued
command. The input file's complete directory entry (including attributes)
and all allocated data remain unchanged; independent fsck passes.

The private System Disk was reconstructed from the complete isolated BIOS 1.13
build used for MM CLEAR qualification. Its manifest files and both CONFIG
validation paths pass before injection. Its source image SHA-256 is
`fbd2af92fde647b5f70b882f0084e40371e0e15d4a0a3e0813ecaf6727f5ec80`.
The campaign runs this exact Build 002 artifact with matching M4SCRN and ADM3A.
A private STARTUP.SUB queues both viewer invocations and a following marker
program. The marker proves return through the CCP, without guessing a short
fixed delay between warm reconstruction and the next command.

Earlier harness attempts used a development image without a suitable startup
profile, a pre-CLEAR-change image, or short fixed inter-command waits. Those
attempts are not reported as passing native campaigns. A bounded exit trace
confirmed stack restoration and entry to BIOS warm boot; capture during that
reconstruction can show a blank screen. The completed scripted campaign uses
normal native-validation timeouts and checks the subsequent command instead.
No production behavior was changed to make these harness attempts pass.

Native evidence is guest keyboard-matrix and screen evidence, not a claim to
have synthesized macOS Fn/Home events or tested a physical Model 4.

## Utilities media — passed, provisional

`tools/build_utilities_disk.py` packages this exact candidate into both daily
Utilities images. Complete file readback and filesystem checks pass, as does
native DMK/raw round-trip verification. XSUB and BATCHIO remain included.

This does not complete Utilities Disk release acceptance: remaining Utilities
selections/implementations are independent, and the System Disk/core acceptance
record is not extended to unrelated artifacts.

## Reproduction

```text
python3 tools/build_dump.py
python3 tools/test_dump.py
python3 tools/test_dump_enhanced.py
python3 tools/build_native_dump.py
python3 tools/test_dump_live.py --baseline <accepted-cpmsim-directory>
python3 tools/test_dump_view_live.py --baseline <accepted-cpmsim-directory> --output <fresh-directory>
python3 tools/test_dump_model4.py --image <matching-System-Disk.dmk> --output <fresh-directory>
python3 tools/build_utilities_disk.py
```

The live viewer runner requires the pinned terminal-test dependencies in
`tools/requirements-monitor-tests.txt`. Native execution requires the current
CLEAR/ESC BIOS, matching shipped M4SCRN and the normal startup SUBMIT profile.
No daily user disk or running daily emulator is used as test media.

## Retained evidence

The local CP/M project workspace retains
`validation-evidence/BetterCPM-DUMP-Build002-evidence.tar.gz`, SHA-256
`20936bf4e9b1b97fb62fba87416286fab629b23777e0933a063833ce13e28305`. Its manifest verifies every retained member, including production
source, exact cross/native binaries, compiled-code reports, both live platform
captures, input-image identity and provisional Utilities media reports.
The archive was reopened and every member hash verified.

## Shared input source extraction, 2026-10-22

The legacy basic editor now resides in `src/utilities/common/ui/input.inc`, with
caller-owned state and bound keyboard, redraw, cancellation and message hooks.
DUMP retains its renderer and Find/Go To validation. The native builder and
cross builder both expand the shared source through `build_dump.expanded_source`.

The cross-built result remains 14,154 bytes with SHA-256
`1d1f260172e5d4cea26d32965b30f524a044a206aa659695f6c1f483f467e5c8`, identical
to the previously qualified Build 002. Native ZSM4/LINK comparison passed for
all 14,154 bytes. All 80 enhanced compiled cases and 19 DRI/version cases were
rerun and passed. There is no utility-version increment because the executable
bytes and behavior are unchanged.

Native screen campaigns were not rerun for this source-only extraction: their
previous evidence applies to the identical program bytes. These results do not
qualify future standard-profile features such as word commands, defaults,
Ctrl-C field cancellation or DEL aliases. The extraction is the first increment
of the [Shared Input and UI Specification](Shared%20Input%20and%20UI%20Specification.md).
