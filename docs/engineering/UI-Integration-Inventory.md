# Shared UI integration inventory

Review date: 3 November 2026. Implementation branch:
`stabilization/shared-ui-conformance`, based on
`fb062255d3ea465cf8ba6a9b77ac0f4a4aac5c32`.

GitHub main was checked at `1fda9b6194c5b2055814ab9ae74711ad7c37191f`.
Its 15 subsequent commits change documentation only; no utility/shared UI source
changed relative to this baseline. The only open PR found was #570, the distinct
post-1.0 functional-commonality audit. The Model 4 lowercase branch is independent
BIOS work and is not incorporated here. No shared-library work is overwritten.

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
| TED | Standard text fields/renderer already selected; confirmations still call a text field | Record precise behavioral conflict below; no silent interface change. |
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

## Outstanding decision: TED confirmations

`src/utilities/ted/frontend.mac:TE_CONFIRM` currently calls `TE_PROMPT`, waits
for Enter, then approves any submitted value whose first character folds to Y.
An invalid value declines instead of retaining the question. All callers share
this behavior, including overwrite, protected-file authorization, recovery and
modified-document abandonment. `operations.mac:OP_SUB_LOOP` also uses text input
for per-match substitution decisions.

The accepted TED specification, section on separate interaction states, says
“Confirmation Enter means No; invalid choices retain the question.” The shared
standard additionally calls for immediate single-character choices. This is an
existing implementation/specification discrepancy, not a newly introduced
regression or an automatically approved compatibility exception.

Recommended next change: reuse TED's existing checks module with its choice-only
controller, distinguish No from Cancel for substitution, accept Y/N immediately,
retain default No and invalid-response retry, and display `(Y/N) [N]`. Update
all scripted TED interactions and qualify save/protection/abandon/substitution
on both platforms. Alternative: explicitly approve the present line-based
policy as an exception. That alternative retains surprising first-character
acceptance and is not recommended. This consequential established-behavior
change is left for maintainer approval under the assignment's review boundary.
TED is therefore **Outstanding**, not conforming by library inclusion.

## Outstanding execution

Model 4 LaunchServices preflight returns 1100 (BOOTSTRAP_NOT_PRIVILEGED) in this
session. No app launch or native display pass is claimed. The focused media test
supports `--platform model4 --prepare-only` to produce private disks, exact
binary hashes, input steps and a native invocation. Run the full test from a
normal Terminal to execute and perform independent file readback/filesystem
checks. Historical Model 4 receipts remain bound to their original bytes.

See the [matrix](UI-Conformance-Matrix.md),
[library candidate report](Shared-Library-Candidate-Report.md) and
[engineering summary](UI-Integration-Engineering-Summary.md) for disposition,
reproducible commands, sizes and evidence boundaries.
