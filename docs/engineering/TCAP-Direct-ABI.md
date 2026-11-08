# TCAP 2.0 direct-operation ABI

Engineering integration candidate qualified 8 November 2026, **subsequently
selected for BetterCP/M 1.1 by explicit maintainer release assignment**.
Final delivered-media acceptance remains separate from this contract's
engineering qualification. TYPE, TED and HELP migrations remain deferred.
This contract supersedes the abandoned, unreleased
[TCAP 1.0 template candidate](TCAP-Template-ABI-Historical.md). A 2.0 provider
does **not** advertise the incompatible 1.0 service. See the
[1.1 scope and acceptance contract](../releases/1.1-SCOPE-AND-ACCEPTANCE.md).

## Display ownership and lifetime

A personality interprets its application's protocol; a renderer implements the
display effects on its platform. The integrated build links both, together with
the portable entry point and facts, into one ordinary unloadable STATEFUL RSX.
They remain distinct source components. The normal workflow is:

`RSX LOAD ADM3A` → run an ADM3A application → `RSX UNLOAD ADM3A` → select another personality.

There is no separate screen backend dependency on this path. Existing SCRN/SCX
modules remain optional for applications explicitly using their broader API.
Neither a utility migration nor removal of SCRN/SCX is implied.

The selected module owns its display mode, parser state and capability facts.
The application owns its helper, discovery records and any cached pointers.
There is no permanent TCAP allocation, global validity counter, session object,
owner registry, transaction worker or recovery engine. Complete unload must
restore the exact prior TPA boundary and maximum COM capacity.

## Advertisement and admission

The public service ID is `TCAP`, major 2, minor 0, advertisement capabilities
zero. Its entry uses A as the operation selector. The same module also advertises
native MCON 1.0 for its platform. Existing MCON selectors 0 through 5 retain their
meanings; an unsupported MCON selector returns 255.

Before calling the TCAP entry, the application helper:

1. Resolves TCAP 2.0 and the selected MCON through ordinary Function 182.
2. Requires the two results to have the **same provider index** in that layout.
   A standalone or foreign-owner TCAP query must not be executed.
3. Checks console routing. CRT is eligible; TTY is eligible only for the cpmsim
   native host MCON (platform capability 2). BAT and discarded output are refused.
4. Queries the same-owner entry and verifies `TC`, record version 2 and length 8.
   This helper deliberately requires the exact 2.0 header; incompatible facts fail
   discovery with no cached entry left available.

The ordinary carrier validators remain responsible for executable entry bounds,
relocations, checked build binding and platform admission. Model II native MCON
1.0 requires platform bit 4 **and exact private checked-system binding**, as does
its native screen renderer. A public binding or a foreign private binding does
not grant access to the Model II video overlay. Generic TCAP admission neither
executes a query nor substitutes for these checks.

The loader's successful admission does not imply that a utility has admitted the
current console route. The client checks the route again before each operation.

## Eight-byte immutable facts

| Offset | Bytes | Meaning |
| --- | --- | --- |
| 0 | 2 | ASCII `TC` |
| 2 | 1 | Record version: 2 |
| 3 | 1 | Record length: 8 |
| 4 | 1 | Usable rows; zero means unknown |
| 5 | 1 | Usable columns; zero means unknown |
| 6 | 1 | Operations: bit 0 clear, bit 1 absolute position, bit 2 erase line, bit 3 strong emphasis |
| 7 | 1 | Strong rendition: 0 plain, 1 bold, 2 reverse video |

Reserved operation bits are zero in 2.0. Unknown geometry is represented by both
dimension bytes zero. Dimensions describe the provider's usable logical viewport;
they do not imply terminal-size probing. All three current native and host
personalities declare a fixed 24-row, 80-column viewport. ADM3A and ANSI select
reverse-video strong emphasis; VT52 provides readable plain text.
The cpmsim host qualification covers an ANSI host endpoint; it is not physical
terminal or resize-negotiation qualification.

Facts are read-only module storage. A query returns A=0 and HL pointing to them;
BC and DE are preserved. The provider stores no caller pointer.

## Operations

| A | Operation | Inputs and effects |
| --- | --- | --- |
| 0 | Query | Return the facts pointer in HL; no display, parser or rendition change |
| 1 | Clear | Clear the viewport using current rendition, position at 0,0 and discard an incomplete personality sequence |
| 2 | Position | B=row, C=column, zero based; reject out-of-viewport coordinates before display changes |
| 3 | Erase line | Fill from the current cursor through the last column, using current rendition; preserve cursor position |
| 4 | Strong begin | Select the advertised strong rendition |
| 5 | Strong end | Select readable normal rendition |
| 6 | Initialize | Select normal rendition and discard an incomplete personality sequence |
| 7 | Deinitialize | Select normal rendition and discard an incomplete personality sequence |

Text goes through ordinary BIOS/BDOS console output and therefore the selected
personality. The caller does not format protocol templates and feed them back
through the same personality parser. Operation arguments are typed and bounded.
An operation does not read a caller-supplied string, buffer or executable pointer.

Status 0 means success, 2 means a defined operation is unsupported, 3 means invalid
arguments, and 255 means unknown selector. The application helper uses status 1
for unavailable/refused discovery or route; it clears its cached entry on failed
discovery. Unsupported or invalid operations must leave the display and parser
unchanged. Except for query's BC/DE preservation, AF, BC, DE and HL may be changed;
IX and IY are not used. Flags have no additional public meaning.

Initialization is a normal baseline, not a display snapshot. Strong begin/end are
not nested and do not restore arbitrary prior application attributes. An editor
must still own its saved state and exit policy. Calling clear or moving beyond
unknown dimensions is not a substitute for acquiring valid geometry. A consumer
with unknown geometry must use its explicit plain-text or unpaged policy.

## Client use and invalidation

[tcap2.inc](../../src/utilities/common/tcap2.inc) supplies `T2_OPEN` and `T2_EMIT`.
OPEN returns status and the facts pointer. EMIT accepts the operation and its
typed arguments. Text remains on the application's normal console path.

Both cached code and facts pointers are valid only in the layout where OPEN
succeeded. **Rediscover after every RSX load, unload, replacement or other layout
mutation.** Do not retain either pointer across warm reconstruction. Warm return
ends the transient; the next invocation opens again. This is an explicit lifetime
rule, not a hidden promise that a raw pointer survives compaction.

Model II maps video only while executing a bounded renderer operation. It saves
interrupt state, switches to a guarded 20-byte private stack below the overlay, maps the
video bank, renders, restores bank/stack/interrupt state and clears the saved SP.
Keyboard input/status bypass that mapped interval. The private stack is included
in the module's charged allocation.

## Full-path accounting and qualification

Charge the complete required personality, renderer, facts, runtime callable
records, cache footer and page rounding, plus the application helper and shared
BIOS display state. Disclose call-site and stack allowances. Only generic RSX
machinery is excluded. Do not describe this as incremental capability-layer cost.

The [explicit inline cache permission](RSX-Inline-Cache-Footer.md) keeps the footer
inside the charged allocation. ADM3A allocates 768 resident bytes on Model 4 and
Model II, and 1,024 on cpmsim. VT52 allocates 768 bytes on Model 4 and 1,024 on
cpmsim and Model II. ANSI allocates 1,536 resident bytes on all three platforms.
The helper is 159 bytes. With 32-byte call-site and 32-byte
stack allowances, the complete counted paths are:

| Platform | ADM3A | VT52 | ANSI |
| --- | ---: | ---: | ---: |
| cpmsim | 1,247 bytes | 1,247 bytes | 1,759 bytes |
| Model 4 | 994 bytes | 994 bytes | 1,762 bytes |
| Model II | 994 bytes | 1,250 bytes | 1,762 bytes |

The accepted ceilings are 1,280 bytes for ADM3A/VT52 and 1,792 bytes for ANSI,
counting the full path and excluding only general RSX machinery. ANSI retains
its recognized ASCII command set and full host rendition/color groups. The
combined candidate uses a fixed 80x24 viewport and seven-bit terminal protocol;
see the [coverage boundaries](TCAP-Integrated-Display-Redesign.md#protocol-coverage-and-boundaries).

Three existing BIOS cursor bytes are charged on the native platforms. The native
renderers perform their own display work; no extra rendering code is hidden in
the BIOS. The generic first-RSX machinery is
an additional 1,024 bytes, explicitly excluded from those display-path totals.
There is no permanent display reservation in the unloaded system.

VT52 advertises operation mask 7 and strong rendition 0. Defined strong begin/end
calls return status 2 without changing the display. Its parser implements seven-bit
VT52, clamps out-of-range encoded positions, and holds one complete identification
reply plus a previously observed keyboard byte in a four-byte queue. A new reply
is refused as a whole when it cannot fit; existing input order is preserved.
This replaces the development personality's larger 16-byte reply ring and
nonstandard high-bit glyph extension. Native typed cursor presentation remains
independent of portable strong emphasis.

Build and qualification are separate gates. Source/install/cold/warm/load/run/
unload results must identify their exact module, consumer and emulator hashes.
Passing the historical 1.x portable-stack campaign does not qualify a 2.0 module.
See the [integrated design](TCAP-Integrated-Display-Redesign.md) for current scope.
