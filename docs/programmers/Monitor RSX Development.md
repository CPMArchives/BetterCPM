# Developing monitor RSXs

BetterCP/M 1.0 uses a bounded monitor-provider interface to add terminal
personalities that the basic console does not implement. ADM-3A (Montezuma
Micro behavior on Model 4), VT52 and an ANSI/VT100-compatible subset are the
committed 1.0 providers, each
with a dedicated test utility. The native Model 4 ADM3A provider and ADMTST
are implemented, as are cpmsim VT52 and the bounded ANSI/VT100 provider.

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

New portable personalities use MCON 1.1 with capability 0004h and the manager-
bound SCRN reference described below. The hardware-specific SCRN 1.0 backend
advertises exactly 0001h for Model 4 or 0002h for cpmsim. Legacy MCON 1.0
providers use those platform bits directly; that includes the historical host
starter. These bits are not a terminal-capability database.

## Build the carrier

Use the existing BRSX-v2 builder, tools/build_rsx_module.py. A portable
personality advertises callable MCON 1.1, capability 0004h, STATEFUL, with its
entry offset measured from the payload base. Preserve the canonical chain at
+8, initially zero backend word at +12 and executable callback at +14 or later.
The manager owns the external reference after load. See the integration section
below for relocation exclusions. Existing platform-bound MCON 1.0 examples
instead permit callbacks at +8 or later and require no SCRN dependency.

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

`src/rsx/vt52.mac` is being converted to portable MCON 1.1. It parses VT52
commands into typed SCRN operations rather than emitting terminal strings.
The same assembled carrier is tested with M4SCRN (Model 4 video memory) and
ANSISCRN (cpmsim with an ANSI host). A backend must be loaded first; the manager
fills the private reference at payload +12. A partial address does not change
the displayed cursor until complete. Provider version is 1.2; the user exercise
remains VT52TST.

`tools/test_vt52_foundation.py` exercises parsing against a controlled screen
service; `tools/test_vt52_rendering.py` executes both actual renderers.
`tools/test_vt52_lifecycle.py` executes the production manager with the real
pair, checking dependency rejection, state preservation, rebinding and unload.
Native ZSM4/LINK parity, live cpmsim/trs80gp exercises, original VT52 WordStar
edit/save, protected-ROM cpmsim and clean distribution boot checks now pass;
see the [integration evidence](../engineering/VT52%20Portable%20Backend%20Integration.md). The earlier native-wire audit describes the superseded
implementation, not the new frontend's output. See the
[screen backend ABI](../engineering/Unloadable%20Screen%20Backend%20ABI.md).

VT52 now also demonstrates a bounded byte-indexed reply ring. It enqueues ESC Z
identification replies atomically, preserves queued bytes across reset/clear,
and observes backend keyboard bytes during status polling only when its logical
queue is empty. This preserves provider-observed ordering without pretending
to know when an unread physical key arrived.

## Start from the editable host template

The fill-in control-code starter below remains available for simple host-output
providers. It is a legacy MCON 1.0 example, not the new portable MCON 1.1
personality template. Do not change its platform bit and assume it has become
portable. The ongoing conversion separates incoming protocol parsing from the
hardware backend; see the [screen backend ABI](../engineering/Unloadable%20Screen%20Backend%20ABI.md).

For a new physical terminal with mostly fixed output strings, a backend template
can hold its clear, erase and movement codes. Parameterized addressing still
needs its encoding routine. For a new application-facing terminal personality,
its incoming codes map to shared screen operations, with parsing for any
parameters, modes or replies. These are distinct extension tasks. The intended
portable starter should make the simple cases table edits while keeping those
required routines explicit; the current host starter does not yet provide that
portable scaffolding.

For a small new host-terminal personality, copy and edit:

- `src/rsx/monitor-template/host.mac`: MCON dispatch, chain entry, parser and raw transport.
- `src/rsx/monitor-template/ansi-demo.inc`: incoming-control translation tables and clear/home bytes.

Build the supplied example from the repository root:

```sh
python3 tools/build_monitor_template.py
```

This emits `build/monitor-template/MONDEMO.RSX`, payload binaries and listings.
The default module is development version 0.1, STATEFUL, MCON 1.0, host backend
bit 0002h. Its payload is 205 bytes with 26 static relocations and a 256-byte
runtime allocation including the service descriptor. It adds no permanent
BIOS/BDOS code. It is not on the distribution disk or normal startup path.

To use your copies and a distinct module name:

```sh
python3 tools/build_monitor_template.py --engine /path/to/host.mac --profile /path/to/profile.inc --name MYMON --output /path/to/output
```

Names contain 1–8 uppercase letters/digits, beginning with a letter. Preserve
the `BASE EQU 08000H`, `TP_ENTRY`, `TP_CLS`, `TP_BYTES`, `TP_CODES` and `TP_END`
labels and the `INCLUDE profile.inc` marker when using this builder. The builder
assembles at two origins, derives static relocations and verifies reproduction
of the alternate image. It also checks table byte counts, unique keys and
terminators before writing a carrier. The profile tables must remain in their
supplied order, ending at TP_END.

### What to change in the tables

`TP_CLS` starts with a byte count followed by the exact bytes needed to clear
and home the selected host. `TP_BYTES` maps incoming ordinary byte values to
counted output strings. `TP_CODES` maps the byte after ESC to counted output
strings. Each translation entry is `key, count, data...`; a zero key ends the
table. A zero count consumes a key without producing output. Counts include
all emitted bytes, including ESC and any binary zero; these are not
zero-terminated strings and must not be printed with BDOS function 9.

For example, this entry maps incoming ESC H to ANSI home:

```asm
        DB 'H',3,27,'[H'
```

The supplied sample accepts ordinary ASCII, FF clear/home and ESC H/J/K/A/B/C/D
for home, erase and relative movement. Unmapped ordinary bytes pass through
MONRAW. NUL and DEL are ignored; ESC is reserved for the parser. Unknown ESC
finals are consumed, and another ESC restarts the pending command. Thus this
example is a deliberately small teaching grammar, not full VT52 or ADM-3A.
All emitted strings go to the basic host backend; they do not reenter the
personality parser. The caller must select a host that understands those codes.

### When table edits are insufficient

A protocol with coordinate parameters, CSI numbers, persistent modes, keyboard
translation or terminal replies needs custom parsing/state routines. Use the
VT52 implementation for bounded coordinates and ordered replies, and
`src/rsx/ansi.mac` for buffered CSI parsing and incomplete-sequence reset.
Adding an escape string to a table does not implement its parameter semantics.

The starter deliberately stores pending state as a byte and table offsets are
computed from relocated instructions. There are no mutable internal pointer
words. If custom handlers introduce such pointers, declare the runtime pointer
slots required by the BRSX lifecycle; the starter builder does not infer them.
Modify the builder accordingly before claiming relocation safety.

This starter targets cpmsim-compatible host output only. Changing its backend
bit to 0001h does not turn it into a Model 4 renderer. For that platform, use
ADM3A's generated hardware symbols and renderer as the backend reference.

### Test before shipping a new personality

```sh
python3 tools/test_monitor_template.py --bios /path/to/host-build
python3 tools/build_monitor_template.py
python3 tools/test_monitor_template_lifecycle.py --bios /path/to/host-build
```

The first test builds the sample and an edited profile, executes each at two
relocated addresses, checks binary output, clear/reset, unknown/restarted ESC
commands and input/status, and rejects an incorrect table count. The second
executes the actual RSX manager: HELLO loads before MONDEMO, an ESC is left
pending, HELLO unload moves MONDEMO, the command completes at its new address,
MCON lookup follows the new binding, and unloading restores the basic monitor
and 53K TPA. These checks use the assembled host BIOS in the instruction runner.

Copy your carrier onto disposable media; unload any existing monitor, then use
`RSX LOAD MYMON`, `CLS`, and your dedicated screen/input test utility. Finish
with `RSX UNLOAD MYMON` and verify TPA recovery. Qualify real terminal rendering,
applications and protected-ROM behavior separately, following the released
providers' campaigns. A passing starter test does not qualify a newly edited
protocol or host. Keep your carrier outside the system-disk manifest until its
own qualification is complete.

This is source scaffolding, not a runtime TCAP database, universal terminal
translator or new BIOS ABI. The general TCAP design remains post-1.0 work.

## Unloadable backend integration status

`SCRN` is reserved for screen-backend callable metadata: ABI 1.0, STATEFUL
reconstruction and exactly the matching Model 4/cpmsim platform capability.
Legacy MCON 1.0 remains platform-bound and independent of SCRN.

Portable MCON 1.1 uses capability bit 2 only (`0004h`). Its canonical dispatch
remains at payload +8; an initially null, manager-owned backend-reference word
is at +12, and the monitor callback starts at +14 or later. Keep that word out
of static and runtime self-pointer lists, including overlapping words at +11
and +13. Do not initialize or retain a backend lookup address yourself.

The manager validates the complete prospective pair and rebinds this word after
movement, before monitor/generation publication. Load a compatible backend
before its personality, and remove the personality before removing the backend.
At most one of each role is allowed; a carrier cannot advertise both roles.
A backend alone is permitted. No dependency callbacks run during commit.

This lifecycle interface is implemented and CPU-qualified. Screen-backend builds and their operation contract now exist as a standalone
checkpoint. Portable VT52 is now on both distribution disks with its matching backend.
Full conversion of ADM3A and ANSI and a portable editable starter remain open. See the
[production integration record](../engineering/Monitor%20Backend%20Production%20Integration.md).
