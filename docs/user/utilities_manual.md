# BetterCP/M Utilities Manual

This manual explains how to use the programs supplied on the BetterCP/M Utilities Disk. For the command prompt, drive and user areas, file management, configuration, and the System Disk commands, see the [BetterCP/M User’s Guide](users_guide.md).

The Utilities Disk is being assembled separately from the System Disk. This manual currently covers the completed DUMP utility. Chapters for other utilities will be added as those programs are completed and selected for distribution.

## Contents

- [Using the Utilities Disk](#using-the-utilities-disk)
- [DUMP hexadecimal file viewer](#dump-hexadecimal-file-viewer)
  - [Quick start](#quick-start)
  - [Command syntax and options](#command-syntax-and-options)
  - [Reading the display](#reading-the-display)
  - [Starting at a particular position](#starting-at-a-particular-position)
  - [Preparing the paged viewer](#preparing-the-paged-viewer)
  - [Moving through the file](#moving-through-the-file)
  - [Finding bytes or text](#finding-bytes-or-text)
  - [Editing an input prompt](#editing-an-input-prompt)
  - [Original CP/M display](#original-cpm-display)
  - [Messages and recovery](#messages-and-recovery)

## Using the Utilities Disk

The daily emulator launch configuration mounts the Utilities Disk as drive B:. The examples below assume its programs are in user area zero. If your disk is mounted elsewhere, substitute its actual drive.

You can run a utility without changing your current drive or user area. For example:

```text
B0:DUMP A0:README.TXT
```

Here, `B0:` locates DUMP itself; `A0:` locates the file it will display. The file operand uses its own drive and user qualification independently of the program’s location. A filename without qualification refers to the caller’s current drive and user area.

In syntax descriptions, `file` and `offset` are placeholders to replace with your own values. `Ctrl-S` means hold Control while pressing S. Do not type the word “Ctrl” or the hyphen.

## DUMP hexadecimal file viewer

DUMP displays the bytes of one file in hexadecimal and readable ASCII. Use it to inspect binary programs, examine text control characters, or locate a particular byte sequence. DUMP reads the file without changing its contents or attributes. It does not disassemble instructions or edit files.

### Quick start

To display a file continuously:

```text
B0:DUMP A0:README.TXT
```

Press Ctrl-C to stop. To browse a page at a time, first load a suitable screen backend as described under [Preparing the paged viewer](#preparing-the-paged-viewer), then enter:

```text
B0:DUMP A0:README.TXT /P
```

Press Space for the next page, Ctrl-R for the previous page, F to find text or bytes, G to go to a position, and Q to quit.

### Command syntax and options

```text
DUMP file
DUMP file /P
DUMP file /40
DUMP file /FROM=offset
DUMP file /P /40 /FROM=offset
DUMP /BARE file
DUMP /VER
```

If DUMP is on B0: and is not otherwise found by your command environment, use `B0:DUMP` in place of `DUMP`.

| Option | Purpose |
| --- | --- |
| `/P` | Browse interactively with paging, Find, and Go To. Requires a loaded screen backend. |
| `/40` | Show eight bytes per row in a layout that fits a 40-column screen. |
| `/FROM=offset` | Begin at the row containing the specified hexadecimal byte position. |
| `/BARE` | Use the original CP/M hex-only display and interruption behavior. |
| `/VER` | Show DUMP’s version and build, then return. Use this option alone. |

Options may appear before or after the filename and are case-insensitive. `/P`, `/40`, and `/FROM=` may be combined. `/BARE` cannot be combined with them. Repeating a flag is harmless. If `/FROM=` occurs more than once, the last value selects the starting position, but every supplied value must be valid and within the file.

Supply exactly one filename. Enhanced modes accept a single drive/user-qualified name such as `B7:FILE.COM`. A drive-only name such as `B:FILE.COM` uses your current user area; an unqualified name uses your current drive and user. Wildcards, file selectors, multiple files, and multiple user areas are not accepted.

`/FIND=` and `/LEN=` are not available. Unknown options, missing operands, incompatible combinations, and invalid values produce a diagnostic and return to the command prompt.

`DUMP /VER` uses the standard BetterCP/M utility identification style:

```text
DUMP 1.0 (Build 002)
  - - -
 | BetterCP/M Utilities
 | Hexadecimal File Display
```

The build number changes with utility updates. Other DUMP commands do not display a sign-on banner.

### Reading the display

Normal output shows 16 bytes per row:

```text
00001230  00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  ................
```

The first eight digits give the hexadecimal position of the row’s first byte, measured from zero at the beginning of the file. Each pair of digits represents one byte. The final column shows the same bytes as ASCII characters. Printable characters, including spaces, appear directly; control characters and bytes outside printable ASCII appear as dots. A dot in that column can therefore represent either an actual period or a nonprintable byte; check the hexadecimal column to distinguish them.

The normal row occupies 76 columns. `/40` uses 37 columns and shows eight bytes per row:

```text
00001230  41424344 45464748  ABCDEFGH
```

Both layouts use eight-digit offsets, including for files larger than 64K. `/40` is selected when you run DUMP; it cannot be toggled while viewing.

CP/M stores files in 128-byte records. DUMP displays all bytes in those records, including padding after the useful text or data. The text end marker `1Ah` is displayed as an ordinary byte; it does not stop DUMP. No tabs, line endings, or embedded terminal controls are interpreted as display instructions.

Without `/P`, output continues to the end of the file. Ctrl-C stops this output and is consumed, so it does not remain waiting at the command prompt. Other keys do not stop enhanced streaming output. An empty file displays `Empty file` and returns, including when `/P` was requested.

### Starting at a particular position

`/FROM=` and the viewer’s G command take a hexadecimal byte position: one to eight digits, optionally followed by H. `1237`, `1237H`, and `00ff` are valid forms. A position is always hexadecimal, even when it contains only decimal digits.

```text
B0:DUMP A0:FILE.COM /FROM=1237H
```

This begins at offset `00001230` in the normal layout: DUMP rounds down to the row containing the requested byte. In `/40` mode it rounds down to a multiple of eight instead of sixteen.

The position must identify an existing byte. The position immediately after the file’s last byte is invalid, as is any explicit position in an empty file. An invalid `/FROM=` reports an error without displaying file data.

In the paged viewer, press G and enter a position. A successful Go To puts the containing row at the top. Press Enter on empty input or ESC to cancel without moving. Invalid input stays available for correction. To return to the beginning, press G, enter `0`, then press Enter.

### Preparing the paged viewer

`/P` needs a loaded screen backend. On Model 4 or trs80gp, the backend is M4SCRN:

```text
RSX LOAD M4SCRN
```

On cpmsim in a suitable ANSI host terminal, use ANSISCRN:

```text
RSX LOAD ANSISCRN
```

These examples assume the backend is available in your current command environment. Use its actual drive/user-qualified location if necessary. Check `RSX LIST` first; the supplied Model 4 startup normally loads M4SCRN already.

DUMP calls the screen backend directly. You do not need to select a particular ADM-3A, VT52, or ANSI personality for DUMP; an existing personality may remain loaded. Other applications may still require that personality. Loaded RSXs consume transient program memory until unloaded; see the User’s Guide for RSX management.

The backend must provide the required screen operations and report enough space: at least 76 columns for normal output or 37 for `/40`, with at least one data row and one bottom row. DUMP does not load a backend automatically, switch to `/40` automatically, or silently replace `/P` with continuous output.

Exactly one bottom row is shared by command hints, messages, and input prompts. All other rows display data. A 24-row screen therefore shows up to 23 data rows: 368 bytes in normal mode or 184 bytes with `/40`.

ANSISCRN supplies its documented 80-by-24 viewport; it does not automatically detect terminal resizing. Keep your host terminal large enough for that viewport. `/40` changes DUMP’s data layout, not the backend’s reported dimensions.

### Moving through the file

| Key | Action |
| --- | --- |
| Space or Ctrl-C | Next page, including while a search is active. |
| Ctrl-R | Previous page, including while a search is active. |
| `.` | Next page; next occurrence when a search is active. |
| `,` | Previous page; previous occurrence when a search is active. |
| F | Enter a new Find pattern. |
| G | Go to a hexadecimal byte position. |
| Q | Quit DUMP. |

Ctrl-C means “next page” only at the viewer’s navigation prompt. In continuous output it stops DUMP. Within text-entry prompts, use the editing controls described below.

A page movement uses the screen’s data capacity. Page Up near the beginning moves to offset zero even if less than a full page precedes the current display. At the beginning, further Page Up requests leave the page unchanged and show `Beginning of file` in the bottom row.

The last page stays visible. If it already includes the end of the file, Page Down shows `End of file` without moving or quitting. Boundary messages do not ring a bell or require acknowledgment. Unrecognized navigation keys are ignored.

### Finding bytes or text

Press F, enter the pattern, then choose H for hexadecimal bytes or A for ASCII text:

```text
Find: CD 05 00
Search as (H)ex or (A)SCII? H
```

For hex, `CD0500` and `CD 05 00` mean the same three bytes. Use complete byte pairs; spaces may separate pairs but cannot split a pair. For ASCII, type the text exactly as it occurs. Search is case-sensitive and preserves spaces: `Hello` differs from `HELLO`, and leading or trailing spaces are part of the pattern. To find control characters or binary bytes, choose hex.

A pattern may contain up to 32 bytes: 32 ASCII characters or 64 hex digits with optional spaces between byte pairs. The input line accepts at most 95 characters, enough for 32 hex bytes separated by single spaces. Additional insertion is refused with a message; existing text remains editable. Invalid hex or an overlong decoded pattern is diagnosed so you can re-enter it. An invalid H/A choice leaves the pattern available and asks again.

A new Find searches forward from the first byte of the current page, including that byte. It does not automatically start at the beginning of the file. To search the whole file, first use G to go to zero.

A successful search puts the row containing the match at the top and shows the exact byte position, for example `Match at 00001237`. The match position may be inside that row; highlighting the matching bytes is not provided.

After a Find, `.` searches for the next occurrence and `,` for the previous one. Matches may overlap: searching for `ABA` in `ABABA` finds offsets zero and two. Continuation starts strictly after or before the last match’s starting position, so it does not repeatedly return the same match.

Searches never wrap around. A new Find with no match shows `Pattern not found` and leaves the page unchanged, but the new pattern becomes active. A continuation reaching its boundary shows `No further matches` and preserves the page and search position. You can then search in the other direction.

Page movement or a successful Go To retains the pattern and establishes a new search starting position at the first byte of the displayed page. From there, `.` includes that byte in its forward search; `,` seeks the nearest match starting before it. Space, Ctrl-C, and Ctrl-R remain available for ordinary paging while the pattern is active. There is no separate clear-search command.

ESC cancels either Find prompt or a running search. Cancelling a new Find keeps the previous pattern, page, and search position. Empty Enter at the pattern prompt cancels. An all-space hex entry also cancels; an all-space ASCII pattern searches for those spaces.

### Editing an input prompt

Find and Go To share the bottom row with the command hints. While either prompt is active, use:

| Key | Action |
| --- | --- |
| Ctrl-S | Move left one character. |
| Ctrl-D | Move right one character. |
| Ctrl-G | Delete the character under the cursor. |
| Ctrl-H or Backspace | Delete the character before the cursor. |
| Enter | Submit the input. |
| ESC | Cancel. |

Typing inserts at the cursor. Long input scrolls horizontally within the bottom row without overwriting the file display. A reverse-video character marks the insertion point; at the end of the text, it appears as an underscore. Movement and deletion past either end leave the input unchanged. Ctrl-G deletes text; it is not a cancellation key.

On Model 4, CLEAR and Shift-CLEAR generate ESC. Control-CLEAR generates DEL, which is a different character. In trs80gp, Home supplies CLEAR; on a MacBook without a Home key, use Fn-Left Arrow to generate Home.

### Original CP/M display

Use `/BARE` for DRI-style hexadecimal-only output:

```text
B0:DUMP /BARE A:FILE.COM
```

```text
0000 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
0010 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
```

There is no ASCII column or command bar. The four-digit offsets wrap to zero after 64K. Every successful 128-byte record is displayed, including padding and `1Ah`.

Any pending key stops output at a row boundary. Unlike enhanced mode, `/BARE` does not consume that key: it remains available to the command environment. An empty file produces no data rows or empty-file message. A missing file reports `NO INPUT FILE PRESENT ON DISK`. A nonzero read result ends output without distinguishing EOF from a read error.

`/BARE` accepts an ordinary filename with optional drive qualification in your current user area. It rejects explicit user qualification such as `A0:FILE.COM`, as well as `/P`, `/40`, and `/FROM=`. The `B0:` prefix locating DUMP itself is independent of this operand restriction. You may put `/BARE` before or after the filename.

### Messages and recovery

Messages in the paged viewer occupy the bottom row, temporarily replacing the hints. Prompts use that same row. Messages remain until the next recognized command; the file display does not scroll to make room for them.

| Situation | What to do |
| --- | --- |
| Missing file | Check its spelling, drive, and user area. An unqualified operand refers to your current drive/user, not necessarily DUMP’s location. |
| Unknown or incompatible option | Correct the command. `/VER` must stand alone; `/BARE` cannot be combined with enhanced options. |
| Invalid position | Use a hexadecimal byte position within the file. In Go To, edit the retained input or cancel with ESC. |
| Missing screen support | Load the appropriate screen backend, or omit `/P` for continuous output. |
| Screen too narrow | Try `/40` if at least 37 columns are available; otherwise use a suitable display. |
| `Beginning of file` or `End of file` | The current page remains visible. Move in the other direction or press Q to quit. |
| `Pattern not found` or `No further matches` | Check the pattern and H/A interpretation, change direction, or use G to choose a new starting point. Search does not wrap. |
| `Read error at XXXXXXXX` | The offset identifies the failed read. A search was not completed; do not interpret this as “no match.” |

A later page-read failure keeps the last complete page and its search position. A search-read failure also preserves the previously committed pattern and position. If the first page cannot be read, DUMP reports the error and returns to the command prompt. Continuous output stops at a distinguishable read error and reports its position.

DUMP restores the caller’s drive and user area on its own normal, cancelled, and handled-error exits. Lower-level disk recovery prompts or system aborts may take control before DUMP can handle the failure. DUMP does not repair a damaged file or disk.
