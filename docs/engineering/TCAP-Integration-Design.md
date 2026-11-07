# TCAP integration design package

> Current design: the [public TCAP ABI and admission contract 1.0](TCAP-Public-ABI.md)
> supersedes the provisional wire values and unresolved admission choices below.
> This document preserves its historical design baseline; it is not evidence
> that the public service is implemented. Utility migrations and release assignment remain deferred.

Status: complete proposed integration design for engineering review,
7 November 2026. Builds on the consolidated
[proposal](TCAP-Engineering-Proposal.md),
[semantic contract](TCAP-Semantic-Contract.md) and
[owner/transaction design](TCAP-Owner-Transaction-Design.md) merged through
PR #651. Source baseline: main `d7c0e831`.

This is documentation, not implementation, a frozen public ABI or proof of
feasibility. No service name, selector, record offset, release or memory budget
is allocated. Record widths below are proposed design constraints for review.
HELP remains held. A subsequent implementation decision must satisfy the gates
at the end; the design does not authorize a prototype.

## Design decisions proposed together

1. Use an optional callable advertisement on the selected personality for the
   portable owner. Discover it through existing Function 182, with no new BDOS
   function number. Leave MCON and SCRN/SCX compatible.
2. Keep live session/capture state in the personality allocation and rendering
   in its backend. The transient binding normalizes facts and consumer policy;
   it does not own state needed after abort.
3. Permit one portable session and one emphasis scope at a time. A takeover may
   contain that scope. Reject profile mutation while either is active or recovery
   is incomplete. Idle providers can move under ordinary manager rules.
4. Classify normal-console routing before dispatch, including bypass/sink routes.
   Portable clients do not change IOBYTE during a session. Unsupported concurrent
   or direct-hardware changes are excluded, not falsely described as detected.
5. Spatial stream eligibility requires no unmodeled CRT echo duplication. Where
   LIST can alias the display, conservatively refuse spatial paging regardless
   of the current ^P flag, unless a separately qualified accounting path exists.
6. Run owner rendering recovery on a safe return stack, then coordinate cooked
   column state outside the callback. Complete this before reconstruction
   diagnostics, CPX initialization, startup or prompt text. Final prompt recovery
   is an idempotent guard, not the only entry boundary.
7. Allocate all required recovery resources before the first mutation. Exhausted
   identities, insufficient storage, unsupported profiles and unqualified return
   paths yield plain/refused eligibility, never an unowned enhanced display.

These decisions resolve the documentation alternatives into one bounded candidate.
Acceptance, actual representation and cost remain review/implementation gates.

## Existing facilities and capacity fit

Current [ANSI builder](../../tools/build_ansi.py),
[ADM3A builder](../../tools/build_adm3a.py) and
[VT52 builder](../../tools/build_vt52.py) each advertise MCON only. The existing
[resident service ABI](../architecture/20%20Resident%20Service%20ABI.txt)
allows two advertisements per RSX, so an optional second logical service fits
that declared per-provider capacity without assuming a third advertisement.
The client must still query actual registry capacity; this is not permission
to hard-code four modules/eight services. A new separate owner RSX is not required
by this design. Unknown/legacy personalities remain valid without the service.

Metadata alone does not establish routing guards or recovery coverage. Admission
must couple the optional owner with a compatible system coordinator and backend
profile. A new personality must not advertise enhanced eligibility on an old
core merely because it can accept rendition commands. Existing MCON revision
admission must not silently imply these stronger guarantees.

## Proposed client interface

Use one callable dispatcher with A selecting a symbolic operation and DE pointing
to a caller-owned request. Return A as a service-local result; preserve SP, IX,
IY and DE, and treat other registers/flags as scratch. This is a proposed calling
convention, not an assigned ABI. Numeric operation/status values remain unallocated.
The request is synchronous, non-reentrant and never retained by the provider.
No operation calls BDOS recursively. Text still uses the existing console path.

| Operation | Input and output semantics |
| --- | --- |
| Discover | Requested stream/fixed-cell class and destination intent; returns copied snapshot facts. No output or terminal input consumption. |
| Admit | Snapshot and required operations, dimensions and cleanup guarantees; returns an eligibility record. Read-only; no live session is created. |
| BeginEmphasis | Eligibility and, if applicable, current takeover token; revalidate, arm capture/recovery and apply semantic emphasis. Return active token or plain with no token. |
| ActivateTakeover | Eligibility for the fixed viewport/required operations; arm persistent ownership before TED's first mutation. Return active takeover token. |
| EndEmphasis | Matching active token; restore prior rendition and retire only the scope. No-op is not success for an unrelated/stale token. |
| Release | Matching takeover token with no open scope; complete normal exit baseline then retire session. |
| Recover | Matching session for explicit client recovery, or an internal coordinator authority for the current obligation; restore prompt baseline and retire all portable ownership. |
| DescribeSession | Read-only state/result query for client diagnostics after partial failure; reveals no callable pointers or unrelated transient storage. It does not repair anything. |

Public Recover must not accept an unchecked “all sessions” token. Internal
command-return authority is a separate validated entry context, not a magic
client-supplied pointer. These tokens are lifecycle correctness handles, not
security boundaries against a program that can overwrite memory.

### Logical request and record shapes

These fields specify data to carry, not packed offsets. All words are proposed
unsigned little-endian 16-bit quantities; identity components are proposed
unsigned 32-bit quantities. A later binary specification must assign exact
lengths, layout and version rules together before any client is implemented.

| Record | Proposed fields |
| --- | --- |
| Request envelope | Version byte, length word, symbolic operation, zero reserved flags, input/output pointers and capacities as needed, result, resulting session state, recovery-required indicator. |
| Snapshot | Record version/length; owner validity identity; resident generation observation; rendering class; destination/interactivity states; rows/columns words with independent known/provenance tags; wrap/control model; operation availability; emphasis and explicit-attribute facts; routing/echo class; cleanup guarantees; explicit plain policy. |
| Eligibility | Snapshot identity/facts needed to revalidate; requested operations/cleanup; client geometry range; resolved mode (spatial, non-spatial/plain, fixed-cell takeover or refused). No provider entry pointer or transient callback. |
| Session token | Owner validity identity, session serial, token kind (takeover or emphasis) and scope serial if needed to distinguish successive scopes within one takeover. Owner/session identities are nonzero; takeover tokens require scope serial zero, while emphasis tokens require a nonzero scope serial. |
| Owner state | Identities, Idle/Active/Recovering/RecoveryRequired state, takeover/scope ownership, route assumptions, baseline progress and one nine-byte prior logical rendition; no transient pointers. |

The snapshot may report unsupported, unknown or incompatible facts independently;
Discover success is not universal capability success. Physical style support and
encoder-only masks remain distinct. Fixed-cell 80×24 does not become stream
geometry. A client outside its 16-bit range refuses rather than truncating.

Validate the whole request shape before effect: supported major/version, minimum
length, allowed flags, field ranges, buffer capacity and address+length without
16-bit wrap. Output buffers may not overlap the request, each other, live provider
state or protected memory under the supported client-memory rules. Reject invalid
ranges before dereference or mutation. The provider copies all needed activation
facts, never retains a request/snapshot pointer, and writes a defined result even
on preflight rejection when the result envelope itself is valid. This is not a
promise to make arbitrary invalid memory accesses safe under unprotected CP/M.

Known-version longer records require zero reserved fields and a documented
extension rule; unknown major versions are incompatible. Malformed requests
leave display/session state unchanged. Result/state fields distinguish preflight
failure from partial apply/restore failure and successful plain fallback. A
caller never interprets carry flags or SCRN's A=255 as this service's error namespace.

### Identity and stale-handle policy

Recommend a boot-lifetime monotonically allocated 32-bit validity identity,
issued whenever the optional owner is installed or its admissions are invalidated
by a committed profile change. Identity zero is invalid. Do not derive identity
from a load address or a wrapping resident-generation value. The allocator must
survive optional provider unload; a core-owned counter or an equivalent
non-reusing mechanism therefore has a measurable cost. Placement is a gate,
not an existing approved fixed field.

Allocate identity prospectively but publish it only with successful profile
publication. Failed preparation may consume identities; it must not reuse one.
Before exhaustion, refuse new enhanced owner validity rather than wrap. Legacy
profile operations and plain console remain available; a profile losing enhanced
eligibility reports that fact. A cold boot begins a new lifetime and invalidates
all old clients; persistence of handles across cold boot is unsupported.

Session and scope serials increase without wrap within a validity identity;
retired serials cannot operate on a later session. Exhaustion refuses activation
without mutation. Re-establishing a fresh validity identity requires a committed
idle profile transition. On idle compaction, the new validity identity invalidates
old admissions even if the same personality instance survives. Idle state has no
active token to migrate. This avoids a false same-address or generation-wrap match.

## Routing, echo and operation ordering

At Discover/Admit/activation, classify current normal-console input/output and
LIST routes from the actual router, not a client assertion. The optional coordinator
must classify before a bypass route can avoid Monitor output. A managed IOBYTE
change during ownership is refused or requires explicit prior End/Release/Recover.
Direct writes by a cooperative portable client violate its admitted contract;
asynchronous/direct-hardware changes outside the qualified boundary are excluded.
The design does not add a universal page-zero write trap.

For an observed mismatch, stop using enhanced ownership on the changed route.
Clean only via the valid original backend path, never by feeding cleanup through
the new unrelated destination. Do not swallow application bytes or silently
reroute them to preserve decoration. The byte continues under ordinary routing
once rendering cleanup is safe; cleanup failure leaves an explicit recovery obligation.
The routing callback may perform only nonrecursive owner rendering repair and
mark RecoveryRequired; it must not invoke the return coordinator or print CR/LF
recursively from inside output. Passing the original byte preserves ordinary
routing, not successful session cleanup. Enhanced calls remain blocked until the
safe return coordinator completes the full baseline. If even rendering repair
fails, take the qualified system failure disposition rather than claiming safe
plain continuation.
No automatic session continuation or same-byte change/revert guarantee is made.

For initial spatial paging, use a stable route whose possible LIST echo does not
duplicate CRT output, or fall back for the entire page/run. The current CRT LIST
configuration can alias the display, so current profiles are not automatically
certified for spatial TCAP paging. This limits future portable eligibility only;
it does not change today's TYPE implementation or disable ^P. A subsequent design
may account for duplicate glyphs and echo toggles before the affected output.

Emphasis text uses BDOS 2/9 normally. Control-plane presentation must bypass the
text/echo channel but stay coordinated with personality state and backend ownership.
CRT LIST aliasing may show echoed glyphs in the active visual rendition; the byte
guarantee remains no TCAP-added presentation controls. Independent-device visual
styling is not promised for two logical routes to the same screen.

One session boundary serializes activation, End/Release/Recover, managed routing
changes and profile publication. With the single-threaded synchronous contract,
no callback may activate or publish recursively. The manager rechecks idle state
at the final precommit boundary and denies activation until publication completes.
Interrupt code must not call the portable interface. Exact guard placement and
reentry handling must be verified in the implementation design; interrupt masking
through terminal I/O or disk work is not proposed.

## Complete recovery path and source responsibilities

Recovery is two-stage and is not a new meaning for MCON operation 5.
The owner marks Recovering, cancels parser continuation, restores normal logical
rendition consistently with backend state, resets margins/visibility and cancels
pending wrap. The coordinator then establishes the profile's prompt-start policy
and safely synchronizes cooked BDOS column state before retiring the obligation.
A callback cannot repair that private BDOS column through an undocumented write.
The [feasibility campaign](TCAP-Feasibility-Results.md) demonstrates that ordinary
BDOS Function 2 CR/LF synchronizes the cooked column on a safe coordinator stack.
Prefer that existing path; no new column-reset entry or public BDOS number is
required for the tested slice. Full return-path integration still needs proof.

Proposed initial prompt policy is normal CR/LF to the selected display with no
screen clear, followed by a cooked-column value of zero. This deliberately starts
a new line, including after full-screen use. CR/LF follows the normal text channel
only after presentation is normalized, so any ordinary echo contains no TCAP
style controls. Do not consume typeahead, change DU/files, or overwrite SCX's
reusable save slot. No owned session means no new CR/LF. A repeated successful
recovery is a no-op. If that policy is unsuitable for a profile, it cannot advertise
this baseline until a separately documented equivalent is reviewed.

| Source responsibility | Required design integration and reason |
| --- | --- |
| [BIOS router](../../src/bios/bios.mac) | Classify routes before destination dispatch and connect the optional qualified coordinator. Preserve no-provider behavior, public vectors and MONRAW non-recursion. |
| [BDOS console](../../src/bdos/unified.mac) | Preserve UB_PUT flow control/echo. Provide a costed internal cooked-column coordination mechanism on safe entry stacks; do not expose UB_COLUMN as utility-owned state. |
| [Portable reloader](../../src/system/command-stage2.mac) and [Model 4 reloader](../../src/platform/trs80m4/ccprelod.mac) | Establish safe stack and perform full portable recovery before reconstruction I/O/diagnostics. Keep legacy parser reset for ordinary sessions. |
| [CCP entry and prompt](../../src/ccp/ccp.mac) | Guard before CPX initialization, loader-error text and startup, as well as CCP_LOOP prompt for resident-command returns. A prompt-only hook misses earlier output. |
| [Gateway](../../src/system/gateway.mac) | Audit direct warm paths and stack transitions; all output paths must cross a qualified baseline boundary before emitting system text. |
| [Personality/parser](../../src/rsx/ansi.mac) and [rendition dispatcher](../../src/rsx/ansi-dispatch.inc) | Optional owner capture and logical/backend agreement; preserve parser-busy refusal, AP_VALUE, margins, wrap and independent SCX slot. Repeat for other admitted personalities. |
| [Finalizer](../../src/system/r3final.mac), [commit](../../src/system/r3comit.mac) and [publisher](../../src/system/r3pst.mac) | Busy rejection and final idle recheck, prospective validity identity, complete binding publication and generation-last ordering. No fallible terminal callback in commit. |
| Consumer bindings | TYPE accounting/replay/fallback; TED pre-takeover activation/release; HELP emphasis/parser boundaries and decoder workspace. These are separate later migrations, not code changes in this package. |

The reloader guard must precede optional CPX-load diagnostics. The CCP entry guard
must precede CPX_INITIALIZE and error/startup text, not just the interactive loop.
Function 0 and cooked ^C may abandon the BDOS private stack; use the reloader/system
stack before any BDOS-assisted coordination. Resident commands returning without
warm boot still cross the prompt guard. Early loader failures that halt need no
invented successful prompt, but recoverable error text must obey the recovery disposition. Fatal
pre-coordinator paths have the explicit limit below.

After partial recovery failure, retain progress and RecoveryRequired. Do not mark
Idle merely because End/Recover returned. A safe retry may repeat idempotent
normalization but cannot claim exact restoration. If owner binding or console is
corrupt/unreachable, use the existing defined system failure path and do not emit
unverified controls. The implementation must demonstrate its safe diagnostic/halt
behavior; arbitrary terminal failure cannot be repaired by the specification.

### Fatal pre-coordinator paths

Source review identifies failures before CRBODY can run:

- [cpmsim platform loader](../../src/platform/z80pack/biosplat.inc), PL_RELOAD:
  raw-sector fetch failure reaches Z_HALT, emits a raw `!` on port 1 and halts.
- [Checked cpmsim loader](../../src/platform/z80pack/checked-load.inc): fetch,
  identity or CRC verification failure reaches its raw `!`/HALT path.
- [Model 4 loader](../../src/platform/trs80m4/reload.inc), M4_RELOAD:
  fetch failure reaches the M4_RLFAIL loop before entering the reloader.

These are fatal platform dispositions, not normal command-return paths. The
reloader/CCP coordinator cannot guarantee a baseline on code it never reaches.
The proposed initial guarantee therefore excludes successful recovery/readable
markers at such a fatal stop; it must report no successful cleanup and must
not release/republish owner state. A raw marker may inherit the endpoint's
prior rendition. Do not reinterpret that as qualified TCAP error reporting.

A stronger guarantee would need a separately costed resident, safe-stack recovery
entry before the reloader fetch/verification, with no dependency on the code
being loaded. That is an implementation-feasibility alternative, not a delivered
entry or an implicit permanent-memory allocation. Normal recovered diagnostics
inside the loaded reloader and the CCP remain fully subject to the baseline.

## Resource ledger and compatibility gates

| Resource | Design requirement | Evidence still absent |
| --- | --- | --- |
| Fixed routing/recovery dispatch and validity allocator | Minimal qualified entry-path changes; charge all growth to unloaded layout. | Assembled size, placement, stack and ROM-relocated parity. No claim of zero fixed growth. |
| Personality owner | One live session, one capture, identities and progress; optional loaded cost. | Payload delta, repair words, page-rounded allocation/cache/manager overhead on each profile. |
| Transient binding | Request/snapshot validation and fallback; no screen buffer or retained abort pointers. | Code size, record layout, peak stack and per-consumer workspace. |
| TYPE replay | Existing rescan approach with geometry/policy invalidation. | Counter widths, overflow rejection, long-file latency and duplicate/changed-file behavior. |
| HELP | No mandatory decoder history in TCAP. | Decoder-specific workspace, prompt-scope splitting and backward-member replay costs. |

Retain the 1.1 unloaded-TPA policy and qualified platform exceptions. If routing
or recovery growth cannot fit without changing that policy, return for a scoped
implementation decision; do not quietly move costs into an unreported reservation.
No such growth has been built or measured here.

## Qualification and delivery plan for later implementation

Execute as one coordinated implementation campaign after explicit authorization,
with separate reviewable code changes only where they help validation:

1. Fix provisional binary layouts/service identity and coordinator compatibility
   only after the metadata/resource review. Build the smallest owner/coordinator
   path; prove admission refuses on old cores and plain fallback stays usable.
2. Qualify request bounds, version/capability filtering, identity exhaustion,
   stale handles and same-address reload. Use [registry/backend tests](../../tools/test_screen_backend_registry.py)
   and [metadata tests](../../tools/test_monitor_metadata.py) as existing foundations.
3. Exercise routing and echo bytes against independent expected streams, including
   CRT LIST alias/sink routes, ^P during output, direct BIOS calls and honest
   refusal of unqualified spatial paths. Reuse the
   [IOBYTE audit](../../tools/audit_iobyte_routing.py).
4. Exercise all scope/takeover states, parser-busy refusal, right-edge wrap,
   saved-slot independence, partial failures and idempotent Recover. Extend
   [rendition](../../tools/test_screen_rendition.py),
   [save-slot](../../tools/test_screen_cursor_save.py) and
   [portable personality lifecycle](../../tools/test_ansi_portable_lifecycle.py)
   campaigns without treating their current success as TCAP evidence.
5. Qualify busy rejection, the precommit guard, idle movement, rollback and
   generation-last publication with the
   [publication](../../tools/test_monitor_commit_publication.py) and
   [coordinator](../../tools/test_rsxcoordinator.py) fixtures. Confirm a separately
   recovered session is not resurrected after a later failed transaction.
6. Trace RET, jump 0, Function 0, cooked ^C, resident command return, CPX startup,
   SUBMIT, loader failures and failed recovery across RAM/protected-ROM cpmsim
   and native Model 4. Independently inspect returning prompt and LIST bytes.
   Audit maintained Model II before admitting its profile. Record missing physical
   endpoint evidence explicitly.
7. Migrate TYPE, TED and then any resumed HELP work only after their prerequisites
   are qualified; adoption order is a recommendation, not a release assignment.
   Recheck memory/stack and distribution compatibility after integration.

The [second feasibility campaign](TCAP-Placement-Results.md) places the larger
bridge in the optional personality and pays for a seven-byte staged BIOS hook
with seven bytes of equivalent savings. The existing carrier format accepts
228 fixups. This private candidate still needs version/coordinator admission,
global identities and real return-path qualification before production use.

## Binary interface review follow-up

The [interface candidate](TCAP-Interface-Candidate.md) supplies proposed packed
records, operation/status tables, bounded recovered-session tombstones and a
cross-contract consistency review. It refines the logical shapes here but does
not allocate or freeze an ABI. Unknown/partial-effect results and plain emphasis
inside takeover must follow the explicit token rules in that candidate.

## Executed feasibility follow-up

The [measured campaign results](TCAP-Feasibility-Results.md) record the authorized
private implementation slice, 168 CPU/model case executions, resource costs and
carrier/placement blockers. They are evidence beyond the original documentation
phase, not a delivered public facility or approval to migrate utilities.

## Review disposition and completion boundary

The documentation package now contains a source audit, semantic contract, selected
bounded integration direction, proposed interface/identity rules, source change
map, resource ledger and an actionable qualification plan for a later campaign.
Its remaining gaps are measured feasibility, binary allocation and runtime proof;
more prose alone cannot supply them. Engineering review may accept/revise this
direction, but must not label TCAP delivered or resume HELP on that basis.
Implementation scope, actual ABI and release assignment remain pending that review
and a separately authorized implementation phase.
