# Developing monitor RSXs

BetterCP/M 1.0 uses a bounded monitor-provider interface to add terminal
personalities that the basic console does not implement. ADM-3A (Montezuma
Micro behavior on Model 4), VT52 and an ANSI/VT100-compatible subset are the
committed 1.0 providers, each
with a dedicated test utility. The native Model 4 ADM3A provider and ADMTST
are now implemented; VT52 and ANSI/VT100 remain separate implementation work.

The BIOS hooks, transactional detach/publication, descriptor validation,
prospective selection, duplicate-provider rejection and retained live-descriptor
reconciliation are installed. Valid MCON carriers now bind through normal RSX
transactions. Command-return reset and internal clear/home integration are installed.
Provider-specific qualification remains required. Native Model 4 ADM3A now
has the recorded implementation and qualification described below; that does
not qualify the other personalities or another hardware backend.

## Select a personality and a backend

A new terminal personality translates the escape sequences expected by the
application into operations on the running platform's console backend. It does
not make direct hardware access or unrelated machine-specific BIOS extensions
portable. Reuse the shared monitor interface for another personality; do not
invent a BDOS-only interceptor, which would miss direct BIOS console callers.

The current compatibility bits are 0001h for Model 4 and 0002h for cpmsim.
Advertise exactly the matching bit, with all other bits zero. These identify
backend compatibility, not a portable terminal-capability database. Adding a
new hardware backend requires an explicit contract extension; choosing another
terminal personality on an existing backend does not.

## Build the carrier

Use the existing BRSX-v2 builder, tools/build_rsx_module.py. Advertise one callable
service named MCON, version 1.0, with the entry offset measured from the payload
base and the matching capability word. The entry must lie inside executable
payload, at offset 8 or greater. Use STATEFUL reconstruction class.

Declare static relocation slots for address operands and runtime pointer slots
for mutable words that can hold internal allocation addresses. Both kinds must
be correctly repaired when the allocation moves. Keep parser state, queued
replies and terminal modes inside the provider allocation. Initial payload
bytes must already contain a valid empty parser and queue state: installation
cannot depend on a fallible callback after live movement starts.

The ordinary RSX BDOS-chain entry must pass unclaimed calls to the next link.
MCON is callable metadata; it does not allocate a numeric BDOS function.

## Implement the entry

A selects the operation and C carries an input/output character. HL is dispatch
scratch and has no preserved caller value at entry.

| A | Operation | Required behavior |
| ---: | --- | --- |
| 0 | Output C | Interpret the personality's ordinary/control/escape bytes |
| 1 | Status | Return 00h or FFh without consuming input |
| 2 | Blocking input | Return a character; the public BIOS applies its 7-bit mask |
| 3 | Cursor presentation | Preserve the existing private cursor query/draw contract |
| 4 | Internal clear/home | Clear, home and discard incomplete output sequences |
| 5 | Sequence reset | Discard incomplete parser continuation; retain display, position and modes |

Honor the BIOS register and stack contracts. Console delivery is sequential and
non-reentrant. Never call BDOS, load an overlay, allocate, modify the RSX profile
or recursively enter routed console services from a callback. Interrupt-driven
console calls are outside this interface.

BIOS API 1.7 provides MONCALL at BIOS+66, MONRAW at +69 and MONBASE at +72.
MONRAW bypasses the provider and executes the basic backend. Use it where a
basic operation is appropriate; do not route back through MONCALL. The renderer
may use generated backend symbols, but those are platform-specific implementation
details. Keep backend cursor/column state coherent so unloading leaves a usable
basic console. Only the BIOS and validated manager publication own the binding;
a provider must never patch ROM or install its own target.

## Loading and state

Only one MCON provider is allowed in the prospective profile. Switch personalities
by unloading the old provider, then loading the new one. Atomic replacement and
simultaneous monitors are outside 1.0. The existing profile limit still applies.
Unrelated RSX changes may move the monitor; declared pointers and persistent
state must survive those transactions. Unload must detach before storage is
released. Warm return resets unfinished output parsing without clearing the
screen or dropping ordinary keyboard input. Cold startup may load the provider
through STARTUP.SUB after the basic console is initialized.

Loaded provider and manager memory reduce TPA under the normal RSX policy.
Unloading all RSXs must restore the 53K core baseline. Report loaded allocation
separately from unloaded memory cost.

## Supply a dedicated test utility

Each personality needs a repeatable screen/input test utility. Exercise its
control bytes and escape sequences, cursor addressing at boundaries, clear/home,
erase, wrapping and scrolling, modes, and any input/reply behavior it promises.
Check malformed and unfinished sequences, operation-5 reset on command return,
operation-4 internal clear, non-consuming status and bounded reply queues.

Also qualify rejection of wrong version/class/platform descriptors, duplicates,
preparation read failures, retained descriptor changes, upward/downward movement,
state preservation, unload, self-retirement and cold/warm reconstruction. Test
both normal BIOS callers and BDOS-mediated applications, raw bypass and protected
ROM deployment. A successful synthetic callback test does not prove rendered
terminal compatibility. Record unsupported behavior explicitly.

## Authoritative references

- [Hook and lifecycle contract](../engineering/Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md)
- [Provider behavioral requirements](../engineering/Monitor%20Provider%20Behavioral%20Requirements.md)
- [BIOS hook qualification](../engineering/Monitor%20BIOS%20Hook%20Qualification.md)
- [Commit spine qualification](../engineering/Monitor%20Commit%20Spine%20Qualification.md)
- [RSX/CPX programmer guide](RSX%20and%20CPX%20Programmer%27s%20Guide.md)

A general TCAP capability schema, terminal database and broader discovery API
remain post-1.0 work. Do not treat the 1.0 backend bits as that future schema.

## First development example: ADM-3A

The Model 4 implementation is in `src/rsx/adm3a.mac`, with its builder in
`tools/build_adm3a.py` and development test utility in `src/utilities/admtst.mac`.
It illustrates the callable entry, ordinary chain pass-through, static
relocation, parser storage, MONRAW bypass and direct Model 4 cursor updates.
Its clear operation fills video memory without reinitializing the keyboard.

See [ADM-3A foundation qualification](../engineering/ADM3A%20Provider%20Foundation%20Qualification.md)
for build dependencies, checks and remaining gates. This example uses Model 4 video memory and BIOS-owned cursor state. A new
personality must implement its own specified semantics rather than relabeling
this provider.


ADMTST now includes movement, reverse/erase/line-operation pages, bell and cursor
queries, and a short keyboard check. Its character-output routine is also an
example of safely sending coordinate bytes that can include 24h; BDOS 9 would
prematurely terminate such a stream. A successful keyboard result is separate
from visual and audible qualification.


For control-stream tests, ADMTST uses BDOS 6 raw console output. Standard BDOS 2
expands TAB using BDOS's own column counter, which terminal cursor-address
sequences do not update. See the [native ADM-3A campaign](../engineering/ADM3A%20Native%20Qualification.md)
for intermediate screenshots, original-application scope, audio checks and
real unload/TPA checks.


## VT52 development example

`src/rsx/vt52.mac` illustrates a personality translating through MONRAW into an
ANSI host transport, with byte-sized cursor/parser state and shared output,
address-formatting and movement routines. `tools/build_vt52.py` and
`src/utilities/vt52tst.mac` build only development artifacts. See
[VT52 foundation qualification](../engineering/VT52%20Provider%20Foundation%20Qualification.md)
for supported controls, host-geometry assumptions and remaining gates. It is
not yet a generic monitor template or a released VT52 implementation.


VT52 now also demonstrates a bounded byte-indexed reply ring. It enqueues ESC Z
identification replies atomically, preserves queued bytes across reset/clear,
and observes backend keyboard bytes during status polling only when its logical
queue is empty. This preserves provider-observed ordering without pretending
to know when an unread physical key arrived.
