# TYPE / TYPE.COM Engineering Specification



Status: resident TYPE (RCP Build 007) and transient TYPE.COM Build 004 are
implemented and qualified on the supported 80-by-24 cpmsim and Model 4 platforms
as of 2026-10-13. See [TYPE Qualification](TYPE%20Qualification.md) for scope and
ordinary-output abort behavior. The user interface is in user-guide section 4.4.

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

Options are repeatable whitespace-delimited tokens before or after one source
operand. Current platforms use 80 columns and 24 rows; no console-geometry query
exists in the current ABI. Paged selection admits at most 65,535 unique files
and rejects counter overflow before opening a file. Page prompts and ordinary
output abort behavior are qualified below.
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
Outside paged input mode, TYPE.COM does not redefine Ctrl-C. Normal console/BDOS
Ctrl-C handling applies. BDOS warm boot abandons the utility before its cleanup
runs, so this abrupt abort retains the active file's drive/user area. Caller-DU
restoration applies to normal completion and controlled paged quit. This same
standard abort exception applies to resident TYPE during ordinary output.
This distinction is intentional and shall be documented.

## 12. Multi-File Navigation

In paged mode:

```
<       beginning of current file
>       beginning of next file

```

File movement is boundary-oriented rather than a fixed page distance. For
example, if only a few lines of the current file lie above the screen, `<`
moves back only as far as its beginning and puts the banner at the top; it
must not move a whole page into the preceding file.

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
* > is a no-op only when the page anchor belongs to the last selected file;
* TYPE.COM may sound the console bell or give another minimal indication;
* backward movement remains available;
* ^Q exits.

A final page may start in an earlier file and include later files below it.
In that case `>` still moves to the next file boundary, placing that file's
banner at the top even though it was already visible mid-screen. This is the
maintainer's clarification of 2026-10-13 and takes precedence over the earlier
unconditional final-EOF `>` no-op rule.

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


## Resident implementation — 2026-10-13

RCP Build 007 uses the shared selector transaction and concrete-file scanner.
The complete syntax and supported A:–D: drive domain are validated before file
access. Sources use the common scanner's unique lexical filename order within
DU bitmap order; each concrete file is displayed once even with multiple
physical extents. RO/SYS do not suppress display; attribute predicates alone
control admission.

`/P` is a separate token before or after the single source operand; repetition
is harmless. Unsupported switches and extra operands are rejected before
opening files. `/VER` retains the common version-query path without file
access. Automatic handoff is still separate work.

Unpaged output streams raw text through BDOS Function 2, including literal `$`
and high-bit bytes, until raw 1Ah or sequential EOF. Empty files remain in the
sequence. A CR/LF-delimited dashed separator appears between successfully opened
files. Open/read failures report a short diagnostic, skip the file and continue.
Files are closed and the caller DU is restored on normal completion and paged
Ctrl-C cancellation.

Resident paging counts source LF bytes across the selection, pausing every 23
lines with `--More--`. Space and `.` continue; other keys are ignored, and
Ctrl-C cancels. This is the permitted small resident accounting model; rendered
rows, configurable geometry and bidirectional navigation belong to TYPE.COM.
Separator rows do not contribute to this source-line counter.

TYPE was the last resident caller of the legacy DU parser. Removing that dead
resident parser and its unused exact-name helper makes the final RCP payload
6,785 bytes, 95 bytes smaller than Build 006. Rounded allocation remains 6,912
bytes; 744 relocations retain the existing 1,536-byte carrier header. Native
ZSM4/LINK and cross assembly produce identical payloads. BDOS, the CPX ABI and
protected-state layout are unchanged. Legacy transient expansions retain their
old parser until TYPE.COM is implemented separately.

`tools/test_resident_type.py` executes relocated production carriers at 4000h,
8101h and A000h. It covers selectors/predicates, protected display, duplicate
extents, empty files, literal `$`, raw EOF/high-bit data, both forward keys,
paging cancellation, open/read failure continuation, invalid syntax before file
access and caller-DU restoration. Shared-selector, resident REN mapping and
utility-version regressions also pass. Real-media qualification uses
`tools/test_resident_type_media.py` with disposable disks and no TYPE.COM.


Real BetterCP/M media campaigns passed on cpmsim and Model 4/trs80gp with no
TYPE.COM installed. They verify protected-file display through compound
selectors, separators, raw text EOF, invalid syntax, resident version reporting
and unchanged selected-file contents/attributes. cpmsim additionally verifies
Space/`.` paging continuation and Ctrl-C cancellation with return to the caller
DU. Model 4 uses a SUBMIT sequence; its queue changes are excluded from the
selected-file immutability check. The representative Model 4 campaign does not
exercise interactive paging keys; those are covered by cpmsim and relocated
assembled-code tests.


## Transient streaming increment — 2026-10-13

TYPE.COM Build 001 links the shared DU/filespec/attribute engine and the common
unique-file scanner into its own executable. It does not call or require RCP.
Sources follow the shared lexical order within DU bitmap order; duplicate
physical extents are displayed once. Syntax/domain checks finish before file
access. Multi-file selections have qualified banners; wildcard single matches
also receive a banner. A single exact match omits it. Empty selected files have
no synthetic content.

`/7`, `/T` and `/CTL` are independent, repeatable, whitespace-delimited tokens
before or after the single source operand. `/VER` uses the shared pure query
path. Bare TYPE, additional operands and unknown switches are rejected before
file access. Raw 1Ah ends text before any transformation. `/CTL` renders raw or
transformed control data, normalizes CR/LF line structure without executing the
visible controls, and takes precedence over `/T`. A pending CR survives record
boundaries and is flushed on EOF or read failure. Source contents/attributes
are unchanged and the caller DU is restored. Open/read failures report the
qualified filename, abandon that file and continue without prompts.

The executable is 3,223 bytes; native ZSM4/LINK and cross builds are byte-identical.
Assembled-code streaming tests cover protected display, selectors, banners,
empty/multi-extent files, high-bit/raw EOF distinctions, tab/control precedence,
CR/LF across record boundaries, error continuation, version purity and invalid
syntax before file access. Bidirectional paging, page anchors, file navigation,
geometry and backward-history reconstruction are the next increment. `/P` is
explicitly rejected by this intermediate build; the historical forward-only
transient pager is retired rather than presented as the settled `/P` contract.
The resident forward-only `/P` remains available.


The streaming media campaign passed under cpmsim and Model 4/trs80gp using
`tools/test_resident_type_media.py --transient`. It checks version reporting,
compound selection of protected files, banners, visible line-end controls,
option placement, unsupported `/P`, raw EOF suppression and unchanged selected
file contents/attributes. The resident fixture and utility-version regressions
also passed after adding TYPE's independent utility identity.


## Transient page replay increment — 2026-10-13

TYPE.COM Build 002 accepts `/P` anywhere among the option tokens. Rendering
counts screen rows using the current platform baseline of 80 columns and 24
rows, reserving one row for the page prompt. Long lines, banners, expanded tabs
and visible-control pairs contribute to row accounting. Raw tabs advance to
8-column stops. Prompts are emitted outside page accounting; partial final
lines remain visible above the prompt.

Space, `.` and Ctrl-C advance; `,` and Ctrl-R go backward; Ctrl-Q quits. Input
uses BDOS Function 6, so Ctrl-C is consumed as Next only at the prompt. Escape
and unrelated keys are ignored. Backward movement at the first page and forward
movement at final EOF are no-ops with a bell. Final EOF retains the displayed
page for backward navigation. A single empty exact file does not invent a
content page or a paging prompt.

The page anchor records the DU/name associated with the first rendered byte of
the page. A lower file banner does not change it. A page beginning with a new
file's banner belongs to that file. The implementation uses a 32-bit logical
page index and reconstructs previous pages from the selection's start instead
of retaining a fixed anchor cache. It suppresses replay output until reaching
the target. This preserves unrestricted history but may make backward paging
slow on floppy systems. It does not snapshot file contents; if changed contents
end before a replay target, it clamps to and redisplays the final available page.

The executable is 3,938 bytes. Native ZSM4/LINK and cross assembly match.
`test_type_paging.py` covers all page-key aliases, final and exact-full-page EOF,
row wrapping, visible controls, source changes during replay, page/file-anchor
binding and reconstruction through ten pages. Streaming, resident TYPE and
utility-version regressions pass. `test_type_paging_media.py` qualifies the
actual Ctrl-C/Ctrl-R/Ctrl-Q path under cpmsim and compares the complete source
disk after navigation.

Explicit `<`/`>` file movement is the next increment; those keys currently do
nothing. Full TYPE.COM release qualification remains pending. There is no
configurable-console query in the current console ABI; the implementation uses
the established 80-by-24 platform geometry and needs geometry review when a
configuration/provider interface is introduced. No BDOS or resident growth is
introduced by this transient implementation.


`test_model4_type_paging.py` also passed the same forward/backward/final-EOF
sequence through actual Model 4 keyboard matrix events in trs80gp. Screen
captures verify page transitions and return to the prompt, and the complete DMK
image remains unchanged. Both platform campaigns confirm Ctrl-C is Next while
waiting for a page command and Ctrl-Q exits. The Model 4 campaign retains its
invocation, captures, media and executable hash in the report directory.


## Transient file-navigation increment — 2026-10-13

TYPE.COM Build 003 implements `<`/`>` using the starting file of the page.
Paged selection counts the complete unique source sequence before display to
establish navigation bounds. Empty files retain their own ordinal and banner.
An unpaged invocation retains its two-match banner probe.

`<` goes to the current file's banner unless already at its beginning; from
there it goes to the previous file. The distance may be less than a screenful.
`>` goes to the next file's banner, including when that banner was already
visible lower on the final page. Only the last anchored file blocks `>`.
Movement beyond selection bounds leaves the page unchanged and sounds a bell.

A boundary jump clears/homes through the current BetterCP/M native console
control (28, the same operation as CLS), suppresses the inter-file blank
separator, and places the banner on the first display row. Other page redraws
also clear/home. Rendering anchors now use 32-bit absolute display-row offsets,
rather than integer page numbers, so page movement after an arbitrary file
boundary can be reconstructed without rounding back to an unrelated page.
The per-page DU/name anchor and beginning-of-file flag remain independent of
later files shown on that page. Row replay includes skipped separator rows in
its absolute coordinates. A source change that removes the requested ordinal
clamps to the last available selected file.

The executable is 4,334 bytes; native ZSM4/LINK and cross assembly are identical.
`test_type_files.py` covers mixed page/file movement, a partial backward jump
near a file's beginning, multi-DU order, empty files, selection bounds, and
file boundaries on final cross-file pages. Existing streaming, paging and
utility-version regressions pass. Platform file-navigation qualification uses
`test_type_file_media.py`, retaining transcripts/screens, media and executable
hashes. Full TYPE release qualification remains separate from this milestone.


The file-navigation media campaigns passed on cpmsim and Model 4/trs80gp with
whole-disk immutability. Model 4 captures independently check that a file
boundary banner occupies display row zero after forward and backward jumps.
The second test command needs a post-WBOOT input delay in the harness, so the
keyboard scanner is ready after the new prompt appears; the campaign retains
an intermediate command-entry capture as evidence. Empty files and final-page
boundaries are exercised in a separate short-file sequence. No production
keyboard or BIOS change is part of this increment.


## Final qualification — 2026-10-13

Build 004 fixes native tab alignment after page clear/home: control 28 homes
physical output but does not reset the cooked BDOS column. A following CR now
synchronizes that column before raw TAB output. Row accounting for remaining
data bytes, including transformed 9Ah -> 1Ah under `/7`, follows the cooked
BDOS one-cell column model rather than treating transformed control data as EOF
or zero width. Use `/CTL` for a predictable visible representation of controls.

A checked source-ordinal increment rejects overflow instead of wrapping the
16-bit selected-file index. The private stack reserves 128 bytes; the fixture
observed 30 bytes used while exercising rendering, paging and file jumps, with
a 16-byte low-end guard intact. The executable is 4,383 bytes and is native/cross
byte-identical. BDOS, BIOS, CCP and RCP production code do not grow.

Both platform campaigns qualify final cross-file EOF, empty-file boundaries,
actual row-zero banners, native BDOS tab expansion and unchanged disk images.
All assembled-code streaming/page/file/limit tests and utility-version tests
pass. Ordinary output cancellation is separately qualified for both resident
and transient TYPE with real BDOS Ctrl-S/Ctrl-C, retaining the active DU as
required by standard WBOOT behavior. Controlled paged exit restores the caller.
See [TYPE Qualification](TYPE%20Qualification.md) for reproduction and limits.
