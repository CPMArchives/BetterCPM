# TCAP owner and transaction design

Status: proposed design, 7 November 2026. Develops the
[semantic contract](TCAP-Semantic-Contract.md) and
[routing/recovery study](TCAP-Routing-Recovery-Study.md) through PR #650.
No implementation, prototype, binary ABI, service allocation, release assignment
or measured memory budget is approved here. HELP remains on hold.
Source baseline: main `d7931c13`. This is a source-informed design, not runtime
evidence that the proposed behavior works.

## Recommended bounded design

Place logical portable-session ownership with the selected personality's
optional provider state, coordinating backend rendering through its existing
binding. Keep hardware access and terminal encoding in the backend. Use a
small transient binding for discovery validation and consumer policy, not for
abort-surviving ownership. A profile without the optional owner remains usable
through ordinary console I/O and returns plain/unsupported portable results.

For the first design, reject profile transactions while a portable session is
active. Require the client to End/Release normally or Recover first. Do not add
a fallible display-cleanup callback inside an otherwise disk-free, infallible
commit. This is a recommendation for review; it trades concurrent active-session
compaction for a simpler ownership guarantee. Idle providers retain ordinary
STATEFUL movement and unloading.

Legacy applications retain selectable ADM-3A, VT52 and ANSI personalities and
normal BDOS/BIOS console paths. These restrictions apply to new portable session
ownership, not to an inferred global lock whenever a legacy application prints.
Existing Monitor 5, SCRN and SCX semantics remain unchanged.

## Existing transaction constraints

[Commit engine `r3comit`](../../src/system/r3comit.mac) validates prepared
inputs, performs the memory transformation and publishes generation last.
STATEFUL movement preserves live allocations and repairs declared pointers.
[Finalizer `r3final`](../../src/system/r3final.mac) prepares binding information
and prefetches the resolver before commit.
[Publisher `r3pst`](../../src/system/r3pst.mac) publishes the prepared monitor
target before final generation publication. These paths do not establish a
TCAP cleanup protocol simply because they already repair monitor bindings.

The initial TCAP design should preserve their separation: all fallible checks
before transformation, no arbitrary backend/terminal callback during publication,
and no new generation visible with a stale owner address. Recovery and transaction
publication are separate operations. A successful recovery may visibly change
the display; a later failed profile transaction does not undo that intentional
recovery or resurrect a closed session.

## Logical owner record and lifetime

The following are semantic contents, not a byte layout or resident-memory size:

| Item | Required meaning |
| --- | --- |
| Owner lifetime identity | Distinguishes this selected personality instance from a replacement, including reload at the same address. Address alone is not identity. |
| Session identity | Distinguishes successive activations, so a retired handle cannot close a new session. Exact representation and wrap/exhaustion policy remain an ABI-design obligation. |
| State | Idle, active emphasis-only, active takeover, takeover with emphasis, recovery-required or recovering. |
| Admission assumptions | Rendering class, qualified route/echo policy, geometry/configuration identity and recovery capability used at activation. |
| Prior rendition | One complete logical rendition capture for the emphasis scope; independent of SCX's reusable save slot. |
| Takeover cleanup policy | The admitted prompt baseline and the valid personality/backend path that can establish it. |
| Recovery obligation | Enough owner-resident state to complete or retry cleanup after transient termination, with no pointers into the departing transient. |

Idle has no abandoned transient ownership. Active state must be armed before
the first rendering mutation. If capture/resources cannot be established,
activation fails without output. Scope-only End returns to Idle after restoring
rendition. End inside a takeover leaves takeover ownership active. Release closes
that takeover only after normal cleanup succeeds. Recovery retires both scope
and takeover and establishes the admitted baseline; failure retains a recovery
obligation and blocks further enhancement and profile publication.

No whole-screen buffer, general nesting stack, terminal database or permanent
PDS field is required by this logical record. This is not evidence of zero
memory cost. Provider code/data and page rounding, transient binding, recovery
dispatch and any fixed entry-path changes require separate measured budgets.
Self-pointers and external references must follow the existing STATEFUL repair
rules; no undeclared pointer is hidden in a nominal identity field.

## Transaction protocol

| Phase | Proposed obligation |
| --- | --- |
| Preparation | Validate the prospective profile normally. Observe portable owner state. If any active/recovering/recovery-required session exists, reject with session-busy before live movement or display mutation. |
| Precommit recheck | Recheck owner identity/state and serialize against portable activation. A state change since preparation invalidates the prepared request. A transient declaration alone cannot replace this check. |
| Transformation/publication | With no active portable ownership, use existing infallible movement and rebinding rules. Publish the complete new profile and monitor binding before generation last. No presentation callbacks here. |
| Success | Invalidate old admissions/callable addresses. A new client rediscovers; no active scope handle migrates across this transaction. |
| Rejection/rollback | Preserve old profile, generation, TPA and owner state. Never auto-close a session merely because a profile change was requested. |

The recommended first restriction covers all profile mutations, even removal of
an unrelated module that would compact an owner. It avoids proving which plan
happens to preserve active identity in the first implementation design. A later
extension may allow active-session movement after explicit lifecycle qualification;
it must not silently claim that capability under the initial contract.

The serialization mechanism remains to be designed. It must prevent an activation
between the final idle check and publication without introducing a callback that
recurses into BDOS. Current code inspection does not establish this new guard.
Manager error reporting while a session is active must not unknowingly print
inside a styled span or overwrite a takeover. Return session-busy to the caller;
the caller closes/recovers before displaying an ordinary diagnostic. Existing
manager command paths need an audit before they can be called safe in this case.

This restriction does not prevent normal warm return retaining the same loaded
profile: early recovery closes the session before command-environment activity.
If a reconstruction path actually mutates an RSX profile, it must obey the same
idle-before-publication rule. Cold boot starts fresh; it never follows old handles.

## Routing and echo boundary

The optional owner cannot observe every IOBYTE store merely by intercepting
Monitor output: sink/non-CRT routes may bypass the Monitor entirely. A design
that checks only `AN_OUT` therefore cannot advertise complete route guarding.
Retain the study's distinction between constrained portable clients and arbitrary
legacy or asynchronous page-zero writes.

Recommended initial eligibility requires a qualified normal-console routing
boundary that observes the route before actual output, plus a portable-client
promise not to mutate IOBYTE or issue raw presentation controls during ownership.
No enhancement may be admitted for a profile lacking that qualified boundary.
Where the boundary lives is still open; any proposed fixed code change must be
costed before approval. Direct hardware access and asynchronous unqualified
routing changes remain outside the enhanced guarantee.

Printer echo is separate from destination selection. ^P must continue to work.
CONOUT/LIST alias duplication cannot be hidden. Without a way to notify the
pager before the next affected glyph, a spatial admission must be refused when
CRT echo aliasing can change during output. Alternatives to study are an explicit
layout-invalidation observation or a conservative non-spatial fallback. Polling
only after an entire page is too late to guarantee screen fit. This document
does not choose new polling calls or change TYPE's input behavior.

## Recovery dispatch and baseline

Candidate boundaries remain the early portable/Model 4 reloader reset points
and the CCP pre-prompt guard identified in the study. They must invoke a distinct
portable recovery action when an owned obligation exists. No obligation means
no extra cursor movement, style reset or change to legacy Monitor 5 behavior.

An owner-resident recovery action may repair parser/backend state without
calling BDOS from a callback. Cooked BDOS column synchronization and entry-stack
safety belong to a return-path coordinator outside that callback. This two-part
logical responsibility avoids pretending that the personality alone owns BDOS's
column. The exact dispatch and state-transfer mechanism remains open. It may not
borrow transient workspace, invoke BDOS on an abandoned private stack or emit
style controls to the echoed text path.

Before diagnostics or prompt output, the coordinator must establish the complete
baseline: parser complete, normal readable logical rendition, full default
margins, visible cursor, no pending wrap and a defined prompt start synchronized
with cooked output. Repeat guards on an already-recovered session do nothing.
If any step fails, retain recovery-required and use a documented safe reporting
or halt path; do not claim restored state. Native endpoint failure cannot be
made infallible by naming a baseline. Per-profile newline/start policy and the
failure-reporting path remain qualification requirements, not current features.

## Design choices and qualification gates

| Choice | Proposed disposition | Proof still needed |
| --- | --- | --- |
| Transient-only capture | Insufficient for full scope semantics; retain only client validation/policy there. | No abandoned transient references in recovery. |
| Personality-associated owner | Preferred logical placement, with backend coordination. | Loaded allocation, ABI/version admission, AP_VALUE consistency, save-slot independence and all supported personalities. |
| Active-session profile movement | Reject initially; close/recover explicitly before mutation. | Side-effect-free busy rejection, precommit serialization and unchanged rollback. |
| Global permanent watcher | Not assumed or approved. | Compare actual routing-boundary options and unloaded TPA impact. |
| Recovery | Split rendering repair from safe cooked-column coordination. | All return/diagnostic paths, entry stacks, idempotence, physical screen output and LIST byte capture. |
| Echo-aware spatial paging | Refuse unless pre-glyph invalidation/accounting is established. | ^P inside a page, CRT alias duplication and safe restart without disabling echo. |

Paper checks: request removal during a scope must return session-busy with the
capture intact; End then removal succeeds under ordinary rules. A failed removal
after a separately requested Recover leaves the recovered old profile, not a
resurrected scope. A queued activation cannot pass the precommit boundary. A
same-address owner reload cannot accept an old handle. Repeated warm-return and
prompt guards cannot print extra newlines. These are future acceptance oracles,
not tests performed for this document.

Review should accept or revise the idle-only transaction restriction and logical
owner/coordinator split, then request a bounded costed integration design for
routing observation and return-path dispatch. Binary ABI, implementation scope,
consumer migration order and release assignment remain later decisions.

## Consolidated integration follow-up

The [integration design package](TCAP-Integration-Design.md) specifies the
recommended optional-owner discovery, provisional records and identity policy,
routing eligibility, recovery ordering and source responsibilities together.
Its selected candidate refines the alternatives here without approving an ABI
or claiming measured implementation feasibility.
