# Shared Input Library

BetterCP/M provides build-time Z80 assembly modules for single-line editing,
text prompts, choices and confirmations. Reuse them when adding utility prompts
instead of introducing another keyboard editor. They require no resident service,
RSX, BIOS change or BDOS extension of their own.

The modules are under `src/utilities/common/ui/`. Their behavior is defined by
the [Shared Input and UI Specification](../engineering/Shared%20Input%20and%20UI%20Specification.md).
The [module reference](../../src/utilities/common/ui/README.md) also documents
DUMP and CONFIG's compatibility bindings.

## Choose a profile

| Requirement | Select |
| --- | --- |
| Preserve the current DUMP/CONFIG editor contract | `input_source()` compatibility profile |
| Process one key at a time without doing I/O | `input_source(standard=True)` |
| Add Ctrl-A/F/Y to the standard editor | `input_source(standard=True, words=True)` |
| Run a complete text-entry prompt | Standard editor plus `controller_source(text=True)` |
| Ask an immediate single-character choice | `events.inc` plus `controller_source(text=False, choice=True)` |
| Use both text and choices in one utility | Standard editor plus `controller_source(text=True, choice=True)` |

The selection helpers are in `tools/shared_ui.py`. Expand exactly the same
selected source for cross and native builds. A native build can instead include
the selected modules directly, with the same `UISTD` and `UI_WORDS` definitions
and source order. `input_source` defines these flags and, in standard mode,
includes `events.inc`; do not include that constants file twice. Include
`checks.inc` once when selecting controllers manually. Word commands follow the
editor source. Controllers follow the editor where a text controller is used.

Current DUMP Build 002 and CONFIG Build 014 deliberately retain the compatibility
profile. The standard event engine and controllers are available to new
consumers, but do not silently change those utilities' keys, defaults or return
contracts. Migration is a separate behavior change requiring qualification.

ED's command language, BDOS Function 10 and the CCP are separate interfaces.
Do not replace their input semantics merely to reuse this library.

## Storage and ownership

All buffers and state belong to the caller. The library emits no work buffers
or persistent state of its own.

The standard editor needs these symbols:

| Symbol | Size and purpose |
| --- | --- |
| `EDITBUF` | Caller-selected capacity, 1 through 255 bytes; length-counted, not NUL-terminated. |
| `EDITLEN` | One-byte current length. |
| `EDITCUR` | One-byte insertion index, from zero through length. |
| `EDITSTART` | One-byte horizontal scroll origin for the renderer. |
| `EDITMAX` | One-byte capacity. |
| `EDITPROMPT` | Two-byte opaque prompt/label pointer for the renderer. |

Keep application state separate from the edit buffer. Cancellation returns a
result; it does not undo writes already made to your application data. Validate
and commit the returned candidate only after successful completion.

Text policy adds four bytes: `UP_MODE` (one), `UP_DPTR` (two), and `UP_DLEN`
(one). Choices add five bytes: `UC_LIST` (two), `UC_COUNT`, `UC_DEF` and
`UC_VALUE` (one each). Optional word commands add no state or undo storage.

One prompt may be active at a time. Callbacks must not recursively open another
prompt or reinitialize the active field.

## Standard event interface

Call `UE_INIT` with A=capacity, B=initial length and HL=prompt pointer. Preload
`EDITBUF` yourself for an explicitly prefilled field. Initialization checks the
capacity, length and printable ASCII contents, sets the cursor to the end and
resets scrolling. It does not draw or read input. Invalid initialization returns
`UI_BAD` with carry set without changing editing state.

Call `UE_KEY` with one logical input byte in A. It performs no I/O and returns:

| Constant | Value | Meaning |
| --- | --- | --- |
| `UI_MORE` | 0 | Recognized editing action; redraw even if movement was clamped. |
| `UI_SEND` | 1 | Enter submitted the editable value, possibly empty. |
| `UI_ABORT` | 2 | ESC or Ctrl-C cancelled. |
| `UI_DEF` | 3 | A controller accepted the separate default. |
| `UI_LIMIT` | 5 | Insertion was refused at capacity. |
| `UI_SKIP` | 6 | Unassigned key; preserve any existing message. |
| `UI_BAD` | 7 | Invalid initialization or controller configuration. |

Value 4 is reserved. `UI_DEF` and controller-configuration errors come from the
controllers, not ordinary key processing. The engine may clobber AF/BC/DE/HL;
read editing state from caller storage. Do not use condition flags to infer a
key event.

The basic standard engine recognizes Ctrl-S/D/G/H, ASCII DEL as Backspace,
Enter, ESC and local Ctrl-C. Printable ASCII inserts without trimming or case
conversion. With the word module selected, Ctrl-A moves a word left, Ctrl-F
moves a word right, and Ctrl-Y clears only the editable buffer. A word is a run
of non-space characters. Ctrl-U and overwrite mode are not implemented.

Physical and terminal aliases belong to an input adapter. The engine does not
parse ANSI/VT52 sequences or wait for an escape-sequence timeout.

## Text prompts

After `UE_INIT`, set `UP_MODE` to an empty-Enter policy:

| Constant | Empty Enter |
| --- | --- |
| `UP_CAN` | Cancel the prompt. |
| `UP_EMPTY` | Submit a legitimate empty value for validation. |
| `UP_NEED` | Display `UI_NEED` and continue editing. |
| `UP_DEF` | Validate and select the separate default. |

For `UP_DEF`, set `UP_DPTR` and `UP_DLEN` to a nonempty printable ASCII default
that fits the field capacity. The editable buffer must initially be empty;
combining a prefilled field and a separately displayed default is rejected.
Defaults remain separate and read-only; they are not copied into `EDITBUF`.

Call `UP_RUN`. It is synchronous and uses these caller hooks:

| Hook | Contract |
| --- | --- |
| `UIREAD` | Return one unechoed logical character in A. |
| `UIDRAW` | Draw the active field from state, clear any transient message and keep the insertion point visible. Render the label/default using the standard notation. |
| `UIMESSAGE` | Display NUL-terminated text at HL without changing the buffer, cursor, scroll origin or focus. |
| `UI_VALID` | Validate A=origin event, HL=candidate, B=length. Carry clear accepts; carry set rejects with HL pointing to a NUL-terminated error message. |
| `UI_CLOSE` | Remove editing presentation/restore the underlying interface; do not commit application data. |

Also provide `UILIMITMSG` and `UI_NEED` as message addresses. Hooks may destroy
general registers but must balance the stack. `UIDRAW` may update the renderer's
scroll origin. Validation is read-only: inspect the candidate without modifying
it, defaults, editing state or application state. If normalization is needed,
validate according to that policy and normalize into application-owned storage
when committing the accepted value.

On return, A is `UI_SEND`, `UI_DEF`, `UI_ABORT` or `UI_BAD`. For accepted input,
HL points to the candidate and B gives its length. An accepted empty value has
B=0 and a valid pointer; cancellation has HL=0 and B=0. Do not mistake B for a
BC length. Bad configuration returns carry set without drawing or reading input;
other controller completions return carry clear. Test the event explicitly.

The controller retains invalid input for correction. Unknown keys leave a
message visible; the next recognized editing action redraws and processes that
same key once. A rejected default is not silently replaced or accepted: the
user can type another value or cancel. `UI_CLOSE` runs once for submission,
default acceptance or cancellation, not for configuration rejection.

A typical call sequence is:

```text
        LD A,32
        LD B,0
        LD HL,PROMPT
        CALL UE_INIT
        JP C,BADSETUP
        LD A,UP_DEF
        LD (UP_MODE),A
        LD HL,DEFAULT
        LD (UP_DPTR),HL
        LD A,7
        LD (UP_DLEN),A
        CALL UP_RUN
        CP UI_ABORT
        JP Z,CANCEL
        CP UI_BAD
        JP Z,BADSETUP
        ; A=UI_SEND or UI_DEF, HL=candidate, B=length.
        ; Copy/commit now, before reusing this field's storage.
```

The renderer should show, for example, `Filename [OUTPUT.TXT]:`. A prefilled
field instead shows the existing value inside the editable area without a
second bracketed default.

## Choices and confirmations

Set `UC_LIST` to a counted printable-ASCII choice list, `UC_COUNT` to its length,
and `UC_DEF` to a permitted default character or zero for no default. Provide
`UC_VALUE` as the candidate byte. Case-insensitive letter choices return uppercase;
punctuation retains its byte value. Repeated entries are harmless set members.

Call `UC_RUN`. It does not include or reference the text editor. A permitted key
completes immediately without Enter. Empty Enter accepts a configured default
or cancels when none exists. ESC and Ctrl-C cancel. Invalid characters retain
or redraw the question; they never reach application input.

Bind `UIREAD`, `UI_VALID`, `UI_CLOSE`, `UC_PAINT` and `UC_ERROR`. The first three
have the contracts above. `UC_PAINT` renders the question, choices and optional
default; `UC_ERROR` displays the validator's message at HL while leaving those
choices visible. For example, show `Continue? (Y/N) [N]:`, not empty brackets.

Accepted results have A=`UI_SEND` or `UI_DEF`, HL pointing to `UC_VALUE` and B=1.
The candidate byte distinguishes Yes from No; neither is cancellation.
Cancellation returns `UI_ABORT`. The caller decides whether No skips a file
while Cancel stops a batch. Validation applies equally to typed and default
choices.

There is no keyboard-buffer flush. Acceptance consumes the chosen key only;
a following Enter or other queued character remains for the caller/input
adapter. Scripted callers should supply the documented immediate-response form.

## Rendering and console integration

The controllers own interaction, not the whole display. Supply a renderer for
reported geometry and the chosen message area. Keep labels/defaults readable;
select another layout rather than silently clipping meaningful values. A shared
bottom row needs no extra acknowledgment row.

`inline.inc` is the existing basic inline field renderer used by CONFIG. It
takes `UI_COLUMNS`, `UI_PUT` and `UI_MARK`, but does not automatically format
separate defaults or choice lists. It is not a terminal-size detector or a
complete standard prompt renderer. Observe its documented bounds in the module
reference. DUMP keeps its own screen-backend renderer.

During interactive redraw and messages, use output that does not intercept
input. Cooked BDOS output polls pending input and can consume Ctrl-S or warm-boot
on Ctrl-C. CONFIG's [binding](../../src/utilities/common/configinput.inc) shows
direct Function 6 input/output and an optional Function 178 cursor marker.
Callbacks must not consume keys merely to dismiss a message or flush typeahead.

## Build and qualify a consumer

New public symbols use at most eight characters because the cross assembler's
default significant-symbol limit is eight. Reserve the selected modules'
`UI`, `UP`, `UC`, `UW` and `EDIT` labels in your program; include each module
once. The compatibility profile retains its established labels and result flags.

Measure the emitted code and caller state. Current module-only code sizes,
excluding renderer, callbacks, field buffers and application data, are:

| Selection | Bytes |
| --- | ---: |
| Standard event editor | 263 |
| Editor with word commands | 377 |
| Basic editor plus text controller | 448 |
| Editor, words and text controller | 562 |
| Choice-only controller | 185 |
| Text, words and choices together | 699 |

Choice-only builds contain no edit buffer or editor code. Basic builds omit the
word module. A combined build includes validation/completion helpers once.
These are transient per-program costs, not shared resident allocation or a
promise that another utility has room for the complete profile.

Run `tools/test_shared_ui.py` and `tools/build_native_shared_ui.py` for the
library's compiled behavior, module omission and native/cross parity checks.
The generated fixtures contain controlled CPU callbacks; they are test inputs,
not distributed utilities. Source and qualification are linked from the
[shared UI engineering record](../engineering/Shared%20Input%20and%20UI%20Specification.md).

Then qualify your real renderer and transport on both applicable platforms,
including narrow fields, long input, visible cursor, cancellation, default
validation and message dismissal. Library tests alone do not establish terminal
rendering or utility save/recovery behavior. DUMP/CONFIG's current qualified
binaries are unchanged by selecting the new library profiles for other clients.


### Optional bounded choice formatting

`src/utilities/common/ui/format.inc` supplies `UF_PICK` for a choice controller's
`UC_PAINT` binding. Include it after selecting the choice controller; it uses
`UC_UPPER` and assumes `UC_RUN` has validated the choice list and default.
It is independent of the editor and performs no terminal I/O.

Provide `UF_LABEL` (word pointing to a NUL-terminated printable ASCII label,
including desired trailing spacing), `UF_WIDTH` (available columns), and
`UF_BUF` (256 caller-owned bytes). It formats, for example, `Erase? (Y/N) [N]`.
No default means no bracketed suffix. Choice letters are uppercased.

Success returns carry clear, A=`UI_MORE`, HL=buffer and B=byte length, with a
NUL terminator after the text. Failure returns carry set and A=`UI_BAD`, leaving
the buffer untouched. Invalid labels, size arithmetic overflow and insufficient
width fail rather than truncate. Registers AF/BC/DE/HL may change; choice and
editor state do not. The formatter adds 148 code bytes and three configuration
bytes, plus its output buffer.

The caller must check failure, position and clear the prompt row, and emit the
returned bytes with direct output. Reserve any column that would trigger wrap;
this routine neither discovers geometry nor draws a cursor. It also does not
implement `UC_ERROR`: retaining choices alongside a validation diagnostic still
requires the caller's layout. Test with `tools/test_shared_ui_format.py`.
