# TCAP routing and recovery: source feasibility study

Status: design recommendations for review, 7 November 2026. Follow-up to the
[semantic contract](TCAP-Semantic-Contract.md) merged in PR #649. Documentation
only: no prototype, runtime qualification, implementation choice, binary ABI or
release assignment. HELP remains on hold. Source baseline: main `c6e3e9b9`.

## Findings

The existing source provides useful routing observations and early command-return
boundaries, but no complete scope owner, routing invalidation protocol or enhanced
recovery mechanism. A transient-only wrapper cannot establish all required
guarantees. Recommend carrying forward a coordinated owner associated with the
active personality as the design candidate, while leaving storage placement and
implementation scope undecided until cost and lifecycle evidence exist.

### Console routing is evaluated at the BIOS call

[BIOS `IO_CON` and `BIOCONOT`](../../src/bios/bios.mac) read the low two
IOBYTE bits for each call. CRT console selection reaches `MH_OUT`/`MC_CALL`.
Another selection routes through LIST; other routes can be sinks. Input routing
is evaluated separately through the same console selector. `IO_CAPS` reports
CRT console and CRT LIST support; it describes supported routes, not the route
currently selected or physical endpoint dimensions.

[BDOS `UB_SETIO`](../../src/bdos/unified.mac) stores E directly into address
0003h. It does not notify the Monitor, publish an epoch or close scopes. A
program can also write page-zero IOBYTE directly. Watching Function 8 alone
therefore cannot establish a system-wide change notification guarantee.
Comparing snapshots before Begin/End would detect only some changes; it would
miss an intervening change followed by restoration to the same byte.

Recommended semantic limit: legacy programs retain unrestricted historical
IOBYTE behavior. Portable emphasis clients declare that they do not alter
routing during a scope. A future owner must additionally verify the actual
route at a serialized output boundary before enhanced display output, or enforce
an equivalently justified policy. Client declarations alone are insufficient
for admission. Any managed route change must retire owned state before publication.
This is a design candidate, not proof that every output path is currently guarded.

An asynchronous agent, interrupt routine or hardware-bypassing client that
changes routing outside the qualified serialization boundary is outside the
initial enhanced contract. Such behavior must not be described as automatically
observed. If the implementation cannot establish its boundary for a profile,
that profile returns plain eligibility. Do not add a permanent global routing
watcher merely on the assumption that one is needed.

### LIST is a logical route, not necessarily another device

In the current BIOS, `BIOLSTST` recognizes the CRT LIST selection, and
`BIOLIST` reaches `MH_OUT` for that selection. Thus console and LIST may use
the same Monitor and physical display. BDOS `UB_PUTNOW` calls CONOUT and then,
when printer echo is enabled, LIST with the same character. The same display
can consequently see duplicated text. This is existing behavior to preserve;
TCAP must not silently suppress or deduplicate echo.

The text-only LIST requirement means no TCAP presentation controls are inserted
into LIST bytes. It cannot mean that a CRT used as LIST is visually independent
of the active display's rendition. A physical endpoint already in reverse may
show an echoed character in reverse even though LIST received plain ASCII.
Likewise, text-only does not mean sanitizing arbitrary control bytes supplied
by the application; TCAP adds no presentation sequences to that stream.

When CONOUT and LIST alias the same display, semantic byte identity can be
qualified, but spatial paging cannot assume one rendered glyph per source glyph.
Recommend marking spatial stream geometry unusable while echo can duplicate
output to that display unless the stream contract models the duplication.
A mid-page echo toggle invalidates spatial anchors/layout accounting. Styling
may remain eligible only if owner coordination and alias behavior are explicitly
qualified. Echo must remain functional, including ^P changes during output.

These facts require future tests for independent LIST, CRT LIST aliasing,
unsupported/sink routes and routing changes. A supported-route bit alone is not
sufficient destination or interactivity evidence.

### Recovery boundaries already exist, with weaker semantics

| Source boundary | Observed behavior | Candidate TCAP role and limit |
| --- | --- | --- |
| [Portable reloader `CRBODY`](../../src/system/command-stage2.mac) | Selects its own stack, calls Monitor operation 5, then performs reconstruction file operations. | Candidate early warm-return recovery boundary before reloader diagnostics. Need prove every selected reloader variant reaches it while the old owner is valid. |
| [Model 4 reloader `CRBODY`](../../src/platform/trs80m4/ccprelod.mac) | Has the same early parser-reset ordering. | Separate build path must remain covered; do not patch only the portable source. |
| [CCP `CCP_LOOP`](../../src/ccp/ccp.mac) | Calls operation 5 before emitting the next prompt, including resident-command returns that bypass warm boot. | Candidate final prompt guard and direct-return coverage. Too late by itself for reconstruction/startup/error output emitted earlier. |
| [BIOS `BIOWBOOT`](../../src/bios/bios.mac) | Transfers to the platform reloader. | Entry trace, not a new automatic cleanup callback. |
| [Gateway `SYS_WARM`/`SYS_ENTER`](../../src/system/gateway.mac) | Restores a system stack and reconstructs command state through existing services. | Recovery must not rely on abandoned transient or BDOS stack frames. Audit failure output and ownership lifetime across this path. |
| [ANSI `AN_RESET`](../../src/rsx/ansi.mac) | Clears parser state/count, retains rendition and other terminal state. | Not the proposed full prompt baseline. Preserve operation 5 semantics for legacy calls. |

Recommend a distinct semantic recovery action at the earliest qualified return
boundary plus an idempotent guard before prompt output. This does not allocate
new callbacks or selectors and does not prescribe how the action is dispatched.
An already-recovered session must not move the cursor or reset modes twice.
Cold boot uses fresh state rather than following abandoned handles. Paths that
halt on loader failure need an explicit diagnostic baseline or an honest recovery
failure disposition; a normal prompt guard is not sufficient evidence.

## Ownership and lifecycle obligations

Recovery ownership must survive transient termination and remain reachable
before any enhanced state is activated. It must contain no transient pointers.
A personality-associated owner must coordinate its logical rendition with the
backend and leave the SCX reusable save slot untouched. Exact storage, allocation
and rebinding records remain open. No fixed PDS/core growth is approved.

Manager transactions that move/remove the owner must either preserve logical
state with explicit rebinding or close it before publication. Failure must
preserve the old usable binding or take the defined recovery path. Do not assume
an existing fallible shutdown callback can simply be inserted after commit.
The [Monitor lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md)
requires safe publication and binding; extending it needs a transaction design,
not merely a new transient End call.

## Recommended decisions and remaining evidence

| Item | Recommendation | Evidence still required |
| --- | --- | --- |
| Routing | Qualify explicit serialized observation/constraint for portable scopes; keep legacy IOBYTE behavior. | Actual boundary coverage, direct byte writes, same-byte change/revert, and no stale-owner cleanup. |
| LIST | Guarantee no TCAP control bytes; preserve echo, including CRT alias duplication. | Captured CONOUT/LIST bytes plus rendered alias cases; independent-device visual styling is not promised for aliases. |
| Spatial pager | Reject geometry assumptions that ignore output duplication. | Define echo-toggle invalidation and demonstrate safe fallback/restart without disabling ^P. |
| Recovery | Early reloader recovery plus final prompt guard as candidate integration boundaries. | Trace normal RET, Function 0, jump 0, cooked ^C, resident commands, startup/SUBMIT and loader/manager failures on each build path. |
| Owner placement | Investigate personality-associated coordination and independent recovery lifetime. | Page-rounded cost, first-provider overhead, movement/removal/rollback and zero transient-pointer dependencies. |

The next implementation-design decision should select the owner/transaction
mechanism only after these boundaries and cost limits are demonstrated. A
bounded prototype remains later work, not authorized or performed by this study.
The current semantic draft can be refined using these findings without claiming
that TCAP is implemented or that its engineering specification is frozen.

## Owner and transaction design follow-up

The [owner/transaction design](TCAP-Owner-Transaction-Design.md) proposes
personality-associated recovery ownership, idle-only profile transactions and
a return-path coordinator. These remain design recommendations; routing guards,
storage, ABI and implementation are not approved or delivered.
