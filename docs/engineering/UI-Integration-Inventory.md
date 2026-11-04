# Shared UI integration inventory

**Coverage correction, 4 November 2026:** the transient migration and its
qualification do not close the resident command paths. Ordinary unqualified
DIR/ERA/TYPE/REN/CLS/USER/VER/COPY/MOVE can execute inside `RCP.CPX`, whose
version-only query gateway lacks standard help dispatch. Treat that as
outstanding integration, not an implicit waiver based on the RCP freeze.
See the [matrix correction](UI-Conformance-Matrix.md#resident-command-coverage-correction--4-november-2026)
for observed failures, source references and evidence limits.

Review date: 3 November 2026. Initial implementation branch:
`stabilization/shared-ui-conformance`, based on
`fb062255d3ea465cf8ba6a9b77ac0f4a4aac5c32`.

GitHub main was checked at `1fda9b6194c5b2055814ab9ae74711ad7c37191f`.
Its 15 subsequent commits change documentation only; no utility/shared UI source
changed relative to this baseline. The only open PR found was #570, the distinct
post-1.0 functional-commonality audit. The Model 4 lowercase branch is independent
BIOS work and is not incorporated here. No shared-library work is overwritten.

Subsequent checkpoint: #571 merged at
`bd4df2cd9f0a7a2edfa12112a8c02151eea5b90d`. The separate
`stabilization/ui-argument-validation` follow-up preserves four no-operand fixes
found during the remaining parser review. All four affected paths build and pass
host/cpmsim and the 22-phase current-payload Model 4 gate. The matrix closes 28
bounded malformed-tail entries, documents five existing language/host exceptions,
and retains six development-only O entries. See the
[follow-up record](UI-Argument-Validation-Followup.md) for exact evidence and limits.

## Authorities and existing work

- [Shared Input and UI Specification](Shared%20Input%20and%20UI%20Specification.md):
  field, choice, default, cancellation, rendering and compatibility boundaries.
- [Utility help](../../specifications/UTILITY-HELP.md),
  [versioning](../../specifications/UTILITY-VERSIONING.md), utility-specific
  engineering specifications and later accepted qualification amendments.
- [Shared library API](../programmers/Shared%20Input%20Library.md),
  `src/utilities/common/ui/README.md`, `tools/shared_ui.py` and selected modules:
  events/input/wordstar/checks/prompt/choice/confirm/append/inline/screen and the
  default/choice-error formatters. Caller storage and existing entry contracts
  remain unchanged.
- Distribution membership comes from the distribution manifest and
  `metadata/distribution.json`, plus Utilities and companion build projections;
  registry tools and RCP are evaluated separately rather than silently excluded.

## Initial assessment and disposition

| Group | Initial finding | Action |
| --- | --- | --- |
| DUMP, CONFIG, COPY, REN, ERA, DUP, SYSGEN, protected PIP replacement | Existing qualified compatibility-profile consumers | Reuse; rerun focused regressions. Do not silently add default/key aliases. |
| DDT adaptation | Standard shared editor already selected; historical reference separately immutable | Preserve debugger command language; no replacement needed. |
| TED | Standard text fields/renderer already selected; confirmations still called a text field | Maintainer-approved immediate-choice correction implemented; bounded host/cpmsim and both current-payload Model 4 campaigns pass. |
| NOAH | Shared choice binding already present | Review separately from frozen six standalone codecs; retain overlay boundaries. |
| BYE | Local Y/N/default-No loop | Adopt existing choice-only controller; standard question/default notation. |
| DASM | Local CHIN only-Y approval in historical command language | Adopt existing strict compatibility binding; preserve raw fold, echo and any-other-key decline. |
| CRCKSUM/MD5SUM | One common overwrite implementation, no shared choice controller | Capacity exception after measured controller trial; retain the existing decision loop and correct local cancellation transport. |
| Other commands | Tail parsing, navigation, streaming, acknowledgments or no interactive input | Evaluate requirements individually; no editor/choice framework forced onto application protocols. |
| ZSM4/LINK and staged MOUNT/R/W | Separate upstream/host integration contracts | Explicitly evaluate and document exceptions; do not rewrite into Z80 macros. |

The first media test exposed a pre-existing checksum defect: cooked Function 1
warm-boots on Ctrl-C, so the documented application cleanup never runs. Host
models previously returned Ctrl-C directly and missed it. The checksum modal
binding now uses direct Function 6 input/output and echoes printable ASCII and
CR/LF/BS locally. It does not implement cooked Ctrl-P printer toggling, Ctrl-S
pause, TAB expansion or echo unassigned control bytes during that prompt.
Outside the modal prompt, existing output and operation polling remain intact.
This deliberate transport correction is independently exercised on real cpmsim.
No core console behavior is changed.

The attempted choice-controller bindings increased both checksum binaries across
2-KiB filesystem allocation boundaries, overflowing the current primary Utilities
volume by 2 KiB. Retaining their already common local loop plus the transport
correction keeps each in its original allocation, with 2 KiB free on the volume.
This is the assignment's explicitly permitted measured memory/space exception;
no disk enlargement, membership change or new competing library is introduced.

## Approved TED confirmation migration

The initial review found that `TE_CONFIRM` called the text editor, required
Enter and accepted any response starting with Y. Invalid responses declined
instead of retaining the question. The maintainer approved the proposed
immediate Y/N, Enter=No and invalid-response retry change on 3 November 2026.

TED revision 004 now selects the existing choice controller alongside its text
controller, sharing the single checks module. `TE_CHOOSE` distinguishes No from
Cancel; confirmed substitution skips one match on No and stops remaining matches
on Cancel. `TE_CONFIRM` preserves its authorization interface: only Y returns
carry clear. Overwrite, protection, recovery and abandonment callers retain
their existing operation boundaries. Questions display `(Y/N) [N]`.

Current compiled and cpmsim evidence is recorded in
[TED shared choice qualification](TED%20Shared%20Choice%20Qualification.md).
Both bounded Model 4 campaigns pass on TED 004. Historical TED 003 receipts are not
transferred to the changed revision. The existing full-screen editor and
command language are otherwise preserved.

## Platform execution

The maintainer's normal-Terminal run now passes the twenty-phase Model 4 campaign
for the current CRCKSUM/MD5SUM/DASM binaries. All captures, exact payload hashes,
independent preserved-input/new-list readback and filesystem checks are archived
in [current native evidence](evidence/2026-11-03-model4-pass/results.json).
The two earlier runner failures remain separately recorded. BYE is cpmsim-only.

TED's changed-binary `choices` native campaign now also passes on the exact current
payload. The corrected `choice-scope` run now also passes, saving precisely
`ONE X ONE ONE` with its original backup; guards and filesystems pass. A RAM
capture establishes that its initial
attempt returned to command input after the physical-key helper uppercased the
search while the fixture remained lowercase. The harness now uses matching
uppercase fixture/search text; corrected cpmsim and native execution pass.
See the [native scope receipt](evidence/2026-11-03-ted-model4-scope/results.json).
This agent session cannot launch AppKit (preflight 1100);
use a normal Terminal. Preparation and historical TED receipts alone do not
qualify the changed TED binary.

See the [matrix](UI-Conformance-Matrix.md),
[library candidate report](Shared-Library-Candidate-Report.md) and
[engineering summary](UI-Integration-Engineering-Summary.md) for disposition,
reproducible commands, sizes and evidence boundaries.
