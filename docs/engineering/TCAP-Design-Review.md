# TCAP proposal: first design review

Status: recommendations for review, 7 November 2026. This is a documentation
review of the [engineering proposal](TCAP-Engineering-Proposal.md) merged in
PR #647. It approves no ABI, implementation or release assignment. HELP stays
on hold. The terminal personality/backend separation and ordinary CP/M console
path remain the compatibility architecture.

## Review outcome

The proposal is suitable as the basis for detailed contract design. Its
strongest constraints are independently reported geometry, admission before
full-screen takeover, and optional styling that cannot compromise readable
text. Three ambiguities need tightening before an implementation specification:
geometry must describe the path actually used, style restoration needs one
logical owner, and abort recovery must distinguish normal restoration from a
safe command-prompt baseline.

This review uses the source baseline cited by the proposal and the merged
main tree `f35f7891`. No runtime experiment, prototype or measured memory
assessment was performed. Recommendations below are not accepted decisions.

## Recommended decisions

| Question | Recommendation | Reason and remaining proof |
| --- | --- | --- |
| Does SCRN's 80×24 descriptor establish TYPE geometry? | Only for fixed-cell operations under their existing contract. Do not infer stream geometry from it. | ANSI normal text uses SCX styled glyph output with endpoint-managed bounds; the same backend retains a separate fixed-cell tracker. A stream profile needs its own established dimensions and wrap behavior. |
| What happens with unknown dimensions? | Keep unknown dimensions explicit. Offer non-spatial logical-line paging for an interactive reader, with continuous output for a noninteractive destination. | A line budget is a utility policy, not a detected screen height. Its value and option syntax stay with TYPE/HELP design. Long logical lines may occupy several physical rows. |
| Does a larger terminal expand TED? | Retain the existing 80×24 editor and its MCON 1.2/SCRN 1.1 admission. | Wider physical geometry alone supplies neither a dynamic editor layout nor permission to change its fixed-cell semantics. |
| Who owns emphasis? | Recommend one logical presentation owner associated with the active console personality, with backend rendering behind it. | The ANSI parser keeps `AP_VALUE`; independent backend changes can diverge from it. Physical placement of the future owner remains undecided. |
| How much nesting is initially required? | Require one active semantic emphasis scope; a second begin is rejected without mutation. Flatten nested strong emphasis in HELP. | This bounds the required contract without claiming a stack exists. Later nesting needs explicit limits, ownership and memory evidence. |
| What does successful normal cleanup restore? | Restore the prior logical rendition of the scope, leaving cursor position and margins unaffected by emphasis itself. | Normal cleanup must not blindly reset all attributes or consume the application's SCX save slot. |
| What does abort recovery restore? | Establish a documented prompt baseline; do not promise exact prior session or screen restoration. | Warm boot can bypass transient code. Current parser reset does not reset all rendering state. A stronger recovery operation needs a separately reviewed contract. |
| Which styles are automatically eligible? | Only known-supported profile mappings, with plain fallback otherwise. | ANSI encoding masks alone do not prove endpoint support; explicit configured policy is distinct from physical detection. |

### Geometry is a property of an output contract

A display snapshot should associate geometry with an output class: fixed-cell
viewport or normal console stream. It must also identify whether output routing
actually reaches that display. A fixed viewport, explicit user configuration
and measured physical geometry remain separate provenance values. Configuration
may establish a usable stream layout only when its wrapping assumptions are
part of that configuration contract.

If either dimension needed for spatial pagination is unknown, use the
non-spatial fallback. A known height with unknown width cannot bound wrapped
rows; a known width with unknown height cannot reserve a prompt row. Discovery
must not issue terminal queries or consume possible query replies as input.

A snapshot needs invalidation rules, not a claim of automatic resize detection.
The resident generation governs service addresses; it does not detect a host
window resize. Until a later design supplies notifications, require the user
to restart/reconfigure after external geometry changes, or expose an explicit
refresh action. Under an undetected change, screen-fit guarantees cannot hold.
Any refresh that changes geometry invalidates row-based replay anchors.

### One logical rendition owner, ordinary text output

For a future emphasis scope, the owner captures prior logical rendition in
storage whose lifetime covers abort recovery. Begin must refuse while a
terminal sequence is incomplete; it must not discard the sequence silently.
A successful begin changes presentation out of band from text, without moving
the cursor. Text continues through BDOS and normal console interception.
End restores the captured logical rendition through the same owner.

These rules avoid asking every utility to know which terminal grammar is
active. A backend may implement a style even when a legacy personality lacks
an equivalent escape sequence; any future owner must coordinate that case
explicitly. An unsupported personality/profile simply offers plain text.
The owner must not alias or overwrite SCX operation 23's reusable slot.

During a scope, independently supplied rendition-changing terminal sequences
need a defined policy. Recommended first contract: the client emits ordinary
text and ordinary console controls only; an attempt to begin/end amid an
incomplete parser sequence fails. Deliberate interleaving of legacy SGR changes
and portable emphasis is outside the initial contract and must not be claimed
as preserved nested state. It needs a later policy before being supported.

Destination changes inside a scope also need explicit handling: styling must
never be encoded into file or LIST bytes. BDOS printer echo receives ordinary
text even if toggled during a span. If routing changes make display ownership
uncertain, suspend enhancements and arrange cleanup through the original owner
while it is still valid. Do not call a stale owner to clean up after removal.
A future design must explain how routing changes are observed; none is claimed
implemented here.

### Recovery cannot depend on a transient exit handler

Source inspection confirms `AN_RESET` clears `AN_STATE` and `AN_COUNT` only.
It does not restore `AP_VALUE`, margins or cursor visibility. `AN_CLEAR`
invokes that parser reset, erases and homes through SCX; it is not a general
session restoration operation. Preserve existing MCON operation 5 semantics
for legacy users; do not silently strengthen it to reset unrelated modes.

A future portable-session recovery mechanism must define its trigger before
command-prompt output, identify owned active state without retaining transient
pointers, and establish the selected prompt baseline. Failed installation must
leave the old profile usable. Movement must rebind owned references; removal
must retire owned scopes before their storage disappears. These are design
requirements, not evidence that manager callbacks for TCAP already exist.

Ordinary scope completion restores the captured rendition. Abnormal return may
instead discard that captured session state and establish a safe prompt
baseline. This distinction avoids promising arbitrary screen restoration while
still requiring a readable prompt. Which margins, rendition, visibility and
cooked-column actions constitute that baseline must be specified per admitted
path before enhanced takeover is permitted.

## Evidence needed before freezing an ABI

| Gate | Required evidence | Disposition now |
| --- | --- | --- |
| Geometry source | Explain how each maintained profile establishes stream geometry and wrapping, or explicitly returns unknown; test fixed and host-managed paths separately. | Static distinction established; runtime qualification remains future work. |
| Destination policy | Trace IOBYTE and printer echo, including changes inside a span; show text-only LIST/file bytes. | Existing paths audited; no coordinated scope mechanism demonstrated. |
| State ownership | Show begin/end, incomplete-sequence refusal, unsupported profile and second-begin rejection without mutation. | Contract recommendation only. |
| Abort recovery | Exercise cooked Ctrl-C, normal return, errors, warm boot, provider movement/removal and rollback; independently inspect the next prompt. | Existing parser reset is insufficient evidence for new scope cleanup. |
| Resource cost | Measure permanent state, loaded page-rounded allocation, first-provider overhead, transient workspace and stack, separately. | No new sizes measured or budget approved. |
| Consumer parity | TYPE replay and right-edge behavior; unchanged TED cell operations/document recovery; HELP readable plain output and decoder costs. | Existing consumers supply requirements; migrations remain unimplemented. |

## Detailed semantic contract draft

The [semantic contract draft](TCAP-Semantic-Contract.md) develops these
recommendations into snapshot, admission, scope, failure and recovery semantics.
It remains proposed and does not allocate an ABI or authorize implementation.

## Next documentation deliverable

Prepare a detailed semantic contract covering snapshot validity, routing,
geometry provenance, single-scope state transitions and prompt recovery. Include
an explicit failure table and per-profile capability/cleanup matrix. Keep
binary layout, service naming, selectors and storage placement unassigned until
the ownership and recovery feasibility gates are resolved. A later bounded
prototype would need implementation authorization; this review does not start
one or resume HELP.

References: [proposal](TCAP-Engineering-Proposal.md),
[ANSI personality](../../src/rsx/ansi.mac),
[ANSI dispatcher](../../src/rsx/ansi-dispatch.inc),
[rendition interpreter](../../src/rsx/screen/rendition.inc),
[Monitor lifecycle](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md),
[backend ABI](Unloadable%20Screen%20Backend%20ABI.md).
