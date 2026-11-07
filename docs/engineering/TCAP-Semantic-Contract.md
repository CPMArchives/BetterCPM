# TCAP semantic contract for TYPE, TED and HELP

Status: proposed contract for review, 7 November 2026. This develops the
[engineering proposal](TCAP-Engineering-Proposal.md) and
[first design review](TCAP-Design-Review.md) merged through PR #648.
“Must” and “shall” below specify proposed obligations, not implemented features
or accepted release requirements. No binary layout, service ID, selector,
provider format, storage placement or release assignment is allocated here.
HELP remains on hold. Implementation and runtime qualification are later work.

Baseline: main `1e55fd85`, with the source audit referenced by the proposal.
This document adds semantic design only; no prototype or runtime test was run.

## Compatibility and ownership

Legacy CP/M programs retain ordinary BDOS/BIOS console I/O and their configured
ADM-3A, VT52 or ANSI protocol. Personality selection remains independent of
hardware/host backend selection. The optional portable interface does not
replace the byte stream or require utilities to load a provider for plain text.
Existing Monitor, SCRN, SCX and Function 182 contracts remain unchanged.

TCAP describes the selected display path and mediates portable presentation.
TYPE owns paging/replay, TED owns editing and document recovery, and HELP owns
parsing/navigation and decoder state. Backends retain hardware and encoding
ownership. One logical presentation owner coordinates the personality and
backend; its physical placement is undecided. Callbacks must be serialized,
non-reentrant and free of recursive BDOS calls.

## Terms and semantic operations

An **output path** combines the selected destination, personality/backend
binding and rendering class. Rendering classes are normal console stream and
fixed-cell viewport. Their dimensions and wrapping rules are independent.
A **snapshot** is immutable descriptive data copied for a client; it is not a
pointer lease or permission to change the screen. An **admission** establishes eligibility for
a declared set of operations under that snapshot's assumptions; it does not
activate recovery ownership or authorize use of stale bindings. A **scope**
is one temporary semantic emphasis change owned by the active display path.
A **takeover** is a full-screen client's admitted use of screen operations.
A **prompt baseline** is the defined recovery state, not a saved screen image.

The semantic operations are Discover, Admit, BeginEmphasis, EndEmphasis,
ActivateTakeover, Release and Recover. These names assign neither call numbers
nor entry points.
Ordinary text is still emitted by the utility's existing console output path;
there is no new TCAP text-output operation in this contract.

## Snapshot contents and validity

Discover shall perform no screen mutation, terminal query, input consumption,
provider load or personality selection. It reports independently:

| Fact | Required meaning |
| --- | --- |
| Destination | Display, non-display or unknown, for the caller's intended output route. Include whether interactive input/prompting is appropriate. A loaded backend alone proves neither fact. |
| Binding | Selected personality/backend identities and resident-layout validity information, where discoverable. Unknown identity must remain unknown. |
| Rendering class | Normal stream or fixed-cell viewport; never substitute one class's geometry for another. |
| Dimensions | Rows and columns independently known or unknown. A known value is a positive integer with representability checked. |
| Geometry provenance | Fixed viewport, explicit configuration or verified measurement; describe the output class to which it applies. Zero host SCX dimensions mean unknown/endpoint-managed. |
| Stream behavior | Wrapping model, CR/LF, tab and backspace behavior sufficient for row accounting, or unknown. Do not confuse BDOS's cooked column with a physical cursor query. |
| Operations | Available, unsupported or unknown for each requested operation, including its precise fixed-cell/stream semantics. |
| Presentation | Known-supported semantic emphasis mapping, explicit-attribute support, encoder-only claims, and plain override. Bold and reverse are distinct. |
| Cleanup | Normal restoration and abnormal prompt-recovery guarantees available for the requested use, separately. |

A known dimension that is outside the client's supported range is unusable for
that client; it is not truncated or treated as unknown. Missing information
must not be promoted to positive support. Known descriptor versions, minimum
lengths and relevant masks must be validated before optional fields or calls
are used. Unknown major versions are incompatible; optional unknown extensions
may be ignored only according to their documented versioning rules.

The snapshot describes observations at discovery time. Admission must validate
its binding, route and policy assumptions before mutation. Resident generation
changes invalidate cached callable addresses; clients rediscover according to
Function 182 lifetime rules. Returned descriptor data must be copied if needed
beyond the lifetime of its provider. No transient pointer is retained for abort
recovery. An implementation may use tokens or epochs, but their representation
is deliberately unspecified.

A route, selected profile, geometry configuration, wrap policy or plain-mode
change invalidates affected admissions. A compatible relocation may preserve
logical ownership only through manager-controlled rebinding; an old raw entry
address never becomes valid merely because the logical owner survives.

Host resizing is not detected by resident generation. Without qualified resize
notification, geometry is conditional on the configured endpoint remaining
unchanged. A client offers restart or explicit refresh; a refresh that changes
layout discards spatial replay anchors. No automatic live-resize guarantee is
made. Detection of every external host change is outside this contract.

## Admission and consumer behavior

Admit takes the intended output class, required operations, geometry constraints
and cleanup requirement. All required facts must be usable together before any
screen mutation. Missing optional styling returns plain eligibility, not a
failure to print. Admission itself is read-only and must not silently normalize
an incomplete personality sequence or clear a display.

| Consumer/use | Required admission | Behavior without it |
| --- | --- | --- |
| Ordinary TYPE | None beyond existing console behavior. | Continue existing console output. |
| Spatial TYPE pager | Interactive display; known stream rows/columns and wrapping; safe prompt placement; any clear/home operation it intends to use. | Use a documented logical-line pager on an interactive console, without spatial claims or clear/home; continuous text for noninteractive output. |
| TED | Existing MCON 1.2/SCRN 1.1 admission, 80×24 fixed viewport and required position/cell/erase/visibility operations. Any additional cleanup guarantee must be established separately. | Report the missing essential requirement before screen takeover or file-editing side effects. Existing editor behavior is not retroactively claimed to implement new TCAP cleanup. |
| HELP | Ordinary readable text; interactive eligibility for prompts. Spatial paging requires the same geometry facts as TYPE. | Plain text, logical-line paging when interactive or continuous output otherwise. |
| HELP strong emphasis | Eligible display, a coordinated owner, known-supported mapping, complete parser state, restoration and abort-recovery support. | Omit markup delimiters in prose and print the same text plainly. Preserve literal example text under HELP's parser rules. |

### Activation and admission lifetime

Admission is read-only eligibility. BeginEmphasis and ActivateTakeover must
revalidate it and arm recovery ownership before their first display mutation.
Failure to reserve that ownership yields resource-unavailable without mutation.
No gap may exist in which an enhanced display is active but abort recovery has
no owner. This is a semantic ordering requirement, not a new manager callback
or an allocated operation number.

ActivateTakeover establishes the declared fixed-cell session and its recovery
obligations before TED hides a cursor, clears or renders. A scope may be opened
inside a takeover only if that admitted path supports it; closing that scope
does not release takeover recovery ownership. Recovery aborts the whole portable
session. Release retires takeover ownership only after its declared cleanup
succeeds. An emphasis-only session can retire ownership after successful End.

A retired admission cannot be reactivated. A fresh Discover/Admit is required
after release or recovery. With unchanged assumptions, sequential emphasis
scopes may reuse an eligible admission; handles from earlier scopes remain
invalid. Profile mutation and cleanup must be serialized with activation.

### Paging semantics

Spatial paging requires rows R≥2, columns C>0 and a supported prompt that fits
the chosen rendering rules. Reserve one row, leaving R−1 content rows. Prompt
output and erasure are excluded from content accounting. Use a compact prompt
where necessary; if it cannot fit safely, fall back. Do not assume the current
61-space TYPE prompt erase is valid at every width.

Visible output and hidden replay must share the same row transition function.
It includes expanded tabs, CR, LF, backspace, file separators and pending wrap.
For delayed wrap, filling the final cell alone does not consume the next row;
the next printable glyph may do so, while CR cancels the pending horizontal
wrap. An exact-width line followed by CR/LF must be counted according to the
selected stream, not by adding an unconditional extra wrap. If arbitrary input
control sequences prevent reliable accounting, the client must not claim
spatial fit: use the documented fallback or a separately reviewed safe renderer.
This contract does not silently change TYPE's byte interpretation.

All dimension arithmetic and row counters require checked bounds. Replay keys
include geometry, rendering policy and relevant file identity/position. On
invalidation, discard spatial anchors and restart from a stable source position
or report a restart requirement. Never reuse row ordinals at a different width.
TYPE retains its changed-file handling; HELP separately specifies compressed
member replay and measures decoder workspace. TCAP stores no screenful or
archive history on their behalf.

Pager prompts and diagnostics must be outside authored emphasis: close the
scope before printing a prompt, and reopen semantic emphasis after continuation
only when the remaining text requires it. A failed close requires recovery
before prompting. A logical span crossing a page therefore becomes multiple
physical scopes. Backward replay computes emphasis from source/parser state;
it must not reuse a retired scope handle or replay style controls as text.

Logical-line paging counts rendered logical line breaks, not terminal rows.
Its finite default budget, prompt wording and option syntax belong to the
consumer specification. It makes no promise that long lines or prompts fit an
unknown physical screen. Noninteractive output must not wait for pager keys.

## Emphasis scope state machine

One scope may be active for an owner. Its capture stores prior logical rendition
independently of SCX operation 23. HELP flattens nested strong emphasis before
requesting scopes. A second BeginEmphasis is an error, not an implicit push.
A profile maps strong emphasis to supported bold, supported standout/reverse,
or plain. The mapping must preserve readable text and must not move the cursor.
Explicit bold is never satisfied by relabeling reverse as bold.

| State/event | Result | State after operation |
| --- | --- | --- |
| Idle + eligible BeginEmphasis | Capture prior logical rendition, apply mapping through the owner; return an ownership handle. | Active. |
| Idle + plain/unavailable mapping | Return plain result; make no change and issue no active handle. | Idle. |
| Idle + incomplete parser sequence | Return parser-busy; preserve buffered sequence. | Idle. |
| Active + BeginEmphasis | Return already-active without output or mutation. | Active, original capture unchanged. |
| Active + matching EndEmphasis, parser complete | Restore captured rendition, retire handle. | Idle. |
| Active + EndEmphasis, parser incomplete | Return parser-busy without discarding sequence or capture. Caller must resolve the sequence or invoke recovery before exit. | Active. |
| Idle + EndEmphasis, or wrong/retired handle | Return invalid-scope; no mutation. | Unchanged. |
| Active + explicit Recover or abnormal command return | Retire scope and establish the documented prompt baseline through the valid owner. Exact prior session is not restored. | Idle after successful recovery. |
| Active + binding/route invalidation | Retire/clean owned state before old owner is released or route is published; stale clients cannot invoke cleanup through old addresses. | Idle on the new path, or recovery-required if cleanup failed. |

Successful Begin/End must leave cursor position, pending-wrap behavior, margins,
visibility and the existing SCX save slot unchanged, except for the logical
rendition owned by the scope. Text emitted while active can of course advance
or scroll normally. Normal End restores prior rendition, not the cursor position
at Begin. Do not use a blanket reset as a substitute for prior-rendition restore.

Ordinary text/control output must retain BDOS pause, cancellation, typeahead,
interception and printer-echo behavior. The client may not deliberately mix
legacy rendition-changing sequences, raw backend state changes or profile
changes into a scope. Such interleaving is outside the initial scope contract;
no nested legacy-state preservation is promised. A detected conflict requires
recovery, not guessed restoration. Calls are not permitted from inside output
callbacks.

### Destination and mutation safety

Styling changes travel outside the text byte stream. File and LIST output
receive the same ordinary text without style controls. Toggling printer echo
inside a scope does not change this requirement. IOBYTE/routing changes must be
observed or constrained under an admitted policy; otherwise emphasis cannot be
admitted. A client claiming a console destination is insufficient evidence.

Before a controlled route/provider change commits, cleanup uses the still-valid
old owner; failure must prevent publication or enter a defined recovery path.
Rollback preserves the previous usable binding. Uncontrolled/undetected external
routing changes are not promised safe merely by snapshot checks. The later
implementation design must demonstrate the observation and serialization
boundary before advertising enhanced eligibility.

Preflight rejection shall have no mutation. If applying/restoring presentation
can fail after partial output, the owner must either roll back completely or
mark recovery-required and establish the prompt baseline before further enhanced
use. It must not report success or quietly return plain while leaving a style
active. Plain fallback is safe only after cleanup succeeds. On unrecoverable
cleanup failure, report the failure through a safe available console path and
refuse further enhanced use; never claim the prompt baseline was restored.

## Normal release and abnormal recovery

Release requires no open emphasis scope and the cleanup promised at admission.
An active scope yields scope-active without mutation; callers End or Recover
first. Full-screen normal release uses its declared console baseline unless a
separate, explicitly supported prior-session restoration contract was admitted.
Exact previous screen contents and arbitrary host modes are excluded.

For a TCAP-admitted enhanced session, recovery must occur before returning
command-environment text, even when Ctrl-C/warm boot bypasses transient cleanup.
The recovery owner must not depend on transient buffers or an exit handler.
The proposed prompt baseline is:

- No incomplete terminal sequence from the departing client.
- Default, readable logical rendition with backend/personality agreement.
- Full default scrolling region and normal visible console cursor behavior.
- Pending wrap canceled and a defined prompt start established by the selected
  console path, with cooked BDOS column state synchronized to that start.
- No consumption of ordinary typeahead or alteration of file/DU/decoder state
  merely to repair presentation; consumer cleanup retains those responsibilities.

Recovery does not require clearing the screen and does not restore previous
screen contents. Any cursor movement/newline required to establish the prompt
start must follow the path's documented policy. It must not emit presentation
controls to LIST. This stronger recovery applies only to admitted portable
sessions. Preserve legacy MCON operation 5 behavior for other callers; do not
silently turn its parser reset into a universal mode reset.

The [interface candidate](TCAP-Interface-Candidate.md) bounds repeat-recovery
recognition to the latest successfully recovered session until a newer activation
or owner-validity transition. Plain Begin during takeover leaves the takeover
token intact and creates no emphasis token. A partial activation failure must
return an identifying token when possible while retaining owner-resident recovery
state even if the transient aborts before receiving it.

Recover is idempotent with respect to owned recovery work: after successful
recovery, repeating it for the retired session reports already-recovered and
performs no output, cursor movement or mode reset. Recovery of an unrelated or
unknown session is invalid-session with no mutation. A recovery-failed session
retains a recovery-required state for a safe retry or system recovery path;
it is not reopened for ordinary enhancement. These rules do not make repeated
legacy Monitor resets into TCAP recovery.

If both takeover and emphasis are active, recovery retires the scope and
takeover together. Normal End restores the enclosing takeover's rendition;
normal Release must still establish the declared exit baseline. Ownership
metadata must distinguish eligibility, active takeover and active scope without
requiring transient storage to survive command return.

## Failure contract

These result names are semantic categories, not numeric codes. Results include
whether a scope/admission remains active and whether recovery is required.

| Condition | Required result and caller action |
| --- | --- |
| No provider/optional service | Unavailable; plain text remains usable. TED refuses missing essentials. |
| Unsupported operation or explicit attribute | Unsupported; omit optional effect or refuse the required takeover. |
| Unknown route, geometry or endpoint support | Unknown for that fact; do not infer support. Select the applicable fallback. |
| Incompatible/malformed metadata | Incompatible; do not follow unvalidated entries or read beyond validated fields. |
| Dimension outside client range | Unusable-geometry; no truncation or unchecked arithmetic; fallback/refusal. |
| Binding, route or policy no longer matches admission | Stale; discard callable addresses and affected replay anchors, rediscover. Owned cleanup follows lifecycle rules, not the stale handle. |
| Incomplete personality sequence | Parser-busy; preserve parser state; no Begin/End mutation. |
| Second begin, wrong handle or end without begin | Scope-state error; leave existing owner/capture unchanged. |
| Invalid/retired admission or unknown recovery session | Invalid-session; do not activate or reset an unrelated display. |
| Repeat Recover after successful recovery | Already-recovered; no output or mutation. |
| Release with active scope | Scope-active; End or Recover before release. |
| Insufficient scope/recovery resources | Resource-unavailable before mutation; plain fallback or takeover refusal. |
| Partial apply/restore failure | Recovery-required; roll back or recover before plain continuation. Never report successful restoration without evidence. |
| Recovery cannot complete | Recovery-failed; disable enhanced admission and report through a safe path. No successful-baseline claim. |

## Current profile evidence versus proposed eligibility

This matrix summarizes existing source evidence, not new TCAP certification.
Personality/backend pairs still require their documented admission and platform
qualification. An available backend does not identify the active personality.

| Path/profile | Existing geometry and operations | Cleanup evidence and TCAP disposition |
| --- | --- | --- |
| Basic console, no monitor | Usable ordinary console; no general TCAP stream geometry established by this audit. | Plain output supported. No new scope or enhanced-recovery guarantee inferred. |
| Model 4 SCRN backend with admitted personality | SCRN fixed viewport 80×24; SCX reports 24×80, all current control operations, reverse/conceal, no physical bold/color. | Candidate for fixed-cell TED and known reverse mapping. Normal-stream wrapping and coordinated scope/recovery still need profile-specific proof. |
| ANSI-host SCRN backend with admitted personality | SCRN fixed viewport 80×24; SCX zero dimensions denote endpoint-managed geometry. Attribute masks describe encodings. | Candidate for TED fixed cells; stream dimensions/physical styles need explicit profile facts. No automatic host measurement or scope cleanup inferred. |
| Portable ANSI personality | Normal printable output uses SCX glyph 21; logical rendition held in AP_VALUE. AN_RESET clears parser state/count. | Supports the state-ownership analysis; reset alone does not satisfy the proposed prompt baseline. |
| ADM-3A or VT52 personality | Preserve each personality's existing protocol and admitted backend contract. | Do not transfer ANSI ownership/cleanup claims automatically. Qualify semantic emphasis or return plain. |
| Model II maintained port | Use actual maintained console/backend facts when audited. | No TCAP capability or cleanup certification asserted by this document. |
| File, LIST or uncertain routing | No eligible enhanced display established. | Text-only output; no spatial pager or emphasis controls. Interactive eligibility is evaluated separately. |

## Worked semantic review cases

These are paper walkthroughs and future acceptance oracles, not runtime test
results. They expose the expected decisions without choosing implementation.

| Case | Required sequence and observable outcome |
| --- | --- |
| TYPE, established 80×24 delayed-wrap stream | Discover/Admit the stream; budget 23 rows; count 80 printable cells followed by CR/LF as one completed line, without a duplicate wrap. Prompt outside content accounting. Backward replay uses the same transition rules. |
| TYPE, host SCX dimensions zero | Keep stream dimensions unknown even if SCRN reports 80×24. Interactive invocation selects logical-line paging; noninteractive output continues without waiting. No terminal query or clear/home is emitted to guess geometry. |
| TYPE, explicit refresh from 80 to 100 columns | Retire affected spatial admission and row anchors; rediscover/admit; restart from stable source position under utility policy. An old row ordinal cannot select the new page. |
| TED, missing required operation | Admit refuses without clearing, hiding the cursor or modifying a file. Report the requirement through existing console output. |
| TED, complete fixed-cell eligibility | Read-only admission alone changes nothing. ActivateTakeover arms cleanup before the first screen operation; position/cell/erase retain legacy semantics. Release establishes the declared console baseline. |
| HELP, Model 4 known reverse mapping | Begin captures prior rendition, applies semantic reverse, and text follows BDOS console output. End restores the prior record, including previously unsupported stored attributes, without restoring the old cursor position. |
| HELP, encoder-only bold support | Return plain unless an explicit eligible profile establishes a supported mapping. Print the prose without Markdown delimiters; no active handle exists to close. |
| HELP span crosses a page | End before the pager prompt, preserve parser/source emphasis state, then Begin a fresh scope for remaining emphasized text after continuation. The prompt is not emphasized by the author's span. |
| Second Begin or stale End | Reject without replacing the first capture, touching the save slot or changing output. The valid original scope can still end normally. |
| Parser incomplete at Begin/End | Reject without discarding the sequence. End leaves its scope active; resolve or Recover before leaving. No plain-success claim is allowed while owned style remains. |
| Printer echo toggles during HELP emphasis | Printed glyphs reach LIST through the existing echo path; no presentation controls reach it. Begin/End must not use the echoed text channel for controls. |
| Cooked Ctrl-C inside a scope | Warm-return recovery uses valid owner state, retires the session and establishes the baseline before the next prompt. No transient exit handler is required. A repeat recovery has no effect. |
| Provider relocation while owned state exists | Only an admitted manager-controlled transition may preserve logical state; rebind through its lifecycle. Old callable addresses remain invalid. Scope ownership is not inferred from a reused address. |
| Controlled route change or removal | Clean through the old valid owner before publication, or prevent commit/use a defined recovery path. Do not send cleanup to the newly selected unrelated endpoint. |
| Restore fails after partial effect | Return recovery-required, block enhanced use and recover before plain continuation. If recovery fails, report that fact rather than reporting restored state. |

## Remaining review decisions

The following cannot be settled by documenting existing interfaces alone:

| Decision | Required answer before implementation design |
| --- | --- |
| Route observation | Which paths can enforce or observe routing changes, and what happens for direct IOBYTE writes? Restrict enhanced eligibility when this cannot be guaranteed. |
| Recovery storage/trigger | Which owner survives transient abort, and which existing command-return paths invoke its recovery before prompt output? Do not alter MCON 5 semantics implicitly. |
| Prompt baseline policy | For each admitted profile, specify the exact start position/newline, full-region reset, visibility, rendition and cooked-column coordination; show LIST remains free of controls. |
| Failure completion | Identify a safe reporting/retry path after partial restore failure. No arbitrary host-terminal recovery is guaranteed. |
| Consumer policy | TYPE/HELP must settle logical-line budgets, prompt keys and restart behavior in their own specifications. These do not block semantic review but do block claims of a complete utility migration design. |

Until these answers and cost evidence are reviewed, this is a detailed semantic
proposal, not an implementation-ready engineering specification.

## Routing and recovery source follow-up

The [routing and recovery study](TCAP-Routing-Recovery-Study.md) audits IOBYTE,
CRT LIST aliasing and existing command-return reset boundaries. Text-only LIST
means no TCAP-added presentation controls; it does not promise a visually
independent device when LIST aliases the same CRT. Echo duplication must be
included in spatial row accounting or invalidate spatial pager eligibility.
The study recommends candidate boundaries, not implemented cleanup hooks.

The [owner/transaction design](TCAP-Owner-Transaction-Design.md) recommends
rejecting profile mutations while portable ownership is active as an initial
implementation-design restriction. It narrows the possible lifecycle mechanism
without claiming active-session movement support or changing legacy contracts.

## Gates before an implementation specification

Review and accept or revise the semantic choices above, especially single-scope
behavior and the prompt baseline. Then resolve how routing invalidation is
observed, who owns persistent recovery state, how takeover cleanup is admitted,
and how partial failure reaches a safe console. A later design must map those
requirements to existing discovery and manager lifecycle without weakening
legacy contracts or bypassing console behavior.

Measure permanent growth, optional loaded/page-rounded allocation, first-provider
overhead and transient stack/workspace separately against the 1.1 memory policy.
No memory budget or feasibility claim is approved here. Qualification must cover
all failure rows, scope transitions, prompt recovery, exact-edge paging/replay,
plain/file/LIST byte equality, printer toggles and manager movement/rollback on
cpmsim RAM/protected-ROM and Model 4; include Model II once audited. Existing
backend tests are evidence to reuse, not evidence that this new contract passes.

Implementation scope, utility migration order, ABI allocation and release
assignment remain subsequent decisions. This document does not start a prototype
or resume HELP development.
