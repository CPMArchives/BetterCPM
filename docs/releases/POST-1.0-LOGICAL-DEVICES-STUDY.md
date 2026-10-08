# Post-1.0 exploration: extensible logical devices

Status: exploratory proposal, recorded 2026-10-07. No implementation commitment,
ABI allocation, or BetterCP/M 1.0 release requirement.

Explore generalizing CP/M logical byte-stream devices (`CON:`, `RDR:`, `PUN:`,
`LST:`) into dynamically bindable named endpoints. This is synchronous I/O
routing, not a concurrent-process or interprocess pipe model.

A working utility name is `DEV.COM`. Illustrative operations are add, remove,
list and query. Bindings might alias another device, shadow a standard device,
or target a file, serial device, null sink, or suitable registered service.
Removing a shadow should restore the underlying device. These examples are
conceptual, not accepted command syntax:

```text
DEV /ADD P: PTR:
DEV /ADD LST: A0:OUTPUT.TXT
DEV /ADD RDR: B3:INPUT.DAT
DEV /REMOVE LST:
```

Session bindings could route output across a SUBMIT sequence. Persistent
bindings are a separate possible feature. Define how abnormal termination,
warm boot, cold boot and reconstruction affect bindings and open targets.
A saved binding description does not imply that live FCBs, handles, provider
addresses or transfer state have the same ownership or lifetime.

An RSX or registered service might implement endpoint behavior; do not select
that architecture until costs and consumers are known. No large pipe buffer is
inherent, but buffering, filesystem reentrancy, final flush and close behavior
must be assessed for file-backed standard devices.

Generic-aware programs could copy between files and newly registered byte-stream
endpoints without containing provider-specific code. Existing binaries do not
automatically gain arbitrary-name support. Distinguish adoption by generic-aware
utilities from interception of traditional BDOS/BIOS character-device calls,
including the behavior of applications which bypass BDOS.

## Bounded research questions

- Names and namespace: `P:` also denotes CP/M drive P; define unambiguous
  endpoint versus drive/user parsing before adopting examples as syntax.
- Read/write/bidirectional capabilities, end-of-input, binary/text behavior,
  blocking and error semantics; do not assume standard devices are identical.
- File create/replace/append, user-area ownership, flush/close, full-disk and
  failure handling, and safe filesystem calls from character-device hooks.
- Session versus persistent bindings, shadow/restore, alias-cycle rejection,
  discovery, enumeration and provider replacement/unload safety.
- Ownership and lifetime of binding descriptions versus live I/O state, memory
  cost and behavior through SUBMIT abort, WBOOT and RSX reconstruction.
- Compatibility with logical devices and IOBYTE, PIP/COPY and future utilities;
  utility endpoint support must not become an implicit 1.0 prerequisite.
- Whether future command redirection could share this facility rather than
  create a competing routing model.

Investigate a minimal demonstrated consumer first. Report compatibility benefit,
API/lifecycle costs and qualification burden before proposing implementation.
This may be substantial 1.x or 2.0 work. Coordinate the study with CONFIG policy
and the later architecture review; defer any endpoint schema or dependency
framework until a concrete design demonstrates the need.

## Addendum: DU-Granular Logical-Device Endpoints

Add the following considerations to the post-1.0 **Extensible Logical Devices / Named Endpoints** exploration.

## DU-Granular Bindings

Explore allowing an endpoint binding to occupy an individual **drive/user (DU) address**, rather than consuming an entire CP/M drive letter.

For example:

```
DEV /ADD P10: PTR:
```

would bind only `P10:` to `PTR:`. Other user areas on P: remain ordinary filesystem namespaces:

```
P0: ... P9:     normal filesystem
P10:            PTR: endpoint
P11: ... P31:   normal filesystem
```

This avoids consuming an entire drive letter merely to establish one logical-device endpoint.

Similarly:

```
DEV /ADD A1: PTR:
DEV /ADD A2: RDR:
```

could establish different endpoint bindings within individual user areas of the same drive.

Bindings may also target other bound DUs. Endpoint resolution therefore may form a chain:

```
A0>DEV /ADD P10: PTR:
A0>DEV /ADD C7: P10:
A0>DEV /ADD D3: C7:
```

The resulting bindings remain three independent mappings:

```
P10: -> PTR:
C7:  -> P10:
D3:  -> C7:
```

At this point all three names ultimately resolve to `PTR:`:

```
P10: -> PTR:
C7:  -> P10: -> PTR:
D3:  -> C7: -> P10: -> PTR:
```

The binding table should preserve those mappings rather than flattening them into three independent `PTR:` mappings. Each binding therefore remains independently removable and replaceable.

This possibility should be explored rather than assumed; it has implications for ordinary filesystem semantics.

## Chained Binding Semantics

Removing a binding removes **only that binding**. It does not rewrite, remove, or otherwise disturb bindings that happen to refer to it.

For example, beginning with:

```
P10: -> PTR:
C7:  -> P10:
D3:  -> C7:
```

executing:

```
DEV /REMOVE P10:
```

restores the ordinary filesystem meaning of `P10:`. The other mappings remain:

```
C7: -> P10:
D3: -> C7:
```

Their effective resolution consequently changes:

```
P10: -> filesystem P10:
C7:  -> P10: -> filesystem P10:
D3:  -> C7: -> P10: -> filesystem P10:
```

Similarly, removing `C7:` would restore ordinary filesystem C7 while leaving both `P10:` and `D3:` definitions intact:

```
P10: -> PTR:
C7:  -> filesystem C7:
D3:  -> C7: -> filesystem C7:
```

Thus a binding records a relationship between names, not a cached copy of the ultimate endpoint to which the relationship happened to resolve when it was created.

This provides predictable alias semantics and permits bindings to be reconfigured without reconstructing every dependent binding.

The design must detect binding cycles. For example:

```
DEV /ADD C7: P10:
DEV /ADD P10: C7:
```

must not result in unbounded endpoint resolution. Cyclic mappings should preferably be rejected when created, with runtime cycle detection retained as a defensive measure.

## Resolution of Unqualified Drive References

A drive reference without an explicit user number should inherit the **current user number before endpoint resolution occurs**.

For example:

```
A0>DEV /ADD P10: PTR:

A0>COPY FILE.TXT P:
Copying FILE.TXT to P0:...
```

Because the current user is 0, `P:` first resolves to `P0:`. Since P0 has no endpoint binding, COPY performs an ordinary filesystem copy.

After changing user:

```
A0>10:

A10>COPY FILE2.TXT P:
Copying FILE2.TXT to PTR:...
```

Here `P:` first resolves to `P10:`. P10 is bound to `PTR:`, so the operation is directed to that endpoint.

The proposed resolution sequence is therefore:

```
drive specification
    ↓
resolve omitted user from current user
    ↓
obtain complete DU
    ↓
check for endpoint binding
    ↓
follow binding chain
    ↓
reach concrete filesystem or device endpoint
```

This preserves BetterCP/M's existing DU semantics rather than giving an unqualified drive reference an independent endpoint meaning.

## Make Endpoint Resolution Visible

When an ordinary-looking DU resolves through one or more bindings, utilities should make the effective endpoint visible to the user where doing so helps explain the operation.

For example:

```
A10>COPY FILE2.TXT P:
Copying FILE2.TXT to PTR:...
```

or, with:

```
D3: -> C7:
C7: -> P10:
P10: -> PTR:
```

an operation against D3 might report:

```
A0>COPY FILE.TXT D3:
Copying FILE.TXT to PTR:...
```

This reduces the risk of a user believing that a file has been copied to disk when it has actually been sent to a device.

Diagnostic or verbose facilities may additionally expose the complete resolution chain when useful:

```
D3: -> C7: -> P10: -> PTR:
```

Ordinary utilities need not print the complete chain during every operation; the final resolved endpoint is normally the important information.

## Directory Semantics

The behavior of commands such as:

```
DIR P10:
```

must depend on the final resolved endpoint.

If P10 is currently bound to `PTR:`, DIR must not misleadingly display the directory of an underlying filesystem area while other operations against P10 reach the endpoint.

A possible behavior is:

```
A0>DIR P10:
P10: = PTR:
```

or an equivalent diagnostic identifying P10 as a non-directory endpoint.

If a chain ultimately resolves to a filesystem DU, DIR should operate on that filesystem endpoint while making the resolution visible where appropriate.

For example:

```
C7: -> B2:
```

could permit:

```
A0>DIR C7:
C7: = B2:
[contents of B2:]
```

Unbound DUs retain ordinary filesystem directory semantics.

This raises the broader question of whether endpoints should advertise a `directory-capable` capability and whether future endpoint types might legitimately provide directory-like enumeration.

## Endpoint Capabilities

Endpoints should expose capabilities rather than requiring every utility to know every endpoint type.

Possible capabilities include:

- readable;
- writable;
- directory-capable;
- sequential;
- seekable/random-access;
- other capabilities introduced by future endpoint providers.

Capabilities are determined by the **final resolved endpoint**, not by intermediate aliases.

Thus:

```
D3: -> C7: -> P10: -> PTR:
```

gives D3 the effective capabilities of `PTR:`.

Utilities then request operations from the resolved endpoint and fail naturally when the required capability is unavailable.

For example, if P10 resolves to `PTR:` and PTR is an input-only device:

```
A10>COPY FILE.TXT P:
Copying FILE.TXT to PTR:...
Error writing PTR: Device is read-only
```

The exact wording should follow BetterCP/M's eventual standard error conventions.

Conversely, a `LST:` endpoint might accept output but reject attempts to use it as an input source.

This allows existing utility concepts to extend naturally to devices. COPY need not contain special cases for `PTR:`, `LST:`, serial devices, filesystem aliases, future service endpoints, etc. It operates against a source and destination and requires appropriate capabilities from each.

## Filesystem-Like Error Semantics

Where practical, endpoint failures should reuse familiar filesystem semantics.

A destination that cannot accept data can behave analogously to a read-only destination. An endpoint that cannot supply data can report an appropriate read failure.

The user-facing diagnostic should nevertheless identify the **resolved endpoint**, so that indirection remains understandable.

Conceptually:

```
resolve DU
    ↓
follow endpoint bindings
    ↓
reach concrete endpoint
    ↓
query capabilities
    ↓
perform requested stream operation
    ↓
report ordinary operation errors where applicable
```

## Namespace Safety

DU-granular endpoint binding introduces a risk because `P10:` visually resembles ordinary disk storage.

The design must therefore specifically investigate how to prevent surprising behavior.

Important principles identified so far:

1. An omitted user number always inherits the current user before endpoint lookup.
2. Endpoint resolution should be visible when an operation is performed.
3. `DIR` and other filesystem-oriented commands must not pretend a non-directory endpoint is an ordinary filesystem.
4. An endpoint binding should not silently expose an underlying filesystem through some operations while redirecting other operations elsewhere.
5. Removing an endpoint binding restores the ordinary meaning of that DU.
6. Bindings remain independent even when they form resolution chains.
7. Removing or changing one binding must not rewrite other bindings that refer to it.
8. Endpoint capabilities come from the final resolved endpoint.
9. Binding cycles must be prevented or safely detected.

The goal is to obtain the namespace and aliasing benefits of DU-granular bindings without making ordinary filesystem operations unpredictable.

## Example

A complete session might look conceptually like:

```
A0>DEV /ADD P10: PTR:
A0>DEV /ADD C7: P10:
A0>DEV /ADD D3: C7:

A0>DEV /LIST
P10: -> PTR:
C7:  -> P10:
D3:  -> C7:

A0>COPY FILE1.TXT D3:
Copying FILE1.TXT to PTR:...

A0>DEV /REMOVE P10:

A0>DEV /LIST
C7: -> P10:
D3: -> C7:

A0>COPY FILE2.TXT D3:
Copying FILE2.TXT to P10:...
```

After `P10:` is removed as an endpoint binding, it again denotes ordinary filesystem P10. Neither C7 nor D3 has been modified; their existing chains now terminate at that filesystem.

This demonstrates the central idea:

> A binding maps one logical endpoint name to another. Resolution follows those mappings until it reaches a concrete endpoint. Bindings remain independent objects, so changing one may change the effective destination of dependent aliases without altering their definitions.

## Status

This remains **post-1.0 exploratory work**.

In particular, the exploration should determine whether DU-granular endpoint binding can actually be reconciled cleanly with CP/M BDOS/FCB semantics before adopting it as an architectural feature.

The namespace and aliasing advantages are substantial, but ordinary CP/M filesystem behavior must remain unsurprising and predictable.


### DEV listing and resolution queries

Illustrative additional parameters:

```text
DEV /LIST
P10: -> PTR:
C7:  -> P10:
D3:  -> C7:

DEV /RESOLVE P10:
P10: -> PTR:

DEV /RESOLVE D3:
D3: -> C7: -> P10: -> PTR:
```

`/LIST` shows all current defined mappings, preserving direct targets rather
than flattening aliases. `/RESOLVE` shows the effective resolution of a named
endpoint; a chained query may display each step and its final target. Define
unbound-DU, unavailable-target and cycle diagnostics during the future study.
These commands remain exploratory syntax, not a 1.0 utility requirement.

## Addendum: evaluate named endpoints as an extension of STAT device assignments

The proposed conceptual starting point is CP/M's existing logical-device routing
and IOBYTE facility, rather than a parallel routing model. The familiar STAT
operations remain the BetterCP/M 1.0 compatibility target:

```text
STAT DEV:
STAT VAL:
STAT CON:=...
STAT RDR:=...
STAT PUN:=...
STAT LST:=...
```

For the future study, evaluate retaining STAT as the operational interface to
an enlarged endpoint namespace. A dedicated DEV utility is an alternative only
if the size or responsibilities justify it; DEV is not a committed component.
Possible future syntax, not an accepted contract:

```text
STAT P10:=LST:
STAT MYDEV:=UL1:
STAT PRINTER:=P10:
STAT LOG:=B3:OUTPUT.TXT
STAT C7:=P10:
```

Aliases remain independent mappings and resolve through the previously
proposed chain rules. A chained assignment spelling such as
`STAT C7:=P10:=LST:` is merely a syntax candidate; what mappings it creates
must be defined before adoption. The earlier DEV /LIST and /RESOLVE examples
express needed operations, not a requirement for a separate executable.

CONFIG could expose the same assignment operations for saved startup policy,
while STAT retains traditional operational/compatibility access. Both should
use the same owner and validation rules rather than duplicate routing state.

This is a natural generalization of the existing device-assignment concept,
but conceptual continuity is not proof that implementation is small. IOBYTE's
fixed selectors cannot by themselves represent arbitrary names, DU aliases,
files or service endpoints. The study must still determine the runtime service,
namespace/FCB boundary, live I/O ownership, error behavior, compatibility with
existing binaries, and costs of resolution and lifecycle handling.

Preserve traditional device assignments without adding new 1.0 requirements.
The current utility iteration should specify and qualify ordinary STAT device
behavior; the generalized namespace remains post-1.0 exploration.

## DU-Level Protection and Optional WHEEL Privilege Policy

Explore read-only policy for an individual filesystem drive/user area, so
P10: could be protected while P0:–P9: and P11:–P31: remain writable, subject
to any drive-wide protection. This is distinct from endpoint capabilities:
a binding to an input device is not writable because of its provider, while
a filesystem DU may be made read-only by policy. DU-granular endpoint bindings
make this a useful related question; they do not automatically implement it.

Define the scope of prohibited mutations: creation, existing-file writes,
deletion, rename and attribute changes. Establish interactions with drive-wide
R/O, individual file attributes, aliases and their resolved targets, saved
configuration, WBOOT and binding removal. If ordinary programs are to obey
filesystem DU protection, enforcement must cover their direct BDOS calls;
checks in STAT, COPY or other cooperating utilities alone are insufficient.
Measure resident memory and code costs during the architectural review,
especially given the current BDOS capacity constraint.

Consider a WHEEL-style privilege flag if the intended policy restricts who
may clear protection or modify endpoint bindings. It is a candidate, not a
prerequisite: accidental-write protection can exist without privilege control.
Define who may change the flag, its initial and saved/session state, behavior
across WBOOT and recovery, and whether the model is cooperative restriction
or a stronger security boundary. A directly writable flag in ordinary program
memory must not be presented as strong security. Do not assume a byte alone
supplies enforceable privilege separation.

Study DU protection and privilege policy together before choosing mechanisms.
This remains post-1.0 exploration, with no new WHEEL byte, BDOS contract,
protection schema or implementation requirement for 1.0. Retain drive-wide
R/O and existing file attributes for the frozen release.
