# BetterCP/M DUMP.COM Engineering Specification

**Enhanced read-only viewer design — range display revision 2026-10-26**

## 1. Status, scope and references

This is the normative design for the enhanced DUMP. It supersedes the initial
DRI-only specification and the subsequent review addendum. DUMP 1.0 revision 006 implements this design. Qualification scope and limitations
are recorded in [Enhanced DUMP Qualification](DUMP%20Enhanced%20Qualification.md);
this is not a claim of final Utilities Disk acceptance.

The implemented DUMP 1.0 Build 001 is the initial DRI-compatible Z80 clone with
BetterCP/M `/VER`. Its evidence remains historical evidence for that binary:
[DUMP Baseline Qualification](DUMP%20Baseline%20Qualification.md). It does not
qualify the enhanced parser, viewer, search or DU support specified here.

DUMP displays one file without modifying it. Its normal mode provides streaming
hexadecimal and ASCII output; `/P` adds interactive viewing. `/BARE` preserves
DRI CP/M 2.2 DUMP's observable reading, display and interruption behavior.

Implement in native Z80 assembly using ZSM4. The DRI reference source and binary
are retained under `third_party/dri-dump/`; they define compatibility behavior,
not the required implementation technique. The unused DRI source string
`FILE DUMP VERSION 1.4` is not a sign-on message.

Use the shared [DU syntax](208%20Extended%20DU%20Syntax.md) and
[Visual Identity](../../specifications/VISUAL-IDENTITY.md).

## 2. Command line and validation

```text
DUMP file
DUMP file /P
DUMP file /FROM=offset
DUMP file /LEN=count
DUMP file /FROM=offset /LEN=count
DUMP file /40
DUMP file /P /40 /FROM=offset
DUMP file /BARE
DUMP /BARE file
DUMP /VER
```

Switches may precede or follow the filename and are case-insensitive. DUMP
shall parse its own command tail, identify the filename and construct its FCB.
It must not assume the first CCP-prepared FCB names the file: in
`DUMP /BARE FILE.COM`, that FCB may represent `/BARE`. No CCP change is required.

Validate the entire tail syntactically before opening the file. File-dependent
position bounds are checked after obtaining its length and before any data
is displayed. Require exactly one exact
filename except for an exact `/VER` query anywhere in the tail. Reject missing or extra operands,
wildcards, selectors, unknown switches, malformed values and incompatible
combinations. Print a diagnostic identifying the offending option or operand
where applicable, then return to the CCP. Never fail silently. For example:

```text
DUMP: Invalid option or operand: /UNKNOWN
```

Repeated independent flags are harmless. For value options such as `/FROM=` and `/LEN=`,
the last valid value wins, but every occurrence must be valid; a later valid
occurrence does not excuse an earlier malformed one.

`/VER` ignores all other arguments. `/BARE` rejects `/P`, `/40`, `/FROM=`, `/LEN=`
and all other extensions rather than ignoring them. Deferred `/FIND=` remains unknown.

### 2.1 File addressing

Enhanced mode accepts one exact filename in one DU, for example `B7:FILE.COM`,
using shared BetterCP/M operand conventions. Unqualified names inherit the
caller's drive and user. Drive-only names inherit the caller's user. Compound
selectors, multiple DUs and multiple files are excluded.

`/BARE` accepts only ordinary optional drive qualification, such as
`B:FILE.COM`, in the caller's current user area. It rejects explicit user/DU
qualification. Its sealed compatibility path begins after command parsing and
FCB construction; `/BARE` does not require using the CCP's original FCB.

## 3. Version identification

`DUMP /VER` shall print the metadata-owned utility version and revision using the
finalized compact implied-corner layout:

```text
DUMP 1.0 (nnn)
  - - -
 | BetterCP/M Utilities
 | Hexadecimal File Display
```

Use ordinary 7-bit ASCII and CR/LF. No file access, monitor provider, terminal
controls or warm boot is required. Ordinary output has no identification banner.
`nnn` is a metadata placeholder, not a literal or independently maintained value.

## 4. File representation and implementation boundaries

All modes display the CP/M logical-record representation: every byte of every
successful 128-byte logical record, including final-record padding. File length
for navigation and search means this record length, not an inferred application
byte count. `1Ah` is ordinary data, not EOF. Do not strip high bits, expand tabs,
normalize line endings or interpret binary data as terminal commands.

DUMP shall not write files, directories, sectors or attributes; rename, truncate
or allocate file blocks; or modify the input by any other means. Use BDOS file
services, not platform-specific direct disk access.

Enhanced access shall be position-oriented with bounded memory. The complete
file and complete match list must not need to fit in RAM. Pages must be
regenerable from their offsets. Random or suitable sequential BDOS access may
be used; reverse search may scan backward or rescan earlier regions. Support
positions beyond 64 KiB without wrapping, subject to BDOS's supported range.

Save the entry stack pointer, use sufficient private stack space, restore the
caller's drive/user on normal exit and DUMP-handled errors or cancellations,
and return directly to the caller with `RET`, without an intentional warm boot.
Clean up DUMP's resources on all such exit paths. Lower-level nonreturning
BDOS/BIOS aborts remain outside DUMP's control.

## 5. Enhanced row formats

Offsets are exactly eight uppercase hexadecimal digits with leading zeroes.
Byte values are exactly two uppercase hexadecimal digits. Status positions
use the same eight-digit offset format. There is no 64 KiB offset wrap.

### 5.1 Wide output

A full row occupies 76 columns and represents 16 bytes:

```text
00001230  00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  ................
```

The fields are eight offset digits, two spaces, eight individually spaced byte
values, two spaces, eight individually spaced byte values, two spaces and
sixteen ASCII characters. The wider gap separates the two eight-byte groups.
This layout applies to streaming and paged wide output.

### 5.2 Required `/40` output

`/40` is required in the initial enhanced release, without an implementation-
cost condition. It represents eight bytes in 37 columns:

```text
00001230  41424344 45464748  ABCDEFGH
```

The fields are eight offset digits, two spaces, four contiguous hex byte values,
one space, four more contiguous hex byte values, two spaces and eight ASCII
characters. `/40` is selected only on invocation, not toggled interactively.
It changes row width and page byte capacity, not search or offset semantics.
It can be used with streaming output or `/P`, never `/BARE`.

### 5.3 ASCII column

Display bytes `20h` through `7Eh` directly, including spaces. Render `00h`–`1Fh`,
`7Fh` and `80h`–`FFh` as `.`. Hex values and searched bytes remain unchanged.
Never send file bytes as terminal controls.

## 6. Starting positions, Go To and empty files

`/FROM=` and interactive `G` accept one to eight hexadecimal digits, optionally
followed by `H` or `h`. Digit case is immaterial. Examples: `1237`, `1237H`,
`00ff`. Input is always hexadecimal, never implicitly decimal. Reject signs,
missing digits, invalid characters and overflow without truncation or wrap.

A position must name an existing byte: zero through record-length minus one.
EOF itself is invalid. Check the supported BDOS position range as well as file
length. `/FROM=` begins displaying at the exact requested byte. Row addresses
remain aligned to multiples of 16 in wide mode or eight in `/40`; byte and ASCII
columns before the requested byte are spaces. For example, `/FROM=1237H` starts
with row address `00001230`, seven blank byte/ASCII positions, then byte `1237h`.
Do not shift bytes left or change subsequent row alignment. Go To still places
the containing aligned row at the top; it does not introduce a new clipping boundary.

An invalid or out-of-range `/FROM=` reports a diagnostic and exits without
emitting file data; do not clamp it. Without `/FROM=`, start at zero.

With no explicit `/FROM=`, an empty file prints `Empty file` and returns normally,
including with `/P`; do not enter an empty viewer. Explicit `/FROM=0` or any
other position on an empty file is out of range. `/BARE` has no empty-file message.

`G` is positional only, not a string-search command. Empty Enter or ESC cancels
it, preserving page, pattern and search continuation state. Invalid or out-of-
range input produces a diagnostic and permits correction in the same prompt,
retaining the entered text for editing. Use the shared bottom row for diagnostic
and input; no extra row is reserved. Only successful Go To changes the page
and resets the continuation anchor as defined in Section 10.

### 6.1 Maximum byte count and interactive range

`/LEN=count` accepts the same one-to-eight-digit hexadecimal syntax and optional
H/h suffix as `/FROM=`. It is a maximum number of displayed file bytes, not an
ending offset, row count or decimal quantity. Last valid value wins; validate
every occurrence syntactically. Zero is valid and displays no data, performs no
data reads and does not enter `/P`. File opening, explicit `/FROM=` bounds and
physical-empty-file handling still occur first. Thus an empty file still says
`Empty file`; explicit `/FROM=0` on it remains an error, even with `/LEN=0`.

With `/LEN=`, the fixed range begins at the final `/FROM=` (default zero) and
ends exclusively at the smaller of record EOF and the mathematical sum of start
plus count. A sum beyond 32 bits saturates at EOF; never wrap or reject a valid
count merely because fewer bytes remain. Numeric values longer than eight digits
remain invalid. Validate every `/FROM=` against physical EOF as before.

Only bytes within that interval are displayed. Blank both hex digits and the
ASCII cell for every excluded position in the initial/final row, retaining all
separators and the 76/37-column width. Emit no wholly excluded data rows. A count
past EOF displays the available bytes without an error or artificial padding.
Buffers retain aligned slots, with bounded additional counters only; excluded
slots do not issue byte reads (BDOS still reads whole 128-byte records).

In `/P`, `/LEN=` defines the fixed range for the whole invocation. Page Down
adds the screen byte capacity and stops at its exclusive end. Page Up subtracts
capacity and clamps to the aligned row containing the range start. The existing
`Beginning of file` / `End of file` status messages denote range boundaries in
this mode. Go To must name an existing byte inside the range; it retains the
range and count, and places the containing row at the top. It does not restart
the count. Invalid/cancelled/failed movement preserves the page and search state.
Find and continuation stay inside the fixed range; the entire pattern must fit.
Search and paging mask range-edge cells by the same rule as initial display.
Continuation anchors use the first included byte when a row starts before the
range. Existing overlap, cancellation and transactional error rules apply.

Without `/LEN=`, `/FROM=` remains an initial position: subsequent paging, Go To
and search can access the whole file, including earlier bytes. Only the initial
page's leading cells are clipped at `/FROM=`; successful repositioning restores
ordinary whole-row display. A new Find starts at the first included byte of that
page. Go To and search continue to display their containing aligned row as before.

## 7. Enhanced streaming output

Without `/P` or `/BARE`, display enhanced rows from the selected starting row
through the selected range (EOF when `/LEN=` is absent), then return on a fresh line. No monitor provider is required.

Ctrl-C stops output and returns to the CCP; consume it so it is not pending
at the next command prompt. Other keys are not dump-abort requests. WordStar
viewer navigation does not apply to streaming output. `/BARE` retains its
separate any-pending-character, nonconsuming interruption rule.

A distinguishable read error reports the failing byte offset and stops; it
must not be represented as ordinary EOF.

## 8. Paged viewer and screen requirements

Before entering `/P`, verify usable active monitor/backend capabilities for
page redraw, cursor positioning and the shared bottom row. A loaded provider
name alone is insufficient. If unavailable, explain the missing requirement and
return to the CCP. Do not automatically load a provider or silently fall back
to streaming. The broader monitor-availability usability issue remains deferred
for architectural review; this rule does not claim to solve it.

Use actual reported width and height, not assumed 80-by-24 geometry. Wide data
rows require 76 columns; compact rows require 37. At least one data row and one
shared bottom row must fit. If dimensions are insufficient, report the required
dimensions and return to the CCP without truncation or an automatic `/40`
selection. Suggest `/40` if that layout would fit.

Reserve exactly one physical bottom row. All other usable rows contain data:
23 on a 24-row screen, 39 on a 40-row screen. Wide mode therefore displays up
to 368 bytes on a 24-row screen. `/40` changes bytes per row, not screen height.
Do not invent dimensions the backend does not report.

### 8.1 Shared bottom row

Normally show the principal available commands. Status messages replace hints
until the next recognized command; after processing that command, show its
resulting status or restore hints. Examples are `Beginning of file`, `End of
file`, `Pattern not found` and `Match at 00001237`.

Find and Go To prompts temporarily replace hints until submission or cancellation.
Messages and prompts must clear/replace only this row without scrolling or
overwriting data. Do not reserve a second interface row. Exact compact hint
wording is an implementation presentation choice, and must fit reported width
and reflect whether punctuation keys navigate pages or search matches.

### 8.2 Prompt editor

Text-entry prompts use these WordStar controls:

| Key | Operation |
| --- | --- |
| Ctrl-S | Move one character left |
| Ctrl-D | Move one character right |
| Ctrl-G | Delete character under cursor |
| Ctrl-H / Backspace | Delete character before cursor |
| Enter | Submit |
| ESC (`1Bh`) | Cancel |

Ordinary characters insert at the cursor, shifting following text right.
Movement or deletion beyond an end leaves input unchanged. Long input scrolls
horizontally within the shared row, keeping the insertion point visible; it
must not wrap into data rows. Show a reverse-video cell at the insertion point,
using the underlying character or an underscore at end of input; redraw it
without leaving stale cursor cells. This is software-rendered so it also works
on Model 4 without a hardware cursor. Editing controls do not invoke viewer navigation
or cancellation. Existing pattern and offset limits remain in force.

## 9. Viewer navigation

| Key | No active search | Active search |
| --- | --- | --- |
| `.` | Page Down | Next occurrence |
| `,` | Page Up | Previous occurrence |
| Space or Ctrl-C | Page Down | Page Down |
| Ctrl-R | Page Up | Page Up |
| `F` | New Find | New Find |
| `G` | Go To | Go To |
| `Q` | Quit | Quit |

Ctrl-C means Page Down only during normal viewer navigation, not a system-wide
redefinition. Unrecognized navigation keys are ignored without a bell, message,
page movement or search-state change. Prompt input follows its own rules.

Page Down advances by one page's data capacity unless the current page already
includes EOF. Page Up subtracts that capacity, clamping to zero. Thus a search
or Go To can leave less than one page above the display, and Page Up still
moves to the first page. This also applies from a partial final page.

At BOF, Page Up leaves state unchanged and shows `Beginning of file`. If the
current page includes EOF, Page Down leaves state unchanged and shows `End of
file`. These are bottom-row messages without bells or acknowledgment. A partial
final page stays visible; reaching EOF does not exit the viewer.

Successful paging retains the pattern but resets its continuation anchor.
Failed boundary movements do not reset it.

## 10. Find and search continuation

### 10.1 Input and interpretation

`F` first asks for the pattern, then asks how to interpret it:

```text
Find: CD 05 00
Search as (H)ex or (A)SCII? H
```

Do not guess the interpretation: `41 42` may mean literal ASCII or two hex bytes.
Hex accepts contiguous pairs or spaces between pairs: `CD0500` and `CD 05 00`
are equivalent. Hex digit case is immaterial. Odd digits, nonhex characters or
spaces splitting a byte pair are invalid; diagnose and allow re-entry without
exiting DUMP. ASCII matches exact entered bytes, preserving case and spaces;
`Hello` does not match `HELLO`. Do not trim meaningful ASCII spaces or normalize
text. Binary/control byte patterns can be entered as hex.

The limit is 32 decoded bytes: 32 ASCII characters or 64 hex digits, plus optional
spaces between byte pairs. Do not mistake raw spaced-entry length for decoded
length. Overlong patterns receive a diagnostic and permit re-entry; never
truncate silently. Empty Enter cancels before the H/A prompt. An all-space
Hex entry cancels; an all-space ASCII entry is meaningful within the limit.

### 10.2 Origin, matches and continuation

A new Find searches forward inclusively from the current page's first byte,
not automatically from zero. Use `G 0` first to search from BOF.

On success, place the row containing the match's first byte at the top and show
its exact unrounded position, such as `Match at 00001237`. Highlighting is not
required. The new pattern becomes active and replaces any previous pattern.

Search permits overlap. With no intervening repositioning, next/previous
occurrence seeks a match starting strictly after/before the last successful
match's start. Searching `ABA` in `ABABA` therefore finds offsets zero and two.

Successful paging or Go To retains the pattern but resets its anchor to the
new page's first byte. From that anchor, next occurrence searches forward
inclusively; previous occurrence finds the nearest start strictly before it.
Invalid Go To or a boundary command that does not move leaves the anchor intact.

Do not wrap. A continuation with no match before its boundary shows `No further
matches` and leaves the page and existing continuation state unchanged. A valid
new Find completing without a match shows `Pattern not found`, leaves the page
unchanged, but makes the new pattern active. With no established match, its
anchor is the page's first byte (forward inclusive, backward strictly before).

### 10.3 Cancellation and read errors

ESC cancels either Find prompt or an in-progress search. A new Find is provisional
until completed; cancellation preserves the old page, active pattern and
continuation state. No Ctrl-G cancellation alias is provided; Ctrl-G edits input.

A distinguishable search read error likewise preserves the page and previously
committed pattern/continuation state. A failed continuation does not advance its
anchor. Show `Read error at XXXXXXXX` with the failing byte offset in the bottom
row. Never report an incomplete search as `Pattern not found` or `No further
matches`.

## 11. Viewer I/O failures

On a distinguishable page-read failure, retain the last complete valid page and
report the failing byte offset in the shared row. Do not commit a partial
replacement page as complete. Failed repositioning must not advance the page or
its associated search anchor.

If reading the initial page fails, no valid page exists: diagnose the failing
offset, clean up and return to the CCP, rather than entering an empty viewer.
These rules apply when BDOS returns a distinguishable failure. Lower-level
operator recovery and nonreturning aborts are outside DUMP's control.

## 12. Sealed `/BARE` compatibility contract

Following ordinary filename parsing and FCB construction, preserve these DRI
behaviors independently of enhanced code:

- Clear the FCB current-record field and open with BDOS. Open returning `FFh`
  prints `NO INPUT FILE PRESENT ON DISK`, preceded by CR/LF, then exits through
  the common terminating CR/LF path. Parser errors remain Section 2 errors.
- Read sequentially in 128-byte records. Display every successful record,
  including `1Ah`, binary bytes and padding. Any nonzero read completion
  terminates without an added DUMP-specific read-error diagnostic.
- Print 16 bytes per line, hexadecimal only, each byte preceded by one space.
  Four-digit uppercase offsets begin at `0000`, increment by `0010` per row,
  and wrap modulo 65536. No ASCII column or command bar is present.
- At each 16-byte boundary, emit CR/LF, check console status, and only if no
  character is pending print the row offset and bytes. Any pending character
  stops output without consuming it. Once a row begins, finish its 16 bytes
  before the next check. Output therefore begins with CR/LF before the first
  data row, and all normal exits emit the common final CR/LF.
- Empty files have no data rows or added empty-file message. EOF, interruption
  and open failure return directly through the saved entry stack without an
  intentional warm boot.

Examples:

```text
0000 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
0010 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
```

DRI's private 64-byte stack and use of DMA buffer `0080h` are implementation
details, not mandatory addresses or sizes. Provide safe private storage and
preserve observable behavior. The original default-FCB-only implementation
remains documented by the historical baseline qualification, not a requirement
to abandon the enhanced command parser.

## 13. Deferred and excluded features

Defer `/FIND=` until a concrete command/script workflow and match/no-match/error
reporting contract justify it. The current CCP uppercases command tails,
including quoted text, so command-line case-sensitive ASCII cannot be promised
without a separate decision. Interactive Find preserves entered case.

`/LEN=` is defined in Section 6.1; only `/FIND=` remains deferred.

No editing, patching, memory/sector/track dumping, directory inspection or repair,
file comparison, archive browsing, decompression, disassembly, multi-file viewing,
extra output-redirection mechanism, decimal/octal display or record annotations
are included. Monitor auto-loading is not introduced.

## 14. Qualification requirements

All enhanced behavior requires new evidence. Reuse historical baseline evidence
only for its identified binary and scope. Require native ZSM4 build parity and
representative execution on cpmsim and native/emulated Model 4, including actual
screen evidence for `/P`. A host CPU model alone does not qualify terminal output.

Required coverage includes:

- Parser: option order, repeat flags, last-value precedence, every invalid
  occurrence, unknown/deferred switches, extra/missing operands, standalone
  version, `/BARE` conflicts, exact DU inheritance and caller-DU restoration.
- `/VER`: exact metadata-owned implied-corner layout, no file access or monitor
  requirement, no ordinary sign-on display and direct return.
- `/BARE`: differential DRI cases for empty, missing, one-record and multi-record
  files; all byte values; `1Ah`; final-record padding; drive qualification;
  offsets across 64 KiB; nonconsumed interruption at row boundaries; read
  termination; initial/final CR/LF and direct CCP return.
- Enhanced output: exact 76/37-column formats, every ASCII classification,
  eight-digit offsets beyond 64 KiB, final-record bytes and required `/40` in
  both streaming and paged modes; consumed streaming Ctrl-C.
- Positions: exact unaligned `/FROM=`, `/LEN=0/1`, partial initial/final rows,
  range across rows/records/pages, count past EOF and 32-bit addition carry,
  fixed-range paging/Go To/search and preservation without `/LEN=`,
  all accepted numeric forms, aligned/unaligned Go To,
  overflow, EOF rejection, empty files, invalid-input correction and cancellation.
- Screens: backend-reported dimensions, one shared row, different heights,
  missing capabilities, insufficient geometry, no silent fallback, horizontal
  prompt scrolling and no data-area corruption. Native Model 4 ESC generation
  must work through the documented CLEAR mapping.
- Navigation: forward/backward pages, BOF clamping after arbitrary positioning,
  partial final page, EOF/BOF status, unknown keys, search retention and anchors.
- Prompts: insertion, Ctrl-S/D/G/H at internal/end positions, Enter/ESC, long
  spaced patterns, meaningful ASCII spaces and limits without truncation.
- Search: both interpretations, exact case, 32-byte limits, invalid hex,
  overlapping and row/record/page-boundary matches, forward and nearest-backward
  progression, no wrap, reposition anchors, new no-match versus continuation
  no-match, ESC in both prompts and during scanning, and state preservation.
- Failures: distinguishable initial-page, later-page, stream and search errors;
  no partial committed pages, false EOF or false no-match; cleanup and direct
  return. Independently verify input bytes/attributes and filesystem integrity
  are unchanged after viewing, search, cancellation and errors.

Record each check's platform, revision, binary/image identity, evidence and
passed/failed/blocked/not-applicable outcome. Unsupported fault mechanisms must
not be reported as passed.

## 15. Remaining review details

The consolidated contract above resolves the superseded baseline-only default,
old `/VER`, variable-width offsets, optional `/40`, default-FCB assumption,
ambiguous search state and provisional range proposals. `/FIND=` remains deferred.

Implementation resolves the remaining bounded details as follows:

- Raw Find input is limited to 95 characters, enough for all 32 hexadecimal
  bytes separated by single spaces. Further insertion is refused with an
  input-limit message; existing text remains editable. The decoded limit is
  still 32 bytes. Extra optional spaces do not grant an unbounded raw buffer.
- Invalid H/A choices show `Choose H or A; ESC cancels` and reprompt without
  changing the entered pattern or previously active search.
- No explicit clear-search command is added. Paging remains available through
  Space/Ctrl-C/Ctrl-R while `.` and `,` navigate occurrences. A new Find replaces
  a pattern only on its committed outcome; cancellation does not clear it.

All occurrences of `/FROM=` must also pass file bounds, even if superseded by
another occurrence. The implementation retains the largest requested offset for
that validation and the last requested value for initial positioning.

Exact hint wording and minor presentation remain implementation choices within
the single-row and screen-width constraints. Input uses unechoed direct-console
reads so the command key is neither echoed through an unsynchronized monitor
personality nor interpreted as cooked Ctrl-C abort.

## 16. Shared editor extraction

The basic input engine is now shared source under `src/utilities/common/ui/`.
DUMP retains its qualified legacy behavior and its own renderer and validation.
The [Shared Input and UI Specification](Shared%20Input%20and%20UI%20Specification.md)
defines the broader standard and staged migration; its new keys/defaults do not
silently amend this DUMP contract.
