# TYPE / TYPE.COM Engineering Specification



Status: revised target contract recorded on 2026-10-12. Implementation and
qualification of the enhanced behavior remain separate work. The proposed user
interface is in user-guide section 4.4.

Uses the shared [DU selector](208%20Extended%20DU%20Syntax.md) and utility
version/build convention. Supersedes the historical
[stock TYPE baseline](114%20Stock-Compatible%20TYPE.md) where behavior differs.

## Implementation notes



Page anchors define the current file, including pages spanning files. Empty
files stay in the selected sequence without synthetic content. Cached history
may be reconstructed without a user-visible backward-navigation limit. File
contents are not snapshotted; redisplay may reflect changes. Open/read errors
skip without prompts. The revised contract settles these earlier questions.

EOF recognition is settled: only raw source 1Ah ends text. Raw 9Ah under `/7`
becomes display data 1Ah; `/7 /CTL` renders it as `^Z`. Without `/CTL`, that
transformed byte passes through the ordinary display path without another EOF
test.

Option placement/repetition, geometry fallbacks, selection capacity and exact
page-prompt presentation remain routine implementation/qualification details.
Audit resident growth against RCP's current carrier limit; no BDOS or CPX ABI
expansion is authorized by this specification.

## Qualification requirements




Qualify both platforms with native/cross-build parity, unchanged source data
and attributes, and caller-DU restoration. Cover selectors/predicates, invalid
syntax, exact/multiple/empty files, raw 1Ah/high-bit bytes, tabs/controls/long
lines at page edges, cross-file pages, every navigation boundary, final EOF,
cache reconstruction beyond retained anchors, cancellation, geometry, and
open/read failures that skip without prompting. Verify `/VER` performs no file
access. Test Ctrl-C separately at paged input and during ordinary output.


## 1. Purpose

TYPE displays the contents of one or more files on the console.
BetterCP/M provides two implementations:

* resident TYPE, intended as a small core command;
* transient TYPE.COM, providing a more capable text-display and paging facility.

Both commands remain fundamentally file-display utilities. Rich inspection features such as searching, line numbering, decompression, hex display, horizontal scrolling, and runtime display-mode changes belong to VIEW.COM, not TYPE.COM.
The design objective is:
TYPE displays files, optionally with paging. VIEW interactively inspects files.

## 2. Resident and Transient Relationship

The resident and transient forms shall use compatible command syntax wherever their capabilities overlap.
Resident TYPE provides the minimal useful subset.
Transient TYPE.COM extends that behavior without changing the basic meaning of the command.
A resident implementation may hand off to TYPE.COM when the invocation requests a feature not supported resident-side, according to the common BetterCP/M resident/transient handoff mechanism.
The leading force-transient forms:

```
:TYPE ...
.TYPE ...

```

shall bypass the resident command and invoke TYPE.COM directly.

## 3. Common File Selection

Both resident TYPE and transient TYPE.COM shall use the BetterCP/M shared object-selection syntax.
Examples:

```
TYPE README.TXT
TYPE B3:README.TXT
TYPE B[-]:*.TXT
TYPE [A0,B3,C[4-6]]:*.DOC
TYPE B[-]:*.DOC[$ARC]

```

Selectors may identify:

* one drive/user;
* multiple users;
* multiple drives/users;
* wildcarded files;
* attribute-qualified files.

Selection syntax and attribute predicates are defined by the common BetterCP/M selector engine and shall not be reimplemented independently by TYPE.
Files shall be processed in native directory-selection order unless otherwise specified by the common selector implementation.

## 4. Text Interpretation

TYPE is a text-display command.
In normal text mode:

* file data is read sequentially;
* **only a raw file byte of 1Ah** terminates displayed text;
* CR/LF controls normal line structure;
* files are not interpreted as compressed data;
* no character-set translation beyond explicitly selected options is performed.

Binary files may therefore display poorly. Users requiring binary inspection shall use VIEW.COM or DUMP.COM.
EOF recognition shall occur on the raw file byte before /7, /CTL, or any other display transformation.
A byte that becomes 1Ah only after transformation is **not** treated as EOF.
Example:

```
raw 1Ah  -> EOF
raw 9Ah  -> /7 -> 1Ah -> ordinary display data

```


## 5. Resident TYPE

## 5.1 Syntax

```
TYPE filespec
TYPE filespec /P
TYPE /VER

```

The command may accept BetterCP/M selectors and attribute predicates as part of filespec.
Resident TYPE shall reject transient-only options or request transient handoff where supported by the common handoff mechanism.

## 5.2 Default Operation

Without /P, resident TYPE streams all selected files continuously to the console.
No pause occurs between screenfuls.
If more than one file is selected, files are displayed sequentially.
A lightweight separator shall be printed between files, for example:

```
--------------------

```

The resident implementation need not print elaborate filename banners.

## 5.3 Resident Paging

/P enables simple forward paging.
Resident paging shall:

* pause after each screenful;
* reserve no permanent status line;
* allow only forward movement;
* require minimal resident code.

Accepted forward-page keys:

```
SPACE
.

```

Both keys are synonyms.
No backward paging, file navigation, search, horizontal scrolling, line scrolling, or runtime display changes are provided resident-side.
Resident page accounting may be simpler than transient page accounting if precise display-row tracking would materially increase resident size. If shared console-geometry support makes identical behavior inexpensive, matching the transient page count is preferable.

## 6. Transient TYPE.COM

## 6.1 Purpose

TYPE.COM is the enhanced transient implementation of TYPE.
It remains a text-display and paging utility, not a general-purpose interactive file viewer.
It adds:

* full BetterCP/M selectors;
* multi-file banners;
* bidirectional page navigation;
* explicit file navigation;
* optional 7-bit display;
* optional tab expansion;
* visible-control display.

It deliberately excludes the richer functionality assigned to VIEW.COM.

## 6.2 Syntax

```
TYPE filespec [options]

```

Supported transient options:

```
/P
/7
/T
/CTL
/VER

```

Options may appear according to normal BetterCP/M utility option-placement rules.

## 7. Default Transient Operation

Without /P, TYPE.COM streams the selected files continuously.
There shall be no interactive pauses.
If a selection resolves to more than one file, TYPE.COM shall print a banner before each file.
Recommended form:

```
---------- B3:FILENAME.TXT ----------

```

The banner shall include the full BetterCP/M DU and filename.
For a single exact file, the banner may be omitted.

## 8. Empty Files

An empty file is a valid selected object and is not an error.
For a multi-file selection:

* its normal file banner is displayed;
* no synthetic content or [EMPTY] annotation is inserted;
* processing proceeds immediately to the next selected file.

For a single exact empty file, TYPE may display nothing and return normally.
In /P mode, an empty file remains part of the selected file sequence for < and > navigation, but it does not generate a fictitious display page.

## 9. Transient Paged Mode

## 9.1 General Behavior

/P enables bidirectional paging.
This remains paging mode, not a full viewer mode.
TYPE.COM shall retain enough positional information to move backward and forward through the displayed text.
There shall be no user-visible limit on backward page navigation.
An implementation may cache page anchors for efficiency. If a requested previous page is no longer represented in the cache, TYPE.COM shall reconstruct it by reopening, seeking, or rescanning as necessary.
The command shall not report that an older page is unavailable merely because an internal history buffer has wrapped.

## 9.2 Page Anchor

Each displayed page has a page anchor identifying the file and position associated with the top of that page.
The page anchor defines the **current file** for file-navigation purposes.
If the current page begins in one file and later crosses into another file, the file containing the page anchor remains the current file.
Example:

```
A.TXT tail
---------- B3:B.TXT ----------
B.TXT beginning

```

If the page anchor lies in A.TXT, then:

```
<   beginning of A.TXT
>   beginning of B.TXT

```

If a page begins with a file banner, that banner belongs to the file that follows it, and that file is the current file.
An explicit > operation makes the target file the current file by anchoring the display at its beginning.

## 9.3 Page Size

Page size is defined in **display rows**, not source lines.
TYPE.COM shall use the configured console dimensions.
When paged mode needs a prompt/status line, that line is not part of the file-display area. Thus, on a 24-row console, a normal page contains 23 display rows.
A source line that spills beyond the right edge and continues onto another terminal row consumes additional display rows.
TYPE.COM does not implement soft word wrapping; this accounting merely reflects actual screen-edge spillover.
The implementation shall track the current display column sufficiently to determine when output crosses the configured console width.

## 9.4 Long Lines and Tabs

Long-line row accounting shall reflect the rendered display position.
TAB handling affects page-row calculation:

* with /T, TYPE.COM expands tabs internally to fixed 8-column tab stops;
* without /T, TAB is passed to the console, but TYPE.COM shall still account for it as advancing to the next 8-column tab stop for page sizing.

This permits page boundaries to correspond as closely as practical to the visible screen.

## 10. Page Navigation

The following keys shall be supported in transient /P mode:

```
^R      previous page
^C      next page

,       previous page
.       next page
SPACE   next page

```

^R and ^C are WordStar-style page-key aliases.
, and . are the native BetterCP/M punctuation paging keys.
SPACE is an additional forward-page synonym.
TYPE.COM does not otherwise implement the full WordStar movement diamond.
In particular:

```
^E/^X   not used for line scrolling
^S/^D   not used for horizontal scrolling

```

Those operations belong to VIEW.COM.

## 11. Ctrl-C Boundary

In TYPE.COM /P, ^C is explicitly consumed by TYPE.COM as **Next Page**.
While TYPE.COM is waiting for a paged-mode navigation command:

```
^C = next page

```

and does not mean abort.
^Q is the explicit TYPE.COM exit key.
Outside paged input mode, TYPE.COM does not redefine Ctrl-C. Normal console/BDOS Ctrl-C handling applies.
This distinction is intentional and shall be documented.

## 12. Multi-File Navigation

In paged mode:

```
<       beginning of current file
>       beginning of next file

```

< behaves as follows:

* if not already at the beginning of the current file, jump to the beginning of the current file;
* if already at the beginning, move to the beginning of the previous selected file.

> moves directly to the beginning of the next selected file.
The definition of current file is the file associated with the current page anchor as described in §9.2.
At the first or last selected file, movement beyond the selection shall leave the display at the nearest valid position. TYPE.COM may sound the console bell or give another minimal indication.

## 13. Multi-File Page Boundaries

Paged output treats the selected files as a navigable sequence.
When moving forward normally, a page may cross a file boundary.
If a file ends partway through a screenful, TYPE.COM may continue with:
1. the next file banner;
2. the beginning of the next file;
3. remaining rows of the current screenful.
A file boundary does not force an artificial full-screen pause.
The appearance of another file lower on the page does not by itself change the current file. The current file remains determined by the page anchor.
Explicit > always jumps directly to the beginning of the next file.

## 14. End-of-Selection Behavior

Reaching the end of the final selected file shall **not** automatically exit paged mode.
The final page remains displayed so that the user may navigate backward.
At end of the selection:

* next-page commands are no-ops;
* > is a no-op;
* TYPE.COM may sound the console bell or give another minimal indication;
* backward movement remains available;
* ^Q exits.

This preserves bidirectional navigation through the completed display.

## 15. Quit Key

In transient paged mode:

```
^Q      exit TYPE.COM

```

^Q is the canonical quit key.
ESC does not exit TYPE.COM.
The BetterCP/M convention that ESC exits a subordinate interactive mode belongs to programs such as VIEW.COM; TYPE.COM currently defines no subordinate modes.

## 16. /7 — 7-Bit Display

/7 enables high-bit stripping.
For each displayed data byte:

```
display_byte = file_byte AND 7Fh

```

This transformation occurs only after raw EOF detection.
Therefore:

* raw 1Ah terminates text;
* raw 9Ah with /7 becomes 1Ah for display purposes only;
* the transformed 1Ah does **not** terminate TYPE.

With /7 /CTL, raw 9Ah shall therefore be rendered as:

```
^Z

```

With /7 but without /CTL, the transformed 1Ah is passed to the display path as ordinary data and shall not be interpreted internally as EOF.
The transformation applies only to displayed text and shall not modify the file.

## 17. /T — Tab Expansion

/T enables tab expansion.
Tabs shall expand to fixed 8-column tab stops.
For BetterCP/M 1.0:

* tab width is not configurable;
* /T is off by default;
* without /T, TAB bytes are passed through to the console according to normal terminal behavior.

Tab expansion is display-only and does not modify the source file.

## 18. /CTL — Visible Controls

/CTL displays control characters visibly using conventional caret notation.
The complete mapping is:

```
00h       ^@
01h-08h   ^A-^H
09h       ^I
0Ah       ^J
0Bh       ^K
0Ch       ^L
0Dh       ^M
0Eh-19h   ^N-^Y
1Ah       ^Z when it is display data
raw 1Ah   CP/M EOF -- not displayed
1Bh       ^[
1Ch       ^\
1Dh       ^]
1Eh       ^^
1Fh       ^_
7Fh       ^?

```

Control characters other than CR and LF shall not perform their ordinary terminal-control function while /CTL is active.
Examples:

* TAB is shown as ^I;
* FF is shown as ^L and does not clear the console;
* ESC is shown as ^[;
* DEL is shown as ^?.

A transformed value of 1Ah, such as raw 9Ah processed by /7, is display data and shall appear as ^Z.
A raw source byte of 1Ah never reaches /CTL; it has already terminated text input.

## 18.1 Line-End Rendering under /CTL

CR and LF remain structurally meaningful even though they are displayed visibly.
The required behavior is:

```
CR LF     display ^M^J, then begin a new display line
CR alone  display ^M,   then begin a new display line
LF alone  display ^J,   then begin a new display line

```

The visible markers shall not be allowed to execute the terminal-control action they represent.
Thus, for example, displaying ^M shall not cause an actual carriage return that overwrites previously displayed text.
This preserves both:

* visible representation of the control byte;
* readable source line structure.

## 18.2 /CTL and /T

When /CTL is active, TAB shall be displayed as:

```
^I

```

rather than expanded.
Therefore /CTL takes precedence over /T for TAB rendering.

## 19. Display Processing Order

The rendering pipeline shall behave conceptually as follows:

```
raw file byte
     |
     +-- raw byte == 1Ah? ---> EOF
     |
     +-- /7 active? --------> clear bit 7
     |
     +-- transformed byte may now equal 1Ah,
     |   but is NOT EOF
     |
     +-- /CTL active? ------> visible-control rendering
     |
     +-- /T active and TAB? -> expand to 8-column stop
     |
     +-- ordinary display

```

Important consequences:

* EOF is determined exclusively from the **raw source byte**;
* raw 1Ah always terminates text before /7;
* /7 may produce a display value of 1Ah without terminating the command;
* /7 /CTL renders transformed 1Ah as ^Z;
* /CTL handles control bytes before /T;
* /CTL /T displays TAB as ^I;
* display transformations never modify the file.

## 20. Screen-Edge Behavior

TYPE.COM does not implement configurable wrapping.
There is no /W or /C= option.
Long lines continue according to the console's ordinary behavior at the screen edge.
If the terminal wraps automatically, the output spills naturally onto the next display row.
TYPE.COM shall account for those additional display rows when determining page boundaries.
No horizontal scrolling is provided.

## 21. Files Modified During Display

TYPE.COM does not provide snapshot semantics.
The command assumes that selected files remain stable for the duration of the operation.
If another program or process modifies a file while TYPE.COM is running:

* redisplayed pages may reflect the changed contents;
* backward-page reconstruction may therefore differ from what was displayed previously;
* no attempt is made to preserve an old copy of the file;
* no guarantee is made that changes can be detected.

If reconstruction encounters an open or read failure after such a change, normal skip-and-continue error handling applies.
This behavior is intentional. TYPE.COM shall not implement elaborate file-change detection that cannot be made reliably portable across CP/M systems.

## 22. Error Handling

TYPE and TYPE.COM are observational commands. They do not modify files.
Accordingly, recoverable file failures use a simpler policy than destructive or mutating utilities.

## 22.1 File Open Failure

If a selected file cannot be opened:

```
TYPE B3:FOO.TXT - Cannot open.

```

TYPE.COM shall abandon that file and continue with the next selected file.
No interactive retry prompt is required.

## 22.2 Read Failure

If a read error occurs:

```
TYPE B3:FOO.TXT - Read error.

```

TYPE.COM shall abandon the current file and continue with the next selected file.
A partially displayed file remains partially displayed; no rollback is necessary.

## 22.3 Fatal Errors

An error that prevents TYPE.COM itself from continuing safely shall terminate the command.
Examples may include unrecoverable internal state or console failures.

## 22.4 Unattended Operation

No /B or other batch-specific switch is required.
The default error policy is already suitable for unattended use:

* report the error;
* skip the affected file where possible;
* continue with the remaining selection;
* abort only on a genuinely fatal condition.

TYPE shall never wait indefinitely for an error-response prompt merely because it encountered an unreadable selected file.

## 23. /VER

Both resident and transient forms shall support /VER.
Resident form:

```
BetterCP/M TYPE 1.0 (Resident, Build nnn)

```

Transient form:

```
BetterCP/M TYPE 1.0 (Build nnn)

```

/VER prints the version banner and exits without processing files.

## 24. Excluded Features

The following are explicitly outside TYPE.COM and belong to VIEW.COM or another utility:

* line numbering;
* configurable word wrapping;
* explicit wrap columns;
* line-by-line scrolling;
* horizontal scrolling;
* full WordStar movement diamond;
* search;
* interactive display-mode toggles;
* SQ/USQ decompression;
* CRUNCH decompression;
* CrLZH decompression;
* automatic compression detection;
* hex display;
* raw-byte inspection;
* page numbering;
* editing;
* file modification.

These exclusions are architectural, not merely deferred implementation details.

## 25. Behavioral Summary

Resident examples:

```
TYPE README.TXT
TYPE *.TXT
TYPE B[-]:*.DOC[$ARC]
TYPE README.TXT /P

```

Transient examples:

```
TYPE *.TXT
TYPE B[-]:*.DOC /P
TYPE README.TXT /7
TYPE README.TXT /T
TYPE README.TXT /CTL
TYPE README.TXT /7 /CTL

```

Transient paged controls:

```
^R / ,     previous page
^C / .     next page
SPACE      next page
<          beginning of current file;
           previous file if already there
>          next file
^Q         quit

```

Current file means the file associated with the current page anchor.
At the end of the final selected file, TYPE.COM remains in paged mode until ^Q is pressed.

## 26. Design Boundary

The defining implementation rule is:
TYPE displays text and may page through it. It does not become a general interactive file-inspection environment.
Any feature that requires persistent interactive navigation beyond page/file movement, dynamically changes the interpretation of the file, or turns TYPE into a screen-oriented inspection tool belongs in VIEW.COM.
This specification deliberately keeps TYPE.COM substantially more capable than resident TYPE, while preserving TYPE's identity as a text-display command rather than a full viewer.
