# Monitor RSX hook and lifecycle contract

Design worked out 2026-10-12 against the production BIOS and Stage-3 manager.
This is the implementation design for the accepted
[1.0 monitor decision](../architecture/31%20Terminal%20Monitor%20RSX.md), not a
claim of installed monitor support. Isolated dispatch and size probes exist;
production metadata selection, transactions and terminal providers are pending.
This is a bounded private monitor interface, not the post-1.0 TCAP API.

## One binding, one provider

Use one protected two-byte BIOS-owned target, initialized to the basic-console
multiplexer. An installed provider replaces that target with its single entry.
All standard console paths reach it; BIOS does not resolve services, search disk,
walk the RSX chain or call BDOS while delivering a character.

A provider advertises one callable service `MCON`, version 1.0, using existing
BRSX-v2 callable metadata. It is STATEFUL, with all internal pointer words
properly declared. Its ordinary BDOS-chain dispatch passes unclaimed operations
onward; the monitor does not require a numeric BDOS service. No carrier-format
change or general RSX lifecycle callback mechanism is required.

At most one MCON provider may appear in a prospective profile. A second is
rejected before mutation; switching personalities uses UNLOAD followed by LOAD.
There is a usable basic console between those commands. Atomic replacement is
outside this bounded contract. The existing four-provider profile limit remains.

For this implementation, capability bit 0 identifies the Model 4 backend and
bit 1 the cpmsim backend. Exactly one must match the running platform, with other
bits zero. Validate MCON version, class, capabilities and entry bounds before
commit, including retained members. Do not bind a mismatched platform binary.
These bits identify backend compatibility, not a TCAP capability database.

## Entry operations

A selects the operation; C contains any input character. HL is dispatch scratch
and must not be assumed to retain its caller value at provider entry.

| A | Operation | Result |
|---|---|---|
| 0 | Console output, character in C | Ordinary BIOS CONOUT behavior |
| 1 | Console status, non-consuming | A = 00h or FFh |
| 2 | Blocking console input | A = character; public BIOS applies its existing 7-bit mask |
| 3 | Existing private cursor presentation, C = 0 query or character to draw | Preserve the current private cursor contract |
| 4 | Internal clear screen and home | Clear/home and reset any incomplete output sequence |
| 5 | Reset incomplete terminal sequence | Discard parser continuation; retain screen, position and normal terminal modes |

Honor the existing BIOS calling/register contracts and balance the stack. The
provider may use its own bounded state but must not recursively enter routed
console operations, invoke BDOS, allocate, load an overlay or mutate the RSX
profile from a callback. This console is single-context and non-reentrant;
console use from interrupt handlers is not supported by this contract.

The public CONST wrapper still normalizes status, and CONIN retains its current
mask. The original 17 BIOS vectors and existing four private vectors retain
their offsets. Append three private JMP vectors:

| BIOS offset | Entry | Purpose |
|---:|---|---|
| +66 | MONCALL | Route the selected operation through the current binding |
| +69 | MONRAW | Execute the basic backend directly, bypassing the monitor |
| +72 | MONBASE | Set the binding to the basic backend; manager/cold-init use |

The provider uses MONRAW for supported basic operations without recursion.
Its platform-specific renderer may additionally use build-generated internal
backend symbols; these are not a public portable screen API. Reuse the existing
backend cursor/column state or keep it explicitly coherent. Direct video writes
must not leave the basic backend at an obsolete position after unload.

MONRAW operation 4 preserves the basic backend's existing clear behavior, and
operation 5 is a no-op. Unknown operations return FFh without performing output.
The dispatch prototype checks routing, not full provider implementations.

## Preparation and commit

Keep the existing all-fallible-work-before-mutation transaction structure:

1. Stream and validate candidate and retained carriers; compute the complete
   prospective layout, snapshots, pointer unions and monitor identity.
2. Derive the monitor's **prospective** address from its validated entry offset
   and new allocation base. With no monitor, use the basic multiplexer address.
   Validate retained live service facts against the prepared facts rather than
   blindly trusting a stale external address or a changed disk file.
3. Retain that address in caller-owned durable scratch across overlay replacement.
   Extend the private mode-1 commit request from 35 to 37 bytes: +35 holds this
   target word. No public Function-177 request change is needed.
4. Complete finalizer/scheduler validation before detaching. At RS_PREPARE,
   after the scheduler's validation loop and before any live movement or fresh
   image copy, call MONBASE. Do this even for a zero-member profile.
5. Move retained STATEFUL allocations, repair their internal pointers and copy
   prepared images using the existing disk-free commit path.
6. The existing persistent publisher installs the prepared target alongside
   the profile fields, before the commit engine's final generation store.
   The publisher performs only validated stores; it calls no provider or BDOS.

There must be no callback in progress when step 4 begins. The manager and BIOS
operate sequentially; no asynchronous console reader observes the intermediate
profile. A Z80 word-store instruction is not interrupted halfway by a maskable
CPU interrupt, but that alone would not make concurrent provider execution safe.
Do not advertise interrupt-driven console support or general concurrent atomicity.

All ordinary failure/rollback cases occur before detach: the old profile and
binding remain intact. A failure after movement starts is an internal invariant
violation, not a recoverable disk error; leave the basic binding safe and stop
rather than call a possibly moved old instance or claim restoration of its old
address. No new fallible provider initializer or shutdown callback belongs after
that boundary.

Mode-zero audit fixtures retain their original private request contract and must
not read +35. Production mode-one publication owns the extra field. Preparation
must compute it for every LOAD, UNLOAD and self-retirement, including changes to
unrelated providers that move the retained monitor.

## State, boot and return

A new monitor image contains initialized parser/queue state in its payload;
static relocation and declared pointer repair establish its instance. No
existing init/shutdown header field is assumed to provide automatic hook binding.
Installation must not need a fallible post-commit callback.

Cold initialization selects the basic binding before any console use. The
existing once-only startup SUBMIT script subsequently loads the platform monitor.
Warm boot retains its allocation and binding and does not rerun startup.

Before warm reconstruction emits command-environment output, call operation 5
through MONCALL. This prevents an application's unfinished escape sequence from
consuming the returning prompt. It does not reset an unrelated RSX, clear the
screen or silently discard ordinary keyboard input. Qualify all command-return
paths, including those that do not enter the ordinary warm-boot vector.

Unloading the monitor detaches before its memory can be released and commits the
basic target. Unloading another provider rebinds any moved monitor without
resetting its retained state. Unloading the last RSX releases the manager
reservation and restores the 53K core TPA baseline. Cold boot discards session
state; it reconstructs a fresh monitor only through the startup script.

## Clear-screen conflict

MCON operation 4 is the internal clear/home operation. Migrate resident CLS
(`src/cpx/rcp.mac`) and disk-utility HEADER (`src/utilities/disk/common.inc`) from
literal 1Ch output to this operation. Audit other internal callers and tests.

With the MM personality active, a legacy output byte 1Ch means insert-line,
as in the selected MM reference. With no monitor, the basic console keeps its
existing 1Ch clear convention. The internal explicit operation works in both
cases. No heuristic can distinguish the two meanings of the same output byte.

## Measured feasibility and limits

Isolated Model 4 assembly produced:

| Component | Baseline | Prototype | Constraint |
|---|---:|---:|---|
| BIOS dispatch/backend access | 636 | 700 | +64 bytes against the 122-byte candidate budget |
| Scheduler | 494 | 496 | Fits exactly before the existing +310h handoff |
| Persistent publisher region | 105 | 105 | Rebind fits existing padding; continuation offsets unchanged |
| Commit overlay | 1007 | unchanged | 1012-byte executable/data prefix |

The scheduler uses one CALL to MONBASE and shortens an existing nearby JP to JR.
The publisher consumes padding before its fixed continuation; the request +35
load and target store need no growth in its current 105-byte region. These are
isolated assembly results, not proof that every preparation change fits. The
prospective-profile scanner/validator and caller scratch changes remain to be
implemented and measured. Do not add another helper file or enlarge the 1KiB
manager reservation merely because one phase is tight.

The measured permanent dispatch growth leaves 58 bytes of the *candidate* core
budget for other required changes. Warm-return reset, complete backend exports,
ROM shadow ownership, metadata preparation and packed layouts are not included
in the 64-byte figure. Qualified memory savings/repacking are still prerequisites.
Provider payload, STATEFUL data, descriptor and page rounding are additional
loaded memory charges; first-provider manager cost remains 1KiB.

## Reproducible probes and next implementation gate

```sh
python3 tools/audit_monitor_hooks.py
python3 tools/audit_monitor_binding.py
python3 tools/test_monitor_hooks.py
```

Outputs remain under `build/audit/monitor-efficiency/hooks-multiplex/`.
The small CPU tests execute public routing, input/status normalization, raw
bypass, safe fallback after destroying a stale fake provider, and the prepared
publisher's target store. The existing scheduler campaign also executes upward
and downward STATEFUL movement with the detach insertion and checks that a
rejected mixed-direction plan keeps the old binding. Full production transaction
integration, metadata selection, terminal screen behavior and ROM deployment
remain unqualified.

Before production adoption, test rejected/duplicate/mismatched providers,
preparation failures at each read, scheduler rejection with the old binding
unchanged, zero-profile detach, forced up/down moves and state preservation,
self-retirement, warm-return parser reset, ROM immutability and both platform
layouts. Prove generation publication follows rebinding and no I/O/provider
callback occurs in the irreversible phase. Rendered-screen compatibility and
real terminal input/replies require their own provider campaigns.

## Provider behavior

[Monitor Provider Behavioral Requirements](Monitor%20Provider%20Behavioral%20Requirements.md) defines the MM-style ADM-3A and VT52 personalities, input/reply queue semantics and qualification cases.

The BIOS 1.6 character-capability query occupies +63. Existing vectors at
+0..+60 are unchanged. The reserved monitor vectors therefore start at +66;
the combined routing/capability/monitor prototype is 757 bytes and fits the
757-byte BIOS allocation without reducing unloaded TPA.
