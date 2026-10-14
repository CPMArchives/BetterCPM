# Developing monitor RSXs

BetterCP/M 1.0 uses a bounded monitor-provider interface to add terminal
personalities that the basic console does not implement. ADM-3A (Montezuma
Micro behavior on Model 4) and VT52 are the initial planned providers, each
with a dedicated test utility. Their completed implementations will be added
as worked examples here. This guide does not claim those providers exist yet.

The BIOS hooks, transactional detach/publication, descriptor validation,
prospective selection, duplicate-provider rejection and retained live-descriptor
reconciliation are installed. Valid MCON carriers now bind through normal RSX
transactions. Command-return reset, internal clear/home integration and the
initial terminal providers remain implementation gates. Do not describe the
terminal personalities as released until those gates and rendering/input
qualification pass.

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
