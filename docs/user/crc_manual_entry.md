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
