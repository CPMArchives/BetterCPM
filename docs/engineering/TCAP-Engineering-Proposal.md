# TCAP engineering proposal for TYPE, TED and HELP

Status: draft for review, 7 November 2026. Documentation only. This proposes
an application contract; it is not an accepted ABI or a completed TCAP facility.
Implementation scope, release assignment and utility migration order remain
undecided. HELP remains on hold under its existing design checkpoint.

## Purpose and boundaries

Give aware utilities one conservative account of the active display, while
preserving ordinary CP/M console behavior. A terminal personality defines the
protocol an application sees; a backend renders it on hardware or a host.
Users retain ADM-3A, VT52 and ANSI selection for legacy applications. Legacy
programs keep their existing BDOS/BIOS console calls and terminal sequences.
The optional portable interface neither replaces that path nor requires a new
provider merely to print text. Hardware access remains backend-owned.

TYPE owns paging and file replay; TED owns editing and document recovery;
HELP owns Markdown parsing, navigation and data lookup. TCAP supplies display
facts, operation admission and presentation lifecycle. It does not choose HELP
syntax, change pager keys or add terminal emulation protocols.

## Audit baseline and method

Static audit of repository tree at `8cd1a6ad69367c743fa9e4dd7b881673869879e4`,
the reviewed head of PR #646. Source inspection and existing qualification
records are evidence for this proposal; no runtime tests or prototypes were
executed for this draft. Historical sections in the backend ABI describe
successive checkpoints, so their earlier masks and sizes are not current
capability declarations. Consult current source and final admission rules.

| Layer or consumer | Observed interface and behavior | Consequence for TCAP |
| --- | --- | --- |
| Resident discovery | Function 182 uses a caller-owned 20-byte request with service ID, required major/minor and capability mask. Returned entry addresses are valid for the resident-layout generation. | Reuse discovery and lifetime rules; do not invent a parallel service registry. Missing or incompatible services are ordinary admission results. |
| Monitor | BIOS console vectors dispatch through the active monitor or basic fallback. MCON operations 0–5 cover output, status, input, private cursor, clear/home and command-return reset. | A screen backend is not the whole active console profile. Preserve interception and personality state. Reset is not arbitrary state restoration. |
| SCRN | Current backends advertise callable SCRN 1.1. Operation 12 still returns the legacy nine-byte `SCR`, version 1.0, 24 rows, 80 columns and operation mask. Operations 6–15 provide fixed viewport cell operations. | Callable version and descriptor version are distinct. The fixed viewport is usable geometry for that interface, not measured host dimensions. |
| SCX | Operation 16 returns `SCX`, 1.0, length 12, rows/columns, operation mask and rendition/color masks. Current masks cover operations 17–24. Model 4 reports 24×80, reverse/conceal and no colors. Host reports zero dimensions, flags FFh and colors 7. | Host zero means endpoint-managed/unknown, not detected size. Encoding an ANSI style does not establish physical endpoint support. |
| SCX state | Operations 20/21 set a nine-byte rendition and write styled ASCII. Operation 23 offers one reusable cursor/rendition slot. Margins and visibility are excluded; restore clears pending wrap. | No general nested style stack or exact screen restoration exists. Canonical rendition and personality state need coordinated ownership. |
| TYPE | `TP_PUT` emits through BDOS 2; prompt uses 9; commands poll 6. Row counting assumes 80 columns and 23 content rows. Four-byte row anchors drive replay, including rescanning rather than retaining every page. | Geometry affects wrapping, page anchors and replay together. Parameterizing just the prompt interval is insufficient. |
| TED | `TE_START` requests MCON 1.2 and SCRN 1.1, compares the fixed SCR descriptor and checks required mask bits. Rendering uses position 6, cell 7, erase-line 8 and visibility 15. | Existing full-screen admission is a strong starting point; do not weaken it to “provider present.” Current editor layout remains 80×24. |
| TED exit | Exit shows the cursor, invokes monitor clear/home and restores drive/user/DMA. It does not capture and restore an arbitrary prior display session. | State the supported exit baseline honestly; restoring prior screen contents requires a different contract. |
| HELP | The held reader design requires semantic strong emphasis and plain readability; a production reader is not yet delivered. | Treat HELP as a consumer requirement, not implementation evidence. |

### Three output traces

**Console line:** BDOS 2/9 → cooked output (`UB_COCHAR`) → `UB_PUT` → BIOS
CONOUT → active monitor personality → backend → display. Cooked handling
expands tabs, tracks its own column, polls pause/cancel controls and can echo
text to LIST. Direct BIOS access is also covered by monitor hooks; it does not
supply BDOS cooked behavior. IOBYTE routing matters before assuming CONOUT
reaches the screen. A direct SCRN call does not traverse this entire path.

**Paged TYPE:** selected file bytes pass through TYPE's renderer and `TP_PUT`;
visible bytes use BDOS output while hidden replay counts rows. `TP_INDENT`
uses explicit clear/home and CR to synchronize the cooked column. Backward
paging subtracts 23 rows and replays the selected stream. Geometry and wrap
rules must be the same in visible rendering and hidden counting, including
file separators, tabs, CR/LF, backspace and exact right-edge transitions.

**TED update:** Function 182 binds SCRN after MCON admission; `TE_RENDER`
positions and erases individual rows, then writes fixed cells and restores
cursor visibility. Cell operation 7 clamps at the right edge. SCX styled glyph
21 uses delayed wrap instead. Substituting 21 for 7 would change rendering
semantics and is not proposed.

Source references: [BDOS console](../../src/bdos/unified.mac),
[BIOS dispatch](../../src/bios/bios.mac),
[TYPE pager](../../src/utilities/common/typepage.inc),
[TED frontend](../../src/utilities/ted/frontend.mac),
[Model 4 backend](../../src/rsx/screen/model4.mac),
[host backend](../../src/rsx/screen/ansi-host.mac), and
[ANSI personality dispatcher](../../src/rsx/ansi-dispatch.inc).

## Proposed application contract

The following names describe semantics for review, not allocated service IDs,
selectors, binary fields or assembly calling conventions.

### Discover a display snapshot

Discovery is read-only: it must not emit terminal queries, consume input, load
a provider, change personality or alter rendition. Report independently:

- Destination eligibility: active console display, non-display, or unknown.
  Provider presence alone does not prove that the caller's output reaches it.
- Geometry for the requested output path: usable rows/columns plus provenance
  (fixed viewport, explicit configuration or verified measurement), or unknown.
  Describe each unknown dimension separately. Zero must never be used as an
  arithmetic width or height. A configured viewport is not a physical measurement.
- Required operations and their semantics: fixed cells versus stream wrapping,
  cursor positioning, erasure, visibility and available cleanup guarantee.
- Presentation: semantic emphasis mapping, explicit physical attributes, and
  whether support is known or only encodable. Bold and reverse are distinct.
- Binding lifetime: the current resident generation and profile assumptions.
  No utility may retain raw service pointers across reconstruction.

Results distinguish usable, unsupported, unknown, incompatible metadata and
stale binding. These are semantic categories, not proposed numeric error codes.
Unknown is not permission to assume ANSI or 80×24. Validate known descriptor
versions, lengths and masks before reading fields or invoking optional calls;
unknown major versions must not be guessed. Preserve the legacy ABI unchanged.

### Admit an operation before changing the display

A caller declares required geometry, operations and cleanup policy. Admission
must either establish them together or refuse without display mutation.
Optional emphasis never blocks line-oriented output. Full-screen clients must
refuse before takeover when an essential operation is unavailable or unknown.

| Consumer | Required contract | Fallback |
| --- | --- | --- |
| TYPE without paging | Normal console stream | Existing readable console output; no TCAP requirement. |
| TYPE with screen paging | Usable dimensions for its actual stream, matching wrap model and a prompt that fits | Proposed conservative fallback: explicitly identify unknown geometry and use logical-line paging without clear/home or spatial-page guarantees. Exact default line budget and user override require review. |
| TED | Existing 80×24 fixed viewport, required MCON/SCRN versions, position/cell/erase/visibility and documented exit cleanup | Diagnostic through normal console before takeover. Larger physical screens do not imply a larger editor. No dumb-terminal editor is promised. |
| HELP | Plain text through normal console; known geometry only for spatial pagination | Plain emphasis-free text; unknown geometry uses logical-line paging or continuous output under reader policy, clearly distinguished from screen-fit pagination. |

For a known R×C viewport, require R≥2 and positive C before computing a
content budget of R−1 rows. Prompt text must fit C, with a compact equivalent
where necessary; prompt erasure may not assume TYPE's current 61 spaces.
If no safe prompt fits, use the non-spatial fallback. Bounds, counters and
multiplication must be checked; descriptor dimensions cannot silently overflow
current byte-sized pager state.

A worked TYPE case: 24×80 permits 23 content rows and one prompt row; 40×100
permits 39 content rows only if the selected stream contract establishes that
geometry and wrapping. Host SCX's zero dimensions do not establish 40×100.
Define exact-edge pending-wrap behavior before counting: an 80-cell line
followed by CR/LF must not accidentally consume two display rows. TCAP reports
the behavior; TYPE implements and tests its matching counter.

Replay anchors must be associated with geometry and rendering policy. Under
an unchanged snapshot, backward replay reproduces the page boundary without
a full-screen buffer. If geometry/profile changes, discard spatial anchors
and restart from a stable file position or offer a documented restart; never
reinterpret an old row ordinal at a new width. TYPE retains its existing
changed/vanished-file policy. HELP must separately measure compressed-member
replay and decoder workspace; TCAP supplies no archive history buffer.

### Scope emphasis through the normal console path

HELP interprets `**read-only**` as plain text plus a semantic emphasis span.
The profile may select known-supported bold, supported reverse, or plain.
Explicit bold must not be reported supported merely because reverse works.
Encoding support with unknown endpoint behavior is insufficient for automatic
physical-support claims; an explicit configured profile may supply that policy.

A proposed presentation scope captures its prior logical rendition, applies a
nonessential change without moving the cursor, emits ordinary text through
the normal console route, then restores that prior rendition. It must coordinate
personality and backend state, including an incomplete parser sequence, and
must not borrow SCX's shared save slot. Nested scopes must either be bounded
and supported explicitly or refused before mutation; plain fallback remains
available. A blind “SGR reset” does not restore an enclosing scope.

File and LIST output contain text without presentation controls. BDOS printer
echo must continue to receive text only, including when toggled during a span.
Sending escape bytes through BDOS 2/9 would echo those controls to LIST; setting
backend rendition directly risks disagreement with the ANSI personality's
`AP_VALUE` record. Neither shortcut satisfies this contract. Until a coordinated
console presentation mechanism exists and is qualified, HELP uses plain text.
No new BDOS selector or Monitor operation is assigned by this proposal.

### Leave a defined console state

Normal return and handled errors close active scopes and restore their prior
logical rendition. Full-screen takeover declares a supported exit baseline:
parser synchronized, normal console cursor behavior, known margins/rendition
and cooked-column synchronization as required by the selected path. Exact
prior screen contents, host terminal modes and arbitrary external state are
outside this minimum proposal. A future exact-session restoration option would
need explicit capture, ownership and cost evidence.

Ctrl-C during cooked output can enter warm boot before transient cleanup runs.
Therefore transient exit code alone cannot fulfill the lifecycle requirement.
Command-return/warm-boot recovery must cancel any scope without dereferencing
transient storage and establish the documented prompt baseline. Existing MCON
operation 5 resets parser state; this draft does not assume it already repairs
all proposed presentation state. Failure to provide that guarantee disables
enhancements, not plain text. Provider removal/change must close or invalidate
owned state before publication and respect manager rebinding/rollback rules.
Callbacks remain serialized and must not call BDOS recursively.

## Implementation choices to investigate later

| Choice | What it can reuse | Remaining obstacle |
| --- | --- | --- |
| Small transient binding over Function 182 and SCRN/SCX | Discovery validation, TED admission, geometry normalization, pager policy and plain fallback; no mandatory resident allocation | Cannot alone guarantee warm-boot scope cleanup or synchronize independently owned personality state. |
| Coordinated optional Monitor presentation extension | Console interception and personality/backend ownership, with typed controls outside the text stream | Requires a reviewed lifecycle, destination/echo policy, service versioning and measured provider changes. No extension selected. |
| Terminal-specific escape strings in each utility | Existing console text calls | Does not solve personality selection, printer-control leakage, restoration or unknown geometry; unsuitable as the shared contract. |

Recommended next design study: retain existing discovery and fixed-cell TED
calls; prototype only the geometry normalization and coordinated emphasis
boundary needed to choose between the first two options. This is a proposed
future study, not authorization to implement it or a release commitment.

## Memory and qualification gates

Keep unloaded TPA, optional provider allocation and transient workspace as
separate budgets under the [1.1 memory policy](1.1-ENGINEERING-SPECIFICATION.md).
Do not add permanent core or PDS state merely to decorate output. Current
provider historical sizes omit later manager/cache accounting in some records;
measure the actual installed profile, alignment and first-provider overhead.
No new byte estimate is asserted without a build. Measure code growth, stack
high-water use, scope records, pager counters and HELP decoder/replay memory.
Unloading must restore each platform's qualified unloaded baseline.

Future acceptance evidence must include:

1. No provider, missing service, old revision, malformed/short descriptor,
   unknown versions, insufficient masks and explicit plain override. Discovery
   produces no output or input consumption; refusal leaves display unchanged.
2. TYPE known 80×24 and wider/narrower viewports, unknown and partially known
   geometry, R≤1, oversized values, prompt fitting, tabs, CR/LF, backspace,
   exact-edge wrap, file boundaries, backward replay and geometry invalidation.
3. TED admission on each supported personality/backend pairing; no takeover on
   refusal; fixed-cell right edge, erase/redraw and cursor recovery on normal
   exit, I/O failure and cancellation. Preserve document recovery semantics.
4. HELP identical readable text with bold, reverse and plain rendering; nested
   or rejected scopes; mixed ordinary console output; no style controls in
   file/LIST output, including printer echo toggled inside a span.
5. Interrupted output, Ctrl-C/warm boot, incomplete personality sequences,
   margins, cursor visibility, pending wrap, saved-slot ownership, movement,
   unload rejection and transaction rollback. Verify the returning prompt.
6. Reuse backend, SCX, personality and manager suites; add independent rendered
   screen and captured-output checks. Run cpmsim RAM/protected-ROM and Model 4
   native display campaigns; qualify Model II when its maintained backend path
   is available. CPU-model success alone is not native visual qualification.

## Decisions requested at proposal review

Agree the snapshot/result semantics, conservative unknown-geometry fallback,
fixed 80×24 TED admission, and text-only printer policy. Settle whether the
minimum restoration guarantee is the defined console baseline above or a more
expensive exact prior-session contract. Choose scope ownership and abort
recovery only after a bounded feasibility study. Assign a binary ABI, provider
format, implementation scope and release only in a subsequent reviewed design.
The engineering proposal itself remains a draft until that review occurs.

## Consolidated design package

This document is the entry point for the complete documentation proposal.
The linked documents supply the detailed contract and source evidence; they
are not separate requests to start another design workstream. Review the
package together. No claim of implementation readiness, accepted ABI or
completed runtime qualification is made.

| Design responsibility | Controlling proposed document |
| --- | --- |
| Candidate packed interface, buffer/token rules and cross-contract review | [Interface candidate](TCAP-Interface-Candidate.md) |
| Complete proposed integration, records, identity rules, source responsibilities and delivery gates | [Integration design package](TCAP-Integration-Design.md) |
| Application-visible operations, failures, geometry, paging and lifecycle | [Detailed semantic contract](TCAP-Semantic-Contract.md) |
| Owner lifetime, activation, transaction ordering and coordinator split | [Owner and transaction design](TCAP-Owner-Transaction-Design.md) |
| Existing route behavior, CRT LIST aliasing and command-return evidence | [Routing and recovery source study](TCAP-Routing-Recovery-Study.md) |
| Rationale for the conservative semantic choices | [First design review](TCAP-Design-Review.md) |

Where the earlier alternatives in this proposal differ from the detailed
recommendations, use the following consolidated design direction for review:

- Retain Function 182 discovery and existing SCRN/SCX operation contracts.
  Add no utility-specific terminal grammar or automatic provider loading.
- Keep portable owner state associated with the active personality; retain
  hardware rendering in the backend. Transient bindings own validation and
  utility policy, not abort-surviving capture.
- Separate read-only admission from activation. Arm owner-resident recovery
  before display mutation. Use one emphasis capture independent of SCX 23;
  close it around prompts and diagnostics.
- Initially reject profile mutations during portable ownership. End/Release
  or Recover first; keep fallible display cleanup outside manager commit.
- Distinguish fixed-cell geometry from stream geometry, and encoder support
  from known endpoint support. Unknowns yield readable fallbacks.
- Preserve printer echo. CRT alias duplication invalidates spatial guarantees
  unless accounted for before affected output; it does not justify disabling ^P.
- Recover rendering through the owner and cooked-column/start coordination
  through a safe return-path coordinator. Preserve legacy Monitor 5 behavior.

These are proposed engineering choices, not maintainer acceptance inferred
from merging documentation.

## Integration responsibilities and ordering

The candidate integration boundary for route eligibility is the normal BIOS
console router before destination dispatch, where both CRT and bypass/sink
routes can be classified. A Monitor-only check is insufficient because some
routes never reach it. The router must not invoke BDOS or accept arbitrary
transient callbacks. Normal output retains the existing BDOS interception and
flow-control path. Exact entry dispatch and permanent code cost remain subject
to feasibility measurement; no new vector is assigned here.

Echo-related spatial eligibility needs information from the BDOS output-flow
layer, where ^P is consumed and the echo flag changes. Proposed conservative
initial policy: if CRT echo aliasing can change during an interactive page and
there is no qualified pre-glyph layout observation, spatial paging is ineligible
for that path. Logical-line paging remains available. This avoids pretending
that a page-end poll repairs rows already displayed. A later richer accounting
path can be reviewed independently.

The recovery coordinator belongs logically to command return. It must run on
a valid system/reloader stack before diagnostic or prompt text. Candidate
insertion boundaries are both reloader CRBODY entries and the CCP prompt guard.
The owner performs rendering repair without recursive BDOS; the coordinator
synchronizes cooked-column state through a separately defined safe system
operation. Writing another subsystem's private column byte from a personality
is not an acceptable shortcut. Dispatch and state-transfer representation stay
unallocated until the implementation feasibility gate.

Recovery ordering for an owned session is: mark recovery in progress; discard
its parser continuation; normalize logical/backend rendition; reset margins and
visibility; cancel pending wrap and establish the profile's prompt start;
synchronize cooked-column state; retire ownership. Failure retains recovery-required
and prevents successful-baseline claims. Repeated guards after success are no-ops.
The path's exact start/newline policy must be qualified; no arbitrary host mode
or prior screen restoration is promised.

Profile transactions prepare and validate normally, then reject active,
recovering or recovery-required portable ownership. Revalidate idle owner state
at the serialized precommit boundary. Only then transform memory, rebind the
prepared monitor/backend and publish generation last. No terminal I/O, fallible
cleanup or active-handle migration occurs inside publication. A failed request
leaves the old profile and owner intact. A separately completed recovery is
not rolled back by a subsequent failed profile request.

## Consumer acceptance and qualification package

| Consumer | Design completion criterion | Evidence required later |
| --- | --- | --- |
| TYPE | Correct geometry class, shared visible/replay transition model, prompt budget and fallback/invalidation rules. | Exact-edge CR/LF, tabs/backspace, changed files, echo alias/toggle, narrow/unknown dimensions and backward replay. |
| TED | Existing 80×24 admission and typed cell semantics retained; recovery armed before takeover. | No mutation on refusal; normal and abnormal cleanup; document recovery unchanged; native visual validation. |
| HELP | Semantic strong emphasis through ordinary console text, single-scope lifecycle, plain readability and prompt boundaries. | Bold/reverse/plain text equivalence, no TCAP controls in LIST/file bytes, decoder/replay memory and cancellation. HELP remains held until the facility is delivered. |

Qualification must distinguish CPU models, wire captures, rendered-screen
oracles and actual native display campaigns. Use cpmsim RAM/protected-ROM and
Model 4; add maintained Model II profile evidence before making claims for it.
The semantic contract's failure table and worked cases are the acceptance
inventory. Test no provider, incompatible metadata, rejected activation,
stale/reused handles, partial cleanup failure, RET/Function 0/jump 0/cooked ^C,
resident command return, startup/SUBMIT and loader/manager error paths. No result
in this list is claimed performed for this proposal.

## Remaining feasibility gates and review disposition

The [integration design package](TCAP-Integration-Design.md) resolves the
documentation alternatives into one bounded candidate, including proposed
request/identity rules and concrete source integration responsibilities.
The documentation proposal is complete enough for a single engineering review.
The remaining work below requires implementation investigation or measurement;
it must not be represented as another completed static audit.

| Gate | Required result before approving an implementation specification |
| --- | --- |
| Routing/echo coverage | Show actual pre-dispatch observation and conservative spatial eligibility on every admitted path; handle or exclude asynchronous/direct-hardware changes honestly. |
| Return-path coverage | Prove owner reachability and valid stacks before every diagnostic/prompt path; define safe failure reporting and exact per-profile prompt start. |
| Transaction serialization | Demonstrate idle checks cannot race activation and busy errors do not print into active takeovers/scopes. |
| Owner representation | Choose identity exhaustion rules, version/capability admission, pointer repair and recovery state lifetime without transient pointers. |
| Resource costs | Measure fixed growth/unloaded TPA, optional page-rounded provider and first-provider overhead, transient code/workspace and stack separately. No reduction of qualified memory policy is implicitly approved. |
| Binary interface | Only after the above, allocate service/version/operation identifiers, record layouts, calling conventions and bounded argument ranges. |

Recommended review disposition: accept or revise the consolidated semantic and
ownership direction as a proposal, retain HELP's hold, and leave implementation,
ABI allocation, migration scope and release assignment undecided pending those
gates. Publishing this package does not authorize a prototype or code changes.

## Final documentation review disposition

The design package through PR #653 was reviewed for state/token consistency
and recovery-entry completeness. The final corrections distinguish End inside
a takeover from scope-only End, allow the takeover's required zero scope serial,
and document fatal pre-coordinator loader failures without a successful recovery
claim. Candidate record sizes are design values; no memory cost is measured.

The documentation phase is ready for a single engineering acceptance/revision
review. It does not need another speculative prose sequence to stand in for
implementation evidence. The next meaningful phase is a bounded feasibility
implementation: owner/coordinator integration, fixed/loaded/transient memory
measurements and the existing qualification plan, before utility migrations.
That phase remains outside the instruction to leave implementation for later.
No prototype, code migration, ABI freeze, HELP resumption or release assignment
is performed or implied here.

## Authorized feasibility evidence

The [isolated feasibility campaign](TCAP-Feasibility-Results.md) now supplies
measured CPU/model evidence and concrete carrier/placement blockers. This
subsequent authorization covers experimental work; utility migrations and
release assignment remain deferred. No public TCAP facility is delivered.

The [carrier/placement follow-up](TCAP-Placement-Results.md) now packages the
private owner within the existing relocation header and places its routing hook
without growing the reference fixed BIOS. These measured feasibility results
do not deliver a public TCAP facility or authorize utility migrations/releases.

## Related contracts

- [Roadmap handoff](TCAP-Design-Thread-Handoff.md)
- [Terminal architecture and optional presentation agenda](POST-1.0-TERMINAL-ARCHITECTURE-OUTLINE.md)
- [Monitor architecture](../architecture/31%20Terminal%20Monitor%20RSX.md)
- [Monitor hook and lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md)
- [SCRN and SCX ABI, including full-control admission](Unloadable%20Screen%20Backend%20ABI.md)
- [Resident service ABI](../architecture/20%20Resident%20Service%20ABI.txt)
- [Held HELP design checkpoint](HELP-1.1-Specification.md)

### Transaction and command-return feasibility follow-up

The [isolated system-path experiment](TCAP-System-Paths-Results.md) executes
transaction guards and command-return recovery in staged real-source entries,
within the existing carrier/overlay limits. It deliberately fails production
version admission. Positive matching-system admission, global validity allocation
and the full candidate request ABI remain incomplete; utility migrations and
release assignment stay deferred. This evidence does not freeze the public ABI.

### Matching-system and global-validity follow-up

The [private matching/validity experiment](TCAP-Matching-Validity-Results.md)
qualifies a permanently placed allocator and matching-artifact gate together
with positive metadata admission and real publication ordering. It charges
512 permanent bytes and an experimental boot-volume reservation change.
Full loader-front-door and finalizer/context integration remain required; this
is not production activation, a public ABI freeze or a utility migration.
Release assignment remains deferred.

### Native-reference manager and loader integration

The [private integrated native campaign](TCAP-Native-Manager-Integration.md)
now constructs validity through the actual manager and enforces native/file-backed
loading gates before installation/execution. It verifies complete load/unload,
cache reconstruction and failure/retry paths. This candidate reserves 1 KiB
permanently; packaging, other-platform qualification and the full public request
ABI remain open. Utility migrations and release assignment stay deferred.
