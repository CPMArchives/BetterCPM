# Shared input modules

Behavior and migration policy are defined in the [Shared Input and UI Specification](../../../../docs/engineering/Shared%20Input%20and%20UI%20Specification.md).

## Initial legacy editor

`input.inc` is the behavior-preserving extraction of DUMP Build 002's editor. It implements insertion, Ctrl-S/D/G/H, ESC and empty-Enter cancellation, capacity refusal, and resume after validation failure. It does **not** yet implement standard-profile Ctrl-A/F/Y, Ctrl-C cancellation, DEL aliases, defaults, choices or distinct event results.

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
