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
| Preserve an existing append-only/BS/DEL/Ctrl-U contract | `events.inc` plus `append.inc` (compatibility only) |
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


### Shared screen field renderer

`screen.inc` exports `UR_DRAW` for either editor profile. The caller clears its
prompt row, prints the label, and calls with A=screen width and D=printed label
length. A label must leave at least one caret cell. Invalid geometry returns
carry set/A=7 before output or state changes; success clears carry. Other
registers may change. Valid initialized editor state is required.

Bind `UR_PUT` (A=plain character), `UR_MARK` (A=caret character) and `UR_POS`
(C=absolute column on the caller's prompt row). Character hooks preserve
BC/DE/HL; the position hook preserves DE/HL. This module neither emits terminal
escape sequences nor discovers geometry. It displays a horizontally scrolled
field, reserves the final available cell for the caret, and positions the cursor
back on that cell. The caret uses the underlying character or underscore at
end of input. Only `EDITSTART` changes; there is no allocated renderer state.
Scroll comparisons use subtraction so length/cursor 255 cannot wrap.

DUMP Build 003 uses this renderer through its existing SCRN backend, with label
lengths measured rather than hard-coded. It retains the compatibility editor
and its field validation. CONFIG retains its smaller inline renderer pending a
space audit. This integration does not yet provide standard text/default layout
or a general choice-error presentation. Run `tools/test_shared_ui_screen.py`
and DUMP's compiled, native-build and real-platform screen checks after changes.


### Standard separate-default prefix

Select `default.inc` for `UT_TEXT`, which uses the text controller's validated
configuration and caller-owned `UF_LABEL`, `UF_WIDTH`, and 256-byte `UF_BUF`.
The label is NUL-terminated printable ASCII, including desired trailing spacing.
An empty `UP_DEF` field formats `label[DEFAULT] `; once editing contains text,
the prefix becomes just the label. Deleting back to empty restores the visible
default. The default is never copied into or counted as editable input.

Success returns A=0/carry clear, HL=buffer, B=prefix length, NUL appended. At
least one cell remains for the insertion caret. Invalid labels, size overflow
or insufficient width return A=7/carry set without changing the output buffer.
AF/BC/DE/HL may change; editor/controller state and configuration do not. Call
after `UP_RUN` has validated the default's pointer, length and printable data.
The module adds 128 code bytes, no state beyond the common formatter bindings.

A screen caller clears its shared prompt row, emits the prefix with direct
output, then passes D=returned prefix length and A=`UF_WIDTH` to `UR_DRAW`.
Handle a layout failure before reading input; controllers do not themselves
interpret a rendering hook's return flags. A caller must preflight its longest
possible prefix for the chosen geometry, or explicitly choose another layout.
It must not silently drop a default to make a narrow field fit.

### Choice validation diagnostics

Select `choiceerror.inc` alongside `format.inc` and the choice controller.
`UE_ERROR` takes HL pointing to a NUL-terminated printable diagnostic. It retains
the complete question, choice list and default produced by `UF_PICK`, appends a
space and as much diagnostic text as fits `UF_WIDTH`, and marks shortening with
`~`. For example: `Erase? (Y/N) [N] Invalid value.`. There must be two spare
cells beyond the complete question. Only diagnostic text may be shortened.

Success returns A=0/carry clear, HL=buffer and B=length, NUL appended. Failure
returns A=7/carry set; the buffer may contain partially formatted text and must
not be drawn. Insufficient space requires another explicit caller layout.
Displayed diagnostic bytes must be printable ASCII. This module adds 64 code
bytes, no extra state, and preserves editor/choice configuration and state.

Both routines format bytes only. They perform no terminal I/O, clear no rows,
and consume no keys. The next key remains the controller's responsibility; no
acknowledgment-only input is added. They have compiled and native-assembler
qualification, not a claim of real-platform default/error screen integration.
Use `tools/test_shared_ui_layouts.py`, then
`tools/build_native_shared_ui.py --extra-fixture build/shared-ui/layouts.mac`.


### Runnable reference consumer

[`src/examples/uiexample.mac`](../../src/examples/uiexample.mac) is a complete
consumer of the standard editor, word commands, text/choice controllers, default
and choice-error layouts, and screen renderer. It is a developer example, not a
distribution utility or an alteration to DUMP/CONFIG's prompt policies.

Build it with `tools/build_ui_example.py`; output is
`build/shared-ui/UIEX.COM`. It requires a callable SCRN backend with at least
40 columns and four rows. On cpmsim load `ANSISCRN` and `ANSI`; on Model 4 load
`M4SCRN` and `ADM3A`, then run `UIEX`. `UIEX /40` exercises a narrow prompt
region on the same screen. The example's minimal command-tail handling uses
any nonempty tail to select that demonstration; it is not a utility parser.

The example clears through typed position/erase primitives, preserves separate
body rows, and puts prompts/messages on the last row. Its keyboard hook uses
unechoed direct BDOS 6 input. Rendering uses literal SCRN cells rather than
cooked BDOS output, so redraws cannot consume Ctrl-S/Ctrl-C as console flow
control. Application state is separate from provisional editing state.

The deliberately simple validator rejects text `BAD` and choice `Y` to make
correction/error paths easy to exercise. Start with `BAD`, press Enter, then
Ctrl-Y to clear and restore the visible default; type a replacement or press
Enter to accept `DEFAULT`. At the choice prompt, `Y` shows a diagnostic while
retaining `(Y/N) [N]`; `N` or Enter completes the demonstration. Ctrl-C/ESC cancel
locally. A final key returns to the CCP. No files are changed by the program.
This validation policy is demonstration code, not shared library policy.

Run `tools/test_ui_example.py` for compiled interaction checks. Real-platform
campaigns are `tools/test_ui_example_live.py` (requires test-only `pyte`) and
`tools/test_ui_example_model4.py`, on disposable images. Native assembly parity
uses `tools/build_native_shared_ui.py --extra-fixture build/shared-ui/uiex.mac`.
Use this example to adapt your application's own validation and restoration
hooks; select only the modules it needs and remeasure its complete binary.


### SYSGEN choice-only compatibility consumer

SYSGEN Build 006 uses `common/sysgeninput.inc` for both installation approval
and existing-package replacement. Its caller has already printed the original
question, so paint/close hooks do nothing. The read adapter reuses SYSGEN's
existing case-folding direct-input routine, passes Y/N to the choice controller,
and maps every other response to local cancellation. `SG_ASK` returns Y or N
for typed choices, zero for cancellation or bad configuration. This preserves
SYSGEN's stricter existing rule: only Y authorizes, every other key declines.
It deliberately does not adopt the standard controller's retry-on-invalid-key
behavior or introduce a default, extra question or typeahead flush.

The complete binding is 220 bytes (185 shared code, 28 adapter code, a two-byte
choice list and five bytes of controller state). No editor, word module,
formatting buffer or screen dependency is linked. Cross/native builders use the
same `expand_sysgen_ui` selection helper. The 5,734-byte program still uses its
existing 4000h–8FFFh payload workspace and 36K TPA guard; unloaded OS TPA is
unchanged. `tools/test_sysgen_shared_choice.py` checks every nonzero key byte,
fail-closed configuration handling, typeahead preservation and /VER purity.


### Shared one-key confirmation adapter and DUP

`ui/confirm.inc` now supplies the common any-non-Y-declines adapter used by
SYSGEN and DUP Build 005. The caller prints its original question, then calls
`UI_ASK` (or its utility entry alias). Bind `KEY` to return an unechoed,
uppercase-folded key. The adapter uses the shared choice-only controller,
returns Y/N for those typed responses and zero for cancellation or malformed
configuration, consumes one key and leaves typeahead untouched. It adds neither
a default nor an invalid-key retry. Paint/close hooks intentionally do nothing.

Select through `confirmation_source()`, `expand_sysgen_ui()` or `expand_dup_ui()`
in `tools/shared_ui.py`. No editor, word module, field renderer or formatting
buffer is included. The binding remains 220 bytes including two choice bytes
and five controller-state bytes. Extracting it preserves SYSGEN Build 006's
qualified binary exactly. DUP's two destructive format/copy approval sites call
`DP_ASK`; its menus, drive selection and operation/cleanup logic are unchanged.
DUP Build 005 is 8,483 bytes, 220 more than Build 004, with the same private
buffers, stack and 51K TPA requirement. No resident allocation changes.

`tools/test_dup_shared_choice.py` and `tools/test_sysgen_shared_choice.py` share
the key-safety, invalid-configuration and version-purity campaign. Native DUP
assembly/parity is available through `tools/build_native_dup.py`.


### ERA confirmation and recovery compatibility consumer

ERA Build 004 selects `common/erainput.inc` through `expand_era_ui()` in both
build paths. It shares the choice-only controller, with two context-specific
bindings: `EU_YN` returns uppercase Y/N or byte 3 for local cancellation;
`EU_RCHO` returns uppercase R/S/A, literal `?`, or byte 3. Both preserve
BC/DE/HL/IX. ERA's original caller retains echo/newline, help, accounting,
retry/skip/abort, protected-file admission and unattended-mode decisions.

The binding intentionally preserves ERA's existing policy. Invalid confirmation
keys retry silently; invalid recovery keys repeat `R/S/A/?`. Enter and ESC are
invalid in both contexts, while Ctrl-C cancels. There is no default, typeahead
flush or new cancellation alias. Raw input still uses ERA's existing direct
BDOS 6 reader. The adapter maps Enter/ESC to an invalid choice rather than
adopting the generic controller's cancellation policy. Each entry resets its
choice pointer/count/default and context; confirmations and recovery may share
the controller state safely. `/Y` bypasses input in the application as before.

The complete selection is 280 bytes: 185 controller code, 83 adapter code,
six choice-list bytes and six state bytes. Replacing ERA's old recovery display
site removes six bytes, for 274 bytes of migration growth. An additional
8-byte safety correction binds the single-file prompt to the selected record
rather than the classifier's one-past-list cursor. Final ERA is 7,897 bytes,
282 larger than Build 003. Its existing 256-byte stack remains; the bounded
selection heap begins 282 bytes later. No editor, formatting buffer or resident
allocation is added.

`tools/test_era_shared_choice.py` retains the original Y/N routine with source
provenance and links it to the unchanged production console helpers. It compares
all byte inputs, returned flags, echo, register/stack and typeahead behavior,
then checks recovery choices, context switching and exact target naming.
Native assembly uses `tools/build_native_era.py` with paths appropriate to your
installed CP/M tools. See the ERA shared-input qualification for real-platform
interaction and disk-state evidence; recovery fault injection remains a
compiled-code qualification, not a claim of native hardware faults.

### REN choice compatibility consumer

`src/utilities/common/reninput.inc` binds confirmation (`RU_YN`), collision
(`RU_COL`) and recovery (`RU_FAIL`) to the choice-only controller. The caller
owns rename/help/retry/skip/abort policy. The binding retains cooked BDOS 1 echo
and REN's historical AND-5F folding, preserves BC/DE/HL/IX, and returns a selected
uppercase choice or byte 3 for Ctrl-C. No default, input flush or ESC alias is
introduced. Invalid Y/N input silently retries; other contexts repaint their
original full question.

Build 007 is 5,856 bytes (+307 transient bytes), with the same 128-byte stack and
no resident allocation. The rename ledger begins correspondingly later; its
bounded refusal remains required. Build 007 left REN's replacement-filename editor unchanged; Build 008
extracts it separately as described below. See [qualification](../engineering/REN%20Shared%20Input%20Qualification.md).


### REN replacement-name compatibility profile

REN Build 008 also uses `ui/append.inc`. This is a separate small, I/O-free
compatibility event engine for historical append-only fields; use the standard
editor for new fields. It preserves REN's original BS/DEL last-byte deletion,
Ctrl-U clear, Ctrl-C abort, empty submission and sticky overflow policy. It does
not add the standard editor's cursor movement, ESC cancellation, redraw or
printable-input filtering.

Provide `UA_BUF` (capacity bytes), `UA_LEN`, `UA_FULL`, and `UA_MAX` (one byte
each). `UA_INIT` takes A=capacity 1..255, clears length/overflow and returns
`UI_MORE`; zero capacity returns `UI_BAD` without changing state. `UA_KEY` takes
a raw byte and returns `UI_MORE`, `UI_SEND`, `UI_ABORT` or `UI_LIMIT`, with carry
clear. AF/BC/DE/HL may be clobbered; no I/O occurs. CR submits even empty input;
other unassigned bytes append literally, so callers must validate them. There
is no terminator. `UA_FULL` remains set after a refused append even if the user
backspaces or submits. The caller must reject such input. Ctrl-U and fresh
initialization clear that flag. Do not treat `UI_SEND` as proof of validity.

REN aliases its existing `R_IBUF`, `R_ILEN` and `R_IFULL`; only `UA_MAX` adds a
state byte. Its caller retains BDOS 1 echo, ASCII-only uppercase conversion,
newlines, blank-to-collision behavior, strict filename parsing and commit/abort.
Build 008 is 5,884 bytes (+28 over Build 007), with the same 128-byte stack and
no resident allocation. See [qualification](../engineering/REN%20Name%20Field%20Qualification.md).

### COPY prompt compatibility binding

`common/copyinput.inc`, selected only by the transient COPY builder, binds
`CU_OW` overwrite choices and `CU_VER` verification choices to the choice
controller. Raw BDOS 6 input waits through no-key/CR/LF and retains Ctrl-C.
Unknown input (including ESC) maps to the explicit help member while retaining
the original folded byte for the caller's existing echo/help path. Application
code alone owns overwrite/skip-all state and retry/cleanup. Do not substitute
REN's invalid-input policy.

COPY's replacement field reuses the append compatibility engine and existing
126-byte storage. CR and LF submit; BS/DEL erase the last byte using the existing
BS/space/BS echo. Ctrl-U is literal rather than clear. For such policy adapters,
`UA_PUT` accepts a literal byte without interpreting editing controls and returns
`UI_MORE` or `UI_LIMIT` with the same bounds/sticky-overflow behavior as ordinary
append. The label emits no extra bytes in existing consumers. The caller must
initialize valid state and validate the candidate before committing it.

Build 005 is 12,010 bytes (+307 transient bytes), with no resident allocation or
additional text buffer. MOVE currently has no interactive prompt to migrate.
See [qualification](../engineering/COPY%20Shared%20Input%20Qualification.md).
