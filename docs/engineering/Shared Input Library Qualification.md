# Shared Input Library Qualification

**2026-10-22 — standard event and controller profiles**

## Scope

Adds the standard profile to the shared basic editor with conditional assembly,
so insertion/deletion logic remains common rather than copied. Adds optional
Ctrl-A/F/Y, separate empty/default policies, read-only validation and immediate
choices. Source and build usage are documented in the
[developer guide](../programmers/Shared%20Input%20Library.md).

The event engine reads no console, draws no screen and allocates no storage.
Controllers use caller-owned state and bound input/render/validation callbacks.
Choice-only code is independent of the editor. No production utility switches
to these profiles in this increment. The compatibility selection emits the
same previously qualified DUMP Build 002 and CONFIG Build 014 bytes.

## Compiled-code checks

`tools/test_shared_ui.py` assembles six selections and executes 68 cases in the
Z80 fixture. Callbacks deliberately destroy general registers. Checks cover:

- initialization, prefill validation, insertion, deletion, movement boundaries,
  full 255-byte capacity and adjacent-buffer guards;
- Ctrl-C/ESC cancellation, DEL, printable case/spaces and ignored controls;
- optional word movement including spaces, punctuation, end clamps and clear;
- all four empty policies, separate defaults, semantic validation of defaults,
  default preservation and explicit accepted-empty versus cancelled results;
- invalid-input retention and correction, limit messages, unknown keys and a
  recognized boundary key processed exactly once while dismissing a message;
- immediate case-insensitive choices, No versus Cancel, invalid choices,
  default/typed validation, preserved typeahead and bad configurations;
- caller application-state and stack preservation, combined controllers and
  actual absence of optional editor/word symbols in smaller emitted builds.

These are compiled logical/UI-protocol checks, not native screen evidence.
Renderers must still be qualified through a real consumer.

## Native assembly and measured cost

`tools/build_native_shared_ui.py` assembles and links every selection with ZSM4
and DRI LINK in isolated CP/M disks. All six native images match their cross
fixtures byte for byte. Fixtures are not shipped utilities; their entry returns
to CP/M and their controlled CPU callbacks are not terminal implementations.

| Selection | Library code bytes | Caller state, excluding data buffers |
| --- | ---: | --- |
| Event editor | 263 | 6 bytes |
| Event editor and word commands | 377 | 6 bytes |
| Basic editor and text controller | 448 | 10 bytes |
| Editor, words and text controller | 562 | 10 bytes |
| Choice-only controller | 185 | 5 bytes |
| Text, words and choices | 699 | 15 bytes |

Counts exclude renderers, callbacks, constant messages, input/default buffers
and application data. State is supplied by the caller, not emitted by the
library. The word module adds 114 code bytes including dispatch, and no state.
The combined selection shares the 48-byte validation/completion block once.
The choice fixture contains neither an edit buffer nor an editor entry point;
basic selections contain no word-command code.

## Existing-consumer preservation

Cross and native builds retain:

| Utility | Bytes | SHA-256 |
| --- | ---: | --- |
| DUMP 1.0 Build 002 | 14,154 | `1d1f260172e5d4cea26d32965b30f524a044a206aa659695f6c1f483f467e5c8` |
| CONFIG 1.0 Build 014, dual profile | 15,552 | `2167646cfe1506405cd1834deaf26d3bc4712dc8a5911d04c26e9040fbfad9e4` |

Native ZSM4/LINK parity is checked for both consumers. The 80 enhanced DUMP and
19 DRI/version regressions, plus 24 focused CONFIG input cases, are rerun for
the compatibility selection. Prior real-platform evidence remains attached to
these identical executable bytes; native screen campaigns are not rerun merely
for conditional source organization.

## Remaining work and evidence

No undo, overwrite, raw terminal-sequence adapter, general standard prompt
renderer or automatic driver loading is implemented. New clients must render
readable labels/defaults/choices and use output that cannot swallow editing
keys. Existing qualified utility contracts are not silently expanded.

Generated evidence is under `build/shared-ui/`: sources, cross/native fixtures,
listings, `results.json`, `native-results.json` and `NATIVE-UI-BUILD.LOG`. Reports
identify all fixture hashes, code sizes and their scope. This does not constitute
a new System Disk or Utilities Disk acceptance run.


## Bounded choice formatter follow-up

`format.inc` adds a 148-byte transport-independent formatter for a validated
choice controller. Compiled checks cover empty and long labels, case-normalized
choices, optional defaults, exact and insufficient widths, invalid label bytes,
arithmetic overflow, unchanged output on failure, guard bytes, stack balance
and unchanged controller state. Run `tools/test_shared_ui_format.py` for the
current case count. This is formatting evidence only; native assembler parity,
real screen integration, standard text/default rendering and choice-error
layout are not claimed by this increment. Existing DUMP/CONFIG consumers do not
include this module and retain their qualified rendering paths.


## Shared screen renderer and DUMP Build 003

`screen.inc` extracts the screen field renderer behind caller-owned position,
plain-character and caret hooks. DUMP measures prompt labels and uses this
module instead of its private renderer. Its compatibility editing/validation
contract remains unchanged. Scrolling compares cursor minus start, avoiding
byte overflow with 255-byte fields. Invalid geometry fails before output.

- 252 compiled screen cases pass: 40/80/255 columns, one-cell fields, invalid
  geometry, empty/short/full 255-byte input, cursor/start combinations, exact
  cell contents, caret positioning, stack and input/state preservation.
- All 80 enhanced DUMP and 19 reference/version regressions pass.
- Native ZSM4/LINK emits the same 14,177-byte DUMP Build 003 as the cross build.
  SHA-256: `f36d1cdf49aa8d6099efe53e102e89b8a8d82401c27bef3ab45b0cb77f56b803`.
  This is 23 bytes larger than Build 002; no resident code or allocation changes.
- Real cpmsim with shipped ANSISCRN/ANSI passes both layouts, paging, Go To,
  forward/backward Find, ESC cancellation and command return. Independent pyte
  screen captures and filesystem checks are retained.
- Real trs80gp Model 4 with shipped M4SCRN/ADM3A passes wide/compact page cells,
  Ctrl-C Page Down, Go To with all four basic WordStar edit keys, software caret,
  forward/backward Find, physical CLEAR cancellation and command return.
  Native screen captures, unchanged viewed-file allocations/attributes and an
  independent clean filesystem check are retained. Reference disks are unchanged.

Developer bindings are documented in the shared library guide. CONFIG retains
Build 014's qualified inline renderer and 64-byte stack margin. General standard
text/default layout and choice-error presentation remain future integration
work; these results do not claim those are implemented.
