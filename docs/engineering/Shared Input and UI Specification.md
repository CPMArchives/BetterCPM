# BetterCP/M Shared Input and UI Engineering Specification

**Status:** Accepted behavioral design, 2026-10-22. Implementation begins with a behavior-preserving extraction of DUMP's editor. This is not a requirement to retrofit every validated System Disk utility before release.

## 1. Scope and compatibility

Provide small, reusable, build-time Z80 assembly modules for single-line editing, choices, defaults, confirmations and messages. Use the native ZSM4 build path as well as cross builds. Add no resident service, BIOS/BDOS interface, mandatory RSX or general full-screen document engine.

Apply the standard to new utility prompts. Migrate existing utilities individually, with specification and qualification updates for observable changes. Preserve ED's DRI-compatible command language and insertion behavior. A future BetterCP/M full-screen editor may reuse these prompt routines and conventions while providing its own document engine.

BDOS Function 10 remains unchanged. CCP editing configuration remains the separate [post-1.0 policy study](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#command-line-editing-follow-up--2026-10-18). Do not replace CP/M input semantics globally.

## 2. Prompt notation and completion

Parentheses identify permitted choices; square brackets identify a separately displayed default. Omit brackets when there is no default; never display empty `[]`.

```text
Filename:
Filename [OUTPUT.TXT]:
Continue? (Y/N) [N]:
Select drive (A/B/C) [A]:
```

The default is not initially editable text. Typing supplies a replacement without requiring deletion of the default. An explicitly prefilled editing field is a distinct presentation: place the existing value in the buffer, cursor at its end, and do not duplicate it as a bracketed default. A dedicated import-default key is deferred.

Each prompt explicitly selects one empty-Enter policy:

| Policy | Result |
| --- | --- |
| Accept default | Select the displayed default, subject to normal validation. |
| Cancel | Abandon this prompt. |
| Accept empty | Submit an intentionally empty value. |
| Require value | Retain the prompt and explain the requirement. |

Freeform and multi-character responses require Enter. When all choices are single characters, accept a valid character immediately, case-insensitively. Enter selects the configured empty policy. Invalid choices retain the question and available responses; never hide the question behind an unexplained error.

Defaults undergo the same semantic validation as typed values. Do not treat a default as authorization to bypass range, filename or protection checks.

Do not flush queued keyboard input indiscriminately after accepting a choice. Any CR/LF pairing policy belongs to the input adapter, not a generic buffer purge. A terminal adapter must document its treatment of paired line endings without discarding independent subsequent input. Scripted input support remains a caller/adapter contract, not an automatic property of the line editor.

## 3. Cancellation and application state

ESC cancels an active prompt without committing its proposed value. Ctrl-C in a text field has the same local cancellation meaning, without forcing a warm boot. Neither is a global redefinition: DUMP's navigation Ctrl-C may remain Page Down and streaming Ctrl-C may remain interruption.

The caller keeps application state separate from provisional input. Cancel restores the previous application state, including a previous search pattern or page where applicable. The reusable editor need not retain an original-field copy merely to provide application cancellation.

During a longer operation, honor cancellation at documented safe boundaries. Completed writes are not undone by this UI contract; report partial completion accurately. Do not promise transactional rollback of destructive operations.

Return distinct results for No and Cancel. In a batch, No may skip one object while Cancel stops the operation; the caller defines that scope. Do not represent cancellation solely as a zero-length string.

Q quits the main interactive screen where the utility uses that convention. In text fields it is ordinary input unless explicitly offered as a choice. ESC at a main screen is not implicitly a quit alias. Existing command languages remain exceptions under Section 1.

## 4. Standard text-field profile

Use insertion-only editing initially. Insert characters at the cursor and shift subsequent characters right. No overwrite mode or toggle is included.

| Key | Action |
| --- | --- |
| Ctrl-S | Move one character left. |
| Ctrl-D | Move one character right. |
| Ctrl-H / Backspace | Delete the character before the cursor. |
| Ctrl-G | Delete the character under the cursor. |
| Ctrl-A | Skip spaces to the left, then move to the beginning of the preceding word. |
| Ctrl-F | Pass the current word and following spaces to the next word's beginning. |
| Ctrl-Y | Clear the editable buffer and move to its beginning; leave a separately displayed default unchanged. |
| Enter | Submit according to the prompt's empty policy. |
| ESC / Ctrl-C | Cancel the text field. |

A word is a run of non-space characters. Movement/deletion beyond an end leaves input unchanged without a bell. Ctrl-U is unassigned in this profile. Defer undo; if added, evaluate single-level undo first and distinguish it from restoring initial contents. Multilevel histories, grouping rules and overwrite are not approved initial features.

Printable ASCII `20h` through `7Eh` is insertable. Preserve case and all spaces. Do not silently trim, uppercase, expand tabs or insert unsupported control bytes. Ignore unassigned control keys unless the caller defines their context. Callers normalize and semantically validate values explicitly.

At capacity, refuse further insertion and show a nonmodal limit message; preserve the buffer and allow deletion and movement. Never silently truncate a submitted value.

## 5. Input adapters and aliases

The editor consumes logical key actions, not terminal protocols. An optional adapter may map Left/Right to Ctrl-S/D, Home/End to the corresponding field boundaries, and forward Delete to Ctrl-G. These aliases are not prerequisites for a basic text field.

ASCII DEL (`7Fh`) aliases Backspace; it is distinct from a decoded forward-Delete action. Model 4 Ctrl-CLEAR generates DEL; CLEAR and Shift-CLEAR generate ESC. Under trs80gp, Home maps to CLEAR; MacBook Fn-Left Arrow supplies Home. Keep these physical mappings out of the portable editing engine.

Do not embed an ANSI/VT52 sequence parser into every field. If an adapter decodes sequences beginning with ESC, it must explicitly resolve literal ESC versus sequence prefixes. Raw terminal-key decoding is deferred from the initial shared library.

## 6. Messages and rendering

Full-screen utilities may share exactly one bottom row among command hints, text fields, nonmodal messages and modal confirmations. Location does not determine modality. Non-full-screen utilities may print messages inline; do not require a loaded screen backend merely to ask a simple question.

A nonmodal message preserves focus, input, cursor and horizontal scroll. It remains until the next recognized key. That key clears the message and is processed exactly once in the original context, never consumed merely as acknowledgment. Further invalid input may refresh the message. A renderer restores the active field before applying/redrawing an edit. An invalid single-choice response must leave its question intelligible.

Unknown-key feedback remains utility-specific; DUMP may continue ignoring unknown navigation keys. Do not impose a universal error message or bell.

Modal prompts capture input until resolved. On cancellation, restore the underlying interaction and application state. Confirmation policy is utility-specific; the library does not decide which disk operations require approval.

The field renderer takes actual reported geometry and caller-supplied position/width. Do not assume 80 by 24. Forty-column utility layouts remain optional unless the utility's own specification requires them, as DUMP requires `/40`. A configurable field width does not imply an entire utility supports 40 columns.

Use horizontal scrolling to keep the insertion point visible without wrapping into the data area. Provide a visible software cursor where no hardware cursor is available. DUMP's reverse character, or underscore at end, remains its qualified presentation.

Labels and defaults must leave usable input space. Do not silently clip a meaningful filename/default into misleading text. The caller must shorten the label or select another suitable layout. The library does not own the entire display.

## 7. Architecture and ownership

Separate three responsibilities:

1. Editor: buffer, length, cursor, insertion/deletion and optional word commands.
2. Prompt controller: defaults, choices, empty policy, completion/cancellation and caller validation.
3. Renderer: layout, scrolling, cursor and messages, with a separate input adapter.

Use caller-owned bounded state and storage. Do not allocate large fixed work areas or a mandatory original-value/undo buffer. Keep one active synchronous prompt initially. Validation returns acceptance or an error description; it must not recursively open another prompt.

The complete controller interface distinguishes continue, submitted, cancelled and default accepted. A submission can contain zero bytes when allowed. Invalid semantic input remains editable with its cursor position, rather than being cleared. The editor enforces storage bounds; the caller validates utility-specific meaning.

Use shared source with conditional or selected-module inclusion first. Relocatable modules may be evaluated later without changing behavior. Core, word commands, prompt policy, choices and rendering must be independently selectable where practical. A choice-only consumer must exclude text editing, and a basic editor must exclude optional word commands. Verify emitted bytes; source separation alone is not evidence of omission.

Shared code reduces maintenance duplication, not the runtime size of each linked utility. Measure code, input state and optional storage per consumer. No permanent unloaded-TPA reduction is introduced by this library.

## 8. DUMP extraction and migration

The first implementation extracts DUMP Build 002's existing basic editor into `src/utilities/common/ui/input.inc`. Its legacy profile intentionally retains the existing keys, empty-Enter cancellation, result flags and ignored controls. This profile is not a claim that the full standard profile is already implemented.

DUMP retains its Find/Go To semantics, validation, case-sensitive patterns, significant spaces, 95-character raw input bound, decoded-pattern limits, page/search cancellation and bottom-row renderer. Do not add standard-profile keys or defaults silently during a source extraction. Changes such as text-field Ctrl-C or DEL aliases require a separate deliberate behavior update and qualification.

The extracted source receives caller-owned storage and keyboard/rendering hooks. It contains no DUMP filename/search logic, SCRN discovery, BDOS calls or prompt-label-dependent geometry. DUMP's builder expands the shared source for both cross and native builds. Preserve binary identity for this initial extraction where feasible.

Subsequent increments implement the standard event interface, optional word commands, policies/defaults and reusable renderers, then migrate selected consumers. Keep compatibility-profile adaptation explicit and temporary; avoid duplicating the edit algorithm.

## 9. Qualification

Require compiled-code coverage for insertions/deletions, word boundaries, movement limits, case/spaces, full buffers, prompt cancellation, empty policies, validated defaults, immediate choices, and invalid-input retention as each feature is implemented. Exercise nonmodal-message dismissal with the editing key handled exactly once and modal focus restoration.

Verify caller storage boundaries and register/stack contracts. Demonstrate omission of unused modules with basic, extended and choice-only builds when those profiles exist. Record code/state costs rather than assuming modularity guarantees small output.

Retain native ZSM4/cross parity and DUMP regression evidence for extraction. Any changed rendering/input behavior requires appropriate cpmsim and native Model 4 checks at different supported field widths, including cursor visibility, scrolling and ESC. Do not report future-profile coverage as passed by legacy-profile tests.

## 10. Standard profile implementation

The standard profile is implemented as selected build-time source, with the
[developer interface](../programmers/Shared%20Input%20Library.md) documenting
entry points, result codes, storage, callbacks and examples. `input.inc` uses
assembly-time selection so its insertion/deletion algorithm is shared with the
legacy profile. `wordstar.inc` adds optional Ctrl-A/F/Y without extra state.
`prompt.inc` provides empty policies, validated separate defaults and correction;
`choice.inc` provides immediate, case-insensitive responses without linking the
editor. `checks.inc` shares read-only validation and completion between them.

The controllers require caller rendering/input hooks and application-owned
state. A general standard renderer for default/choice layout and integration of
the standard profile into existing utilities are subsequent work. The original extraction retained byte-identical compatibility consumers; DUMP
Build 003 subsequently adopts the shared screen-field renderer while retaining
the compatibility editor. CONFIG remains unchanged.
No native display qualification of a new consumer is implied by controller tests.

[Shared library qualification](Shared%20Input%20Library%20Qualification.md)
records compiled behavior, native ZSM4 parity, actual module omission and costs.


The optional default and choice-error layout modules now implement bracketed
separate defaults and bounded diagnostics without hiding the full choice
question/default. Geometry that cannot retain the essential content fails
explicitly. These are transport-independent formatters with compiled/native
qualification; production standard-controller screen integration remains open.


The runnable `src/examples/uiexample.mac` reference consumer binds the standard
controllers, word editor, layout formatters and screen renderer to direct BDOS
input and callable SCRN cells. It provides integrated interaction qualification
and a practical developer template, without inventing defaults for existing
utilities or adding another distribution utility. Further production migrations
must respect each utility's specification and measured space budget.


### Current production consumers

| Consumer | Shared selection | Preserved policy |
| --- | --- | --- |
| DUMP Build 003 | Compatibility editor and shared screen-field renderer | Existing Find/Go To behavior and no invented defaults |
| CONFIG Build 014 | Compatibility editor and compact inline renderer | Existing startup/numeric validation and save behavior |
| SYSGEN Build 006 | Standard choice-only controller with compatibility input adapter | Only Y authorizes; any other response declines |
| UIEX developer example | Standard editor, words, text/choice controllers and layouts | Demonstration policy only; excluded from distribution manifests |

Select only modules an application actually needs. Utility-specific input policy
may require an adapter rather than adopting standard retry/default behavior.
Further migrations remain incremental, with specification review, size checks
and appropriate native interaction/failure regressions. CONFIG's full profile
still requires a space audit; ED/PIP compatibility boundaries remain intact.
