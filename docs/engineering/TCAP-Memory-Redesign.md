# TCAP memory redesign: Z-System model

Status: compact replacement design, 8 November 2026. The maintainer selected
Z-System as the model, accepted a 1–1.25 KiB budget if needed, and requires no
permanent memory loss. Utility migrations, HELP delivery and release assignment
remain deferred.

Revised scope: the maintainer now requires the **full display path**, excluding
only generic RSX machinery. The earlier incremental capability-layer figures
below are historical milestones, not acceptance of that broader memory goal.
The [integrated display redesign](TCAP-Integrated-Display-Redesign.md) records the
current implementation, full accounting and qualification. The maintainer later
accepted a 1,792-byte full-path ceiling for ANSI; the ADM3A/VT52 ceiling remains
1,280. The capability-layer budgets below retain their historical scope.

## Decision and budget

Use a small terminal description carried by the selected personality and small
routines linked into applications. Preserve the division between personality
protocol and backend rendering. The workflow remains load personality, run its
configured application, unload; load the next personality only after unloading
the first. A backend may stay loaded between personalities.

The [measured historical core](TCAP-ZSystem-Benchmark.md) uses 857 bytes including
the full environment, or 869 with geometry access. Aim at that size or less.
The maximum accepted comparable footprint is **1,280 bytes**. This is a ceiling,
not a request to consume the allowance.

Count all added TCAP resident allocation, service descriptors, alignment and any
added descriptor page, plus application helper code and working data. Also
report whole-stack loaded totals, application call sites and observed stack use.
Do not hide an engine in a bank, resolver tail, BIOS padding, boot counter,
mandatory cache, or build profile with a lower unloaded TPA ceiling.

After complete unload the exact original transient boundary and maximum COM
capacity must return. There may be **zero permanently reserved TCAP bytes**.
Ordinary printing with TCAP absent must remain usable.

## Rejected direction

The 2,560-byte permanent reservation is rejected. The later optional-root variant
is also rejected: moving the reservation into an optional allocation still left
13.5 KiB loaded including the existing 4.5 KiB rendering/resolver/personality
baseline. Its roughly 9 KiB TCAP increment is unacceptable.

The [old public transaction contract](TCAP-Transaction-ABI-Historical.md), its machine-readable
wire tables and its implementation experiments are historical evidence. They are
not the target for this replacement. Passing their structural/CPU checks cannot
establish compact TCAP completion. The earlier compact null-hook experiment
proved unchanged memory boundaries for ordinary personalities; it did not make
its counters, callback gate or recovery engine requirements of the new design.

## Allocation and lifetime

| Component | New design | Lifetime |
| --- | --- | --- |
| Terminal facts and protocol templates | At most 128 bytes with personality | Existing RSX allocation; removed with personality |
| Description query | Small read-only entry, second service beside MCON | Same personality |
| Lookup, bounded snapshot, sequence formatting | Application-linked helper | Reclaimed when application exits |
| Output and hardware rendering | Existing BDOS console, Monitor, SCRN and SCX | Existing architecture |
| Pager/editor/navigation state | Owned by relevant application | Application lifetime |
| Global TCAP owner, tokens, boot counter, protected stack, cache | None | No allocation |

Reuse the existing checked carrier binding, metadata validation, duplicate-service
rejection, single-MCON selection and commit/publication mechanism. Do not build a
parallel TCAP loader or whole-system admission inventory. Initial prototypes use
private **XTAB 0.1**, not the superseded TCAP 1.0 wire identity. The [compact public contract](TCAP-Template-ABI-Historical.md) now assigns TCAP 1.0 to the
replacement. XTAB remains a private feasibility baseline.

Lookup must verify that the description service and selected MCON belong to the
same provider. The normal checked loader remains responsible for admitting that
provider and binding its backend. A description cannot authorize arbitrary code
or forge a different provider's rendering capabilities. No client may retain raw
entry/data pointers across reconstruction. Copy a bounded description for use
within a transient run; rediscover after layout or output-route changes.

## Facts and output semantics

The description records the protocol the application must emit, not the host
terminal protocol. An ADM3A profile supplies its implemented control vocabulary;
an ANSI profile supplies ANSI sequences. Helpers send those bytes through normal
BDOS console output, where the selected personality interprets them and invokes
the backend. No new Monitor selectors, BDOS function or console interception are
needed. Printable application text uses its existing console output path.

Strong emphasis maps to an available semantic choice. The integrated ANSI and
ADM3A profiles use reverse video, including on physical Model 4/II backends;
the present VT52 profile uses readable plain text. The record can also describe
bold when a future qualified personality/backend supports it.
Begin/end sequences must be balanced by the application. This interface does not
promise arbitrary prior-rendition restoration, nested scopes or output ownership.
Initialization/deinitialization templates establish the documented normal
baseline; they are not a saved-screen mechanism. Existing warm-return parser
reset remains unchanged; it is not a new guarantee of recovery from abandoned
application presentation state.

Geometry is scoped to the operation path. Current ADM3A/VT52 fixed-cell behavior
uses 80×24, but the ANSI host stream may have unknown dimensions. SCRN operation
12 describes its existing fixed 80×24 cell contract. SCX operation 16 separately
reports stream geometry; zero rows/columns mean unknown on the host. Do not turn
that zero into 80×24 or call an encoded host control verified physical support.
A full-screen client may separately select the qualified fixed SCRN viewport.
Its admission must check the required position, write, erase and restoration
operations against that backend, not infer them from an emphasis string.

Route eligibility is checked before emitting controls. The first private
experiment supported CRT only. The public helper also admits cpmsim TTY through
its qualified shared Monitor path; other TTY, BAT and discard routes are refused.
No input-consuming host terminal probe is introduced. A client that changes routing must reopen and
reassess geometry and capabilities before further controls.

## Application responsibilities, without migrations

- TYPE owns wrapped-row counting, the prompt-line reservation, page replay and
  file-position history. Unknown stream dimensions require an explicit viewport
  or a non-paginated/manual fallback. TCAP does not buffer file pages.
- TED checks cursor positioning, literal writing, erasure and the selected fixed
  viewport before taking over. It owns exit cleanup and any use of existing SCX
  cursor/rendition save/restore. No resident takeover transaction is introduced.
- HELP owns parsing, navigation and balanced emphasis. Unsupported emphasis emits
  readable plain text. Unknown dimensions use the same explicit pagination policy
  rather than inventing a screen size.

These describe future consumers; this work does not migrate TYPE, TED or HELP.

## Explicit contract changes

The old Discover/Admit/Begin/Takeover/End/Release/Recover/DescribeSession envelope,
32-byte requests, 64/96-byte eligibility records, 16-byte tokens, global validity
allocation and matching-system recovery package are removed from this design.
There is no automatic recovery guarantee for abandoned scopes and no globally
non-reused session identity. Applications use ordinary cooperative CP/M lifetime
rules and existing loader generations. Existing Monitor 0–5, SCRN 1.1, SCX 1.0
and Function 182 keep their meanings.

This is a deliberate revision of the unreleased engineering contract. It must
not be represented as a smaller implementation conforming to the old wire ABI.
The existing source/binary experiments remain unshipped diagnostics until the
replacement is integrated and qualified.

## Qualification gates

1. Reproduce the original Z-System module closure and execute its core routines.
2. Build the table/helper experiment; count resident allocation and application
   helpers together, inspect emitted output, and reject malformed descriptions.
3. Run a complete ordinary checked cpmsim guest from cold boot: absent TCAP,
   backend load, personality load, application output, JP 0 warm reconstruction,
   repeat discovery, personality unload and switching, complete unload. Measure
   exact boundaries, not just rounded RSX listings.
4. Complete public replacement-contract integration, rejected-package cases,
   route/geometry checks and actual installation qualification on cpmsim.
5. Qualify Model 4, then Model II independently, with backend rendering evidence
   and exact before/loaded/after memory measurements on each.

A private source-image lifecycle pass is narrower than installation qualification
or public ABI completion. Native platform results must be reported separately.

The [first executable compact-model results](TCAP-Compact-Model-Results.md) now
pass gates 1–3 for the stated private scope: 799 bytes maximum comparable static
footprint, exact boundary restoration and a 57,344-byte COM before/after unload.
The subsequent [public integration results](TCAP-Public-Integration-Results.md)
now pass gates 4–5 on cpmsim, Model 4 and Model II. The public helper increases
the maximum added static TCAP footprint to 1,033 bytes; the diagnostic application,
resident increment and stack allowance total 1,218 bytes. These are capability-layer
costs, not a measurement or optimization of the entire console subsystem.
