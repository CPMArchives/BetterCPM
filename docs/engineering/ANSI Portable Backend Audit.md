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
