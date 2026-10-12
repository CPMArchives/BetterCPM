# BetterCP/M 1.0 Monitor Provider Behavioral Requirements

Accepted behavioral implementation basis, 2026-10-12. Historical cases explicitly marked unresolved remain qualification gates; this document does not claim installed or fully qualified provider support.

## 1. Scope

This specification defines the externally observable behavior of the initial BetterCP/M monitor personalities:

- **MM-style ADM-3A** — for the TRS-80 Model 4 target, using Montezuma Micro 2.32 console behavior as the principal compatibility target.
- **VT52** — for the general BetterCP/M target.

It covers:

- output character interpretation;
- cursor movement and addressing;
- screen erasure;
- wrapping and scrolling;
- keyboard encoding;
- cursor presentation;
- terminal-generated replies;
- parser state;
- malformed and incomplete sequences;
- concrete compatibility tests.

It does **not** specify:

- BIOS hooks;
- RSX loading, unloading, relocation or lifecycle;
- provider metadata;
- memory layout;
- manager transactions;
- TPA cost;
- internal renderer organization.

Those matters belong to the separate Monitor RSX hook/lifecycle contract. That contract explicitly defines the 1.0 monitor interface as a bounded private mechanism rather than the eventual post-1.0 TCAP architecture. [Monitor hook/lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).

---

## 1.1 Initial Personalities and Long-Term Goal

ADM-3A and VT52 are the **initial qualification targets**, not the intended limit of BetterCP/M terminal support.

The long-term goal is:

> **Support as broad a range of historically significant CP/M terminal personalities as is practical.**

Future personalities may include, among others:

- Kaypro;
- Osborne;
- Hazeltine;
- Televideo;
- ANSI/VT100;
- other DEC terminals;
- machine-specific CP/M consoles;
- terminal types represented in historical CP/M and Z-System terminal-definition libraries.

ADM-3A and VT52 therefore constitute:

> **the first supported monitor personalities**

rather than permanent BetterCP/M terminal standards.

---

## 1.2 Extensibility Principle

A new terminal personality should normally be added by supplying another monitor provider conforming to the same monitor-provider contract.

Adding one should not require:

- modifying legacy CP/M applications;
- introducing a BetterCP/M-specific console API into those applications;
- changing the standard CP/M console interface;
- teaching individual utilities about each terminal type.

The compatibility objective is:

> A CP/M application already configured for a supported historical terminal should run unmodified when the corresponding BetterCP/M monitor personality is active.

The eventual general TCAP/profile system remains post-1.0 work.

---

# 2. Requirement Classes

Features are classified as follows.

### REQUIRED

Part of the BetterCP/M compatibility contract for that personality. Qualification tests must pass.

### OPTIONAL

Historically valid behavior which is not required for the initial compatibility floor.

### UNSUPPORTED

Deliberately outside the initial personality. Recognizable unsupported commands should normally be consumed harmlessly rather than leak command bytes to the display.

### UNRESOLVED

Historical evidence is incomplete, contradictory, or insufficiently authoritative. BetterCP/M shall not invent behavior merely to complete the table.

---

# 3. Common Provider Requirements

## 3.1 Geometry

Both initial personalities target:

```text
80 columns × 24 rows
```

Coordinates in this specification are zero-based except where encoded wire values are shown:

```text
row     0..23
column  0..79
```

---

## 3.2 Parser State

A provider may retain bounded parser state across output calls.

The explicit parser-reset operation shall:

- abandon any incomplete terminal sequence;
- return the parser to ordinary-character state;
- preserve screen contents;
- preserve cursor position;
- preserve unrelated persistent terminal modes;
- preserve queued keyboard input and terminal replies.

The internal clear/home operation shall additionally abandon any incomplete sequence. These operations are part of the accepted MCON interface. [Monitor hook/lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).

Warm command-return handling specifically requires parser reset so an application's unfinished escape sequence cannot consume returning CCP output. [Monitor hook/lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).

---

## 3.3 Personality-Specific Semantics

Shared renderer code must preserve real differences between terminal personalities.

For example:

```text
MM-ADM3A printable at right margin -> wrap
VT52 printable at right margin     -> remain at column 79
```

The implementation must not normalize all providers to a lowest-common-denominator terminal.

---

# 4. MM-ADM3A Compatibility Target

The Model 4 provider targets the console behavior represented by the reconstructed **Montezuma Micro 2.32 BIOS**, with historical documentation and eventual comparison to the selected MM binary used to resolve uncertain edges.

The reconstructed source is useful implementation evidence but is not proof that every Montezuma release behaved identically. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

The audited source identifies the console as ADM-3A emulation and establishes a much more specific MM control contract than generic physical ADM-3A documentation alone. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

---

# 5. MM-ADM3A Control Table

The current provisional MM 2.32 behavioral contract is:

| Byte | Behavior | Status |
|---:|---|---|
| `00h–06h` | Ignore | REQUIRED |
| `07h` | Bell | REQUIRED |
| `08h` | Cursor left/backspace | REQUIRED |
| `09h` | Horizontal tab | REQUIRED |
| `0Ah` | Down / scroll | REQUIRED |
| `0Bh` | Cursor up | REQUIRED |
| `0Ch` | Cursor right | REQUIRED |
| `0Dh` | Carriage return | REQUIRED |
| `0Eh` | Reverse video OFF | REQUIRED |
| `0Fh` | Reverse-video action | **UNRESOLVED** |
| `10h–14h` | Ignore | REQUIRED |
| `15h` | Erase to end of line | REQUIRED |
| `16h` | Toggle reverse video | REQUIRED |
| `17h` | Erase to end of screen | REQUIRED |
| `18h` | Erase to end of line | REQUIRED |
| `19h` | Erase to end of screen | REQUIRED |
| `1Ah` | Clear screen and home | REQUIRED |
| `1Bh` | Begin escape sequence | REQUIRED |
| `1Ch` | Insert line | REQUIRED command; exact edge behavior to qualify |
| `1Dh` | Delete line | REQUIRED command; exact edge behavior to qualify |
| `1Eh` | Home | REQUIRED |
| `1Fh` | Ignore | REQUIRED |

The audit establishes `15h/18h` as EOL erase, `17h/19h` as EOS erase, `1Ch` insert line and `1Dh` delete line. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

---

## 5.1 Reverse Video `0Fh`

The reconstructed source routine reached by `0Fh` **toggles** reverse video even though its descriptive comment says that the control turns reverse video on.

The audit explicitly recommends confirmation against the selected MM binary before promising this behavior. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

Therefore:

```text
0Eh   reverse OFF
16h   reverse TOGGLE
0Fh   UNRESOLVED pending binary qualification
```

No final 1.0 behavioral claim shall be made for `0Fh` until that comparison is complete.

---

# 6. MM-ADM3A Escape Commands

The reconstructed MM source establishes:

```text
ESC = row+20h column+20h    direct cursor address
ESC 0                       cursor OFF
ESC 1                       cursor ON
```

Unknown ESC selectors reset parser state without printing the selector. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

All three recognized commands are part of the MM compatibility target.

---

# 7. MM Printable Output and Right Margin

Required behavior:

```text
ordinary position:
    write character
    advance column

column 79:
    write character
    cursor -> next row, column 0

row 23, column 79:
    write character
    scroll upward one line
    cursor -> row 23, column 0
```

---

# 8. MM Cursor Movement

## 8.1 `08h` — Backspace / Left

Required:

- column > 0 → move left one;
- column 0, row > 0 → previous row, column 79;
- `(0,0)` → remain `(0,0)`.

The audited reference explicitly notes cross-row backspace behavior. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

---

## 8.2 `09h` — Tab

Required:

- fixed 8-column stops;
- advance to next stop;
- line overflow follows MM rightward wrap behavior;
- crossing the screen bottom scrolls.

---

## 8.3 `0Ah` — Down / Line Feed

Required:

- move down one row;
- preserve column;
- bottom row causes upward scroll;
- cursor remains row 23 after scrolling.

---

## 8.4 `0Bh` — Up

Required:

- move up one row;
- row 0 → no-op;
- no downward scroll.

---

## 8.5 `0Ch` — Right

Required:

- move right one column;
- right-margin crossing wraps to next row;
- bottom crossing scrolls.

---

## 8.6 `0Dh` — Carriage Return

Required:

```text
column := 0
row unchanged
```

---

# 9. MM Erasure and Home

## 9.1 `15h` and `18h` — Erase to EOL

Required:

- erase cursor cell through column 79 inclusive;
- cursor unchanged.

---

## 9.2 `17h` and `19h` — Erase to EOS

Required:

- erase cursor cell through the bottom-right screen cell inclusive;
- cursor unchanged.

---

## 9.3 `1Ah` — Clear/Home

Required:

- clear entire screen;
- cursor `(0,0)`.

---

## 9.4 `1Eh` — Home

Required:

```text
cursor := (0,0)
screen unchanged
```

---

# 10. MM Insert/Delete Line

The audited MM reference implements:

```text
1Ch   insert line
1Dh   delete line
```

[MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

These commands are therefore part of the required MM personality.

However, before freezing framebuffer-level edge semantics, qualification shall verify against the selected MM binary:

- which row is inserted/deleted relative to cursor position;
- which direction existing rows shift;
- what happens to the discarded edge row;
- what fills the newly created row;
- whether cursor row and column change;
- interaction with reverse-video state if relevant.

The commands themselves are no longer unresolved; only exact edge semantics await qualification.

---

# 11. MM Direct Cursor Addressing

Required:

```text
ESC = row+20h column+20h
```

Examples:

```text
ESC = 20h 20h   -> (0,0)
ESC = 25h 2Ah   -> (5,10)
ESC = 37h 6Fh   -> (23,79)
```

---

## 11.1 Coordinate Clipping

The reconstructed source clamps unsupported coordinates to:

```text
row     -> 23
column  -> 79
```

after unsigned subtraction of `20h`. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

This is provisionally REQUIRED.

Low encoded values whose unsigned subtraction produces a large result shall be tested explicitly against the selected binary before final provider qualification.

---

# 12. MM ESC Parser

## 12.1 Unknown Selector

Example:

```text
ESC X
```

where `X` is not `=`, `0`, or `1`.

Required:

- consume `X`;
- perform no display action;
- reset ESC parser state;
- do not print `X`.

This behavior is established by the audited reference. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

---

## 12.2 Incomplete Cursor Address

After:

```text
ESC
ESC =
ESC = row
```

the provider remains in the corresponding incomplete state until:

- the remaining bytes arrive; or
- parser reset occurs.

Parser reset abandons the sequence without otherwise changing the display or cursor.

---

# 13. MM Cursor Visibility

Required:

```text
ESC 0    cursor hidden
ESC 1    cursor visible
```

Cursor visibility state survives ordinary character output.

Parser reset shall not itself change cursor visibility.

Clear/home shall follow the selected MM historical behavior once qualification establishes whether clear has any visibility side effect; no side effect should be invented in advance.

---

# 14. MM Keyboard Scope

The monitor contract fundamentally transports **character bytes**, not portable abstract key events.

For the initial Model 4 provider:

- preserve the selected BetterCP/M/Model 4 keyboard byte behavior;
- qualify that behavior against the intended MM compatibility environment;
- ordinary printable and CTRL keys remain ordinary character/control bytes;
- ENTER produces `0Dh`.

Historical MM special-key mappings were configurable, so a universal Montezuma arrow/CLEAR/BREAK table shall not be invented.

The audit explicitly calls for keyboard behavior to be qualified against the MM binary and real ADM-3A-configured applications. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

---

# 15. MM Terminal Replies

The MM personality shall generate **no unsolicited terminal replies** unless historical qualification establishes a specific required reply.

For 1.0, do not invent:

- answer-back strings;
- terminal identification replies;
- modem-control responses.

---

# 16. BetterCP/M Clear-Screen Migration

BetterCP/M's current basic console uses literal `1Ch` for clear/home, which conflicts with MM's `1Ch` insert-line meaning.

Therefore internal BetterCP/M users of literal `1Ch` **will be migrated** to the explicit MCON clear/home operation.

This migration is specified but production implementation remains pending. [Monitor hook/lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).

---

# 17. VT52 Compatibility Target

The general provider targets DEC VT52 behavior sufficiently closely that CP/M software installed for a VT52 can run without modification.

The required base model is:

```text
80 columns × 24 rows
```

with historically documented:

- cursor motion;
- direct addressing;
- erasure;
- right-margin behavior;
- scrolling;
- identification.

Parser edge cases not yet independently established from sufficiently strong original-VT52 evidence remain explicitly unresolved.

---

# 18. VT52 Printable Output

Required:

- print at current cell;
- column < 79 → advance one;
- column 79 → remain at column 79.

Thus:

```text
(5,78) + A -> A at 78, cursor 79
(5,79) + B -> B at 79, cursor 79
         C -> C replaces B, cursor 79
```

No automatic printable-character wrap occurs.

---

# 19. VT52 Basic Controls

Required:

| Byte | Behavior |
|---:|---|
| `00h` | Ignore |
| `07h` | Bell |
| `08h` | Cursor left; no line wrap |
| `09h` | VT52 TAB |
| `0Ah` | Line feed; scroll at bottom |
| `0Dh` | Carriage return |
| `7Fh` | Ignore |

No additional screen functions shall be invented for undocumented control codes.

---

# 20. VT52 Tab Behavior

Required zero-based stops:

```text
8, 16, 24, 32, 40, 48, 56, 64, 72
```

Required examples:

```text
col 0  -> TAB -> 8
col 8  -> TAB -> 16
col 72 -> TAB -> 73
col 78 -> TAB -> 79
col 79 -> TAB -> 79
```

TAB never wraps or scrolls.

---

# 21. VT52 Cursor Commands

Required:

```text
ESC A    up
ESC B    down
ESC C    right
ESC D    left
ESC H    home
ESC I    reverse line feed
```

### `ESC A`

Row - 1; row 0 → no-op.

### `ESC B`

Row + 1; row 23 → no-op.

**No scroll.**

### `ESC C`

Column + 1; column 79 → no-op.

### `ESC D`

Column - 1; column 0 → no-op.

### `ESC H`

Cursor `(0,0)`.

### `ESC I`

Normally move up one row.

At row 0:

- scroll screen downward;
- old bottom row discarded;
- new blank row at top;
- cursor remains row 0, same column.

---

# 22. VT52 Line Feed

`0Ah`:

- normally moves down one row;
- preserves column;
- at row 23 scrolls upward;
- new bottom row blank;
- cursor remains row 23.

Critical differential:

```text
LF at bottom     -> scroll
ESC B at bottom  -> no-op
```

---

# 23. VT52 Erasure

Required:

```text
ESC K    erase cursor through end of current line
ESC J    erase cursor through end of screen
```

Both include the cursor cell.

Cursor remains unchanged.

---

# 24. VT52 Direct Cursor Addressing

Required:

```text
ESC Y row+20h column+20h
```

Normal ranges:

```text
row      20h..37h
column   20h..6Fh
```

Examples:

```text
ESC Y 20h 20h -> (0,0)
ESC Y 25h 2Ah -> (5,10)
ESC Y 37h 6Fh -> (23,79)
```

---

## 24.1 High Invalid Row

Required where established by the historical reference:

```text
row > 37h -> retain existing row
```

A valid column parameter still takes effect.

---

## 24.2 High Invalid Column

Required:

```text
column > 6Fh -> column 79
```

---

## 24.3 Malformed Coordinate Values

Control-valued or otherwise malformed parameters whose original hardware behavior is not adequately documented remain **UNRESOLVED**.

Required safety properties:

- remain within the 80×24 screen model;
- never corrupt memory;
- never become permanently parser-stuck;
- explicit parser reset always restores normal parsing.

---

# 25. VT52 Identification

Required:

```text
ESC Z
```

generates:

```text
ESC / K
```

meaning VT52 without copier.

The reply modifies no screen state.

---

# 26. VT52 Reply Queue Semantics

Terminal-generated replies and keyboard input form one logical terminal-to-host byte stream.

## 26.1 Ordering

Bytes are delivered in the order they enter the provider’s input queue. This is provider-observed enqueue order, not a guarantee of physical keyboard arrival order: a polled backend may have an unread key that the provider has not yet observed. Already queued keyboard bytes remain ahead of a newly generated complete reply; bytes enqueued subsequently follow it.

Example:

1. keyboard byte `A` already queued;
2. host sends `ESC Z`;
3. reply `ESC / K` is queued;
4. keyboard byte `B` arrives.

Input order shall be:

```text
A
ESC
/
K
B
```

---

## 26.2 Reply Atomicity

An identification reply is one indivisible logical reply:

```text
1Bh 2Fh 4Bh
```

The queue shall never contain only a truncated prefix because capacity ran out midway.

---

## 26.3 Repeated Identification

Repeated:

```text
ESC Z
ESC Z
```

shall enqueue two complete replies:

```text
ESC / K ESC / K
```

subject to queue-capacity policy.

---

## 26.4 Queue Overflow

The provider must reserve enough buffering for at least one complete identification reply.

If insufficient room exists to enqueue a newly generated complete reply:

> discard the entire newest reply.

Do not enqueue a partial reply.

Existing queued keyboard or reply bytes remain intact.

---

## 26.5 Console Status

Console status remains **non-consuming**.

Checking status shall not remove:

- keyboard bytes;
- reply bytes.

This follows the MCON console-status contract. [Monitor hook/lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).

---

## 26.6 Parser Reset

Parser reset shall **not** discard queued input or completed replies.

It resets incomplete **output parsing**, not terminal-to-host input.

This matches the monitor contract's requirement that warm-return parser reset not silently discard ordinary keyboard input. [Monitor hook/lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).

---

# 27. VT52 Keyboard Scope

The current monitor interface exchanges character bytes; it does not define a general abstract keyboard-event API.

Required ordinary byte behavior includes:

```text
RETURN       0Dh
LINE FEED    0Ah
BACKSPACE    08h
TAB          09h
DELETE       7Fh
ESC          1Bh
```

A VT52 historically represents cursor keys as:

```text
Up       ESC A
Down     ESC B
Right    ESC C
Left     ESC D
```

However:

> Translating a physical or emulator-specific cursor-key event into those byte sequences is a backend responsibility unless and until BetterCP/M defines an abstract-key mechanism.

The monitor provider cannot infer an Up Arrow from an arbitrary character byte.

Therefore VT52 arrow-sequence generation is REQUIRED only when the platform/backend exposes a corresponding distinct logical key mechanism.

---

# 28. VT52 Auxiliary Keys

Historical sequences:

```text
ESC P
ESC Q
ESC R
```

for auxiliary keypad keys.

BetterCP/M status:

**OPTIONAL**

Only applicable where the backend exposes suitable distinct key events.

---

# 29. VT52 Alternate Keypad

Historical:

```text
ESC =    alternate keypad on
ESC >    alternate keypad off
```

BetterCP/M 1.0:

**OPTIONAL**

If not implemented:

- consume both sequences;
- perform no visible operation;
- do not print the final character.

If implemented later, use VT52 rather than VT100 keypad semantics.

---

# 30. VT52 Graphics Mode

Historical:

```text
ESC F    graphics on
ESC G    graphics off
```

BetterCP/M 1.0:

**OPTIONAL**

If unimplemented, consume as harmless no-ops.

Do not claim graphics-mode compatibility without the actual VT52 glyph mapping.

---

# 31. VT52 Hold-Screen Mode

Historical:

```text
ESC [
ESC \
```

BetterCP/M 1.0:

**UNSUPPORTED**

If received:

- consume harmlessly;
- do not generate XON/XOFF;
- do not alter normal scrolling.

---

# 32. VT52 Copier

**UNSUPPORTED**

BetterCP/M shall:

- not emulate the physical copier;
- never identify with `/L`;
- always identify with `/K`;
- not synthesize copier flow-control behavior.

---

# 33. VT52 BREAK

Physical VT52 BREAK is an electrical communications condition rather than an ordinary terminal character.

BetterCP/M:

**UNSUPPORTED as part of the monitor personality.**

Machine-specific BREAK/interrupt handling is outside this specification.

---

# 34. VT52 Parser Qualification

Well-established VT52 movement, erasure, addressing and identification behavior is normative.

More obscure parser edge cases shall be divided into:

### Normative

Behavior supported by sufficiently authoritative historical documentation and required before claiming VT52 compatibility.

### Research / Qualification

Candidate historical behavior which remains non-contractual until independently verified.

This distinction prevents a behavior merely observed in a later VT52-compatible implementation from being mistaken for proven original-VT52 behavior.

---

# 35. Pending-ESC Edge Cases

The following cases shall remain **UNRESOLVED unless confirmed by the selected primary VT52 reference**:

```text
ESC ESC A
ESC NUL A
ESC DEL A
ESC BEL A
other controls while ESC pending
unknown ESC finals
```

Candidate behavior documented in historical VT52-compatible sources may be used to build research tests, but those tests are not yet normative.

The implementation must nevertheless satisfy:

- bounded state;
- no memory corruption;
- no spurious terminal reply;
- parser-reset recovery.

---

# 36. MM Compatibility Tests

## MM-01 — Clear/Home

Input:

```text
ABC
1Ah
```

Expected:

- all cells blank;
- cursor `(0,0)`.

---

## MM-02 — Printable Wrap

Start `(5,79)`, output `A`.

Expected:

```text
A at (5,79)
cursor -> (6,0)
```

---

## MM-03 — Bottom Printable Scroll

Start `(23,79)`, output `A`.

Expected:

- upward scroll;
- cursor `(23,0)`.

---

## MM-04 — Cross-Line Backspace

Start `(10,0)`, output `08h`.

Expected:

```text
(9,79)
```

---

## MM-05 — Backspace at Home

Start `(0,0)`, output `08h`.

Expected unchanged.

---

## MM-06 — Tab

Start `(4,3)`:

```text
09h -> col 8
```

Start `(4,78)`:

Expected next-row behavior according to MM tab/wrap rules.

---

## MM-07 — LF at Bottom

Start `(23,17)`, output `0Ah`.

Expected:

- upward scroll;
- cursor `(23,17)`.

---

## MM-08 — Up at Top

`0Bh` at row 0 → no-op.

---

## MM-09 — Right at Edge

`0Ch` from `(6,79)` → `(7,0)`.

---

## MM-10 — Reverse OFF

Set reverse state active through a qualified mechanism, send `0Eh`.

Expected following text normal.

---

## MM-11 — Reverse Toggle

Send `16h` twice.

Expected:

- first changes reverse state;
- second restores previous state.

---

## MM-12 — `0Fh`

**RESEARCH TEST pending binary qualification.**

Determine whether it:

- sets reverse ON; or
- toggles reverse.

Do not make normative until confirmed.

---

## MM-13 — Erase EOL `15h`

At `(8,20)`, send `15h`.

Expected cols 20–79 blank, cursor unchanged.

---

## MM-14 — Erase EOL `18h`

Same expected behavior as `15h`.

---

## MM-15 — Erase EOS `17h`

At `(8,20)`, send `17h`.

Expected cursor cell through bottom-right blank.

---

## MM-16 — Erase EOS `19h`

Same expected behavior as `17h`.

---

## MM-17 — Direct Address

```text
ESC = 25h 2Ah
```

Expected:

```text
(5,10)
```

---

## MM-18 — High Coordinate Clipping

```text
ESC = 40h 7Fh
```

Expected provisionally:

```text
(23,79)
```

---

## MM-19 — Unknown ESC Selector

```text
ESC X A
```

Expected:

- `X` consumed;
- parser normal;
- `A` printed.

---

## MM-20 — Cursor OFF/ON

```text
ESC 0
```

Expected cursor hidden.

Then:

```text
ESC 1
```

Expected cursor visible.

---

## MM-21 — Parser Reset

Send:

```text
ESC =
```

invoke parser reset, then output `A`.

Expected ordinary printable `A`.

---

## MM-22 — Insert Line

`1Ch`.

Required command.

Framebuffer-level expected result to be frozen after MM-binary qualification.

---

## MM-23 — Delete Line

`1Dh`.

Required command.

Framebuffer-level expected result to be frozen after MM-binary qualification.

---

# 37. VT52 Normative Tests

## VT-01 — Printable Right Margin

Start `(5,79)`.

Output:

```text
A
B
```

Expected:

- final cell contains `B`;
- cursor remains `(5,79)`;
- no wrap.

---

## VT-02 — BS at Left Edge

Start `(7,0)`, send `08h`.

Expected unchanged.

---

## VT-03 — Tabs

```text
0  -> 8
8  -> 16
72 -> 73
78 -> 79
79 -> 79
```

---

## VT-04 — LF Bottom Scroll

`0Ah` at `(23,12)`:

- upward scroll;
- cursor `(23,12)`.

---

## VT-05 — `ESC B` at Bottom

At `(23,12)`:

```text
ESC B
```

Expected no-op, no scroll.

---

## VT-06 — Reverse LF at Top

At `(0,12)`:

```text
ESC I
```

Expected:

- screen shifts downward;
- blank top row;
- old bottom row discarded;
- cursor `(0,12)`.

---

## VT-07 — Up at Top

`ESC A` at row 0 → no-op.

---

## VT-08 — Right at Edge

`ESC C` at col 79 → no-op.

---

## VT-09 — Left at Edge

`ESC D` at col 0 → no-op.

---

## VT-10 — Home

`ESC H` → `(0,0)`.

---

## VT-11 — Erase EOL

`ESC K` erases cursor cell through column 79 inclusive.

Cursor unchanged.

---

## VT-12 — Erase EOS

`ESC J` erases cursor cell through bottom-right inclusive.

Cursor unchanged.

---

## VT-13 — Direct Address

```text
ESC Y 25h 2Ah
```

Expected `(5,10)`.

---

## VT-14 — High Invalid Row

Start `(7,3)`:

```text
ESC Y 40h 2Ah
```

Expected:

```text
row    7
column 10
```

---

## VT-15 — High Invalid Column

Valid row plus column greater than `6Fh`.

Expected column 79.

---

## VT-16 — Identification

Send:

```text
ESC Z
```

Expected queued input:

```text
1Bh 2Fh 4Bh
```

Screen unchanged.

---

## VT-17 — Identification Status Non-Consuming

After `ESC Z`:

- status reports ready;
- repeated status calls remain ready;
- first input returns `1Bh`;
- status remains ready until all three bytes have been consumed.

---

## VT-18 — Identification Ordering

Queue keyboard byte `A`, generate identification, then queue `B`.

Expected input:

```text
A ESC / K B
```

---

## VT-19 — Repeated Identification

Two `ESC Z` commands with enough queue space:

```text
ESC / K ESC / K
```

---

## VT-20 — Reply Queue Overflow

Arrange insufficient free space for a new three-byte reply.

Expected:

- existing queued bytes untouched;
- new identification reply entirely absent;
- no partial `ESC` or `ESC /` fragment.

---

## VT-21 — Parser Reset Preserves Reply

Generate `ESC Z`, invoke parser reset.

Expected:

- `ESC / K` still available through input.

---

## VT-22 — Unsupported Hold Screen

```text
ESC [
ordinary output
ESC \
```

Expected:

- control sequences consumed;
- no XON/XOFF;
- normal scrolling unaffected.

---

## VT-23 — No Copier Claim

Every successful `ESC Z` reply ends:

```text
/K
```

never `/L`.

---

# 38. VT52 Research Tests

The following remain characterization tests until historical evidence is sufficient to make them normative:

```text
ESC ESC A
ESC NUL A
ESC DEL A
ESC BEL A
unknown ESC final
control-valued ESC Y row
control-valued ESC Y column
```

Results shall be documented rather than silently promoted into the compatibility contract.

---

# 39. Cross-Personality Differential Tests

## DIFF-01 — Printable Right Margin

```text
MM-ADM3A -> wraps
VT52     -> holds at col79
```

---

## DIFF-02 — Left at Column 0

```text
MM BS   -> previous row, col79
VT52 BS -> remains col0
```

---

## DIFF-03 — Bottom Motion

```text
MM LF bottom    -> scroll
VT52 LF bottom  -> scroll
VT52 ESC B      -> no scroll
```

---

## DIFF-04 — Tab Near Right Margin

```text
MM    -> may advance to next row
VT52  -> never leaves current row
```

---

## DIFF-05 — High Invalid Row Address

```text
MM    -> clamp row23
VT52  -> retain previous row
```

---

## DIFF-06 — Legacy Clear

```text
MM 1Ah   -> clear/home
VT52 1Ah -> no VT52 clear-screen operation
```

BetterCP/M internal code will use the explicit monitor clear/home operation rather than rely on a personality-specific literal byte. [Monitor hook/lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).

---

# 40. Qualification Beyond Synthetic Tests

Before advertising the Model 4 provider as MM/ADM-3A-compatible, qualification shall include:

- addressing boundaries and clipping;
- interrupted escape sequences;
- parser reset;
- every supported control byte;
- insert/delete-line behavior;
- cursor visibility;
- reverse video;
- scrolling;
- keyboard behavior;
- comparison with the selected MM binary;
- at least one real ADM-3A-configured CP/M application under the target emulator/system.

These requirements directly follow the project's MM compatibility audit. [MM compatibility audit](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md).

VT52 qualification should likewise include representative real CP/M software configured for VT52 rather than rely solely on synthetic unit tests.

---

# 41. Outstanding Historical Questions

The current unresolved set is intentionally small.

### MM

1. **`0Fh` reverse-video semantics**
   Reconstructed code toggles; comment implies ON. Verify against selected MM binary.

2. **Insert-line exact semantics**
   Command existence is established; exact edge effects need qualification.

3. **Delete-line exact semantics**
   Same.

4. **Special Model 4 keyboard mappings**
   Historical MM tables were configurable; freeze only the selected target mapping.

### VT52

5. **Unknown ESC-final behavior**

6. **Controls while ESC is pending**

7. **Double ESC / NUL / DEL pending-ESC behavior**

8. **Malformed `ESC Y` control-valued coordinates**

These shall remain explicitly unresolved rather than being converted into invented terminal behavior.

---

# 42. Expansion Beyond ADM-3A and VT52

After the first two providers qualify, additional monitor personalities may be added incrementally.

Each should have:

- an identified historical target;
- documented provenance;
- required/optional/unsupported feature classification;
- output parser tests;
- movement and margin tests;
- keyboard encoding tests;
- terminal-reply tests where applicable;
- malformed-sequence recovery tests;
- differential tests against existing providers where useful.

The existence of many providers must not encourage false behavioral convergence.

If two historical terminals behaved differently, BetterCP/M should preserve that distinction.

---

# 43. Long-Term Compatibility Objective

The monitor-provider subsystem ultimately targets this use case:

```text
historical CP/M application
configured for terminal X
        |
        v
BetterCP/M terminal-X personality
        |
        v
actual BetterCP/M console backend
```

The application itself remains unchanged.

ADM-3A and VT52 therefore serve two roles:

1. immediate BetterCP/M 1.0 compatibility targets;
2. the first validation of an architecture intended eventually to support a broad range of CP/M terminal environments.

The general TCAP database, terminal discovery system and permanent post-1.0 terminal architecture remain future work.
