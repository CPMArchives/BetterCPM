# VIEW.COM Engineering Specification

## 1. Status and Release Target

Functional specification accepted 2026-10-12. Implementation is pending.
Related architectural discussion: [post-1.0 terminal architecture](POST-1.0-TERMINAL-ARCHITECTURE-OUTLINE.md).

`VIEW.COM` is a **post-BetterCP/M 1.0 utility**.

Its design is being finalized during BetterCP/M 1.0 development so that the intended behavior is preserved, but implementation is explicitly deferred until after the 1.0 release.

`VIEW.COM` belongs on the **Utilities Disk**, not the minimum System Disk.

The BetterCP/M Monitor RSX architecture has been accepted for 1.0 but is not yet implemented. It is an interim terminal solution and shall not be frozen into this specification as VIEW's permanent screen interface. VIEW shall use the post-1.0 terminal/screen architecture available when implementation begins.

---

## 2. Purpose

`VIEW.COM` is BetterCP/M's full-screen, read-only file viewer.

It provides capabilities deliberately excluded from `TYPE.COM`, including:

- line-by-line navigation;
- bidirectional paging;
- horizontal scrolling;
- file-to-file navigation;
- configurable wrapping;
- logical line numbers;
- interactive searching;
- runtime display-mode changes;
- text/hex switching;
- optional 7-bit display;
- visible-control display;
- automatic and forced decompression of supported CP/M compression formats.

The architectural distinction is:

> **TYPE displays files and may page through them. VIEW interactively inspects and navigates them.**

VIEW shall never modify the file being viewed.

---

## 3. Invocation

General form:

```text
VIEW filespec [options]
```

Examples:

```text
VIEW README.TXT
VIEW B3:README.TXT
VIEW B[-]:*.DOC
VIEW B[-]:*.DOC[$ARC]
VIEW *.TXT /N /W
VIEW MANUAL.TXT /W /C=72
VIEW FILE.BIN /H
VIEW OLD.DOC /7
VIEW OLD.?Q? /RAW
```

VIEW is always interactive. There is no `/P`.

---

## 4. File Selection

VIEW shall use the common BetterCP/M object-selection syntax.

Examples:

```text
VIEW README.TXT
VIEW B[3-5]:*.TXT
VIEW [A0,B3,C[4-6]]:*.DOC
VIEW B[-]:*.DOC[$ARC]
```

The common selector implementation provides:

- DU expansion;
- user ranges;
- compound selectors;
- wildcards;
- attribute predicates.

VIEW shall not implement a separate selector parser.

Selected files form one navigable sequence and are processed in native directory-selection order unless the common selector layer specifies otherwise.

---

## 5. Command-Line Options

VIEW shall support:

```text
/N          logical source line numbers
/7          strip high bit in text mode
/W          enable VIEW-managed word wrapping
/C=n        preferred wrap width
/CTL        display control characters visibly
/H          start in hex mode
/RAW        disable decompression
/Q          force SQ/USQ decompression
/Z          force CRUNCH/UNCR decompression
/Y          force CrLZH decompression
/VER        print version and exit
```

`/RAW`, `/Q`, `/Z`, and `/Y` select mutually exclusive text-stream modes.

If more than one is specified, the last one wins.

With none specified, VIEW starts in **AUTO** compression mode.

### Tab handling

VIEW does **not** provide a `/T` option.

Because VIEW is a full-screen application, TAB handling cannot safely be delegated to arbitrary terminal tab settings. TABs are always rendered internally at fixed 8-column stops.

When `/CTL` is active, TAB is instead displayed as `^I`.

---

## 6. Screen Model

VIEW is a full-screen application.

The bottom console row is reserved for:

- navigation/status information;
- mode prompts;
- Find status and editing.

For a conventional 24-line display:

```text
23 rows    file viewport
 1 row     status/control line
```

VIEW shall use the console geometry supplied by BetterCP/M's screen/terminal layer.

The file viewport shall never overwrite the reserved bottom row.

---

## 7. Minimum Supported Geometry

The minimum supported VIEW geometry is:

```text
40 columns × 12 rows
```

If the available display is smaller, VIEW shall refuse to start and print a concise diagnostic.

Example:

```text
VIEW: Screen too small; 40x12 required.
```

Status-line legends may be abbreviated on narrower supported displays.

---

## 8. Multi-File Display

When multiple files are selected, each file shall be identified by a banner such as:

```text
---------- B3:FILENAME.TXT ----------
```

The banner includes the full DU and filename.

For one exact file, the banner may be omitted.

Normal forward display may cross a file boundary. If a file ends before the viewport is full, VIEW may continue with:

1. the next-file banner;
2. content from that file;
3. enough content to fill the remaining viewport.

Explicit file navigation remains boundary-oriented.

---

## 9. Navigation Model

VIEW adopts the WordStar movement vocabulary together with BetterCP/M punctuation aliases.

### 9.1 Line Movement

```text
^E      previous display row
^X      next display row
```

Movement is by **rendered display row**, not logical source line.

In hex mode, one movement means one hex row.

### 9.2 Horizontal Movement

```text
^S      left one display column
^D      right one display column
```

Movement is exactly one column.

The leftmost position is column zero.

Movement beyond a meaningful boundary is a no-op and may ring the bell.

### 9.3 Page Movement

```text
^R      previous page
^C      next page

,       previous page
.       next page
SPACE   next page
```

A page movement advances or retreats by one viewport height.

### 9.4 File Movement

```text
<       beginning of current file;
        if already there, beginning of previous file

>       beginning of next file
```

The current file is the file containing the current display anchor.

If a screen contains the tail of one file and the beginning of another, merely seeing the second file does not make it current.

### 9.5 Quit

```text
^Q      exit VIEW.COM
```

Within VIEW's command loop, `^C` means Page Down, not abort.

---

## 10. ESC Semantics

`ESC` means:

> **Exit the current subordinate mode and return to its parent mode.**

`ESC` does not exit VIEW.COM.

For example:

- from Find-string edit mode, `ESC` leaves edit mode;
- from active Find mode, `ESC` leaves Find mode.

`^Q` exits VIEW itself.

---

## 11. Display Anchors and Navigation History

VIEW shall maintain anchors sufficient to reconstruct displayed positions.

There shall be **no user-visible backward-history limit**.

Implementations may cache:

- page anchors;
- rendered-row anchors;
- raw file offsets;
- logical-stream offsets;
- decompressor checkpoints.

If a requested position has fallen out of the cache, VIEW may reconstruct it by:

- reopening;
- seeking;
- rescanning;
- rescanning the directory;
- redecompressing.

Unlimited backward reach does **not** imply instantaneous navigation.

Long reconstruction delays are permitted.

---

## 12. Memory Pressure and Large Selections

VIEW is not required to keep:

- the complete selected-file catalogue;
- all page anchors;
- all file offsets;
- complete decompressed streams;
- all decompressor checkpoints

in memory simultaneously.

It may reconstruct or rescan data as needed.

If insufficient workspace prevents a particular optional mode from operating safely, VIEW shall report that mode as unavailable rather than corrupting operation.

VIEW shall degrade in speed before degrading correctness.

---

## 13. End-of-Selection Behavior

VIEW does not automatically exit on reaching the final selected file.

At the final position:

- forward line movement is a no-op;
- forward page movement is a no-op;
- `>` is a no-op;
- backward navigation remains available;
- `^Q` exits.

Boundary attempts may ring the bell.

---

## 14. Empty Files

An empty file is valid.

For a multi-file selection:

- its normal banner appears;
- no `[EMPTY]` contents are synthesized;
- it remains reachable through file navigation.

For one exact empty file, VIEW remains active with an empty viewport.

---

## 15. Logical Text Stream

VIEW distinguishes:

1. **source-file bytes**;
2. **logical text bytes**;
3. **rendered screen cells**.

For an uncompressed RAW file, source bytes become logical text bytes directly.

For compressed input, the decompressor converts source bytes into the logical text stream first.

Text semantics such as EOF, line endings, and TAB are evaluated against the **logical text stream before `/7` processing**.

---

## 16. Text EOF

In text mode:

```text
logical byte 1Ah -> CP/M text EOF
```

Text display stops there.

This prevents VIEW from showing final-record padding or garbage after a conventional CP/M `^Z`.

EOF recognition occurs before `/7`.

Therefore:

```text
logical 1Ah -> EOF

logical 9Ah
    /7
     |
     v
    1Ah -> display data, NOT EOF
```

---

## 17. Hex EOF Semantics

Hex mode does not interpret `1Ah` as EOF.

Hex asks:

> **What bytes are actually stored in the CP/M logical records?**

It therefore displays all bytes through the end of the final 128-byte logical record.

Text mode may consequently appear shorter than hex mode for the same file.

This is intentional.

---

## 18. Structural Text Interpretation and `/7`

Structural text semantics are determined **before `/7`**.

The following logical bytes are structural:

```text
09h     TAB
0Ah     LF
0Dh     CR
1Ah     CP/M EOF
```

Bytes that become one of these values only after `/7` remain display data.

Therefore:

```text
89h -> /7 -> 09h   display data, NOT TAB
8Ah -> /7 -> 0Ah   display data, NOT LF
8Dh -> /7 -> 0Dh   display data, NOT CR
9Ah -> /7 -> 1Ah   display data, NOT EOF
```

This establishes one consistent rule:

> **`/7` changes representation, not text structure.**

---

## 19. `/N` — Logical Line Numbers

`/N` displays logical source-line numbers.

Example:

```text
   27  This source line wraps onto
       another rendered row.
   28  Next source line.
```

Rules:

- numbering starts at 1 for each file;
- resets at each new file;
- wrapped continuation rows have a blank gutter;
- wrap changes do not alter logical line numbers;
- line numbering is inactive in hex mode;
- state is restored when returning to text mode.

Interactive command:

```text
N       toggle line numbers
```

---

## 20. `/7` — 7-Bit Display

`/7` performs:

```text
display_byte = logical_byte AND 7Fh
```

after structural EOF, line-ending, and TAB interpretation.

It never modifies the file.

Interactive command:

```text
7       toggle 7-bit display
```

Changing state redraws the viewport.

---

## 21. `/W` — Word Wrapping

`/W` enables VIEW-managed wrapping.

Interactive command:

```text
W       toggle wrapping
```

VIEW shall render wrapping deliberately and shall not rely on terminal automatic wrapping.

---

## 22. `/C=n` — Preferred Wrap Width

Default:

```text
72
```

Valid range:

```text
8..255
```

The value refers to the **text field only**, excluding any line-number gutter.

Effective width:

```text
min(configured width, available text viewport width)
```

Thus `/C=72` on a narrower display automatically clamps to the usable viewport.

`/C=n` does not itself enable wrapping.

Interactive command:

```text
C       prompt for wrap width
```

---

## 23. Wrap Algorithm

With wrapping enabled:

1. structural line endings terminate the logical source line;
2. VIEW attempts to break before the effective boundary;
3. whitespace is preferred;
4. boundary whitespace need not begin the continuation row;
5. an uninterrupted word exceeding available width is hard-wrapped.

Continuation rows do not create new logical source lines.

---

## 24. Horizontal Scrolling and Wrapping

When wrapping is disabled, long logical lines are displayed through a controlled horizontal viewport.

VIEW does not rely on terminal automatic wrapping.

When wrapping is enabled, horizontal scrolling normally has no useful range and `^S/^D` become no-ops at the relevant boundaries.

---

## 25. Safe Character Rendering

VIEW shall never emit arbitrary file bytes directly to the physical terminal.

All output is converted into deliberate screen cells first.

This prevents file contents from:

- moving the cursor;
- clearing the screen;
- changing terminal modes;
- overwriting the status line;
- issuing escape sequences.

### 25.1 Printable ASCII

Bytes:

```text
20h-7Eh
```

are rendered normally.

### 25.2 C0 Controls and DEL

Without `/CTL`:

- CR/LF provide logical line structure;
- structural TAB expands internally to fixed 8-column stops;
- all other `00h-1Fh` controls and `7Fh` are rendered harmlessly and never executed as terminal controls.

A simple placeholder such as `.` may be used for non-layout controls.

### 25.3 High-Bit Bytes

When `/7` is **off**, bytes:

```text
80h-FFh
```

must not be emitted raw to the terminal.

They shall be represented using a harmless display mapping.

For the initial implementation, a non-ASCII high-bit byte may be displayed as:

```text
.
```

unless a later defined character mapping exists.

`/CTL` does not create an `M-` meta-character notation; high-bit bytes remain harmlessly represented rather than being interpreted as terminal data.

When `/7` is active, high-bit bytes are transformed into 7-bit display values, but transformed values do not acquire structural meanings.

---

## 26. Tab Rendering

Structural TAB bytes (`09h` in the logical text stream before `/7`) are always interpreted internally.

Default TAB stops are every 8 columns.

There is no configurable TAB width in the initial VIEW implementation.

With `/CTL`, a structural TAB appears as:

```text
^I
```

rather than expanding.

A transformed `89h -> 09h` under `/7` is **not** a structural TAB and therefore does not expand.

---

## 27. `/CTL` — Visible Controls

`/CTL` displays C0 controls and DEL using conventional caret notation.

Interactive command:

```text
^       toggle visible controls
```

Mapping:

```text
00h       ^@
01h-08h   ^A-^H
09h       ^I
0Ah       ^J
0Bh       ^K
0Ch       ^L
0Dh       ^M
0Eh-19h   ^N-^Y
1Ah       ^Z when it is display data
1Bh       ^[
1Ch       ^\
1Dh       ^]
1Eh       ^^
1Fh       ^_
7Fh       ^?
```

A logical `1Ah` already recognized as EOF never reaches the renderer.

A byte transformed to `1Ah` by `/7` is ordinary display data and therefore appears as `^Z`.

### 27.1 Visible Line Endings

With `/CTL`:

```text
CR LF     display ^M^J, then begin next logical line
CR alone  display ^M,   then begin next logical line
LF alone  display ^J,   then begin next logical line
```

The visible symbols occupy screen columns and affect wrapping.

They do not execute their represented terminal operations.

---

## 28. Compression States

Text mode supports five stream states:

```text
AUTO
RAW
SQ
CRUNCH
CrLZH
```

Compression state is maintained **per file** once that file has been encountered.

---

## 29. Command-Line Compression Default

The invocation establishes the initial compression state for each newly encountered file.

```text
no switch   -> AUTO
/RAW        -> RAW
/Q          -> SQ
/Z          -> CRUNCH
/Y          -> CrLZH
```

This invocation default does not subsequently change when the user changes one file interactively.

Each newly encountered file begins with the invocation default and then acquires its own remembered state.

---

## 30. AUTO

AUTO is the normal default.

VIEW may detect compression using:

- filename conventions;
- format signatures;
- decoder-specific criteria.

If no supported compressed format is recognized, the file behaves as RAW.

---

## 31. RAW

RAW disables decompression.

Command line:

```text
/RAW
```

Interactive command:

```text
R
```

`R` toggles RAW/AUTO **for the current file only**.

That state is remembered if the user leaves and later returns to the file.

---

## 32. Forced Decoders

```text
/Q      SQ/USQ
/Z      CRUNCH/UNCR
/Y      CrLZH
```

Interactive equivalents:

```text
Q
Z
Y
```

Interactive changes affect **only the current file**.

Only one forced decoder may be active for that file.

Selecting a different decoder replaces the previous state.

Selecting the currently forced decoder again returns that file to AUTO.

The resulting state is preserved when revisiting the file.

---

## 33. Per-File Compression State

Each selected file therefore has an independent compression state.

Example:

```text
VIEW *.DOC
```

may result in:

```text
A.DOC    AUTO -> detected SQ
B.DOC    user selects RAW
C.DOC    AUTO
```

Leaving `B.DOC` and later returning to it restores its RAW state.

Changing `B.DOC` does not change:

- the invocation default;
- `A.DOC`;
- `C.DOC`;
- any other file.

---

## 34. Compression-State Positioning

RAW and decompressed logical offsets have no reliable positional correspondence.

Therefore **any change of compression state for the current file**:

```text
AUTO <-> RAW
AUTO <-> forced decoder
RAW  <-> forced decoder
decoder A <-> decoder B
```

shall:

1. change that file's logical text stream;
2. reset that file's text position to BOF;
3. rebuild and redraw from BOF.

No approximate raw/decompressed position mapping is attempted.

---

## 35. Text Processing Pipeline

Conceptually:

```text
source-file bytes
       |
       +-- RAW --------------------------+
       |                                 |
       +-- AUTO/forced decoder ----------+
                                         |
                                         v
                                logical text bytes
                                         |
                          structural interpretation
                          - TAB 09h
                          - LF  0Ah
                          - CR  0Dh
                          - EOF 1Ah
                                         |
                                        /7
                                         |
                                       /CTL
                                         |
                            safe character rendering
                                         |
                              wrapping/rendering
```

Important consequences:

- compressed source bytes are not mistaken for text EOF;
- decompression precedes text interpretation;
- structural text semantics precede `/7`;
- `/7` cannot create new TAB, LF, CR, or EOF semantics.

---

## 36. Decoder Failure

Decoder failure is **local to the current file**.

If that file's forced or AUTO decoder fails at any point:

1. VIEW reports the failed decoder;
2. that file's compression state becomes RAW;
3. its text position resets to BOF;
4. raw display restarts from the beginning of that file.

Example:

```text
VIEW: SQ decompression failed; displaying raw file.
```

The failure does not alter:

- the invocation default;
- any other file's compression state.

The file remains RAW if the user leaves it and later returns, unless the user explicitly changes its state again.

VIEW shall not attempt to resume RAW display at an approximate decompressed position.

---

## 37. Hex Mode

Command line:

```text
/H
```

Interactive command:

```text
H       toggle text / hex
```

Hex displays **raw source-file bytes**.

Compression is irrelevant to hex presentation.

---

## 38. Hex File Length

Hex mode displays the complete CP/M file image through the final 128-byte logical record.

Any bytes following an application-defined `^Z` are shown.

VIEW does not pretend CP/M provides a universal exact application byte length.

---

## 39. Hex Layout

Each row displays:

- hexadecimal file offset;
- hexadecimal bytes;
- printable ASCII;
- `.` for nonprintable bytes.

Canonical example:

```text
00000120  41 42 43 0D 0A 00 7F ...  ABC....
```

Row width automatically adapts:

```text
16 bytes/row    if it fits
 8 bytes/row    otherwise
 4 bytes/row    on narrow supported screens
```

VIEW reduces bytes per row rather than introduce horizontal scrolling merely to preserve 16-byte rows.

Offsets are hexadecimal.

---

## 40. Text Features Inactive in Hex Mode

The following are inactive in hex mode:

- line numbers;
- `/7`;
- wrapping;
- wrap column;
- `/CTL`;
- decompressed presentation;
- text Find.

Their states are preserved and restored when returning to text mode.

---

## 41. Independent Text and Hex Positions

Each file maintains independent:

- text position;
- hex position.

Switching modes restores the last position used in that mode.

On first entry to hex for an uncompressed file, VIEW may initialize the hex position near the corresponding raw file location.

For compressed text, no correspondence between logical decompressed position and raw compressed-file offset is promised.

---

## 42. Runtime Display Commands

In normal text-view mode:

```text
N       toggle line numbers
7       toggle 7-bit display
W       toggle wrapping
C       set wrap width
^       toggle visible controls
H       text/hex
R       RAW/AUTO for current file
Q       SQ for current file
Z       CRUNCH for current file
Y       CrLZH for current file
F       Find
```

Rendering changes redraw from the same logical anchor where meaningful, except compression-state changes, which reset the current file to BOF.

---

## 43. Find Overview

Find is interactive and text-only.

There is no command-line `/F`.

Find:

- searches the current file only;
- never crosses a file boundary;
- wraps circularly within that file;
- performs literal search only;
- is case-insensitive;
- does not support wildcards or regex;
- searches the logical readable text stream;
- searches decompressed text when decompression is active;
- applies `/7` before comparison;
- ignores rendering decoration.

Search is disabled in hex mode.

---

## 44. Find Status Line

Entering Find replaces the normal bottom legend with:

```text
FIND: search-string-goes-here                , Prev . Next ESC Exit
```

Rules:

- `FIND: ` is fixed left;
- `, Prev . Next ESC Exit` is flush right;
- the search field occupies the space between them.

On narrow displays, the right-hand legend may be abbreviated, for example:

```text
,P .N ESC
```

The implementation shall preserve usable search-field space while retaining recognizable controls.

---

## 45. Find String Length

Maximum:

```text
63 characters
```

Once length 63 is reached:

- further printable insertion is refused;
- the string is unchanged;
- VIEW may ring the bell.

VIEW does not accept extra characters and truncate later.

---

## 46. Find Edit Display

While editing, the search field is a horizontally scrolling window onto the complete search string.

The cursor remains visible.

After leaving edit mode, an overlong visible representation is truncated with:

```text
...
```

The complete stored term remains intact.

---

## 47. Find Editing

Find editing is deliberately barebones.

Supported:

```text
^S          cursor left
^D          cursor right
BACKSPACE   delete left
printable   insert at cursor
ESC         leave edit mode
ENTER       leave edit mode and search next
```

There is:

- insert mode only;
- no overwrite mode;
- no DEL command;
- no word deletion;
- no Home/End;
- no undo.

---

## 48. Immediate Find-Edit Commitment

There is one live search buffer.

All changes are applied immediately.

There is no temporary copy and no cancel/revert operation.

Therefore:

```text
ESC
```

means:

> Stop editing.

It does **not** restore the previous string.

`ENTER` means:

> Stop editing and perform a forward search.

If editing leaves the string empty, no search is active and VIEW returns to normal mode.

---

## 49. Re-Editing an Active Search

Pressing:

```text
F
```

while Find mode is active re-enters edit mode.

The existing search string remains loaded.

The cursor is placed at the beginning of the string.

---

## 50. Search Direction

There is no independent initial-direction state.

Direction is selected by:

```text
.       forward / next
,       backward / previous
```

`ENTER` from Find edit mode is equivalent to `.`.

---

## 51. First Search Boundary

For a newly entered or newly edited term:

- first `.` or `ENTER` begins **at** the current logical display anchor;
- first `,` begins **immediately before** the current logical display anchor.

This allows a forward match beginning exactly at the current anchor while giving backward search a definite preceding boundary.

---

## 52. Search after a Found Match

Once a match has been found:

- subsequent `.` begins after the end of that match;
- subsequent `,` begins before the start of that match.

Changing direction uses the current match as the boundary.

Matches do not overlap.

For a file containing exactly one occurrence, repeated forward or backward searching wraps and eventually returns to that same occurrence.

---

## 53. Search after Manual Navigation

If the user manually moves away from a found match using ordinary viewer navigation, the old match ceases to be the search boundary.

Manual navigation makes the **new display anchor** the current search origin.

Therefore, after manual navigation:

- `.` searches forward beginning at the new anchor;
- `,` searches backward beginning immediately before the new anchor.

The previous found occurrence has no special search status after such movement.

This rule applies to navigation such as:

```text
^E/^X
^R/^C
SPACE
```

within the current file.

---

## 54. Circular Search

Search is circular within the current file.

Forward:

```text
last occurrence -> first occurrence
```

Backward:

```text
first occurrence -> last occurrence
```

Search never enters another selected file.

---

## 55. Search Case Folding

Case-insensitive matching uses **ASCII case folding only**:

```text
A-Z == a-z
```

No locale, national-character-set, or high-bit case folding is required.

---

## 56. Search and Line Endings

Search terms are entered through the barebones Find editor and cannot contain CR/LF.

Therefore matches do not span logical line boundaries.

Line-ending structure terminates candidate matching across lines.

---

## 57. Find-Mode File Lock

During Find mode:

```text
<       disabled
>       disabled
```

The current file cannot change.

---

## 58. Navigation During Find

Ordinary navigation remains available within the current file:

```text
^E/^X       line movement
^R/^C       page movement
SPACE       forward page
```

Such movement stops at the current file boundaries.

`,` and `.` retain their Find meanings and are not page aliases while Find is active.

Manual navigation also resets the search origin as described above.

---

## 59. Display Toggles During Find

The following display-state commands are disabled while Find mode is active:

```text
N  7  W  C  ^  H  R  Q  Z  Y
```

The user must leave Find mode before changing the logical or rendered stream.

---

## 60. No-Match Behavior

If the current file contains no occurrence:

```text
No matches found
```

is displayed on the bottom line.

VIEW waits for **any key**.

That key:

1. dismisses the message;
2. clears Find mode;
3. restores normal viewer mode.

The viewport remains where it was.

---

## 61. Match Placement

A successful search positions the viewport so the match is visible.

VIEW need not force it to the first row.

Where practical, surrounding context should remain visible.

No elaborate highlighting is required initially.

---

## 62. Persistent Bottom Legend

Normal VIEW mode reserves the final row for a compact legend, for example:

```text
^E/^X Line  ^R/^C Page  </> File  F Find  H Hex  ^Q Quit
```

Exact abbreviations may vary with screen width.

Find mode replaces this line with the Find status line.

---

## 63. Keyboard Input Requirements

VIEW's keyboard-input path must deliver the command characters VIEW needs without normal system interception while VIEW owns the interactive console.

In particular:

```text
^C
^Q
ESC
^E ^X ^S ^D ^R
```

must reach VIEW as command input.

The user or platform remains responsible for any modern-keyboard mapping such as arrows or PageUp/PageDown onto WordStar control codes.

VIEW itself does not require knowledge of modern physical keys.

---

## 64. Ctrl-C Boundary

Within VIEW:

```text
^C = Page Down
```

It is not the ordinary CP/M abort character while VIEW is in control of interactive command input.

```text
^Q = Quit
```

is the explicit VIEW termination command.

---

## 65. Long Operations and Interruption

Potentially lengthy operations include:

- backward reconstruction;
- directory rescanning;
- decompression/redecompression;
- searches;
- rebuilding wrapped-line positions.

Where practical, VIEW shall periodically poll for user interruption during such operations.

At minimum, `^Q` should be honored as an abort/quit request during lengthy work.

`ESC` may cancel the current subordinate operation where a meaningful parent mode exists.

The implementation need not make every byte-level operation instantaneously interruptible.

---

## 66. Terminal Lifecycle

VIEW shall leave the console in a sane ordinary state on **every exit path**, including:

- normal `^Q`;
- fatal errors;
- startup failures after terminal initialization;
- interrupted lengthy operations that terminate VIEW.

Any terminal state changed by VIEW shall be restored as appropriate.

In particular:

- cursor visibility shall be restored;
- temporary screen/terminal modes shall be undone;
- VIEW shall not leave the CCP with an unexpectedly hidden cursor or altered terminal mode.

---

## 67. Files Changed While Viewing

VIEW provides no snapshot semantics.

If a file changes externally:

- reconstructed pages may change;
- old anchors may no longer correspond exactly;
- decompressed reconstruction may differ;
- VIEW need not detect every modification.

If reopening or reconstruction fails, normal error handling applies.

---

## 68. File Errors

If a selected file cannot be opened:

```text
VIEW B3:FOO.TXT - Cannot open.
```

VIEW skips it where possible.

If a read error occurs:

```text
VIEW B3:FOO.TXT - Read error.
```

VIEW abandons that file and continues where possible.

A fatal internal error may terminate VIEW after restoring terminal state.

---

## 69. Terminal/Monitor Architecture Dependency

VIEW requires a screen subsystem capable of providing at least:

- screen geometry;
- cursor positioning;
- controlled screen output;
- clear-line/screen operations;
- cursor visibility;
- interactive command input;
- bell or equivalent notification.

BetterCP/M 1.0 has **accepted but not yet implemented** the Monitor RSX architecture as an interim solution, including:

- ADM-3A personality for Model 4;
- VT52 as the general target;
- basic-console fallback;
- terminal personality selection through loadable RSX facilities.

VIEW implementation is deferred until post-1.0 and shall use the terminal/screen architecture then available.

The VIEW specification shall not freeze the 1.0 Monitor RSX arrangement as the permanent BetterCP/M TCAP architecture.

---

## 70. Version Reporting

```text
VIEW /VER
```

prints:

```text
BetterCP/M VIEW 1.0 (Build nnn)
```

and exits.

This is VIEW's utility version, not the BetterCP/M system release number.

---

## 71. Explicitly Excluded Features

The initial VIEW implementation does not provide:

- editing;
- save;
- overwrite;
- rename;
- delete;
- regex search;
- wildcard search;
- cross-file search;
- binary/hex search;
- bookmarks;
- goto-line;
- goto-offset;
- configurable TAB width;
- page numbering;
- split-screen display;
- multiple panes;
- sophisticated Find-field editing.

These exclusions are architectural scope decisions.

---

## 72. Relationship to TYPE.COM

`TYPE.COM` provides:

```text
streaming text display
multi-file display
/P bidirectional page navigation
/7
/T
/CTL
```

It does not provide:

```text
line scrolling
horizontal scrolling
logical line numbers
VIEW-managed wrapping
Find
hex mode
decompression
runtime view toggles
```

VIEW is therefore not merely `TYPE /P` under another name.

---

## 73. Distribution

`VIEW.COM` belongs on the **BetterCP/M Utilities Disk**.

It is not part of the BetterCP/M 1.0 distribution.

Implementation is deferred until post-1.0.

---

## 74. Implementation Staging

When implementation begins, recommended order is:

1. **Text viewport and anchors**
   - safe rendering;
   - line/page/file navigation;
   - horizontal viewport.

2. **Text presentation**
   - wrapping;
   - line numbers;
   - `/7`;
   - visible controls.

3. **Find**
   - logical-stream search;
   - Find status line;
   - minimal field editor.

4. **Hex**
   - adaptive 16/8/4-byte rows;
   - record-level length semantics;
   - independent hex anchors.

5. **Compression**
   - AUTO/RAW/forced decoding;
   - per-file compression state;
   - decoder failures;
   - logical-stream reconstruction;
   - backward navigation through decompressed data.

The logical-stream and anchor architecture shall be designed from the outset so later stages do not require replacing the navigation model.

---

## 75. Design Principle

The governing rule is:

> **VIEW is a read-only interactive inspection environment for files.**

Navigation, decompression, searching, wrapping, line numbering, visible controls, and hex display are alternate ways of observing the selected files.

Correctness and reversibility of navigation take precedence over retaining every intermediate result in memory.

The screen renderer owns every cell written to the viewport; arbitrary file bytes are never trusted as terminal commands.

And because implementation is post-1.0, VIEW shall take advantage of the more robust BetterCP/M terminal architecture developed after 1.0 rather than forcing that architecture to be finalized prematurely.