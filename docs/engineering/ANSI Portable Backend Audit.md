# Portable ANSI/VT100 backend audit and region prototypes

Status: implementation preparation after portable ADM3A, 2026-10-16.
The production ANSI.RSX is unchanged. This is not a completed portable ANSI
provider or a published SCRN ABI extension.

## Existing commitments

The current bounded ANSI personality forwards CSI A/B/C/D, H/f, J/K, m, r,
s/u, ESC 7/8/D/E/M and exact CSI ?25h/l to the host after complete validation.
It buffers unfinished sequences, consumes unknown commands/OSC/DCS/queries,
and preserves ordinary input bytes. Parameter interpretation, rendition and
geometry currently follow the host. Its TE application qualification uses an
unchanged configuration requiring 25 rows, on 80x25 and 100x40 host screens.
See [the existing qualification](ANSI%20Provider%20Foundation%20Qualification.md).

The existing SCRN 1.0 interface supplies fixed 80x24 coordinates, normal/reverse
cells, suffix erasure and full-screen scrolling/line operations. It does not
supply arbitrary scrolling margins, erase-before-cursor, extended text styles,
or host geometry discovery. Simply changing ANSI's callable descriptor or
routing its output through SCRN would lose existing behavior. Raw host escape
strings must not be introduced into the portable personality as a shortcut.

A portable parser can implement movement, save/restore, erasure ranges and
parameter defaults in its own state. A backend must implement hardware-specific
region movement and rendition. Model 4 cannot physically reproduce every host
style or a 25th row; those limits must be explicit. The previous host-only TE
25-row result must not be cited as proof of a portable 24-row implementation.

## Executed region prototypes

Two standalone assembled routines accept A=0 scroll up / 1 scroll down,
B=top row, C=bottom row, E=20h/A0h blank fill. Bounds are fixed 80x24 for this
experiment. Invalid inputs return A=255 without screen/output mutation.
Valid calls return zero; other registers are scratch and the stack is balanced.

- `src/rsx/screen/region-prototype.mac`: Model 4 video RAM movement and fill;
  141 bytes, 17 relocation operands. It never changes BIOS cursor storage.
- `src/rsx/screen/host-region-prototype.mac`: ANSI-host region selection,
  scrolling, explicit blank painting and physical cursor/rendition restoration;
  277 bytes, 49 relocation operands. Host margins finish full-screen.

Both preserve rows outside the selected region, including a single-row region
where DECSTBM cannot be used. Host rendition is restored, including bold,
underline and reverse, rather than leaving a stale backend rendition cache.
These sizes include standalone dispatch, validation and transport helpers.
They are measurements, not promised incremental production costs: integrating
with the backend's existing helpers should remove duplication.

`python3 tools/test_screen_region_prototype.py` checks every legal Model 4
region, both directions/fills and two relocated addresses: 2,400 cases, guarded
video boundaries and invalid-input rejection.

`tools/test_host_region_prototype.py` uses the monitor-test Python environment
with pyte, the actual cpmsim BIOS transport and two relocated addresses. Its
48 cases include full, interior, two-row and single-row regions, both directions
and fills, unchanged surrounding rows, cursor/rendition restoration, full-screen
margin restoration and invalid inputs. Host test BIOS is currently selected
from `build/audit/release-090-z80pack`.

These are CPU/interpreter experiments, not native ZSM4, live application or
manager lifecycle qualification. No production builder/distribution selects the
prototypes. There is no permanent BIOS/BDOS change and no new published service
number or callable descriptor.

## Remaining integration work

1. Preserve SCRN 1.0's fixed 80x24 behavior for existing ADM3A/VT52 carriers;
   define a versioned extension for ANSI's additional backend requirements.
2. Resolve geometry explicitly, including the host provider's existing 25-row
   application case, without pretending Model 4 has more physical rows.
3. Add rendition support/capability reporting with an explicit hardware fallback
   for attributes unavailable on Model 4, and preserve reverse blank fills.
4. Convert ANSI's buffered final-command dispatch into typed backend operations,
   retaining cancellation/overflow/unknown-sequence behavior.
5. Qualify both actual backends, lifecycle/relocation, native assembler parity,
   live/ROM cpmsim, native Model 4, application and clean distribution paths.

The portable developer starter follows a stable common interface; it must not
present the legacy host template as a universal personality merely by changing
its capability word.

## Rendition interpreter experiment

`src/rsx/screen/rendition-prototype.mac` implements a portable interpreter for
up to sixteen 16-bit SGR parameters. It returns a nine-byte canonical record:
flags (bold, faint, italic, underline, blink, reverse, conceal, strike), then
foreground kind plus three color bytes, then background kind plus three bytes.
Kind zero is default, one is indexed and two is RGB. This is an experimental
representation, not yet an ABI commitment.

The prototype covers attribute enable/reset, normal/bright palettes, 256-color
indices, RGB colors and independent foreground/background defaults. Unknown
ordinary values are ignored without byte truncation. Malformed/incomplete
extended-color groups or too many parameters return 255 and leave the previous
committed rendition unchanged. Buffer pointers are per-call scratch; they are
not production BRSX runtime state. The production parser's full host-dependent
SGR behavior is not yet replaced or claimed covered by this subset.

`python3 tools/test_rendition_prototype.py` passes 1,164 cases at two relocated
addresses, including all palette indices, RGB extremes, combined attributes,
reset/default handling, oversized numeric values, incomplete groups and atomic
failure. Cost: 469 standalone bytes, 84 relocation operands. No backend or
permanent core code is changed. Backend attribute rendering/capability fallback
and the existing ANSI parser integration are still required.

## Geometry-neutral host motion experiment

`src/rsx/screen/host-motion-prototype.mac` accepts typed up/down/right/left
and absolute positioning with 16-bit numeric arguments. It emits controls in
the host endpoint, allowing the host to clamp positions to its actual geometry.
It does not assume 24 rows, probe for terminal responses, consume input or require
BDOS/BIOS geometry support. The portable personality would contain the command
parser; the backend contains its own hardware/transport encoding.

`tools/test_host_motion_prototype.py` passes 420 assembled-code cases at two
relocation addresses against independent 80x24, 80x25 and 100x40 pyte screens.
It checks zero/default values, edge clamping, full 16-bit values and invalid
operation rejection. Cost: 162 standalone bytes, 24 relocation operands.
This proves motion can preserve the host's existing geometry while Model 4
operations remain bounded by physical 80x24 hardware.

This suggests an additive typed control interface alongside the existing fixed
SCRN 1.0 cell interface, rather than changing its coordinates or shrinking ANSI's
host screen. Geometry-neutral host erasure, wrapping, margins and cursor
save/restore still need equivalent integration checks. There is no published
operation-number assignment, production descriptor change or completed portable
ANSI carrier in this increment. All prototype costs are unloadable candidate
costs, not permanent memory growth.


## Typed parser candidate checkpoint — 2026-10-16

The complete private candidate is `src/rsx/ansi-portable.mac` plus
`ansi-dispatch.inc`. Build it with `python3 tools/build_ansi.py
--portable-candidate`; output stays under `build/ansi-portable-candidate/`.
Normal builds still select the existing 460-byte host personality. A byte hash
check confirms rebuilding normal ANSI produces the identical production carrier.
The temporary separate parser source permits qualification before activation;
it is not intended as a second permanently maintained ANSI personality.

The candidate retains the existing bounded byte-state machine: 31-byte sequence
limit, CAN/SUB reset, restart on ESC, overflow discard through final byte, and
suppression of unknown/private commands, queries, OSC and DCS. Validated sequences
now dispatch to typed backend operations instead of replaying host escape bytes:
movement/position, J/K erasure, SGR, margins, CSI s/u and ESC 7/8 save/restore,
ESC D/E/M index/next-line/reverse-index, and exact ?25h/l visibility. Printable
ASCII uses styled glyph output. CR/LF/backspace use typed movement/index so the
Model 4 honors the selected scroll region; other ordinary bytes retain the raw
platform path. Physical cursor presentation remains delegated to the backend,
with visibility gated by the personality.

Numeric lists are bounded to sixteen words and accumulated with saturation at
65535, never wrapping large values into a different active command. Missing
parameters are zero and receive backend defaults. Excess parameters for motion,
position and erasure cause that command to be ignored; unsupported erase modes
are ignored. This is an explicit bounded portable interpretation, not a promise
to duplicate every endpoint's handling of malformed or irrelevant parameters.
The portable SGR set is the canonical flags, normal/bright palette, indexed/RGB
colors and resets already qualified by the rendition interpreter. Unknown SGR
values are ignored; malformed extended-color groups fail atomically. Broader
host-specific SGR behavior is not silently claimed portable and remains part of
the compatibility/application review before activation.

The SGR implementation is now shared source (`screen/rendition.inc`) used by
both the candidate and the standalone experiment. Its scratch input pointer is
cleared on success/failure; the dispatcher likewise clears its buffer pointer
before returning. Saved cursor restoration also restores the interpreter's
canonical record, so later incremental SGR changes start from the restored
state. Before a first save, restore selects home/default rendition. Later saves
replace the reusable slot. Margins remain backend state.

Candidate payload: 1466 bytes, 207 static relocation operands, 1536-byte loaded
allocation including callable descriptor. Local relative branches brought it
below the existing 232-entry carrier limit; there is no carrier-format growth.
The candidate uses a provisional MCON 1.2 descriptor with the manager-owned word
at +12. The current manager deliberately rejects that descriptor. Actual-manager
tests on both platform BIOS profiles prove rejection even with a backend loaded,
unchanged live binding/registry/TPA/generation, and clean unload to 53K.

`tools/test_ansi_portable.py` passes 340 streams through actual assembled
front/back code, with frontend/backend relocation varied independently. It checks
rendering, canonical colors, malformed atomic SGR, save/repeated restore,
visibility, movement/defaults, margins, parser cancellation/overflow, guards and
cleared scratch pointers. Host cases also exercise 80x25 and 100x40 last-row/right-
edge output and saved positions. The shared SGR experiment passes 1164 cases.
`tools/test_monitor_backend_native.py --portable-ansi` proves native ZSM4/LINK
byte parity for the candidate as well as the current backends/manager helpers.
Existing production ANSI foundation and lifecycle tests still pass unchanged.

This checkpoint is CPU/terminal-model and native assembly evidence, not installed
portable ANSI qualification. Remaining work: define and implement admission of
only sufficiently capable backends, activate the converted personality, qualify
partial-parser/saved-rendition compaction through the real manager, and rerun live
applications, RAM/ROM cpmsim, native Model 4 and clean distribution paths. No
permanent BIOS/BDOS bytes are added here and no distribution identity changes.


## Capability admission checkpoint

The provisional candidate contract is now admitted as MCON 1.2, requiring SCRN
1.1 (complete SCX control set). Current backends declare that revision; older
personalities remain compatible. The manager compares validated prospective
metadata before publication, with no callbacks during preparation. See the
Screen Backend ABI for the temporary two-byte context extension and exact
version rules. Actual-manager tests now execute the complete parser on both
platform profiles, including partial-sequence and saved-rendition compaction.
The old negative candidate test now deliberately downgrades the backend's
metadata to valid SCRN 1.0 and proves incompatible admission remains atomic.
A live cpmsim RAM candidate exercise passes with matching overlays and 53K
recovery (`build/ansi-development/live/cpmsim-u3ysk1k7`). Normal builds still use
the original ANSI personality; activation and remaining application/ROM/native
screen/distribution validation are the next checkpoint.
