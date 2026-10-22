# Shared input modules

Behavior and migration policy are defined in the [Shared Input and UI Specification](../../../../docs/engineering/Shared%20Input%20and%20UI%20Specification.md).

## Initial legacy editor

`input.inc` is the behavior-preserving extraction of DUMP Build 002's editor. It implements insertion, Ctrl-S/D/G/H, ESC and empty-Enter cancellation, capacity refusal, and resume after validation failure. This compatibility profile does **not** enable standard-profile Ctrl-A/F/Y, Ctrl-C cancellation, DEL aliases, defaults, choices or distinct event results. Select the standard profile explicitly for those features.

Include it once per assembled program. The `EDIT*` labels are reserved within that program. No buffer, screen backend or BDOS service is allocated by the module.

Caller-owned symbols:

| Symbol | Storage / meaning |
| --- | --- |
| `EDITBUF` | At least the configured capacity bytes; length-counted, no terminator. |
| `EDITLEN` | One byte, logical input length. |
| `EDITCUR` | One byte, insertion position from zero through length. |
| `EDITSTART` | One byte, renderer's horizontal scroll origin. |
| `EDITMAX` | One byte, maximum length, 1 through 255. |
| `EDITPROMPT` | Two bytes, opaque prompt pointer passed to the renderer. |

Bind these symbols to caller hooks with `EQU`, placing bindings after their target definitions where the assembler requires it:

| Hook | Contract |
| --- | --- |
| `UIREAD` | Wait for one unechoed character, return A. |
| `UIDRAW` | Draw field from caller state; preserve buffer/state except render scroll. |
| `UICANCEL` | Restore the caller's nonediting presentation. |
| `UIMESSAGE` | Show the NUL-terminated limit message addressed by HL. |
| `UILIMITMSG` | Address of the caller's input-limit message. |

Hooks may destroy AF/BC/DE/HL and must balance their stacks. They must not recursively invoke the editor. The core preserves no general registers; caller state must remain in memory. Platform/input normalization belongs to `UIREAD`, subject to the consumer's compatibility contract.

`EDITNEW`: A is capacity, HL is prompt pointer. Resets input length, cursor and scroll, then runs synchronously. Returns carry clear for nonempty Enter, carry set for ESC or empty Enter. Data remains in `EDITBUF` with its length in `EDITLEN`; the caller commits or validates it. Cancellation does not restore application state by itself.

`WAITEDIT`: resume existing input after the caller displays a validation error. It reads one key, redraws the field, and processes that key exactly once. It uses the same return convention. Do not reinitialize the field before calling it.

Rendering remains caller-owned. DUMP's renderer retains its prompt labels, SCRN calls, screen position, horizontal scrolling and reverse-video insertion marker. A future generic renderer must take those as parameters rather than copying DUMP's label comparisons.

## Qualification of the extraction

The extracted DUMP remains 14,154 bytes, SHA-256 `1d1f260172e5d4cea26d32965b30f524a044a206aa659695f6c1f483f467e5c8`, identical to Build 002. This provides a strict behavior-preservation check in addition to the compiled DUMP regressions. It does not qualify the unimplemented standard profiles.

## Inline renderer and CONFIG binding

`inline.inc` renders one physical console line through `UI_PUT` and `UI_MARK`.
Both hooks take A and preserve BC/DE/HL. The caller supplies `UI_COLUMNS`, shorter
than its physical console width, and a NUL-terminated label at `EDITPROMPT`.
The label must leave at least one input/cursor cell. The caller must ensure
`EDITMAX + UI_COLUMNS <= 255` for this initial byte-indexed renderer. CONFIG
uses 79 columns on its existing 80-column layout, a maximum 126-byte field,
and short fixed labels. This is not terminal geometry detection or a 40-column
CONFIG layout.

The renderer clears/pads the row, scrolls input to keep the insertion point
visible and marks that cell without requiring terminal cursor-position escapes.
It does not own the screen or validate values. `configinput.inc` supplies direct
BDOS 6 input/output, maps Ctrl-C to local ESC and DEL to Backspace, and uses the
existing optional Function 178 for reverse-video marking. Direct output is
required here: cooked BDOS output can intercept pending Ctrl-S/Ctrl-C during
redraw. The fallback marker is an underscore.

CONFIG reuses its counted startup buffer for the length-counted edit text and
six otherwise unused private state bytes below its existing AC00h guard. Its
numeric adapter performs decimal validation; save/activation policy remains in
CONFIG. The standard extended editor, defaults and choice controller remain
unimplemented and are not claimed by this basic migration.

## Standard profiles

The standard event engine, optional word commands, empty/default policies and
choice-only controller are implemented alongside the preserved compatibility
profile. Use `tools/shared_ui.input_source` and `controller_source` to select
only the required code. `events.inc` defines result/policy constants;
`wordstar.inc` is optional; `checks.inc` is shared once by `prompt.inc` and
`choice.inc`. All work buffers and state remain caller-owned.

See the [developer guide](../../../../docs/programmers/Shared%20Input%20Library.md)
for the complete API, build selections, register contracts, examples, measured
costs and rendering obligations. The new controllers do not yet replace either
DUMP's or CONFIG's compatibility binding. No undo, overwrite, terminal escape
parser or automatic screen-driver loading is introduced.


Optional `format.inc` formats validated choice questions with explicit width
checking; it does not output text or replace a screen backend. See the developer
guide for its caller-owned buffer and error contract.


`screen.inc` provides backend-independent field scrolling and caret rendering;
DUMP Build 003 is its first consumer. The caller clears/positions the prompt row
and supplies literal-character, caret and position hooks. See the developer
guide for geometry, register and state contracts.


`default.inc` formats a separate bracketed default for an empty standard text
field; `choiceerror.inc` retains the full choice question/default while bounding
its diagnostic. Both use the common formatter buffer and width configuration.
See the developer guide for preflight, error and direct-output requirements.


For a complete runnable consumer, see `src/examples/uiexample.mac` and
`tools/build_ui_example.py`. It connects the standard controllers and layouts
to real callable SCRN primitives and direct keyboard input without changing
existing utility contracts or distribution manifests.


SYSGEN's installation and package-replacement confirmations select only the
choice controller through `common/sysgeninput.inc`. The compatibility adapter
preserves any-non-Y-declines behavior, original questions and no default; it
adds no editor or formatting buffer. See the developer guide for measured cost.


`confirm.inc` is the shared one-key compatibility adapter selected by DUP and
SYSGEN. It preserves original any-non-Y-declines confirmation policy rather than
introducing defaults or retries. Both utilities reuse their own uppercase,
unechoed `KEY` routine. The selection helpers and developer guide describe the
220-byte complete binding and its output contract.


ERA uses `common/erainput.inc` for its Y/N and R/S/A/? contexts. This adapter
preserves ERA-specific invalid-key retry, Ctrl-C cancellation and the absence
of Enter/ESC aliases. It does not reuse DUP/SYSGEN's any-non-Y-declines policy.
The developer guide documents caller register/state contracts and the retained
legacy confirmation reference used for differential tests.

REN's `../reninput.inc` provides a choice compatibility binding. Unlike the
strict any-non-Y-declines adapter, it retries invalid responses and retains
BDOS 1 echo plus full collision/recovery question repainting. Its filename field uses the separate `append.inc` compatibility event engine.
See the developer guide and REN qualification records.


`append.inc` is the extracted append-only compatibility engine used by REN.
It shares event constants, performs no I/O and owns no storage. The caller
provides `UA_BUF`, `UA_LEN`, `UA_FULL`, `UA_MAX` and handles echo/validation.
It preserves sticky overflow and literal raw-byte storage; it is not the
standard profile for new prompts. See the developer guide for entry contracts.

COPY's `../copyinput.inc` retains raw BDOS 6 choice/field policy and caller-owned
overwrite/retry/cleanup logic. It selects choice plus append modules only.
`UA_PUT` is the append engine's literal-byte entry for adapters where a control
byte must retain its historical candidate-input meaning (COPY's Ctrl-U). It
checks bounds and overflow but does not interpret the byte. Standard new fields
should use the standard editor. MOVE has no current interactive prompt.


PIP's `../pipinput.inc` reuses the one-key confirmation binding with a cooked
BDOS 1 callback, preserving its echo and AND-DF folding. Only protected-file
replacement approval is migrated; command/HEX/device input stays with PIP.


DUP's `../dupmenu.inc` shares its existing controller between main-menu, drive
and destructive-approval contexts. Its CHOICE rendering is retained, and menu
returns reset strict Y/N configuration. Common CONFIG/SYSGEN code is untouched.

SYSGEN Build 007 also reuses its confirmation controller for destination B..D
selection; `../sysgeninput.inc` restores the strict approval context on return.

CONFIG Build 015 uses `../configchoice.inc` for legacy menu and approval keys.
Its one-token transport retains the caller's key policy; the editor keeps its
separate CI_READ binding. See the developer guide for context and size rules.
