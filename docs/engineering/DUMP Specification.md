# BetterCP/M `DUMP.COM` Engineering Specification
**Initial DRI-compatible baseline**

Implementation and evidence: [DUMP Baseline Qualification](DUMP%20Baseline%20Qualification.md).

## 1. Purpose

`DUMP.COM` displays the contents of a CP/M file as hexadecimal bytes.

The BetterCP/M 1.0 baseline implementation shall reproduce the observable behavior of Digital Research's CP/M 2.2 `DUMP.COM`, using the published DRI `DUMP.ASM` as the reference implementation.

The BetterCP/M implementation shall be written natively for the Z80 using ZSM4. The DRI 8080 source defines behavior, not implementation technique.

No enhancements beyond the common BetterCP/M version facility are included in this initial specification.

---

## 2. Invocation

The DRI-compatible command form is:

```text
DUMP filename
```

A normal CP/M drive-qualified filename is also accepted through the CCP-created default FCB:

```text
DUMP B:filename
```

Examples:

```text
DUMP TEST.COM
DUMP B:DATA.BIN
```

The source file is taken from the first default FCB supplied by the CCP.

### 2.1 Addressing

The baseline clone supports ordinary CP/M drive qualification only.

It does **not** initially add:

- BetterCP/M DU syntax;
- explicit user-area selection;
- wildcards;
- multiple files;
- selectors.

An unqualified filename therefore refers to the current default drive and current user area in the ordinary CP/M manner.

---

## 3. BetterCP/M version command

BetterCP/M additionally supports the standard utility version query:

```text
DUMP /VER
```

The version display shall follow the compact utility-identification layout in
[BetterCP/M Visual Identity](../../specifications/VISUAL-IDENTITY.md):

```text
DUMP 1.0 (Build nnn)
  - - -
 | BetterCP/M Utilities
 | Hexadecimal File Display
```

The utility/version/build title begins at the primary margin. The short spaced
hyphen rule and indented vertical strokes form a single implied corner beneath
it. Use ordinary 7-bit ASCII and CR/LF line endings; no terminal-control,
color or special-character support is required.

`/VER` is standalone and performs no file access. This identification display
appears only for `/VER`; ordinary dump output retains the DRI-compatible layout.

The version and build number are supplied by BetterCP/M utility-version metadata,
rather than maintained independently in the DUMP implementation. `nnn` is a
placeholder for that metadata-owned build number.

---

# FILE ACCESS

## 4. Input file

DUMP uses the filename prepared by the CCP in the default FCB at `005Ch`.

The DRI reference performs no separate command-line filename parser.

The implementation shall therefore preserve ordinary CCP filename semantics for the baseline form.

---

## 5. Opening the file

Before reading:

1. the FCB current-record field is cleared;
2. BDOS Open File is performed;
3. an open return value of `FFh` is treated as failure.

On failure DUMP prints:

```text
NO INPUT FILE PRESENT ON DISK
```

and terminates.

There is no distinct diagnostic for:

- omitted filename;
- nonexistent filename;
- inaccessible filename,

where these cases ultimately produce the same Open File failure.

---

## 6. Sequential reading

The file is read with ordinary BDOS sequential reads.

Each successful BDOS read supplies one 128-byte CP/M logical record.

DUMP processes every byte of each successful record before requesting the next record.

Any nonzero sequential-read completion code terminates the dump, as in the DRI reference implementation.

There is no special ASCII end-of-file handling.

In particular:

```text
1Ah
```

has no special significance and is displayed like any other byte.

---

## 7. Final record semantics

DUMP operates on the CP/M record representation of the file.

Consequently, if the file's last allocated logical record contains padding beyond the application's meaningful byte stream, those bytes are displayed.

DUMP does not attempt to infer an exact byte length within the final 128-byte record.

This is intentional DRI-compatible behavior.

---

# DISPLAY FORMAT

## 8. General layout

DUMP displays **16 bytes per line**.

Each line consists of:

1. a four-digit hexadecimal byte offset;
2. sixteen hexadecimal byte values, each preceded by one space.

Conceptually:

```text
0000 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
0010 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
```

There is no ASCII interpretation column.

---

## 9. Hexadecimal representation

All hexadecimal output uses:

```text
0-9 A-F
```

Uppercase hexadecimal letters are required.

Each byte is always printed as exactly two hexadecimal digits.

Examples:

```text
00
07
3A
A0
FF
```

---

## 10. Offset

The offset is a 16-bit byte counter beginning at:

```text
0000
```

The offset printed at the beginning of each line corresponds to that line's first byte.

Successive line offsets are therefore:

```text
0000
0010
0020
0030
...
```

The reference implementation uses a 16-bit counter. Therefore, for files extending beyond 65,536 bytes, the displayed offset wraps modulo 65536 rather than expanding to five or more hexadecimal digits.

Thus:

```text
FFF0
0000
0010
...
```

is the DRI-compatible behavior.

The BetterCP/M baseline clone shall preserve this behavior.

---

## 11. Line construction

For every byte:

1. DUMP increments the logical byte counter;
2. prints one space;
3. prints the byte as two hexadecimal digits.

At every 16-byte boundary, before printing that line's first byte, DUMP:

1. emits CR/LF;
2. checks the console for pending input;
3. if no input is pending, prints the four-digit offset;
4. continues with the byte values.

---

## 12. Initial newline

Because the first byte is itself at a 16-byte boundary, the DRI implementation emits CR/LF before printing:

```text
0000
```

Thus ordinary output begins with a newline.

The BetterCP/M compatibility implementation should retain this behavior unless later deliberately changed as an extension.

---

## 13. Terminating newline

Normal EOF, keyboard interruption, and open failure all eventually pass through the common exit path.

The common exit path emits CR/LF before returning to the CCP.

Thus a dump ends on a fresh line.

---

# KEYBOARD INTERRUPTION

## 14. Break checking

The DRI source describes the operation as a "break key" test, but the implementation actually checks whether **any console character is pending**.

The test occurs once per output line, immediately after CR/LF and before that line's offset is printed.

Therefore any pending key stops output.

There is no requirement that the character be:

```text
^C
```

or any other specific key.

---

## 15. Interruption granularity

DUMP does not check after every byte.

It checks only at 16-byte line boundaries.

Therefore, once a line has begun, all sixteen bytes of that line are normally emitted before another break test occurs.

---

## 16. Pending character is not consumed

The DRI implementation uses BDOS Console Status rather than Console Input.

It therefore detects a pending character without reading it.

The character remains pending when DUMP returns to the CCP.

This is an observable consequence of the reference implementation and belongs to the strict compatibility baseline.

Whether BetterCP/M later chooses deliberately to consume the break character should be treated as an enhancement decision, not silently changed in the clone.

---

# PROGRAM TERMINATION

## 17. Return to the CCP

The DRI program does not terminate through:

```text
JP 0000h
```

and therefore does not deliberately invoke a warm boot.

Instead it:

1. saves the CCP's entry stack pointer;
2. switches to its own local stack;
3. performs the dump;
4. restores the original CCP stack pointer;
5. executes `RET`.

The BetterCP/M implementation shall preserve the semantic behavior:

> Return directly to the invoking CCP without forcing a warm start.

The Z80 implementation need not reproduce the DRI stack code instruction-for-instruction; it need only preserve the resulting program semantics and BetterCP/M calling conventions.

---

# ERROR BEHAVIOR

## 18. Missing input file

The reference diagnostic is:

```text
NO INPUT FILE PRESENT ON DISK
```

preceded by CR/LF in the message itself and followed by the common terminating CR/LF.

The BetterCP/M clone should preserve the text for the compatibility baseline.

---

## 19. Read termination

The reference source does not distinguish EOF from alternative nonzero BDOS sequential-read completion values.

Any nonzero return terminates processing.

No additional DUMP-specific error message is generated by this code path.

Normal BDOS/BIOS handling of lower-level disk errors remains outside DUMP's own diagnostic machinery.

---

# DRI SOURCE DETAILS THAT ARE NOT USER-VISIBLE CONTRACTS

## 20. Internal stack size

The DRI source reserves 64 bytes for a local stack.

BetterCP/M does not need to duplicate this exact size.

The requirement is merely that the Z80 implementation provide sufficient safe transient stack space or use the established BetterCP/M transient-program stack convention.

---

## 21. Input buffer

The reference program uses the normal CP/M DMA buffer at:

```text
0080h
```

and indexes through each 128-byte sequential-read record.

The BetterCP/M implementation may use another transient buffer if preferable, provided externally observable behavior is unchanged.

---

## 22. Reference sign-on string

The DRI source contains the unused string:

```text
FILE DUMP VERSION 1.4
```

but the normal execution path never prints it.

It therefore does **not** form part of DRI DUMP's normal user interface and shall not be reproduced as a BetterCP/M startup banner.

BetterCP/M version identification is instead supplied through:

```text
DUMP /VER
```

---

# BASELINE EXCLUSIONS

## 23. Features deliberately not present

The initial DRI-compatible DUMP does **not** provide:

- ASCII column;
- paging;
- starting offset;
- length limit;
- search;
- byte/string matching;
- multiple files;
- wildcard dumping;
- disk-sector dumping;
- memory dumping;
- output redirection options;
- selectable row width;
- decimal or octal display;
- 32-bit offsets;
- record-number annotations;
- editing;
- comparison;
- DU-qualified BetterCP/M user areas.

Those can be considered separately after the clone baseline is established.

---

# IMPLEMENTATION REQUIREMENTS

## 24. Language and tools

The BetterCP/M implementation shall be:

- Z80 assembly;
- assembled with ZSM4;
- written as native BetterCP/M source;
- behaviorally derived from the DRI reference, not transliterated mechanically from the 8080 source.

Use native Z80 instructions where they simplify or clarify the implementation without changing behavior.

---

## 25. BDOS interface

The DRI behavior maps naturally onto standard CP/M-compatible BDOS operations:

- Open File;
- Read Sequential;
- Console Status;
- Console Output / string output as appropriate.

BetterCP/M's CP/M-compatible BDOS interface should be used rather than direct BIOS file access.

This preserves portability across BetterCP/M platforms.

---

# QUALIFICATION

## 26. Required compatibility tests

The baseline should be qualified against at least the following cases:

1. **Empty file**
   - opens successfully;
   - prints no data rows;
   - exits normally.

2. **1-record file**
   - displays exactly 128 bytes;
   - offsets `0000` through `0070`.

3. **Multi-record file**
   - continuous addressing across record boundaries.

4. **Known byte pattern**
   - verifies uppercase two-digit hex conversion.

5. **Drive-qualified file**
   ```text
   DUMP B:TEST.BIN
   ```

6. **Missing file**
   - prints:
     ```text
     NO INPUT FILE PRESENT ON DISK
     ```

7. **Embedded `1Ah`**
   - byte is printed as:
     ```text
     1A
     ```
   - processing continues.

8. **Final-record padding**
   - entire successful final CP/M record is displayed.

9. **Keyboard abort**
   - any pending console character stops output at the next 16-byte line boundary.

10. **Pending break character**
    - confirm compatibility behavior that the status test does not consume it.

11. **Large file crossing 64 KiB**
    - offset wraps from:
      ```text
      FFF0
      ```
      to:
      ```text
      0000
      ```

12. **Direct CCP return**
    - termination does not require or cause an intentional warm boot.

13. **`/VER`**
    - prints the metadata-owned version/build and compact identification layout
      specified in Section 3, including its ASCII framing and indentation;
    - performs no file access;
    - requires no monitor provider or terminal escape sequences;
    - ordinary file dumping does not print this identification display.

---

# 27. Baseline compatibility contract

The initial BetterCP/M DUMP can therefore be summarized as:

```text
DUMP filename
```

> Read the named CP/M file sequentially and display every byte in uppercase hexadecimal, sixteen bytes per line, with a wrapping four-digit byte address at the left. At each line boundary, terminate if any console character is pending. Return directly to the CCP when EOF, interruption, or open failure occurs.


## Enhanced viewer proposal — settled review decisions

The proposed enhanced viewer remains under review; its other open design
questions do not change the implemented DRI-compatible baseline above.

- Retain Section 3's finalized implied-corner `/VER` display, with version and
  build supplied by utility metadata. The proposed viewer must not revert to
  the former single-line version presentation.
- DUMP shall parse its own command tail, identify the single filename independently
  of option order, and construct the file FCB before file access. Both
  `DUMP /BARE FILE.COM` and `DUMP FILE.COM /BARE` shall work; the first
  CCP-prepared default FCB must not be assumed to contain the filename.
  In `/BARE`, the constructed FCB shall retain ordinary CP/M filename and optional
  drive qualification in the caller's current user area; it shall not admit
  enhanced DU selectors. The sealed compatibility contract covers subsequent
  file reading, display, interruption and return behavior, while allowing this
  command-line option syntax. This is a DUMP responsibility, not a CCP change.
  This decision applies to the proposed enhanced version; the existing initial
  clone above still uses the default FCB until that version is implemented.
- A new interactive `F` search shall start at the first byte of the currently
  displayed page, inclusively. A match beginning at that byte or elsewhere on
  the visible page is eligible. It shall not implicitly restart at file offset
  zero; the user may first use `G` to position at zero when intending to search
  from the beginning. This settles the initial Find origin only; continuation
  anchoring and other search rules remain separate design decisions.
- Overlapping matches shall be reported. Next occurrence shall search from one
  byte after the previous match's starting offset, not after the end of its
  pattern. For example, searching `ABA` in `ABABA` finds matches at offsets
  zero and two.
- Paging and successful Go To retain the active search pattern but reset its
  continuation anchor to the new displayed page's first byte. After such
  repositioning, next occurrence searches forward from that byte, inclusively;
  previous occurrence searches for the nearest match starting strictly before
  that byte. Without intervening repositioning, next/previous occurrence search
  for a match starting strictly after/before the last successful match's start,
  respectively, so overlapping matches remain eligible. A failed boundary or
  invalid Go To that does not reposition the viewer does not reset this anchor.
- Search shall not wrap automatically. Next occurrence stops at EOF; previous
  occurrence stops at the beginning of the file. If no further match exists in
  the requested direction, display `No further matches` and leave the displayed
  page unchanged. Do not silently restart at the opposite end of the file.
- ESC (`1Bh`) shall cancel either interactive Find prompt (pattern entry or
  Hex/ASCII selection) or an in-progress search. Cancellation returns to the
  previously displayed page without replacing the previous active search
  pattern or its continuation state. A new Find request remains provisional
  while it is being entered or searched, so cancellation can restore that
  prior state. Ctrl-C remains Page Down during normal viewer navigation; this
  decision does not introduce a Ctrl-G cancellation alias.
- The maximum search pattern is 32 decoded bytes: up to 32 ASCII characters
  or 64 hexadecimal digits, with optional spaces between hexadecimal byte
  pairs. The limit applies to decoded bytes, not the length of a spaced hex
  entry. Overlong patterns shall receive a clear diagnostic and permit re-entry;
  they shall never be silently truncated or searched as a shorter pattern.
- If a valid new Find completes without a match, display `Pattern not found`
  and leave the page unchanged. The new pattern becomes active, replacing the
  previous pattern, so the user may reposition and continue searching for it
  with `.` or `,`. Since no match has been established, continuation uses the
  displayed page's first byte as its anchor (forward inclusive, backward
  strictly before). This completed no-match outcome is distinct from ESC
  cancellation, which preserves the previous pattern and continuation state.
- Enter with no pattern text cancels Find without an error or a search,
  preserving the previous page, pattern and continuation state. No Hex/ASCII
  prompt is needed for a zero-character entry. If Hex is selected for an entry
  containing only spaces, treat it as empty and cancel in the same way. ASCII
  spaces are meaningful data and shall not be trimmed: a nonempty all-space
  entry selected as ASCII is a valid pattern, subject to the 32-byte limit.
- ASCII Find shall match exact bytes, preserving the case entered at the
  interactive prompt. `Hello` matches `Hello`, not `HELLO` or `hello`; no case
  folding or text normalization is performed. Hex Find also matches exact
  decoded bytes (hexadecimal digit case affects notation only). No case-
  insensitive search option is included in the initial enhanced design.
- On each successful Find or next/previous occurrence, place the display row
  containing the match's first byte at the top of the data area and show the
  exact starting offset in the status area, for example `Match at 00001237`.
  Row alignment must not round the reported match offset. The numeric offset
  identifies the match without requiring highlighting, reverse video or other
  terminal-specific rendition. Status offsets use the enhanced mode's fixed
  eight-digit hexadecimal format.
- Enhanced-mode offsets shall use exactly eight uppercase hexadecimal digits
  with leading zeroes in data rows, Go To position displays and match/status
  messages, for example `00001237`. They shall not wrap at 64 KiB. Position
  input may use fewer digits; the accepted numeric syntax is specified
  separately. `/BARE` retains four-digit offsets wrapping modulo 65536.
- `/FROM=` and interactive `G` shall accept one to eight hexadecimal digits,
  optionally followed by `H` or `h`. Hexadecimal digits are case-insensitive:
  `1237`, `1237H` and `00ff` are valid examples. Input is always hexadecimal,
  never implicitly decimal. Signs, missing digits, invalid characters and
  numeric overflow shall be rejected rather than truncated or wrapped. A
  syntactically valid number must also pass the supported file-position and
  file-length bounds checks before repositioning.
- Positions must identify an existing byte: for nonempty files the valid
  interval is zero through file length minus one. An offset exactly at EOF
  is out of range. Out-of-range `/FROM=` shall report a clear diagnostic and
  exit without dumping file data. Out-of-range interactive `G` shall report
  a clear diagnostic and retain the page, active pattern and continuation
  state unchanged. Empty-file behavior is a separate explicit case below;
  no out-of-range position shall wrap or be silently clamped.
- Defer command-line `/FIND=` from the initial enhanced viewer. Interactive `F`
  remains the intended search interface in that proposal. Revisit command-line
  search when a concrete invocation or SUBMIT workflow justifies it, including
  what should be displayed or returned for a match, no match or error and whether
  the operation should be interactive. The present CCP uppercases command-tail
  text, including quoted text, so case-sensitive command-line ASCII search must
  not be promised without a separately resolved input contract. No CCP change
  or command-line search implementation is authorized by this decision.
