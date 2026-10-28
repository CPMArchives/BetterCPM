# BetterCP/M Utilities Manual

This manual explains how to use the programs supplied on the BetterCP/M Utilities Disk. For the command prompt, drive and user areas, file management, configuration, and the System Disk commands, see the [BetterCP/M User’s Guide](users_guide.md).

The Utilities Disk is being assembled separately from the System Disk. This manual covers DUMP, the initial DDT debugger adaptation, the six standalone compression utilities SQ, USQ, CR, UNCR, LZH and UNLZH, TED, DASM with its DSYM/DLINK companions, and the original ZSM4/LINK development tools. Chapters for other utilities will be added as those programs are completed and selected for distribution.

CRCKSUM has a development implementation; CRCKSUM is included in newly built candidate Utilities images; the maintainer waived the remaining Model 4 validation for PR finalization; full Model 4 qualification and release acceptance are not asserted.

The COMPARE chapter describes a development utility. COMPARE is not yet qualified
or included in current Utilities Disk images. SEARCH 1.0 is included in newly
generated Utilities candidates and has passed paired-image acceptance on both BetterCP/M targets. Public release publication
remains separate.

MD5SUM has a development implementation in newly built Utilities candidates;
The maintainer has waived and deferred the remaining Model 4 validation; full Model 4 qualification and paired release acceptance are not asserted.

PATCH has an engineering specification and a prospective manual chapter. It is
not implemented or included in Utilities images; qualification remains pending.

## Contents

- [Using the Utilities Disk](#using-the-utilities-disk)
- [NOAH archive utility](#noah-archive-utility)
- [SEARCH file-content search](#search-file-content-search)
- [COMPARE binary file comparison](#compare-binary-file-comparison)
- [CRCKSUM file checksums and verification lists](#crcksum-file-checksums-and-verification-lists)
- [MD5SUM file digests and verification lists](#md5sum-file-digests-and-verification-lists)
- [PATCH verified binary file patching](#patch-verified-binary-file-patching)
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

- [DDT debugger](#ddt-debugger)
- [TED full-screen text editor](#ted-full-screen-text-editor)
  - [Starting TED](#starting-ted)
  - [Modes and screen keys](#ted-modes-and-screen-keys)
  - [Block and file sequences](#ted-block-and-file-sequences)
  - [Command mode, search and replacement](#ted-command-mode-search-and-replacement)
  - [Text preservation, saves and recovery](#ted-text-preservation-saves-and-recovery)
- [DASM Z80 disassembler and symbol tools](#dasm-z80-disassembler-and-symbol-tools)
  - [Starting DASM and logical bounds](#starting-dasm-and-setting-logical-bounds)
  - [Analysis and source output](#dasm-analysis-and-source-output)
  - [DLINK and DSYM](#dlink-checked-linking-and-dsym-conversion)
  - [A ZSM4/LINK round trip](#a-zsm4link-round-trip)
  - [Limits and recovery](#dasm-limits-and-recovery)
- [Compression utilities](#compression-utilities)
  - [Shared command rules](#shared-compression-command-rules)
  - [Version identification](#compression-version-identification)
  - [File handling and recovery](#compression-file-handling-and-recovery)
- [Native assembler and linker](#native-assembler-and-linker)

## Using the Utilities Disk

The daily emulator launch configuration mounts the Utilities Disk as drive B:. The examples below assume its programs are in user area zero. If your disk is mounted elsewhere, substitute its actual drive.

You can run a utility without changing your current drive or user area. For example:

```text
B0:DUMP A0:README.TXT
```

Here, `B0:` locates DUMP itself; `A0:` locates the file it will display. The file operand uses its own drive and user qualification independently of the program’s location. A filename without qualification refers to the caller’s current drive and user area.

In syntax descriptions, `file` and `offset` are placeholders to replace with your own values. `Ctrl-S` means hold Control while pressing S. Do not type the word “Ctrl” or the hyphen.

## SEARCH file-content search

**SEARCH 1.0 — included in newly generated Utilities candidates.** This chapter
describes the interface qualified on both paired emulator targets.
The [engineering specification](../engineering/SEARCH%20Specification.md)
controls the design.

SEARCH finds literal text and byte sequences in files without changing them.
Use DIR /WHEREIS when you want to locate filenames instead of searching contents.

### SEARCH syntax and options

```text
SEARCH [options] "pattern" filespec [options]
SEARCH "Error" A0:*.TXT /NOCASE /NOHEX
SEARCH "41 42" B[3-7]:*.COM /NOTEXT /P
SEARCH "4142" [A0,B[-],C[4,7-9]]:*.DAT
```

Put the quoted pattern first, followed by exactly one filespec. Put options before
the pattern or after the filespec. Quotes delimit the pattern; spaces and letter
case inside them are significant. Quoted `/VER` or `/HELP` is search data.
Options and filenames are case-insensitive. Repeating a flag has no extra effect.

| Option | Meaning |
| --- | --- |
| `/NOHEX` | Search only the literal TEXT interpretation. |
| `/NOTEXT` | Search only decoded HEX bytes; the pattern must be valid HEX. |
| `/NOCASE` | Ignore ASCII letter case in TEXT; HEX bytes remain exact. |
| `/P` | Pause result details one page at a time, moving forward only. |
| `/HELP` | Display help without searching; takes precedence over `/VER`. |
| `/VER` | Display utility identification without searching. |

By default SEARCH tries **both** interpretations independently. `"4142"` searches
for the four literal characters `4142` and for the two bytes `41h 42h` (`AB`).
`"41 42"` searches for those five literal characters and the same two decoded
bytes. HEX accepts contiguous pairs of hexadecimal digits or pairs separated by
spaces; hex digit case is insignificant. Odd digit counts, `0x` prefixes, `H`
suffixes, commas and incomplete byte pairs are not valid HEX. Invalid HEX is
silently ignored when TEXT is enabled: `"hello"` is an ordinary TEXT search.
With `/NOTEXT`, invalid HEX is an error. `/NOHEX /NOTEXT` is invalid.

TEXT is literal: no regular expressions, content wildcards or backslash escapes.
It is case-sensitive unless `/NOCASE` is supplied. `/NOCASE` folds ASCII letters
only, leaving high-bit bytes unchanged; it has no effect with `/NOTEXT`.
An empty pattern is invalid. Each enabled interpretation is limited to 64 decoded
bytes. The entire command tail, including quotes, filespec and options, must fit
within 127 bytes; consequently a 64-byte HEX pattern cannot fit on the command
line. SEARCH does not silently shorten a pattern.

The current CCP uppercases command tails, including quoted text. SEARCH cannot
recover original case lost before it starts. On that CCP, use `/NOCASE` for
ASCII text regardless of case, or `/NOTEXT` with HEX to specify exact bytes.
A double quote ends the pattern; no embedded-quote escape is provided. A TAB
inside quotes is literal pattern data; outside quotes it separates arguments.

### Selecting files for SEARCH

An unqualified filespec searches the caller's current drive and user area.
Filename `*` and `?` patterns use the shared CP/M 8.3 rules. Extended DU selectors
can select several locations:

```text
SEARCH "hello" B7:*.TXT /NOCASE
SEARCH "1A" B[-]:*.* /NOTEXT
SEARCH "Error" [A0,B[3-7],D[-]]:*.LOG /NOHEX
```

`B[-]` means all users 0–31 on B; `B[3-7]` means users 3 through 7 inclusive.
A bare drive inherits the caller's user, and a bare user inherits the caller's
drive. Compound terms inherit from the caller, never from the preceding term.
Overlapping selections do not repeat searches. Selected locations are visited
in drive order, then user order, with native directory order within each DU.
Unavailable locations are diagnosed; they are never silently mapped elsewhere.
Existing shared attribute-selection conventions apply. SEARCH does not adopt
WHEREIS's global scope or special default inclusion of system files.

### SEARCH results and totals

TEXT results identify the file, `[TEXT]`, and a one-based line number. An ordinary
matching line is shown once even if it contains several occurrences. The first
occurrence on a line chooses its excerpt. Lines of up to 64 bytes are shown in
full; longer lines use a window of at most 192 source bytes, looking back up to
64 bytes before that occurrence. `[...]` marks omitted edges. Other distant
occurrences on the same line still count, even when outside the chosen excerpt. SEARCH still
searches the whole line and counts every occurrence, including overlaps.
CR/LF is one line break; bare CR and bare LF also end lines. A final unterminated
line is valid. Control bytes are rendered visibly rather than sent to the console.

HEX results identify the file, `[HEX]`, and a zero-based byte offset printed as
eight hexadecimal digits. TEXT and HEX results are independent, including when
both interpretations match at the same position. For example, a file beginning
with `4142 AB 4142` followed by CR/LF yields:

```text
A0:NOTES.TXT [TEXT] line 1: 4142 AB 4142
A0:NOTES.TXT [HEX] offset 00000005
Files searched: 1
Files matched: 1
Text matches: 2
Hex matches: 1
Total matches: 3
```

All successfully read 128-byte CP/M records are searched in full, including final
padding and `1Ah`. `1Ah` does not end TEXT searching. Matches may span records,
extents or line endings. A TEXT match spanning a line ending belongs to the line
where it starts. No bytes beyond record EOF are invented.

The final summary always includes files searched, files matched, TEXT matches,
HEX matches and their sum, including zeros. Files searched includes successfully
opened empty and partially read files. A file with either kind of match counts
once in files matched. No matches is a normal result when coverage is complete.

### SEARCH paging and errors

At a `/P` prompt, Space or Enter advances one page. Ctrl-C suppresses subsequent
details and prompts, prints `DISPLAY INTERRUPTED` and `SEARCH CONTINUING...`,
and lets SEARCH finish every remaining selected file before printing totals.
It does not cancel the search. Error messages remain visible. The supported
console profile is 80 columns by 24 rows: output wraps explicitly at 79 columns,
with 23 content rows per page. No screen backend is required. There is no backward
paging. Ctrl-C during unpaged output also stops display while searching continues;
final totals remain available. Neither display-stop action cancels coverage.

Open, read and directory errors identify the affected location or file. SEARCH
continues elsewhere when safe and marks the final summary incomplete whenever
selected data could not be searched. Such totals describe observed data only;
zero matches after an error is not proof that all selected files lack the pattern.
Some platform disk-error paths prompt or warm boot without returning to SEARCH;
full recovery and final totals cannot be promised on those paths. Ctrl-C at an
OS `Bad Sector` prompt may warm boot; it is different from Ctrl-C at SEARCH's
own paging prompt. SEARCH needs an 8 KiB TPA budget on the qualified platforms.
Large directories can be slow because it replays directory searches after file
reads; a full 64-entry directory took about 23 seconds at an emulated 4 MHz.

SEARCH restores the caller's drive and user area on every handled exit. It does
not alter files or attributes, create temporary result files, search inside
archives, or replace text.

## COMPARE binary file comparison

**Development utility — qualification pending.** This chapter describes the
implemented interface. The [engineering specification](../engineering/COMPARE%20Specification.md)
records the approved design decisions and narrow display layout.

COMPARE compares exactly two files without changing either file, its directory
entry or its attributes. Use it to check a rebuilt program against a reference,
examine a patch, or verify a copied file. It compares binary bytes; use DIFF for
line-oriented text differences.

### Starting a comparison

```text
COMPARE OLD.COM NEW.COM
COMPARE /SIDE A0:OLD.COM B7:NEW.COM
COMPARE /SUMMARY OLD.COM NEW.COM
COMPARE /FROM=0205H /FROM2=0208H /LEN=0100H /SIDE A.BIN B.BIN
```

If the utility is on B0: and is not otherwise found by your command environment,
use `B0:COMPARE`. Options may precede, separate or follow the filenames; option
names are case-insensitive. Supply exactly two filenames. Each may have its own
drive and user qualification. Omitted drive or user selections inherit those
of the caller. Comparing a file with itself is allowed. Wildcards, drive/user
lists or ranges, and extra filenames are rejected.

### COMPARE options

| Option | Effect |
| --- | --- |
| `/LIST` | List individual differences; the default mode. |
| `/SIDE` | Display corresponding hexadecimal bytes side by side, eight per file per row. |
| `/SUM`, `/SUMMARY` | Show totals and the result without detailed output. |
| `/COUNT=n` | Limit the number of displayed `/LIST` entries; default 20. |
| `/ALL` | Display every differing position in `/LIST`. |
| `/FROM=hex[H]` | Start both files at this byte offset unless `/FROM2` overrides file 2. |
| `/FROM2=hex[H]` | Set file 2's starting offset independently. |
| `/LEN=hex[H]` | Examine at most this many comparison positions. |
| `/P` | Pause between pages in `/LIST` or `/SIDE`. |
| `/40` | Four compact bytes per file per row, with both offsets and the marker, in 38 columns. |
| `/VER` | Display the utility's version and revision without accessing files. |
| `/HELP` | Display command help without opening files. |

Choose one display mode. `/COUNT` and `/ALL` apply only to `/LIST` and cannot be
combined. `/P` cannot be combined with summary-only mode; `/40` requires `/SIDE`.
Repeated identical flags are harmless. Invalid combinations produce an error
before either file is opened. An exact `/VER` token takes precedence over other
arguments. Otherwise, an exact `/HELP` token shows help and ignores other
arguments without accessing files. `/VER` wins if both queries are present.

Offsets and `/LEN` values are hexadecimal, with one to eight digits and an
optional trailing `H`. Thus `/LEN=0100` means 256 positions. `/COUNT` accepts
decimal values from 1 through 65,535; zero and larger values are errors.
Use `/ALL` for unlimited listing. `/LEN=0` selects an empty range.

### Bytes, ranges and results

COMPARE includes every byte in each 128-byte CP/M logical record, including
final-record padding. `1Ah` is an ordinary byte. No line endings, tabs or high
bits are translated. File lengths are full logical-record lengths in decimal
bytes; display offsets are zero-based hexadecimal positions and can exceed 64K.

Without range options, the comparison starts at zero in both files and continues
until both reach EOF. `/FROM` sets both starting offsets; `/FROM2` overrides the
second independently, regardless of switch order. `/FROM2=0300` alone starts
file 1 at zero and file 2 at `0300H`. `/LEN` limits comparison positions, rather
than limiting each file to an absolute ending offset.

A byte against the same byte matches. Two unequal bytes count as a byte mismatch;
a byte against EOF counts as an additional byte in the file containing it.
These categories are reported separately. Starting beyond EOF is permitted.
When neither side has data left, comparison stops without inventing differences.

The final summary gives full file lengths, mismatch and additional-byte totals,
and the selected range when applicable. `FILES IDENTICAL` requires established
equality of the complete files. `SELECTED RANGES IDENTICAL` describes only the
chosen regions; differences elsewhere may still exist. Unequal full lengths
are reported separately. An empty selected range does not establish full-file
identity. Independently offset comparisons always report selected-range results.

### Reading comparison output

`/LIST` shows absolute offsets and unequal byte values. When starting offsets
differ, both offsets are shown. A missing byte is marked `---- EOF ----`.
The default limit of 20 entries, `/COUNT`, and `/ALL` control display only:
comparison continues and the final totals cover the complete selected range.

`/SIDE` shows matching rows as well as differing rows. A fixed `<>` marker
identifies rows containing any difference, including a byte against EOF.
Offsets use eight uppercase hexadecimal digits; bytes use two.

File 1 determines row boundaries. An unaligned start leaves leading byte slots
blank, and a partial final row leaves trailing slots blank. Corresponding bytes
in file 2 occupy the same horizontal slots, even if its offsets have different
alignment. Its row label is the conceptual address of slot zero, which may
precede the first byte actually shown. A negative conceptual row base appears
as `--------`; this is an alignment placeholder, not EOF. For example,
`/FROM=0007 /FROM2=0000` labels the first row `00000000` and `--------`.

When one file is exhausted and the other still has bytes, its first fully absent
row displays `---- EOF ----`; later exhausted rows may remain blank. Existing
bytes in a partial row remain visible, with unavailable slots left blank; no
EOF banner is overlaid on that row. In `/40`, the EOF label is shortened to `EOF`
and padded within the byte field.

`/40` removes spaces between the four byte values on each side. Two spaces
separate each offset from its byte field; the central marker occupies two
fixed columns. Data rows use 38 columns:

```text
00000004        54<>--------        20
00000008  47495441<>00000001  54414C20
```

### Paging and errors

`/P` provides forward-only pages using ordinary console output. On a 24-row
console it reserves the bottom row for the prompt, leaving 23 content rows.
Press Space or Enter for the next page. Ctrl-C at the prompt stops detailed
display and further prompts, but comparison continues silently:

```text
DISPLAY INTERRUPTED
COMPARISON CONTINUING...
```

The complete final summary is then printed. Q and Esc at the prompt have the
same display-stop behavior. There is no backward paging or screen redraw, and
no particular terminal personality or monitor is required.

During non-paged output, Ctrl-C cancels the operation cleanly and reports
`COMPARISON INCOMPLETE`. No completed-comparison result is printed; any partial
statistics are explicitly labelled incomplete.

A file-open error identifies the affected file. A read failure prevents a
completed comparison result; partial totals must not be treated as complete.
Handled exits close opened files and restore the caller's drive and user area.

## CRCKSUM file checksums and verification lists

**CRCKSUM 1.0 development candidate.** The implementation and focused cpmsim checks are available; CRCKSUM is included in newly built candidate Utilities images; the maintainer waived the remaining Model 4 validation for PR finalization; full Model 4 qualification and release acceptance are not asserted. This chapter does not claim that CRCKSUM.COM is present on released Utilities Disk images. The [engineering specification](../engineering/CRC-Specification.md) is the controlling design.

CRCKSUM answers two related questions: what check values identify these files, and do the files still agree with an earlier list? It calculates eight values: the original CP/M CRCK calculation, corrected CRCK, CHEK, CRC-32, SUM8, SUM16, KERM6 and KERM12. You can display them, save a list, or check a directory against a saved reference. No input file is altered.

### Getting started with CRCKSUM

```text
CRCKSUM
CRCKSUM B3:*.COM
CRCKSUM B[1,3,4-5]:*.COM
CRCKSUM A0:*.COM B3:*.TXT
CRCKSUM /CHECK B3:
CRCKSUM /CHECK B[1-3]:FILE.TXT
```

With no filespec, CRCKSUM selects `*.*` in your current logged drive/user area. A bare DU such as `B3:` also means `*.*`. Extended DU lists and ranges follow the common BetterCP/M rules. Separate filespecs may select different files in different locations. Overlapping selections do not process a physical file twice.

If CRCKSUM is on the Utilities Disk in B0: and your command environment does not find it automatically, use `B0:CRCKSUM`. The location of CRCKSUM.COM does not determine the locations of the files it checks.

### CRCKSUM options

```text
CRCKSUM [options] [filespec ...] [options]
```

| Option | Effect |
| --- | --- |
| `/CRCK` | Select the original historical CRCK calculation. |
| `/CRCK5` | Select corrected CRCK. |
| `/CHEK` | Select CHEK-compatible CRC. |
| `/CRC32` | Select CRC-32/ISO-HDLC, the common ZIP/Ethernet variant. |
| `/SUM8` | Calculate the unsigned byte sum modulo 256. |
| `/SUM16` | Calculate the unsigned byte sum modulo 65536. |
| `/KERM6` | Calculate the Kermit type-1 six-bit checksum applied to the whole file. |
| `/KERM12` | Calculate the Kermit type-2 twelve-bit checksum applied to the whole file. |
| `/FILE=filespec` | Write one master list. A single destination DU may be supplied. |
| `/LOCAL=filename` | Write an individual list in each selected DU. Supply a filename only. |
| `/LEGACY` | Write historical CRCKLIST records and force historical CRCK alone. |
| `/CHECK` | Verify against a reference discovered in each selected DU. |
| `/CHECK=filename` | Verify against this exact list name in each selected DU. Supply a filename only. |
| `/40` | Stack screen results for a 40-column display. Saved lists are unchanged. |
| `/HELP` | Display help without accessing files. |
| `/VER` | Display the utility's version and revision without accessing files. |

Option names are case-insensitive, and options may appear before, between or after filespecs. Without algorithm switches, calculation displays all eight values. Supplying switches selects their combination: `/CRCK /CHEK` displays those two. Explicit algorithm switches also determine output order: `/SUM16 /CRCK /KERM6` puts those three columns in that order. Repeating a switch neither moves nor duplicates its column. This order also applies to the narrow display and verification reports. When a value option is repeated, every occurrence must be valid and the last value is used. `/HELP` takes precedence over `/VER`; either query suppresses ordinary command processing.

`/LEGACY` always selects historical CRCK only. All other algorithm switches are ignored when `/LEGACY` is present, regardless of their order. You do not have to add `/CRCK` as well.

Calculation/list generation and verification are separate operations. Do not combine `/CHECK` with `/FILE=` or `/LOCAL=`. `/FILE=` and `/LOCAL=` may be used together.

### Which calculation to use

Names caused some confusion even during the CP/M years. SIG/M's CRC utility version 5.0 continued to calculate the original CRCK value. The separately developed corrected CRCK 5.x calculation produces different answers. `/CRCK5` selects that corrected calculation; it does not mean a five-bit CRC.

Use `/CRCK` for original SIG/M catalog and CRCKLIST values. CHEK is another 16-bit CRC calculation, also found in the CP/M library and RCPM tools. CRC-32 gives a 32-bit result. None of these values authenticates a file or establishes that it came from a trusted author; they are file-integrity checks.

SUM8 adds the stored bytes modulo 256; SUM16 adds them modulo 65536. KERM6
and KERM12 use Kermit's six-bit and twelve-bit checksum arithmetic across the
whole file. KERM6 folds bits 6 and 7 of the sum into its low six bits; KERM12
retains the low twelve bits. Results are numeric hexadecimal, not Kermit's
printable packet encoding. No packet headers or data quoting are included.
These values therefore do not represent an individual transfer packet's check.

In the default layout, the four new fields follow CRC32 in the order SUM8, SUM16, KERM6, KERM12.
They contain two, four, two and three hex digits respectively, right-aligned
within fields wide enough for their headings. All eight algorithms are selected
by default; for example, `CRCKSUM B3:*.COM /SUM8 /KERM12` displays just those two.
`/LEGACY` continues to force only historical CRCK.

CRCKSUM includes every byte of each 128-byte CP/M logical record. Embedded Ctrl-Z bytes and padding at the end of the final record are included. Text line endings are not converted. `RECS` is the exact record count; multiply by 128 to obtain the byte count being checked. A host copy with stripped padding or translated line endings may therefore produce a different result.

### Reading the CRC display and native lists

With all algorithms selected, the display and saved list use this layout
(the example is `123456789` padded with 119 Ctrl-Z bytes):

```text
; BetterCP/M CRC list
NAME     EXT  RECS  CRCK  CRCK5  CHEK  CRC32     SUM8  SUM16  KERM6  KERM12
-------- ---  ----  ----  -----  ----  --------  ----  -----  -----  ------
TEST     DAT     1  A687   5D45  E447  2F263492    F3   0DF3     36     DF3
```

The normal display uses a table like the native saved format. With `/CRCK /CRCK5 /CHEK /CRC32`, these two rows use actual values from SIG/M Volume 310:

```text
; BetterCP/M CRC list
NAME     EXT  RECS  CRCK  CRCK5  CHEK  CRC32
-------- ---  ----  ----  -----  ----  --------
ZMD146   LBR  1418  136B   A548  D24B  82A2F154
ZMDOVL2  LBR   372  B06D   6B36  C153  DE35205C
```

The name and extension occupy separate fixed fields with no dot. An extensionless file leaves EXT blank. Decimal record counts and hexadecimal values are right-aligned to their dash fields. Only selected algorithms appear. The RECS column grows when necessary, with a new consistent layout for that DU section.

The column header identifies the calculations; the dash runs establish their positions. CRC reads data by columns, so an empty extension cannot be confused with a record count. Keep the header, separator and rows aligned if editing a list. The reader accepts algorithm columns in any order, blank lines, comments beginning with `;`, and repeated section headers. Unknown or duplicate columns, missing values and malformed records are reported rather than guessed.

`/40` puts the filename on one line and the record count and each selected value on separate lines. It changes screen presentation only. Saved lists retain the standard table, and `/LEGACY` retains its historical file layout.

### Saving master and local lists

```text
CRCKSUM B3:*.COM /FILE=A0:MASTER.LST
CRCKSUM B[1-3]: /LOCAL=CRC.LST
CRCKSUM B[1-3]: /FILE=A0:MASTER.LST /LOCAL=CRC.LST
CRCKSUM B3:*.COM /CRCK /CHEK /LOCAL=CRC.LST
```

The first command saves one master list in A0:. The second writes CRC.LST in each of B1, B2 and B3. The third does both in the same run, reading each input file once. The fourth writes only historical CRCK and CHEK values.

Each DU is handled as a section. Files are alphabetized by name, then extension. Separate filespec operands establish first-encounter DU order; a bracketed selector follows the common canonical drive/user order. A master is the concatenation of the individual sections, with a blank line between them. Each section repeats its header and separator.

Saved sections do not record DU locations. Files with the same name in different DUs remain separate records. This makes local lists easy to move with their files, but a master list does not remember where each section originally lived. Keep that in mind when combining unrelated versions of the same filename.

An unqualified `/FILE=` destination uses the DU you were logged into when CRCKSUM started. `/LOCAL=` takes only a filename because the destination is each target DU. A DU qualifier on `/LOCAL=` is an error and stops the command before files are processed. For example, use `/LOCAL=CRC.LST`, not `/LOCAL=A0:CRC.LST`.

Output lists and temporary files are excluded from input selection. If master and local destinations name the same physical file, CRCKSUM writes that file once with the complete master contents; it does not attempt to keep a second local-only version under the same name.

If a destination exists, CRCKSUM displays its full identity:

```text
B3:CRC.LST exists. Overwrite? (Y/n/a/?)
```

Type `?` for `Y Yes, N No, A All, ? Help`; the same file's question is
then repeated. Help changes no files or choices. Enter still means Yes.

Y or Enter replaces that list. N leaves it alone and continues other requested outputs. A authorizes this and subsequent list replacements for this run. Ctrl-C cancels. CRCKSUM stages output before replacing a completed list. A failed or cancelled operation does not deliberately install a partial list under the final name; any recovery failure identifies the files left behind. Check the final output totals to see which lists were completed, declined or failed.

### Writing a historical CRCKLIST

```text
CRCKSUM B3:*.* /FILE=CRCKLIST.CRC /LEGACY
CRCKSUM B[1-3]: /LOCAL=CRCKLIST.CRC /LEGACY
```

`/LEGACY` uses the historical layout for both console output and saved lists. It reproduces the original prefix, padded dotted filename, two TABs before `CRC =`, space-separated hexadecimal bytes and blank lines between entries:

```text
--> FILE:  ZMD146  .LBR          CRC = 13 6B

--> FILE:  ZMDOVL2 .LBR          CRC = B0 6D
```

TABs are expanded here for reading. Native headers, sizes and the other algorithms are omitted. CRC 5.0 and CRC 6.4 historical readers require the `--> FILE:  ` prefix; `/LEGACY` supplies it. Native output is single-spaced; legacy output deliberately remains double-spaced.

### Checking files against their local list

```text
CRCKSUM /CHECK
CRCKSUM /CHECK B3:FILE.TXT
CRCKSUM /CHECK B[1-3]:*.COM
CRCKSUM /CHECK=REFERENCE.LST B[1-3]:
CRCKSUM /CHECK B3: /CRCK /CRC32
```

Every selected file is checked against one reference list in its own DU. The final example limits verification to recorded CRCK and CRC32 values. CRCKSUM does not fabricate values missing from a list: an entry containing neither selected algorithm is skipped and reported as such.

Bare `/CHECK` tries these names in order, independently in each target DU:

1. `CRC.LST`
2. `CRCKLIST.*`
3. `CRCKFILE.*`
4. `-CATALOG.*`

The first tier containing a candidate wins. If that tier contains several files, CRCKSUM reports ambiguity and asks you to select a name using `/CHECK=filename`. If none is found, it reports `No CRC list found` and continues to the next selected DU. It never searches your logged DU as a fallback. With no target operand, the logged DU is itself the target.

`/CHECK=REFERENCE.LST` means REFERENCE.LST in each target DU. It does not mean a single central reference for every target. A DU qualifier on `/CHECK=` is an explicit error and aborts the command before processing. To check a moved collection, place its reference beside its files and select that DU.

CRCKSUM displays the reference it selected. Once selected, a bad format, malformed list, absent checksum information or mismatch does not cause CRCKSUM to try a different reference. A catalog without checksum entries is not a usable reference. To use another file, name it explicitly.

CRCKSUM recognizes its native tables, historical CRCKLIST/CRCKFILE records, and original SIG/M catalogs containing CRC columns. Historical `CRC =` fields and original SIG/M catalog CRCs mean historical CRCK. Some early SIG/M catalogs contain only descriptions: their separate CRCKLIST or CRCKFILE is the verification reference. Reading a historical list does not require `/LEGACY`.

### Sizes, repeated names and verification results

Size is checked first where available. Native RECS is exact. SIG/M whole-K sizes are rounded: a 3K entry permits 17 through 24 records, rather than requiring exactly 24. An incompatible size rejects that entry. A compatible size, or a list without sizes, always proceeds to checksum comparison.

A master can contain several entries for the same filename. CRCKSUM compares the target file with the size-compatible candidates. A file matches only if every selected value actually recorded in one candidate agrees. It never combines values from different entries to manufacture a match. A complete matching candidate verifies the file; differing alternatives are identified separately. The report identifies which algorithms were actually checked.

Wildcard checking reports both selected files absent from the reference and selected reference entries whose files are missing. The reference file itself is excluded from wildcard targets. Files outside your requested pattern do not count as failures.

Expect separate reports for:

- **MATCH:** one complete applicable reference entry agrees.
- **SIZE MISMATCH / CHECKSUM MISMATCH:** the reference does not agree with the actual file.
- **FILE NOT FOUND:** a selected reference entry names an absent file.
- **FILE NOT LISTED:** a selected existing file has no reference entry.
- **SKIPPED:** no selected algorithm is recorded for the applicable entry.
- **READ ERROR / LIST ERROR:** verification could not be completed reliably.

One compact final summary covers all selected DUs. For example:

```text
1 file calculated; 1 list written.
12 verified; 1 failed; 2 missing; incomplete.
```

Zero counters are omitted. File-specific errors remain beside the affected file. A successful check ends with a summary such as `1 verified.` A check with no verified files reports `No files verified; incomplete.` (with any nonzero error counts included). Cancellation ends with `; cancelled.` Individual matches can still appear when another file or malformed entry makes the overall job incomplete. No per-DU counter block or duplicate total follows the checksum rows.

Ctrl-C cancels and reports an incomplete operation. Completed independent output lists remain, but uncommitted output is discarded. CRCKSUM restores your original drive/user selection before returning.

## MD5SUM file digests and verification lists

**MD5SUM 1.0 development candidate.** MD5SUM is included in newly built candidate Utilities images. Focused native-build and cpmsim checks pass; the maintainer has waived and deferred the remaining Model 4 validation; full Model 4 qualification and paired release acceptance are not asserted. This is not a released-disk qualification claim. The [engineering specification](../engineering/MD5SUM-Specification.md) controls the design.

MD5SUM calculates one MD5 digest for each selected file. Save the results, and you can later check whether the files still agree with that list. Its selection, master/local output, overwrite and checking behavior follows CRCKSUM. There is only one algorithm and one saved-list format.

### Getting started with MD5SUM

```text
MD5SUM
MD5SUM B3:*.COM
MD5SUM B[1,3,4-5]:*.COM C7:*.TXT
MD5SUM B3: /LOCAL=MD5SUM.LST
MD5SUM /CHECK B3:
MD5SUM /CHECK B[1-3]:FILE.TXT
```

Without a filespec, MD5SUM selects `*.*` in your current logged DU. A bare DU also means all files there. Overlapping selections do not hash the same physical file twice. Separate operands establish first-encounter DU order; bracketed selectors follow the common canonical DU order. Files within a DU are alphabetized by name and extension.

If your command environment does not find the executable automatically, give its location, for example `B0:MD5SUM`. That does not change the target DU.

### MD5SUM options

```text
MD5SUM [options] [filespec ...] [options]
```

| Option | Effect |
| --- | --- |
| `/FILE=filespec` | Write one master list; an explicit single destination DU is allowed. |
| `/LOCAL=filename` | Write a separate list in each target DU; supply a filename only. |
| `/CHECK` | Check against MD5SUM.LST in each target DU. |
| `/CHECK=filename` | Check against this exact list name in each target DU; supply a filename only. |
| `/40` | Fit console results and messages within 40 columns; saved lists are unchanged. |
| `/HELP` | Display help without file access. |
| `/VER` | Display the utility's identity without file access. |

Options are case-insensitive and may appear before, between or after filespecs. Repeated value options must all be valid; the last value is used. A later bare CHECK does not erase an explicit CHECK filename. HELP takes precedence over VER, and either query ignores ordinary operands and options.

FILE and LOCAL may be combined. CHECK is a separate operation and cannot be combined with either. There are no algorithm-selection switches or LEGACY mode.

### What the digest covers

MD5SUM includes every byte of every stored 128-byte logical record. Embedded Ctrl-Z, high-bit bytes and final-record padding all count. No text conversion takes place. Files larger than 64 KiB are processed as a stream.

A host MD5 program gives the same answer for exactly the same bytes. If a transfer strips CP/M padding or changes line endings, it changes the file being hashed. Keep the complete stored bytes when comparing a CP/M digest with a host digest. Accepting a text-mode entry in a list does not change this rule.

MD5 is useful for identifying files and detecting accidental changes. It does not establish authorship or protect against deliberately constructed collisions.

### Reading and saving the results

Normal calculation output and saved entries use conventional md5sum notation:

```text
b42a83d49df3489b2324811d5ed28d76 *TEST.DAT
```

This example is the digest of `123456789` followed by 119 Ctrl-Z bytes, one complete logical record. The digest has 32 lowercase hexadecimal digits. One space and an asterisk separate it from the filename. The star identifies binary input; it is not a wildcard. Names are uppercase, with an ordinary dot before the extension. Extensionless names have no trailing dot.

There are no table headings, record counts, DU addresses or blank lines between groups in saved lists. MD5SUM accepts both the starred form and the conventional two-space form:

```text
b42a83d49df3489b2324811d5ed28d76  TEST.DAT
```

Both forms check the same complete stored file. Uppercase digest letters and lowercase filename letters are accepted too. Lists may have CRLF or LF endings and blank lines. Tagged output such as `MD5 (TEST.DAT) = ...`, host paths, escaped filenames and other algorithms are not accepted; unsupported or malformed entries are reported, not guessed.

The console identifies the current DU and ends with a compact summary. Those messages are not saved in the list. Use FILE or LOCAL to make a list rather than capturing the entire console display. With `/40`, the console puts the filename on one line and the intact digest on the next. Saved entries keep their conventional single-line form.

### Master and local lists

```text
MD5SUM B3:*.COM /FILE=A0:MASTER.LST
MD5SUM B[1-3]: /LOCAL=MD5SUM.LST
MD5SUM B[1-3]: /FILE=A0:MASTER.LST /LOCAL=MD5SUM.LST
```

The first command writes one master in A0:. The second writes MD5SUM.LST separately in B1, B2 and B3. The third does both, reading each selected input only once. Without an explicit DU, FILE writes in the DU you were logged into when MD5SUM started.

A master is the uninterrupted concatenation of the local entry streams. It contains no group headers or source locations. Files sharing a name across DUs remain separate entries. A local list can move with its files; a master does not remember which original DU held a particular version.

LOCAL takes only a name because each target DU supplies its location. For example, use `/LOCAL=MD5SUM.LST`, not `/LOCAL=B3:MD5SUM.LST`. A DU qualifier is an error and stops the command before processing. Output lists and transaction files are excluded from input selection. If FILE and LOCAL resolve to the same physical file, it is written once with the complete master contents.

Before replacing a list, MD5SUM asks:

```text
B3:MD5SUM.LST exists. Overwrite? (Y/n/a/?)
```

Type `?` for `Y Yes, N No, A All, ? Help`; the same file's question is
then repeated. Help changes no files or choices. Enter still means Yes.

Y or Enter replaces this destination. N leaves it alone and continues other outputs. A authorizes this and later replacements in this run. Ctrl-C cancels. Output is staged before replacing a completed list. Handled failures or cancellation discard uncommitted output; recovery failures identify any files left behind. Completed independent local lists remain available even if another output fails.

### Checking against a local list

```text
MD5SUM /CHECK
MD5SUM /CHECK B3:FILE.TXT
MD5SUM /CHECK B[1-3]:*.COM
MD5SUM /CHECK=REF.LST B[1-3]:
```

Bare CHECK looks for MD5SUM.LST in each target DU. It does not search other names or fall back to your logged DU. If no list is found, MD5SUM reports it and continues to the next selected DU. With no target operand, your logged DU is itself the target.

CHECK=REF.LST selects that exact filename independently in each target DU. It does not select a central reference for all targets. A DU qualifier, such as `/CHECK=A0:REF.LST`, is an error. Place a reference beside the files it describes and select that location.

The target filespec limits both existing files and reference names being checked. MD5SUM reports selected files absent from the reference and selected reference names whose files are missing. The reference itself is excluded from wildcard targets. Unselected filenames do not become failures merely because they occur elsewhere in the list. A malformed list still prevents an overall successful check.

Conventional MD5 entries contain no file size, so there is no size-only preliminary comparison. MD5SUM calculates and compares the digest. If a master contains several digests for the same name, one matching entry verifies the file; differing alternatives are identified separately. No second list is consulted for precedence. You remain responsible for organizing unrelated files that share a name.

Expect MATCH, MD5 MISMATCH, FILE NOT FOUND, FILE NOT LISTED, READ ERROR or LIST ERROR reports as appropriate. One combined summary follows all DUs, for example:

```text
1 file calculated; 1 list written.
12 verified; 1 failed; 2 missing; incomplete.
```

Zero secondary counters and per-DU total blocks are omitted. A successful check can end simply with `1 verified.` A check verifying no files is incomplete; it is never proof that everything is correct. Ctrl-C reports cancellation, discards uncommitted output and restores your original drive/user selection.

### Exchanging lists with a host system

Export the target files without altering their stored bytes, and keep filename case consistent with the list. Saved CP/M lists may have trailing Ctrl-Z padding. If a host md5sum reader reports that padding as malformed input, remove only the trailing padding from the host copy of the list. Leave target-file padding intact: it contributes to the digest.

Some host readers require LF line endings or the two-space entry form. Convert those list details on the host if needed; target-file bytes must stay unchanged.

The common entry syntax permits exchange of these lists. MD5SUM does not reproduce every host command-line option or support host directory paths inside entries.

## PATCH verified binary file patching

**PATCH 1.0 — specified; implementation and qualification pending.** PATCH is
not yet included in Utilities images. This chapter describes the intended
interface, controlled by the [engineering specification](../engineering/PATCH-Specification.md).
Its repository assessment identifies a few policy details to settle before
implementation; this chapter does not promise behavior for those cases.

PATCH applies verified byte replacements from a patch instruction file to a
binary input file, producing a separate output. The original input remains
unchanged. Every expected byte must agree with the original before PATCH creates
any output. The patched copy retains the input's length and is read back in full
before success is reported.

### Running PATCH

```text
PATCH FIX.PAT
PATCH FIX.PAT /INPUT=B3:PROGRAM.COM /OUTPUT=D0:PROGRAM.NEW
PATCH FIX.PAT /VERBOSE
```

The patch file can name the input and output. `/INPUT=` and `/OUTPUT=` override
those names independently. Both names must be available from the patch file or
the command line; PATCH does not guess them.

```text
PATCH patchfile [ /INPUT=filespec ] [ /OUTPUT=filespec ] [ /VERBOSE ]
```

| Option | Effect |
| --- | --- |
| `/INPUT=filespec` | Select the original input, overriding the patch file's INPUT directive. |
| `/OUTPUT=filespec` | Select a separate patched output, overriding the OUTPUT directive. |
| `/VERBOSE` | Display instructions and validation results, continuing through independently identifiable mismatches. |
| `/HELP` | Display help without file access. |
| `/VER` | Display the utility identity without file access. |

Option names are case-insensitive. Unknown or malformed options, conflicting
duplicate options and missing values are errors. The patch file is the only
positional operand. Exact HELP or VER queries ignore other arguments, with HELP
taking precedence. `/VERBOSE` is an operational option, not a VER query.

Each filename must identify one ordinary CP/M file, optionally with a single
BetterCP/M drive/user qualifier. Wildcards, DU lists and ranges are not accepted.
Unqualified names, including names inside the patch file, refer to the drive/user
logged when PATCH started; they are not relative to the patch file's location.
The output must differ from both the input and the instruction file after DU
resolution. Alternate spellings of the same identity do not bypass this rule.

If needed, qualify the executable separately, for example
`B0:PATCH A3:FIX.PAT`. The executable's location does not change filename defaults.

### Writing a patch file

Use a plain text file, conventionally named with a `.PAT` extension:

```text
; BetterCP/M PATCH file
; Format: OFFSET: OLD -> NEW

INPUT  PROGRAM.COM
OUTPUT PROGRAM.NEW

0120: CD 05 00 C9 -> 00 00
0122: 00 C9       -> 3E 02
02A4: 3E 01 15    -> 3E 02
```

The bytes here illustrate the language; they are not a correction for an actual
program. Use expected and replacement bytes appropriate to the exact file version
you intend to patch.

`INPUT` and `OUTPUT` are optional if supplied on the command line. Each may occur
at most once in the file, even when a command-line override is supplied. Blank
lines are ignored. A semicolon begins a comment, including after an instruction.
The explanatory header is recommended but not required.

Offsets are hexadecimal byte positions measured from the start of the stored
file: offset `0000` is its first byte. A trailing `H` or `h` is optional. These
are file offsets, not DDT load addresses. For a COM file loaded at 0100h, debugger
address 0220h normally corresponds to file offset 0120h; check the actual file
layout when translating a patch notice.

OLD and NEW contain nonempty sequences of two-digit hexadecimal bytes separated
by spaces or tabs. Letter case does not matter. NEW may be shorter than OLD but
cannot be longer. Whitespace around the colon and ASCII arrow `->` is allowed.
Each physical line may contain at most 255 characters, excluding its line ending.
Longer or malformed lines are errors, not truncated instructions. There is no
arbitrary limit on the number of instructions; large patch files may require
additional disk passes.

### Verification context and overlapping ranges

In the first instruction above, PATCH verifies all four original bytes
`CD 05 00 C9`, then replaces only the first two with `00 00`. The trailing OLD
bytes provide context and remain unchanged by that instruction.

The next instruction verifies the original `00 C9` at offset 0122 and replaces
those two bytes with `3E 02`. Together the first two instructions change the four
bytes at 0120 to `00 00 3E 02`.

Every check uses the unmodified input, so instruction order does not change the
result. Verification ranges may overlap. Replacement ranges must not overlap,
even if they would write identical values. Each complete OLD range must fit
inside the input. PATCH rejects any mismatch, duplicate write, overlapping write
or out-of-range instruction before creating output.

### Existing output files

After validating the complete patch, PATCH asks before replacing an existing
output. The message identifies the resolved destination drive/user and filename:

```text
PATCH: D0:PROGRAM.NEW exists.
Overwrite? (y/N/r/?)
```

| Response | Effect |
| --- | --- |
| `Y` | Authorize replacement of this output. |
| `N` or Enter | Abort without changes. |
| `R` | Enter a different output filename, optionally with one DU qualifier. |
| `?` | Display `Y Yes, N No (abort), R Rename, ? Help`, then repeat the same file's prompt. |

Choices accept either case. The default is No. Other keys repeat the question
without authorizing a write. Repeated help changes no files or choices. A renamed
destination is checked again for identity conflicts and existence; another
collision produces the same question.

For an authorized overwrite, PATCH writes and fully verifies a temporary copy
on the destination DU before moving the old output to a backup name and
installing the new file. The backup is deleted only after installation succeeds.
Allow free disk space for the complete new copy while the old output still
exists. The input and patch instruction file are never used as temporary or
backup destinations.

If installation fails, PATCH attempts to restore the previous destination. If
restoration fails too, it retains the backup and reports its exact DU/name and
the staged file's state. If only backup deletion fails after successful
installation, PATCH reports success with a warning naming the retained backup.
Keep reported recovery files until you have checked the final state.

CP/M replacement is not atomic. Power loss can leave backup or temporary files,
and can temporarily leave the requested destination name absent. PATCH cannot
promise cleanup after power loss or a BDOS/BIOS error that never returns.

### Results and errors

PATCH preserves every stored 128-byte logical record, including Ctrl-Z bytes,
high-bit bytes and apparent padding. It never treats the binary input as text,
inserts bytes or shortens the output. Files and offsets beyond 64 KiB are
supported within the implementation's documented addressing limits.

After writing and closing the output, PATCH rereads and compares every byte
against the expected patched copy, including untouched regions. This is mandatory;
there is no NOVERIFY option. A successful summary identifies the input and output,
instruction count, byte totals, actual changed-byte count and full verification
status. Writing a replacement equal to the original does not count as an actual
byte change.

Normal mode stops at the first validation failure. VERBOSE shows individual
instructions and validation results and continues checking independent
mismatches where parsing remains reliable. Any validation failure prevents all
output creation in either mode. VERBOSE never authorizes a partially valid patch.

Diagnostics identify the patch filename and physical line where applicable,
and offsets and expected/found bytes when relevant. Read, write, close, readback,
space, rename and cleanup failures are reported distinctly. A handled failure
after output creation triggers cleanup where possible and explicitly identifies
files that could not be removed or restored. An incomplete output is never
reported as successfully patched.

### Historical patch notices

PATCH reads its native instruction language. It does not read DDT transcripts,
Digital Research notices, assembler source, Unix diff patches or DOS DEBUG
scripts directly. It does not patch system tracks or search for byte patterns.

Historical corrections may be distributed separately as verified native PAT
files, with the original notice and exact target version identified. Translating
and qualifying those files is separate from implementing PATCH.

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
DUMP file /LEN=count
DUMP file /FROM=offset /LEN=count
DUMP file /P /40 /FROM=offset
DUMP /BARE file
DUMP /VER
```

If DUMP is on B0: and is not otherwise found by your command environment, use `B0:DUMP` in place of `DUMP`.

| Option | Purpose |
| --- | --- |
| `/P` | Browse interactively with paging, Find, and Go To. Requires a loaded screen backend. |
| `/40` | Show eight bytes per row in a layout that fits a 40-column screen. |
| `/FROM=offset` | Begin displaying at the exact hexadecimal byte position; earlier columns are blank. |
| `/BARE` | Use the original CP/M hex-only display and interruption behavior. |
| `/LEN=count` | Display at most this many bytes, in hexadecimal; optional H/h suffix. |
| `/VER` | Show DUMP’s version and revision, then return. Other arguments are ignored. |

Options may appear before or after the filename and are case-insensitive. `/P`, `/40`, `/FROM=`, and `/LEN=` may be combined. `/BARE` cannot be combined with them. Repeating a flag is harmless. For `/FROM=` and `/LEN=`, the last value wins, but every occurrence must be valid. Every `/FROM=` must also identify a byte within the file.

Supply exactly one filename. Enhanced modes accept a single drive/user-qualified name such as `B7:FILE.COM`. A drive-only name such as `B:FILE.COM` uses your current user area; an unqualified name uses your current drive and user. Wildcards, file selectors, multiple files, and multiple user areas are not accepted.

`/FIND=` is not available. Unknown options, missing operands, incompatible combinations, and invalid values produce a diagnostic and return to the command prompt.

`DUMP /VER` uses the standard BetterCP/M utility identification style:

```text
DUMP 1.0 (006)
  - - -
 | BetterCP/M Utilities
 | Hexadecimal File Display
```

The revision number changes with executable updates. Other DUMP commands do not display a sign-on banner.

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

Without `/P`, output continues to the end of the file or the `/LEN=` limit. Ctrl-C stops this output and is consumed, so it does not remain waiting at the command prompt. Other keys do not stop enhanced streaming output. An empty file displays `Empty file` and returns, including when `/P` was requested.

### Starting at a particular position

`/FROM=` and the viewer’s G command take a hexadecimal byte position: one to eight digits, optionally followed by H. `1237`, `1237H`, and `00ff` are valid forms. A position is always hexadecimal, even when it contains only decimal digits.

```text
B0:DUMP A0:FILE.COM /FROM=1237H
```

This begins displaying byte `1237h`. The normal row address remains `00001230`; the first seven byte and ASCII positions are blank. `/40` also keeps aligned row addresses and columns, using multiples of eight. Bytes retain their usual columns.

The position must identify an existing byte. The position immediately after the file’s last byte is invalid, as is any explicit position in an empty file. An invalid `/FROM=` reports an error without displaying file data.

In the paged viewer, press G and enter a position. A successful Go To puts the containing row at the top. Press Enter on empty input or ESC to cancel without moving. Invalid input stays available for correction. To return to the beginning, press G, enter `0`, then press Enter.

### Limiting the displayed range

```text
B0:DUMP A0:FILE.COM /FROM=7 /LEN=AH
```

This displays ten bytes, offsets `7h` through `10h`. `/LEN=` is hexadecimal,
with one to eight digits and an optional H/h suffix, just like `/FROM=`. It counts
bytes, including CP/M record padding, rather than lines. Excluded positions in
both edge rows are blank in hex and ASCII. A count past EOF displays only the
remaining bytes; even a start-plus-count beyond `FFFFFFFFh` stops at EOF without
wrapping. `/LEN=0` displays no bytes and does not enter the viewer. It still checks
the file and any explicit `/FROM=`; empty-file handling is unchanged.

With `/P /LEN=`, the range stays fixed. Paging stops at its boundaries; the
existing `Beginning of file` and `End of file` messages refer to those boundaries.
Go To accepts only offsets within it and does not restart the count. Find searches
only this range, and the entire match must fit. The first included byte is the
search anchor when the row starts before the range.

Without `/LEN=`, `/FROM=` selects only the initial position. You can still page
back or Go To zero and search the whole file. Initial leading blanks disappear
after successful repositioning; Go To and Find retain their usual containing-row
display. A new Find starts at the first included byte of the current page.

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

`/BARE` accepts an ordinary filename with optional drive qualification in your current user area. It rejects explicit user qualification such as `A0:FILE.COM`, as well as `/P`, `/40`, `/FROM=`, and `/LEN=`. The `B0:` prefix locating DUMP itself is independent of this operand restriction. You may put `/BARE` before or after the filename.

### Messages and recovery

Messages in the paged viewer occupy the bottom row, temporarily replacing the hints. Prompts use that same row. Messages remain until the next recognized command; the file display does not scroll to make room for them.

| Situation | What to do |
| --- | --- |
| Missing file | Check its spelling, drive, and user area. An unqualified operand refers to your current drive/user, not necessarily DUMP’s location. |
| Unknown or incompatible option | Correct the command. `/VER` ignores other arguments; `/BARE` cannot be combined with enhanced options when no query is present. |
| Invalid position | Use a hexadecimal byte position within the file. In Go To, edit the retained input or cancel with ESC. |
| Missing screen support | Load the appropriate screen backend, or omit `/P` for continuous output. |
| Screen too narrow | Try `/40` if at least 37 columns are available; otherwise use a suitable display. |
| `Beginning of file` or `End of file` | The current page remains visible. Move in the other direction or press Q to quit. |
| `Pattern not found` or `No further matches` | Check the pattern and H/A interpretation, change direction, or use G to choose a new starting point. Search does not wrap. |
| `Read error at XXXXXXXX` | The offset identifies the failed read. A search was not completed; do not interpret this as “no match.” |

A later page-read failure keeps the last complete page and its search position. A search-read failure also preserves the previously committed pattern and position. If the first page cannot be read, DUMP reports the error and returns to the command prompt. Continuous output stops at a distinguishable read error and reports its position.

DUMP restores the caller’s drive and user area on its own normal, cancelled, and handled-error exits. Lower-level disk recovery prompts or system aborts may take control before DUMP can handle the failure. DUMP does not repair a damaged file or disk.


## DDT debugger

Run `B0:DDT` to inspect or enter an 8080 program, or `B0:DDT PROGRAM.COM` to load a program first. A HEX file is also accepted. `B0:DDT /VER` displays the BetterCP/M utility identity without starting the debugger. The initial adaptation is DDT 1.0 Build 001.

The debugger retains CP/M 2.2 DDT's command language. Addresses and numbers are hexadecimal. Commands execute when Enter is pressed.

| Command | Purpose |
| --- | --- |
| `Aaddress` | Enter 8080 assembly instructions; a dot ends entry. |
| `Dstart,end` | Display memory in hexadecimal and ASCII. |
| `Fstart,end,byte` | Fill an inclusive memory range. |
| `Gaddress,bp1,bp2` | Run with optional breakpoints. `G0` returns to CP/M. |
| `Hvalue,value` | Show hexadecimal sum and difference. |
| `Ifilename` then `R` | Select and read a COM or HEX input. |
| `Lstart,end` | List memory as 8080 instructions. |
| `Mstart,end,destination` | Move memory using DDT's existing forward-copy behavior. |
| `Saddress` | Substitute bytes; empty Enter advances, a dot finishes. |
| `Tcount` / `Ucount` | Trace or run a counted number of instructions without trace display. |
| `X` / `Xregister` | Examine machine state or replace a register/flag value. |

The usual omitted-operand and continuation forms remain available. This is an 8080 debugger: the program's use of Z80 code for editing does not add Z80 mnemonics to the debugger or extend its instruction-stepping model. Keep executable test programs and file copies separate from valuable work when modifying their memory.

Line input uses the shared editor with a 32-character limit. Ctrl-S/D move the cursor, Ctrl-A/F move by words, Ctrl-H or DEL erase left, and Ctrl-G erases under the cursor. Ctrl-U, Ctrl-X and Ctrl-Y clear the provisional line. Enter submits even an empty line. Unassigned control keys, including TAB, do not enter command text; type the original command's spaces or commas. Excess characters sound the bell and remain unaccepted until space is made.

Escape abandons the active interactive command and returns to the main `-` prompt. It does not undo earlier accepted assembly or substitution changes. Ctrl-C retains its historical warm-boot meaning. The original dot terminator remains available within assembly and substitution; it is not replaced by Escape. The existing address/register prefix stays visible while editing, with an underscore at end of input and a horizontally scrolling 24-cell field.

DDT relocates below the current BDOS gateway and reduces the debuggee's available memory. This build reserves 20 pages (5120 bytes), compared with the historical debugger's 16 pages. It does not require a loaded screen backend or a monitor personality. Its file is 6528 bytes. The exact 4864-byte historical reference is preserved as a separate engineering baseline and is not the Utilities Disk program.

BetterCP/M cpmsim command/input checks and Model 4/trs80gp screen/physical-keyboard checks pass. The Model 4 campaign verifies cursor editing, scrolling, CLEAR cancellation without committing an operand, A/L and G0/BREAK return on disposable current-system disks. DDT also passes release-placement checks from Utilities B: beside normal System A:, including Model 4 M4SCRN/ADM3A. For example, `B:DDT TINY.COM` loads the debuggee from your current A: drive and returns there after G0 or Ctrl-C. The Utilities images remain provisional pending acceptance of the other selected components.


## TED full-screen text editor

TED edits one text document using command, screen and browse modes. It retains
TED's editing behavior with an agreed subset of WordStar command sequences.
There is no undo, persistent block marking, WordStar document formatting or
Ctrl-Q command prefix. The on-disk guide is `TED.TXT`.

### Starting TED

TED requires an 80-by-24 screen backend and the ANSI terminal module. Before
starting it, use `RSX LIST` to check what is loaded:

| Target | Screen backend | Terminal module |
| --- | --- | --- |
| Model 4 / trs80gp | M4SCRN | ANSI |
| z80pack / cpmsim with an ANSI host terminal | ANSISCRN | ANSI |

Load the missing backend with `RSX LOAD M4SCRN` or `RSX LOAD ANSISCRN`.
Unload a conflicting terminal module, such as ADM3A, before `RSX LOAD ANSI`.
TED does not load these modules itself. Keep the module configuration fixed
while editing and keep the host terminal large enough for the 80-by-24 viewport.

```text
B0:TED A0:PROGRAM.MAC
B0:TED
B0:TED /HELP
B0:TED /VER
```

The first command reads an existing file; the second starts without a filename.
`/HELP` and `/VER` display usage or identification without opening a document.
File operands accept one exact 8.3 name, optionally qualified with drive A
through P and user 0 through 31, such as `A7:PROGRAM.MAC`. Wildcards are not
accepted. An explicitly supplied unqualified filename uses the drive/user from
which TED was launched, independently of the Utilities Disk's location.

### TED modes and screen keys

At `TED>`, enter `S` to start screen editing. Empty Ctrl-C also enters screen
mode; Ctrl-C following a command executes it and then enters screen mode.
Ctrl-Z returns from screen editing to command mode. Ctrl-B or Ctrl-N enters
browse mode; Return, Ctrl-C or Ctrl-Z returns from browse to screen editing.
Enter `EX` at `TED>` to leave TED. Discarding modified text requires an explicit
Yes; the default is No.

These bindings apply in **screen mode**:

| Key | Action |
| --- | --- |
| Ctrl-S / Ctrl-D | Left / right within the line. |
| Ctrl-E / Ctrl-X | Up / down. |
| Ctrl-R / Ctrl-C | Page up / down. |
| Ctrl-A / Ctrl-F | Previous / next word within the line. |
| Ctrl-T | Delete the range traversed by next-word movement. |
| Ctrl-H or Backspace | Backspace, with the mode-dependent behavior below. |
| Ctrl-G, DEL or Ctrl-] | Delete the character to the right; no effect at line end. |
| Ctrl-I or TAB | Insert a literal TAB. |
| Return | Split the line at the cursor. |
| Ctrl-J | Insert an empty line below. |
| Ctrl-P | Duplicate the current line. |
| Ctrl-Y or Ctrl-^ | Delete the current line. |
| Ctrl-V | Toggle insert/overwrite; TED starts in overwrite mode. |
| Ctrl-Q / Ctrl-O | Previous / next tab stop. |
| Ctrl-L | Toggle between line beginning and end. |
| Ctrl-U | Toggle between screen top and bottom. |
| Ctrl-B or Ctrl-N | Enter browse mode. |
| Ctrl-Z | Return to command mode. |
| Ctrl-_ | Redraw. |
| Ctrl-K | Begin a block/file command, listed below. |

Ctrl-W, Ctrl-@ and Ctrl-\ are unused. Escape cancels an active prefix or prompt.
The Model 4's raw arrow codes collide with TED control commands, including
insertion, deletion and the Ctrl-K prefix. Use Ctrl-E/X/S/D for navigation.
The current Model 4 console has no physical chord for Ctrl-underscore; that
ASCII redraw binding remains available where the console can supply it.

In overwrite mode, Backspace blanks the preceding character. In insert mode,
it removes that character and shifts following text left. At the start of a
line it joins the preceding line. Moving beyond a short line enters virtual
columns without adding spaces; typing there supplies the necessary spaces.
Tabs display to eight-column stops but remain TAB bytes in the file. Long lines
scroll horizontally. TED does not wrap words, indent automatically or trim
trailing spaces.

Word operations stop at line boundaries. Separators are space, TAB and
`. , : ; ! ?`; hyphens and underscores remain word characters. Word-right skips
the remainder of the current word and following separators; word-left scans
left over separators to the beginning of the preceding/current word.

### TED block and file sequences

Press Ctrl-K, release it, then the indicated letter. Upper/lowercase letters
and the corresponding Ctrl-letter are accepted. These sequences invoke TED's
existing whole-line operations and file argument prompts.

| Sequence | Action |
| --- | --- |
| Ctrl-K C | Copy: prompt for first/last source lines and the line to copy after. |
| Ctrl-K V | Move: prompt for first/last source lines and the line to move after. |
| Ctrl-K Y | Delete: prompt for first/last source lines. |
| Ctrl-K R | Read a file through TED's R argument prompt. |
| Ctrl-K W | Write through TED's W argument prompt, including ranges and append. |
| Ctrl-K S | Save to the default filename and continue editing. |
| Ctrl-K X | Save, then exit only after successful publication. |
| Ctrl-K Q | Quit, with default-No confirmation before discarding changes. |

Line ranges include both numbered endpoints. There are no block marks or
character-block selections. Ctrl-K replaces TED's former insert-above binding;
move up one line and use Ctrl-J where appropriate. Ctrl-K D is not assigned.
For an unnamed document, supply the required filename through the W prompt.

### TED command mode, search and replacement

Line numbers are decimal and one-based; position columns start at zero.
Enter these commands at `TED>`, without the prompt text:

| Example | Action |
| --- | --- |
| `P 10 5` | Position at line 10, visual column 5. |
| `S 10` | Position at line 10 and enter screen editing. |
| `/text/` | Find a forward, case-sensitive literal match within a line. |
| `/text/(1,20)+1` | Search lines 1..20, then move one line after the match. |
| `SU /old/new/` | Substitute matching text. |
| `SU M /old/new/` | Ask before each substitution. |
| `SU 3 /old/new/` | Replace up to three matches. |
| `M 2 4 8` | Copy lines 2..4 after line 8. |
| `MD 2 4 8` | Move lines 2..4 after line 8. |
| `D 2 4` | Delete lines 2..4. |
| `R (5) OTHER.TXT (2,4)` | Insert source lines 2..4 after document line 5. |
| `W 2 4 PART.TXT` | Write whole lines 2..4 to PART.TXT. |
| `W OTHER.TXT $` | Safely append to OTHER.TXT; `0` selects replacement. |
| `W` | Save the whole document to its default filename. |
| `F` / `FR` | Show the default filename / free memory above the static image. |
| `PR 2 4` | Print selected lines through the console. |
| `CL` / `EX` | Clear / exit, with an abandonment safeguard. |

Search does not wrap or cross line endings. Use `P 1` before searching from
the beginning. There is no repeat-find key. In confirmed substitution, Y
replaces, Return skips and Ctrl-C stops; an empty replacement deletes matches,
while an empty search is refused.

R inserts after the specified line, or appends to the document if that position
is omitted. It also selects the default filename. An alternate filename or
line-range W does not silently change that default or clear unsaved-document
state. Default W retains the full drive/user identity selected by the latest R.

Command-field editing differs from screen editing: Ctrl-E recalls the previous
command, Ctrl-G recalls and enters it, Ctrl-D recalls one byte, Ctrl-U or
Ctrl-^ clears the field, TAB supplies spaces, and Backspace/DEL deletes left.
Ctrl-Z submits EX with its normal abandonment safeguard. These are TED's
command-field facilities, not additional screen bindings.

### TED text preservation, saves and recovery

TED preserves literal tabs, trailing spaces, mixed CRLF/LF/CR line endings and
an absent final newline. An unchanged full-document write preserves physical
EOF padding too. Whole-line transfers add only the separators required at new
boundaries. Unsupported control/high-bit bytes, embedded EOF markers and lines
over 4,095 bytes are refused with line/offset diagnostics. Input is limited to
8,191 data records (1,048,448 bytes) and available disk space. Numeric line
operands remain bounded to 16 bits; the file-size limit does not remove that
command-language limit.

Saves write and verify a unique stage before replacement. The old target is
retained as `TEBnnnnn.BAK`; TED does not erase it to create the new file.
Replacement and read-only/system protection require explicit authorization.
Allow space for checkpoints, the output stage and retained backups. A failed
or cancelled save leaves TED active rather than treating the document as saved.

If saving fails, record the exact workspace, stage and backup names reported.
Keep those files until you have checked which copy is complete. Inspect an
ambiguous rename failure before retrying; do not delete the only complete copy.
Retained backups are yours to clean up after verification.

`WORK A0:` selects a workspace drive/user. `RECOVER A0:TEWnnnnn.$$$` validates
and copies a retained checkpoint after confirmation; replace the placeholder
with the actual name TED reported. The recovery source is retained. Recovery
restores the last committed checkpoint: the latest dirty line can still be
only in RAM. It is not autosave or undo. An older checkpoint may lack a newly
chosen filename, so specify a filename when saving recovered text. Normal exit
removes only a verified session-owned checkpoint; ambiguous stages/backups are
retained for inspection.

TED checks its active transient-memory ceiling before using its private stack.
Loaded extensions reduce available memory. Component qualification covers the
recorded normal RAM z80pack and Model 4/trs80gp configurations; physical hardware,
ROM/XIP and checked-profile application qualification are separate. See the
[TED qualification report](../engineering/TED%20Qualification.md) for exact
images and console limitations. Complete source and native-build material
accompany the host package in `BetterCPM-TED-SOURCE.tar.gz`; retain that companion
and `TEDCOPY.TXT` when redistributing.

## DASM Z80 disassembler and symbol tools

DASM is the maintained Richard Conn 1.5 Z80 disassembler adaptation. It inspects
loaded bytes, records symbols/comments and code/data classifications, saves
analysis and generates Zilog source for the supplied ZSM4/LINK tools. It does
not execute the input program. DSYM converts a verified final-address link
report into symbols DASM can import; DLINK captures that report using the
unchanged packaged LINK 1.3. The on-disk guide is `DASM.TXT`.

### Starting DASM and setting logical bounds

Keep Utilities on B: and work on a writable disk. Run `B0:DASM`, then use H for
the interactive command summary. `B0:DASM /HELP` and `B0:DASM /VER` display
usage or identification without creating files. DSYM and DLINK also accept
noncreating `/VER` queries. ZSM4 and LINK retain their original third-party
interfaces and versions; these queries have not been added to them.

At DASM's prompt, read an exact file with a command such as `RPROGRAM.COM`.
File operands support drives A..P and users 0..31, for example
`RA7:PROGRAM.COM`; unqualified operands use the caller's original drive/user.
DASM keeps at most 8,192 input bytes in memory and refuses an empty input.
It has no disk-backed analysis paging or full-64-KiB input residency.

CP/M records do not reveal the logical byte length of a program. After loading,
use `Nhex` to select its measured logical length; without N, every physical
record byte is input, including trailing `00h`, `1Ah` or `FFh`. Do not infer the
length by stripping those values: they can be real program data. DASM addresses,
lengths and range bounds are hexadecimal. `N5` means five logical bytes.

`Ohex` selects a logical origin, normally `0100h`. Range ends are exclusive;
an end-only bound may be `10000h`, but addresses cannot exceed `FFFFh` and an
interval cannot cross the address-space boundary. Thus `100,105` denotes five
bytes. Non-0100h origins generate PHASE/DEPHASE source: LINK still produces
packed bytes at 0100h, which must not be assumed runnable there.

### DASM analysis and source output

| Command | Purpose |
| --- | --- |
| `H` / `?` | Interactive help / statistics. |
| `Lstart,end` / `QLstart,end` | List instructions; quiet listing feeds staged source output without the normal console listing. |
| `Dstart,end` | Dump bytes in a bounded range. |
| `C` / `Caddress,type` | Inspect control classifications / set a classification listed below. |
| `A` / `B` | Inherited data recognition / automatic symbol generation. |
| `DS` | Inspect the symbol table. |
| `Eaddress,.NAME` / `K.NAME` | Add / delete a symbol. |
| `;address,text` | Add a printable comment; `;address,` deletes it and `;` lists comments. |
| `Iaddress,[+|-]delta` | Safely rebase symbols at/above an address. |
| `Sname.ASM` | Begin staged source output. |
| `Pstart,end` | Emit the source prologue and equates for the selected interval. |
| `Z` | Finish and publish the staged ASM output. |
| `G` | Return to CP/M. |

A control point selects how subsequent bytes are interpreted, up to the next
control point or the selected end:

| Type | Interpretation |
| --- | --- |
| B | Byte data, using quoted strings where appropriate. |
| E | End-of-program marker. |
| H | Byte data in hexadecimal. |
| I | Instructions. |
| S | Storage region; exact source output still retains its initialized bytes. |
| W | Word data. |

Bare/continuation forms of L, D and F retain DASM's existing workflow; use H
for their syntax. Classify embedded data and review symbols before generating
source. Successful assembly alone does not prove a faithful disassembly.

`R` and `S` with `.SYM`, `.CTL` and `.DOC` import/export symbols, controls and
comments individually. `Rname.DSY` imports DSYM's canonical output.
`Sname.ALL` saves a versioned, checksummed session descriptor and uniquely named
components; `Rname.ALL` validates the complete graph before replacing live
analysis. Loading a session requires the same binary drive/user/name and
matching logical bytes. Keep the descriptor and its referenced components
together; the descriptor alone is not the saved analysis.

### DLINK checked linking and DSYM conversion

```text
B0:DLINK PROGRAM
B0:DLINK RESULT ONE TWO
B0:DSYM PROGRAM.LOG
B0:DSYM A7:PROGRAM.LOG C7:
```

`DLINK base` links `base.REL`. With explicit modules, the first operand is the
output base and the remaining operands are input modules. The output base has
no extension; inputs may omit `.REL`. All modules and outputs must share the
output user area, although their drives may differ. Unqualified operands use
the caller's original drive/user. Outputs `base.COM`, `base.SYM` and `base.LOG`
must all be absent before starting.

DLINK loads only the verified packaged **B0:LINK.COM**. It provides a bounded
child workspace, captures the report in a unique `DLGnnnnn.$$$` stage and
publishes the LOG after checked orderly completion. It does not enable LINK's
legacy A disk-scratch option. Jobs needing more child workspace fail safely.
Inspect LINK diagnostics; COM/SYM files left by a failed job are unverified.
DLINK's `/VER` identifies the wrapper, not a new version of LINK.

`DSYM [DU:]base.LOG [destination-DU:]` writes a new `base.DSY`, using the
complete report's final addresses directly. It refuses an existing destination,
a bare `.SYM`, failed-link diagnostics, truncated reports and conflicting
symbols. Use a complete DLINK LOG: a plausible symbol file is not proof of a
successful link. The default public export significance is six characters;
DSYM cannot recover source spelling already lost by LINK. DASM interchange
names may contain up to 12 characters; DSYM permits 255 unique normalized
records, coalesces exact duplicates and preserves distinct aliases.

### A ZSM4/LINK round trip

For a **five-byte** PROGRAM.COM produced from PROGRAM.MAC, use this sequence
from the writable work drive. Change the length and exclusive end for your
actual program, and choose fresh output names:

```text
B0:ZSM4 PROGRAM=PROGRAM
B0:DLINK PROGRAM
B0:DSYM PROGRAM.LOG
B0:DASM
RPROGRAM.COM
N5
RPROGRAM.DSY
SREBUILD.ASM
P100,105
QL100,105
Z
G
B0:ZSM4 REBUILD=REBUILD.ASM
B0:LINK REBUILD[A]
```

Check `Errors: 0` and all LINK diagnostics. Compare every byte of the declared
logical interval against the original; check CP/M record padding separately.
A one-byte absolute image requires an explicit `1Ah` padding byte outside the
logical interval to work around LINK's one-byte-output behavior. Do not execute
arbitrary disassembly inputs or assume output for a different logical origin
is runnable at 0100h.

### DASM limits and recovery

DASM requires an active exclusive transient-memory ceiling of at least B200h
and always retains its fixed 8-KiB input limit. Resident extensions consume
headroom. DLINK gives its child a ceiling of A000h and needs room through
B810h for its own storage and margin; DSYM requires 2A92h. These limits refer
to active program memory, not the machine's total installed RAM.

ASM output remains staged until Z. Interrupting a listing invalidates pending
source output, so Z cannot publish it as complete. Ctrl-C offers confirmed
cancellation; on Model 4 use the BREAK key for ETX. An ordinary key stopping a
listing also invalidates the pending output. A declined Ctrl-C cancellation
does not make an interrupted listing complete.

Replacement retains a uniquely named backup. On errors, preserve the reported
`.$$$` stages and BAK copies until you have identified a complete file. A failed
session save can leave named `DSA00000.SYM`, `.DOC` and `.CTL` generation
components while the old descriptor graph remains usable. Do not delete files
referenced by the descriptor you intend to reload. CP/M renames do not provide
power-loss durability or atomic replacement of multiple files.

The [DASM qualification report](../engineering/DASM%20Qualification.md) records
normal RAM Model 4/trs80gp and z80pack component results and their exact media.
Physical hardware and whole-Utilities-release acceptance are separate. Original
imports, maintained source and build recipes accompany the images in
`BetterCPM-DASM-SOURCE.tar.gz`; retain that companion and `DASMCOPY.TXT` when
redistributing.

## Compression utilities

SQ/USQ, CR/UNCR and LZH/UNLZH compress and restore individual files. They are
separate commands for release 1.0. Each encoder keeps its input file and writes
a compressed file with the original name stored inside it. The matching decoder
restores that stored name. These commands do not create or browse multi-file
archives. Compression can make a file larger; no format is promised to be best
for every file.

| Command page | Purpose | Typical extension change |
| --- | --- | --- |
| [SQ](SQ.md) | Squeeze one file; two input passes | `TXT` -> `TQT` |
| [USQ](USQ.md) | Restore a squeezed file | Restores embedded name |
| [CR](CR.md) | Crunch one file; one input pass | `TXT` -> `TZT` |
| [UNCR](UNCR.md) | Restore supported CRUNCH 2.x files | Restores embedded name |
| [LZH](LZH.md) | Compress one file in CP/M CrLZH format; one input pass | `TXT` -> `TYT` |
| [UNLZH](UNLZH.md) | Restore old and new supported CP/M CrLZH files | Restores embedded name |

The extension is a naming convention. A decoder checks the contents; changing
an extension does not convert the format. UNLZH is for CP/M CrLZH, not general
LHA/`.LZH` archives. Select the decoder that matches the original format.

### Shared compression command rules

```text
SQ    [drive:]file [destination-drive:]
USQ   [drive:]file [destination-drive:]
CR    [drive:]file [destination-drive:]
UNCR  [drive:]file [destination-drive:]
LZH   [drive:]file [destination-drive:]
UNLZH [drive:]file [destination-drive:]
```

Square brackets mark optional parts; do not type them. Give one exact 8.3
filename, optionally with an A: through P: drive prefix. Source and destination
use your current user area. The destination is a drive only, such as `C:`;
you cannot supply a new output filename. Names and drive letters are
case-insensitive. Wildcards, paths, explicit user/DU operands such as
`A0:FILE.TXT`, quoted names, other switches and extra operands are not accepted.
Each command also accepts `/HELP` and `/VER` queries. There is no overwrite option.

With no source prefix, input comes from your logged drive. With no destination
operand, output also goes to your logged drive, independently of where the
source file or command program is located. Thus, while logged onto A:,
`UNLZH B:REPORT.TYT` restores the embedded name on A: in your current user area.

To locate the program itself on BetterCP/M's Utilities B0:, use, for example:

```text
B0:SQ A:REPORT.TXT B:
B0:USQ B:REPORT.TQT C:
```

The `B0:` before SQ/USQ locates the program; it is not a source-file operand.
The command's file operands still use ordinary drive-only syntax. On stock
CP/M 2.2, arrange for the COM program to be accessible by its normal command
lookup rules. Change to the desired user area before running a command.
No screen backend or terminal personality is required. A Z80 processor is required.

### Compression help

Use `SQ /HELP`, `USQ /HELP`, `CR /HELP`, `UNCR /HELP`, `LZH /HELP` or
`UNLZH /HELP` for a compact screen with purpose, syntax and the two query options.
A short corner groups the purpose and Usage line; the Options list is unframed.
Examples and detailed operating rules are provided in the command pages.
Help returns without accessing files. Queries ignore letter case and use spaces or TABs as separators. An exact `/HELP` token anywhere
shows help and ignores all other arguments, including `/VER`.
Longer tokens such as `/HELPER` remain syntax errors. Empty or malformed
commands show short syntax and a hint to use that command's `/HELP`.

### Compression version identification

Run `SQ /VER`, `USQ /VER`, `CR /VER`, `UNCR /VER`, `LZH /VER` or `UNLZH /VER`
to display that command's version and build without accessing files. Letter case
does not matter. For example:

```text
SQ 1.0 (Build 004)
  - - -
 | BetterCP/M Utilities
 | Squeeze File Compression
```

Each utility has its own build counter. The numbers come from BetterCP/M's
utility metadata; the individual command pages show the current identification.
An exact `/VER` token anywhere shows identification and ignores other
arguments. If `/HELP` is also present, help takes precedence in either order.
Ordinary compression and restoration
retain their existing output without a version banner.

### Compression file handling and recovery

All six commands leave the source file in place and refuse to replace an
existing output, including an output that would be the input itself. They use
a temporary file on the destination drive, verify processing, finish writing,
close the files and rename the temporary only after success. A decoder's
checksum failure does not publish a restored file. Allow enough free destination
space; the source remains present throughout the operation.

CP/M stores files as 128-byte records. Encoders preserve every input-record
byte, including existing padding and `1Ah` text-end characters. Restored partial
records are padded with `1Ah`; these commands cannot infer a host file's original
byte length within its last CP/M record. A round trip preserves CP/M record
contents. An empty source restores as an empty file. Files need not fit in RAM,
and extent changes and files over 64K are supported by the sequential file I/O.
Available program memory is still required; loaded extensions can reduce it.

Normal success prints `COMMAND: complete.` and returns to the prompt. These
commands do not display a progress indicator, percentage or compression ratio,
and do not ask permission to overwrite. SQ takes two passes: do not edit or
replace its source between them. Keep input stable for the other commands too.

| Message text after the command prefix | What to do |
| --- | --- |
| `Usage: ...` | Check the exact syntax, filename and drive-only destination. |
| `cannot open input.` | Check source spelling, drive and current user area. |
| `output exists; nothing replaced.` | Choose another destination drive or move/rename the existing output first. |
| `output would replace input.` | Use another destination drive; keep the compressed input. |
| `unsafe embedded filename.` | The stored name cannot safely be used as a plain 8.3 name. Changing the compressed filename does not fix its header. |
| `cannot create temporary output.` | Check destination availability, free space, write protection and directory capacity. |
| `input read failed.` | Check the source media; preserve the compressed/original input. |
| `output write failed.` or `file close failed.` | Check destination media and free space, then retry from the source. |
| `cannot finalize output.` | The final rename failed; resolve destination/media problems before retrying. |
| `checksum mismatch.` | The restored bytes failed the stored check. Obtain another copy if possible; no final output was published. |
| `cleanup failed; check temporary files.` | A close or temporary-file deletion failed. Inspect the destination before retrying. |

A reset, power loss or lower-level system abort can leave a temporary file.
Existing temporary files are skipped on later runs; they are never assumed to
belong to a new invocation. Prefixes are `SQU` (SQ), `USQ`, `CRU` (CR), `UCR`
(UNCR), `LZU` (LZH), and `ULZ` (UNLZH), followed by five digits and `.$$$`.
Do not treat one as a verified finished file. Remove only a leftover you have
identified as belonging to the interrupted operation, while retaining its source.
An additive checksum is a damage check, not a security or authenticity check.

See the individual command pages for naming rules, supported formats and
command-specific messages. The [engineering specifications](../engineering/Compression%20Utilities%20Common%20Specification.md)
describe the reusable macro library and qualification boundaries.

## Native assembler and linker

The Utilities Disk supplies the original [ZSM4 4.7 assembler](ZSM4.md) and
[Digital Research LINK 1.3 linker](LINK.md). Run them from B: while working
on a writable drive. Their original command syntax and identities are retained.
Read `TOOLINFO.TXT`, `ZSM4COPY.TXT` and `LINKCOPY.TXT` for attribution and terms.
The host Utilities package includes the complete ZSM4 source companion.

## NOAH archive utility

NOAH manages CP/M LBR libraries and ARC-compatible `.ARK`/`.ARC` archives.
It is supplied on a separate NOAH Utilities disk for each platform. Mount that
disk in B: in place of the primary Utilities disk when using NOAH.
Keep `NOAH.COM` and its matching `NOAH.OVL` together. Change to their disk/user
before starting NOAH, then qualify the archive and source operands with their
writable work disks. Overlay lookup uses that invocation DU, then A0:.

```text
B:
NOAH /LIST C:FILES.ARK
NOAH /TEST C:FILES.ARK
NOAH /EXTRACT C:FILES.ARK D:
NOAH /ADD C:FILES.ARK D:*.TXT
NOAH /ADD /SQ C:TEXTS.ARK D:*.TXT
NOAH /ADD /CR C:BINARY.ARK D:*.BIN
NOAH /REMOVE C:FILES.ARK *.BAK
NOAH /COMPACT C:FILES.ARK
```

The same operations work with LBR. ADD requires one exact archive target;
LIST, TEST, EXTRACT, REMOVE and COMPACT accept archive selectors and member
patterns. `/CAPACITY=n` sets LBR directory capacity on ADD/COMPACT. Unknown new
extensions require `/FORMAT=LBR` or `/FORMAT=ARK`; existing files are recognized
by contents and are never converted by FORMAT.

ARC ADD stores members without compression unless `/SQ` or `/CR` is explicit.
These select native ARC methods 4 and 8 and preserve the original member name.
LBR compression retains its standalone SQ/CR representation and marked filename.
Standalone `/SQ`, `/CR` and `/EXPAND` remain available; `/EXTRACT /EXPAND` decodes
one inner layer in LBR. ARC extraction decodes its archive-managed method.
Input bytes include CP/M's final physical-record padding when no exact logical
length is available; 00h, 1Ah and high-bit bytes are ordinary input data.

`/Y` approves ordinary replacement/removal and explicit COMPACT. It never
overrides read-only/system protection; `/R` and `/SYS` enable separate protected
questions. `/Q` suppresses routine progress, retaining choices, warnings, errors
and the final outcome. Escape or Ctrl-C cancels at safe boundaries.

NOAH's ordinary replacement prompt offers `Y/N/A/C/?`, default No. Type `?`
for `Y Yes, N No, A All, C Cancel, ? Help`. Safe failure recovery offers
`R/S/A/?`, default Skip; its help is `R Retry, S Skip, A Abort all, ? Help`.
Each explanation returns to the same file/member or failed source/archive.
Repeated help changes no files or choices. Simple protection/removal/COMPACT
Yes/No confirmations and paging retain their existing controls.

Ordinary ARC updates preserve retained headers/payloads and the entire suffix
after the end marker. COMPACT trims only excess 00h/1Ah padding and refuses an
opaque suffix. It does not recompress retained members. No-match REMOVE leaves
the archive unchanged, including combined COMPACT.

Every new archive/update is staged, reopened and verified before publication.
Keep any reported TMP/BAK recovery files until the final state is understood.
Uncertain rollback stops the batch and reports the affected paths. There is no
automatic recovery/resume command or power-loss atomicity guarantee.

The frozen selection limit is 512 candidates; actual transaction capacity also
depends on active TPA and codec/source-plan requirements. Low-memory requests
fail safely. The interactive browser, ZIP and LZH/CrLZH selectors remain deferred.
Current qualification and media status are recorded in the
[engineering integration record](../engineering/NOAH%20ARC%20Write%20Integration.md).
