# Integrated unloadable display path

Engineering integration candidate, 8 November 2026, subsequently
**assigned to BetterCP/M 1.1** by explicit maintainer decision. Exact release-media
qualification remains outstanding. Utility migrations, further personalities
and HELP delivery remain deferred. This is the follow-up to the
[full Model 4 display comparison](TCAP-Model4-Display-Cost-Comparison.md).

## Budget and architecture

Count the complete required display path: personality, renderer, public TCAP
entry and facts, runtime callable records, cache footer, allocation rounding,
application helper, shared BIOS display state and disclosed call/stack allowances.
Exclude only the separate generic RSX machinery. The maintainer's ceilings are
**1,280 bytes for ADM3A and VT52**, and **1,792 bytes for ANSI**. An incremental
capability-layer measurement does not satisfy either ceiling.

Each selected personality and its platform renderer share one ordinary unloadable
STATEFUL RSX. The personality interprets its application's terminal protocol; the
renderer performs its effects. The source components remain separate. Native
renderers use the BIOS's existing three cursor bytes and implement their own
output, erasure and scrolling; they do not hide additional rendering code in the
BIOS. Model II includes a guarded 20-byte private stack and restores its video
bank, caller stack and interrupt state on return.

The workflow is `RSX LOAD ADM3A`, run an ADM3A application, `RSX UNLOAD ADM3A`, then
select VT52 or ANSI in the same way. These modules require no separate M4SCRN,
M2SCRN or ANSISCRN load. Existing broader SCRN/SCX modules remain available to
applications explicitly using those interfaces. This work does not migrate TED,
TYPE or HELP, or claim to replace every SCRN/SCX feature.

There is no new permanent display reservation. Generic RSX admission and exact
checked-system binding remain in force. Model II native MCON 1.0 additionally
requires its platform bit and exact private binding. The
[explicit inline cache permission](RSX-Inline-Cache-Footer.md) assigns ten footer
bytes inside the provider's charged allocation; it does not take padding from
unmodified providers. Full unload must restore the original exact TPA boundary
and maximum COM load, including retirement of general RSX machinery.

## Public portable calls

The implemented candidate advertises [TCAP 2.0](TCAP-Direct-ABI.md), with an
eight-byte immutable facts record and direct clear, position, erase, strong and
baseline operations. It does not advertise the incompatible unreleased 1.x
protocol-template interface. Text continues through ordinary BDOS/BIOS console
output and the selected MCON personality. No global owner registry, generation
allocation, transaction or recovery engine is introduced.

The 159-byte application helper requires the TCAP entry and selected MCON to have
the same provider index and checks console routing. Cached entries and facts
must be rediscovered after every layout mutation; they do not survive a warm
return. This explicit pointer lifetime replaces the abandoned resident validity
machinery. It is not a promise that stale pointers remain callable.

## Complete path sizes

| Platform | ADM3A | VT52 | ANSI |
| --- | ---: | ---: | ---: |
| cpmsim | 1,247 bytes | 1,247 bytes | 1,759 bytes |
| Model 4 | 994 bytes | 994 bytes | 1,762 bytes |
| Model II | 994 bytes | 1,250 bytes | 1,762 bytes |

ANSI allocates 1,536 resident bytes on each platform. Adding its 159-byte helper,
32-byte call-site allowance, 32-byte stack allowance and three native cursor
bytes gives 1,762 bytes on native hardware. cpmsim needs no shared BIOS display
state and totals 1,759. Both fit the maintainer's 1,792-byte limit. These are full
path budgets, not raw assembler payload sizes.

The generic first-RSX machinery is a separate 1,024 bytes. Thus loading ANSI alone
reduces available TPA by 2,560 bytes: 1,024 generic plus 1,536 display module bytes.
The transient helper and disclosed application allowances are counted above but
live within the application's remaining TPA. Complete unload returns all 2,560
loaded bytes; the unloaded system has zero additional display reservation.

## Protocol coverage and boundaries

All candidate profiles declare a fixed 80-column, 24-row usable viewport. This is
not detected physical host geometry. The host renderer keeps its cursor and
screen operations in that viewport, including on a larger endpoint. Arbitrary
physical host sizes and the historical eight-bit raw-BIOS bypass are outside
this candidate's seven-bit terminal protocol. Existing separate backend modules
remain available for explicit SCX clients needing their endpoint-managed behavior.

ADM3A retains its positioning, reverse, erasure, line operations, visibility and
ordinary byte behavior. VT52 supplies movement, addressing, erasure, reverse
index and ordered identification replies. Its four-byte queue holds one full
reply plus a previously observed keyboard byte and refuses a new whole reply
when it cannot fit; it does not discard existing input to admit a partial reply.
VT52 supplies readable plain text when portable strong emphasis is unsupported.

ANSI retains the existing recognized ASCII command set: relative and absolute
movement, all three line/display erase modes, margins, index/reverse index,
next line, cursor visibility, reusable cursor/rendition saves, delayed wrap,
bounded CSI handling, CAN/SUB cancellation and OSC/DCS quarantine. Native display
attributes are reverse and conceal. Host ANSI preserves bold/faint, italic,
underline, blink, reverse, conceal, strikeout, normal/bright indexed colors and
RGB groups through complete validated SGR packets. Rapid blink keeps the prior
ordinary-blink alias. Unsupported attributes remain readable on native screens.

The streaming parser keeps at most sixteen parameters and a 32-byte sequence.
Malformed extended-color groups are refused atomically. Numeric values saturate
for the bounded viewport rather than wrapping into a supported attribute. Native
horizontal tab now performs bounded tab movement; the old incidental raw-BIOS
control glyph is not an ANSI feature being preserved.

## Qualification and engineering package

The executable ANSI comparison runs the old personality/backend and the combined
module on the Z80 CPU core at two relocation addresses. It checks visible cells,
attributes, cursor movement, margins, reusable saves, malformed input, parser
isolation, public facts and operation results. The full native and host candidate
payload hashes match the modules used in the loader campaigns. The comparison
normalizes equivalent palette names and invisible foreground on plain spaces;
it also makes SCX's omitted-bottom endpoint default explicit for pyte, whose
installed implementation otherwise treats that case as a full margin reset.

Independent Model II tests execute the actual carrier and metadata validators,
check public/foreign binding and platform refusal, exercise caller stacks below
and inside the video overlay, preserve both interrupt states, and verify the
private stack guard and restoration of protected upper RAM.

Full-machine campaigns cover cold boot, legacy and portable applications, warm
returns, adding/removing a second RSX, repeated unload/reload, real SYSGEN
installation, installed cold boot and exact original maximum COM loads. Each
receipt identifies the actual modules and core. Passing an older 1.x campaign
does not qualify a new 2.0 module. The generated engineering package keeps the
matching system/cache workers and modules together; the archived candidate
receipt predates release assignment and does not establish acceptance of final
1.1 package bytes.

Builders and shared guest fixtures are `tools/build_integrated_display.py` and
`tools/integrated_display_qualification.py`. Full runners are
`tools/qualify_integrated_cpmsim.py` and `tools/qualify_tcap_trs80.py --integrated`.
`tools/package_integrated_tcap.py` accepts only passing receipts within their
per-personality ceilings. `tools/qualify_tcap_package_capacity.py` separately
checks ordinary packaged startup and actual maximum COM loads while each profile
is present. Generated media remain under `build/`; tracked evidence records the
qualification hashes and measured accounting.
