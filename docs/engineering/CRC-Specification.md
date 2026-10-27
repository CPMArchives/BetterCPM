# BetterCP/M CRCKSUM.COM Engineering Specification

**Target:** CRCKSUM 1.0, BetterCP/M Utilities Disk
**Status:** Implemented development candidate; paired candidate images integrated; cpmsim checks pass, Model 4 execution and release acceptance pending\
**Date:** 2026-10-28
**Authority:** Maintainer decisions in the CRC, CHECKSUM and HASH design discussion. Implementation was subsequently authorized after PR #528 merged. Release promotion is not asserted. See [implementation and qualification notes](CRC-Implementation.md).

## 1. Purpose, scope and controlling conventions

CRCKSUM calculates file-integrity values, writes portable verification lists, and verifies files against native lists, historical CRCKLIST/CRCKFILE lists, and original SIG/M catalogs. It supports historical CRCK, corrected CRCK, CHEK, CRC-32/ISO-HDLC, SUM8, SUM16, KERM6 and KERM12. CRCKSUM.COM supersedes the developing CRC.COM name; internal source/tool paths retain `crc` to preserve continuity. Historical CRCK is an intentionally preserved nonstandard calculation; do not replace it with a mathematically conventional CRC.

CRCKSUM is a streaming Z80 transient using ordinary CP/M 2.2 BDOS services. Support the BetterCP/M cpmsim and TRS-80 Model 4 targets, files larger than 64 KiB, and the existing extended drive/user namespace. Do not change OS interfaces or require a resident service, terminal personality or screen-control protocol. Input files and reference lists are read-only. Only requested output lists and their transaction files may be changed.

Fletcher, Adler, cryptographic hashes, archive-member calculation, recursive host directory handling, list editing and automatic repair are outside this specification. HASH.COM is not specified here.

Repository references:

- `docs/engineering/208 Extended DU Syntax.md`: shared filespec grammar, inheritance, bitmap and canonical selector enumeration.
- `docs/engineering/COMPARE Specification.md`: logical-record byte coverage, streaming, state restoration and supported platforms.
- `specifications/UTILITY-HELP.md`, `specifications/UTILITY-VERSIONING.md`, `specifications/COMPONENT-REVISION-TRACKING.md`, `specifications/VISUAL-IDENTITY.md`: current help/query precedence, metadata and identification. Older utility-specific query precedence does not override the current common help contract.

## 2. Command contract

```text
CRCKSUM [options] [filespec ...] [options]

/CRCK  /CRCK5  /CHEK  /CRC32  /SUM8  /SUM16  /KERM6  /KERM12
/FILE=filespec  /LOCAL=filename  /LEGACY
/CHECK[=filename]  /40  /HELP  /VER
```

Options may precede, separate or follow operands. Names are case-insensitive. An omitted target operand means `*.*` in the caller's original logged DU. A bare target DU means `*.*` there. Multiple target operands, wildcards, extended DU lists and ranges are supported.

| Option | Contract |
| --- | --- |
| `/CRCK` | Select historical CRCK. |
| `/CRCK5` | Select corrected CRCK. The 5 is a family label, not a CRC width. |
| `/CHEK` | Select the CHEK-compatible calculation. |
| `/CRC32` | Select CRC-32/ISO-HDLC. |
| `/SUM8` | Select the unsigned byte sum modulo 256. |
| `/SUM16` | Select the unsigned byte sum modulo 65536. |
| `/KERM6` | Select the Kermit type-1 six-bit checksum applied to the whole file. |
| `/KERM12` | Select the Kermit type-2 twelve-bit checksum applied to the whole file. |
| `/FILE=filespec` | Generate one master list at an explicit destination; a single-DU qualifier is allowed. Unqualified destination uses the original logged DU. |
| `/LOCAL=filename` | Generate one list of this name in each selected target DU. A DU qualifier is an error. |
| `/LEGACY` | Force historical CRCK alone and historical saved-list formatting, including double spacing. Other algorithm switches are ignored regardless of order. |
| `/CHECK` | Verify, discovering a reference independently in each target DU. |
| `/CHECK=filename` | Verify against this exact name independently in each target DU. A DU qualifier is an error. |
| `/40` | Use the stacked screen layout; does not change saved lists. |
| `/HELP`, `/VER` | Common help and metadata-only queries. |

Without algorithm switches, calculation selects all eight algorithms. With one or more algorithm switches, select their union, not the last algorithm mentioned. `/LEGACY` overrides this selection after parsing. Repeated flags are harmless and retain the first occurrence's position. For repeated value options, validate every occurrence and use the last valid value; bare `/CHECK` does not erase an explicit reference filename.

`/FILE=` and `/LOCAL=` may be combined. Both require an unambiguous CP/M 8.3 destination filename; no wildcards or DU sets. `/CHECK=filename` also requires an unambiguous name. A colon/DU qualification on `/CHECK=` or `/LOCAL=` is an explicit command-line error: abort before traversal, file processing or output creation; do not strip or silently ignore it.

Verification and list generation are separate modes: `/CHECK` cannot be combined with `/FILE=` or `/LOCAL=`. This is an integration rule to avoid introducing an unapproved check-and-regenerate operation. `/LEGACY` in verification forces the CRCK selection but does not restrict automatic input-format recognition. `/40` is valid in either mode.

An exact `/HELP` or `/VER` query follows the current common help contract: no file access or DU/DMA changes, other operands are ignored, and `/HELP` wins if both are supplied. Query precedence is the sole exception to validating the complete invocation before operations.

Parse the bounded 127-byte command tail privately before DMA reads can overwrite it. Reject unknown options, missing values, invalid names/selectors and incompatible modes before any file changes. No silent truncation, numeric wrapping or command-tail extension is permitted.

## 3. Target selection and processing order

Use the shared extended DU/filespec parser and its 512-bit/64-byte selection bitmap. The logical domain is drives A-P, users 0-31; hardware availability is a separate issue. Capture the caller's original drive and user once; omitted components inherit those values, never a preceding operand's values. Shared wildcard rules and ordinary system-file selection policy apply; do not invent a CRC-only attribute policy.

Examples:

```text
CRCKSUM
CRCKSUM B3:FILE.TXT
CRCKSUM B[1,3,4-5]:*.COM C7:*.TXT
CRCKSUM /CHECK B[1-3]:FILE.TXT
CRCKSUM /CHECK B[1,3,4-5]:
```

Process separate filespec operands in command-line order, assigning each DU to its first encounter. Within one extended selector, retain shared canonical drive-major/user-minor enumeration; the textual order of bracket terms does not override specification 208. Union all filename selections for a DU before processing it. Each DU produces one section and each physical logical file is processed once, despite overlapping operands, duplicate terms or multiple extent entries.

Within a DU sort by canonical eight-character basename, then three-character extension. This is raw CP/M filename ordering, not locale-sensitive collation. Different DUs may contain the same filename; retain separate rows. No DU is stored in saved rows or native section headings. Source identity for traversal/deduplication remains DU plus filename.

## 4. File length and byte coverage

Read every byte of every logical file record up to BDOS logical EOF. Logical records are 128 bytes. Include embedded `1Ah`, high-bit bytes and final-record padding. No text translation, parity stripping, guessed byte length, decompression or inferred text EOF applies to checksum input.

`RECS` is the exact decimal count of 128-byte logical records, including the final padded record. An empty file has zero records. Use sufficiently wide record, byte, file and summary counters for the supported filesystem limits; at least 32-bit record and length accounting is required. Detect overflow explicitly. Sequential data processing must not wrap at 64 KiB.

Compute all selected algorithms during one streaming pass per file. Sharing a master and local destination does not cause a second input pass. A BDOS file-size query may precede streaming; the observed stream count must agree before publishing results. Detect a size change as an error, while making no promise to detect every same-size concurrent modification.

## 5. Exact algorithm definitions

All results are unsigned and printed as fixed-width uppercase hex, with leading zeros. No filename or size bytes participate in these calculations.

### 5.1 Historical CRCK (`CRCK`; historical label `CRC`)

Initialize a 16-bit accumulator to zero. For each unsigned byte `b`:

```text
top = r & 8000h
s = (r << 1) & FFFFh
r = (s & FF00h) | (((s & 00FFh) + b) & 00FFh)
if top != 0: r = r XOR A097h
```

The byte addition does not carry into the high byte. Perform exactly one shift per input byte. There is no final augmentation, complement or XOR. This reproduces Petersen CRCK and SIG/M CRC results, including the historical arithmetic defect.

### 5.2 Corrected CRCK (`CRCK5`)

Width 16; polynomial `A097h` in normal representation; initial value `0000h`; no input or output reflection; final XOR `0000h`. For each byte XOR `b << 8` into the accumulator, then perform eight left shifts with conditional polynomial XOR on the old high bit. Return the resulting 16-bit value directly. Do not additionally append zero bytes to this direct implementation.

This is the corrected CRCK 5.x calculation, not SIG/M's CRC utility version 5.0, which retained historical CRCK. Do not label it CRC-16/CCITT merely because old comments use that term.

### 5.3 CHEK (`CHEK`)

Width 16; normal polynomial `1021h`; initial value `0000h`; no reflection; final XOR `0000h`. Use the direct eight-step byte update described above with this polynomial. The result is equivalent to the older SYSLIB bit-input routine followed by two zero bytes. Do not append another two zero bytes to the direct calculation. This is the zero-initialized CRC-16/XMODEM parameter set, as used for CHEK compatibility here; it is not the `FFFFh`-initialized variant.

### 5.4 CRC-32 (`CRC32`)

CRC-32/ISO-HDLC: width 32; normal polynomial `04C11DB7h`; initial value `FFFFFFFFh`; reflected input and output; final XOR `FFFFFFFFh`. A reflected implementation uses right shifts and polynomial `EDB88320h`. Print the conventional numerical value as eight hex digits, most significant digit first; do not byte-reverse the printed result or add a second reflection to a reflected implementation.

### 5.5 Additive sums (`SUM8`, `SUM16`)

Initialize to zero; add each unsigned byte once. SUM8 retains the low eight bits;
SUM16 retains the low sixteen bits, including carries from the low byte. There is
no final complement, carry folding, word grouping or XOR. Print SUM8 as two hex
digits and SUM16 as four. Their historical precedents include the XMODEM block
sum and SQ/USQ data sum; whole-file coverage here follows section 4.

### 5.6 Kermit sums (`KERM6`, `KERM12`)

Let `s` be the unsigned arithmetic sum of all input bytes. KERM6 is
`(s + ((s & C0h) >> 6)) & 3Fh`. Only bits 6 and 7 are folded into the low six;
do not repeatedly fold higher carries or substitute a simple modulo-64 sum.
KERM12 is `s & 0FFFh`. Bounded byte/word sums are sufficient to calculate both.
Print KERM6 as two uppercase hex digits (`00`–`3F`) and KERM12 as three
(`000`–`FFF`), with leading zeros.

These reproduce Kermit's type-1 and type-2 checksum arithmetic over the file's
stored bytes, including high-bit bytes and record padding. They do not create
packets, add LEN/SEQ/TYPE fields, quote data, reset at packet boundaries, strip
parity, or apply the printable `tochar()` wire encoding. Consequently these are
whole-file checks, not predictions of a Kermit transfer's packet check bytes.
The controlling arithmetic is documented in the
[Kermit packet reference](https://www.kermitproject.org/kpackets.html#blockchecks)
and the [Kermit Protocol Manual](https://www.kermitproject.org/kproto.pdf).

### 5.7 Independent acceptance vectors

| Exact input | CRCK | CRCK5 | CHEK | CRC32 | SUM8 | SUM16 | KERM6 | KERM12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Empty byte stream | `0000` | `0000` | `0000` | `00000000` | `00` | `0000` | `00` | `000` |
| ASCII `123456789`, nine bytes | `53C5` | `0FB3` | `31C3` | `CBF43926` | `DD` | `01DD` | `20` | `1DD` |
| Same nine bytes followed by 119 bytes of `1Ah` | `A687` | `5D45` | `E447` | `2F263492` | `F3` | `0DF3` | `36` | `DF3` |

The nine-byte case tests the routines, not a nine-byte CP/M file length. The padded case tests real record coverage. Historical file anchors from HUMONGOUS's restored SIG/M Volume 310:

| File | Bytes | RECS | CRCK | CRCK5 | CHEK | CRC32 |
| --- | --- | --- | --- | --- | --- | --- |
| `ZMD146.LBR` | 181504 | 1418 | `136B` | `A548` | `D24B` | `82A2F154` |
| `ZMDOVL2.LBR` | 47616 | 372 | `B06D` | `6B36` | `C153` | `DE35205C` |

## 6. Native output format

Each native DU section begins with the informational comment, a column header and a dash separator. Data rows are single-spaced. The comment is not required for recognition. The default section is:

```text
; BetterCP/M CRC list
NAME     EXT  RECS  CRCK  CRCK5  CHEK  CRC32     SUM8  SUM16  KERM6  KERM12
-------- ---  ----  ----  -----  ----  --------  ----  -----  -----  ------
TEST     DAT     1  A687   5D45  E447  2F263492    F3   0DF3     36     DF3
```

The row illustrates formatting; its values are for a one-record padded `123456789` fixture. The filename contains no dot: eight left-aligned basename positions, one space, then three left-aligned extension positions. Blank extension positions remain blank. There is no unlabeled extension field: the labels are `NAME` and `EXT`.

Separate later columns with two spaces. Header labels are left-aligned over their dash fields. Numeric values are right-aligned to the right edge of the dash fields, not to the end of the header labels. The five-character CRCK5 field therefore has one leading space before a four-digit result. RECS has a minimum four-character width; determine a sufficient width for the complete DU section before emitting its separator. Keep positions stable within that section; never let a wider value spill into the next field. Different DU sections may have different RECS widths.

With `/CRCK /CHEK` the columns are `NAME EXT RECS CRCK CHEK`. Omit unselected algorithm columns. Without algorithm switches, writer order is CRCK, CRCK5, CHEK, CRC32, SUM8, SUM16, KERM6, KERM12. With explicit switches, preserve the order of each algorithm's first appearance on the command line; repeated switches do not move or duplicate its column. The same order applies to screen output, saved lists, narrow display and verification diagnostics. `/LEGACY` overrides the selection and order with historical CRCK alone. The reader identifies algorithms by header labels and accepts any algorithm order.

The separator's dash runs define field starts and widths. Parse native data by these columns, not by whitespace splitting. Associate the header labels with their fields. Require NAME width 8, EXT width 3, a decimal RECS field, at least one recognized algorithm column, and sufficient widths for each declared result. Left/right padding within numeric fields is permitted on input, but their trimmed values must contain exactly the documented two, three, four or eight hex digits as appropriate, with KERM6 limited to 3Fh. Reject missing values, overflow, unknown/duplicate columns and nonspace garbage between fields or after the final field. Accept hex letters in either case.

Readers skip blank lines and lines whose first nonblank character is `;`. A repeated valid header and separator starts a fresh section and replaces the previous column map. Validate both lines together before accepting subsequent rows; a malformed header or separator is a list error, not an ignored comment. The title and separator are not file records. Do not silently skip malformed data rows. A header cannot be confused with a data file named NAME because recognition also requires the column labels and corresponding separator.

Write CRLF line endings, ASCII text and `1Ah` final-record padding. Readers accept CRLF and ordinary LF line endings, stop list text at `1Ah`, and do not treat padding as an entry. This list-text rule does not alter checksum coverage of target files.

## 7. Master and local list generation

`/FILE=` writes one master list. `/LOCAL=` writes one list per target DU. They may be used together: calculate each selected file once and send the completed result to both destinations and the console.

Each DU produces a complete native section. A master list concatenates the same sections that local lists contain, with one blank line between sections. Repeated headers deliberately demarcate separate source groups without recording their original DU addresses. They do not give the reader a target mapping or precedence. Local lists can move with their files.

Exclude every resolved master/local output identity and every transaction file from input selection in all DUs. Exclude existing output lists as well as newly created ones, and deduplicate overlapping target selections. Do not accidentally checksum an old output list merely because replacement was declined. Protect source files from explicit destination collisions before overwriting.

If master and local output resolve to the same DU/name, open, prompt and write that physical destination only once. Because one file cannot contain both a complete master and a different local-only subset, the coincident destination receives the master stream; no separate local-only copy is made at that identity. Other local destinations retain their per-DU contents. This resolves the accepted write-once rule without interleaving duplicate writes.

Before replacing any existing destination, identify the full DU and filename:

```text
B3:CRC.LST exists. Overwrite? (Y/n/a)
```

Y or Enter replaces this destination. N leaves it unchanged and skips this destination, continuing screen output and other destinations. A replaces this and subsequent existing output destinations in this invocation without more prompts. Ctrl-C cancels. Responses are case-insensitive. Declined outputs must be counted and reported, not claimed as generated.

Use private temporary files; close and validate them before promotion. Preserve an existing final list during calculation. A handled cancellation/write/close failure must not leave partial results under the final name. Use established backup/rename recovery where needed; CP/M 2.2 does not provide a guaranteed power-fail-atomic replace. If recovery fails, name surviving files and report the incomplete transaction honestly. Master and local outputs complete independently; a failed local output does not erase already completed lists. Do not promote an incomplete master as complete. A source failure invalidates affected pending outputs; continue unaffected DU jobs where possible.

## 8. `/LEGACY` output

`/LEGACY` selects historical CRCK alone regardless of other algorithm switches and their order. It does not reject those switches. FILE/LOCAL destinations and target selection retain their meanings.

Generate the original record spelling:

```text
--> FILE:  CATALOG .035\t\tCRC = CB BC
```

The `\t` notation above denotes two actual TAB bytes, not literal backslash characters. The exact prefix is eleven characters: `--> FILE:  `. Use an eight-character space-padded basename, dot, three-character space-padded extension, two TABs, `CRC = `, two uppercase hex digits, a space and two uppercase hex digits. High byte precedes low byte. Use the historical leading CRLF and a blank line between entries (two CRLF sequences). Do not add native comments, column headings, RECS, DU headers or other algorithm fields. Finish with normal `1Ah` record padding. Console summaries do not enter the file.

Legacy master output concatenates historical records without native section headers. This is a necessary exception to native section demarcation. Legacy formatting applies to saved lists; the normal console remains a table/stacked display of the forced CRCK selection.

## 9. Reference discovery and locality

Every selected target DU is an independent verification job. Every selected file is checked against one reference in its own DU. Never search another DU or consult an incidental master/local list after selecting a reference. An omitted target still selects the caller's current DU as specified in Section 2; this is not a fallback search.

`/CHECK=filename` uses that exact name in every target DU and bypasses discovery. It cannot point at another DU. If absent, report the missing reference for that DU and continue other jobs.

Bare `/CHECK` searches these tiers in order, in the target DU only:

1. `CRC.LST`
2. `CRCKLIST.*`
3. `CRCKFILE.*`
4. `-CATALOG.*`

Use the first tier containing a candidate. Multiple candidates in that tier are ambiguous: report them and direct the user to `/CHECK=filename`; do not choose by directory order or proceed to a lower tier. No candidates in any tier means `No CRC list found`. A catalog without checksum entries is not a usable reference; report that fact. Once a candidate is selected, unsupported format, malformed content, empty/no-checksum content, missing entries and mismatches never trigger fallback to another list. Display the selected full reference identity before verification.

This is a bounded discovery convention, not universal recognition of historical filenames. An explicit filename may use any name but must contain a supported format.

## 10. Accepted reference formats

Detect format from content rather than filename alone. Support native tables (including repeated sections), original CRCKLIST/CRCKFILE records and original SIG/M indexed catalogs with CRC fields. Distinguish HUMONGOUS's reconstructed catalogs from original SIG/M formats; do not silently promise support for an unexamined reconstruction layout.

### 10.1 Historical lists

Recognize `--> FILE:  ` followed by padded dotted 8.3 name and `CRC = HH HH`. Accept the actual TAB separators, space-expanded equivalents and single or double spacing. The historical CRC label means historical CRCK. Accept a missing presentation prefix on otherwise unambiguous filename/label records as discussed, but never require old readers to accept such output.

Also retain input support for the earlier discussed labelled extension: fields `CRC`, `CRCK5`, `CHEK`, `CRC32`, `SUM8`, `SUM16`, `KERM6`, `KERM12` may appear in any order after the filename. CRC uses separated historical bytes; accept separated or contiguous four-digit forms for recognized 16-bit labelled fields and eight contiguous digits for CRC32. SUM8 and KERM6 use two contiguous digits; KERM12 uses three. SUM16 accepts the same separated or contiguous four-digit forms as other 16-bit fields. This is input compatibility, not the chosen native writer format. Reject unknown or repeated algorithm fields rather than guess. This does not promise compatibility with every historical utility's display transcript.

### 10.2 SIG/M catalogs

Recognize an indexed entry, filename, rounded decimal K size and two hexadecimal CRC bytes, allowing the original observed spacing/tab variations. The index is a volume number, dot and entry number; do not hard-code three digits plus two digits only. Filenames may be contiguous dotted names or space-padded basename/dot/extension fields, including a blank extension. Use real catalog samples to distinguish fields; never parse arbitrary hex-looking words in descriptions as CRC values.

Skip recognizable titles, notes, headings and description continuation lines. Report malformed checksum-bearing entry candidates; do not discard errors as prose. Catalogs without CRC columns are not usable verification lists. Parsing legacy text may mask a historical text parity bit where needed to recognize the examined original catalog forms; never apply that conversion to checked file contents. CRC values in these original SIG/M catalogs mean historical CRCK.

Use rounded K size only as a range filter. For positive K, compatible record counts are `8*(K-1)+1` through `8*K`; zero K means zero records. Use exact RECS when a supported native table supplies it. Do not manufacture an exact record count by multiplying rounded K by eight.

## 11. Verification and duplicate names

An explicit target name or wildcard selects files/entries to check; it never names the reference list. A bare DU means `*.*`. Filter both reference entries and target directory files by the requested selection. Exclude the selected reference identity itself from wildcard checking, but a literal request to check that file is permitted if another listed value exists for it. Report both directions: selected files absent from the list, and selected listed files absent from the directory.

By default check every algorithm actually recorded in a reference entry. Do not synthesize values absent from it. Explicit algorithm switches restrict this to the intersection with the recorded algorithms; `/LEGACY` forces CRCK. No intersection means an entry is skipped, not successfully verified. Report this separately from missing reference information.

Size is a rejection filter only. An exact RECS mismatch, or a size outside a catalog's rounded-K range, rejects that candidate. Compatible size or absent size always proceeds to checksum comparison. Lack of a size field is normal in CRCKLIST.

Preserve duplicate filename entries, including entries in separate native sections. Anonymous sections are not target addresses. For one actual target file, consider all applicable entries of that name in the selected reference:

1. Filter by size where supplied.
2. For each remaining candidate with a selected recorded algorithm, compare all those values against the actual file.
3. A full candidate match verifies the file; report differing alternative entries as alternatives, not as the selected file failing despite a matching candidate.
4. If no candidate matches, report size/checksum failure with candidate/section context. If all entries were skipped for algorithm selection, report skipped rather than verified.

Never assemble a synthetic match using CRCK from one entry and CRC32 from another. A candidate with fewer recorded selected algorithms may match, but report which algorithms were actually verified; do not imply all requested algorithms were present. The same actual file is read once and its calculated values reused for applicable candidates. Streaming the reference again is permissible to bound memory; whole-file or whole-list buffering is not required.

Duplicate names across source DUs remain the user's responsibility when generating a location-free master. Verification does not resolve original source identity, automatically remap sections, or consult other lists for authority.

## 12. Display, interruption and outcomes

Normal calculation output uses the native table layout and selected algorithms. Identify the active DU on the console outside the saved section; show full DU identities in diagnostics and reference-selection messages. Headers repeat per DU. Native saved output has no DU address.

`/40` uses a filename line followed by separate RECS and selected algorithm lines. For example:

```text
CATALOG  035
  RECS  24
  CRCK  CBBC
  CRCK5 0FB3
  CHEK  31C3
  CRC32 CBF43926
```

Keep all /40 headings, prompts and diagnostic lines within 40 columns by wrapping descriptive text; do not wrap saved list records. No paging, cursor addressing, repaint, terminal negotiation or additional `/P` switch is introduced.

Verification displays a result for each selected file and enough algorithm/candidate detail to explain failures and matches. Distinguish MATCH, SIZE MISMATCH, CHECKSUM MISMATCH, FILE NOT FOUND, FILE NOT LISTED, SKIPPED, READ ERROR, LIST ERROR and missing/ambiguous reference. Identify native section/entry or line when useful for duplicate/malformed entries.

Print per-DU totals and overall totals: distinct files verified, failed files, missing listed files, unlisted selected files, skipped files/entries, malformed entries, DU/reference failures and output destinations completed/declined/failed. Label file and entry counts separately so duplicates do not inflate verified-file totals. Avoid double-counting a failed candidate as another failed physical file.

Report complete verification success only when at least one file was verified and no relevant failure, omission, skipped selection or list error remains. Zero checked files is never proof of success. A matched file may be reported individually even if another file or malformed list entry makes the overall job unsuccessful.

Ctrl-C cancels processing, closes files, discards uncommitted outputs, restores caller state and reports an incomplete operation. Do not claim completed verification or list generation after cancellation. Continue independent target DUs after recoverable missing-file/reference or destination errors; never treat a BDOS read error as EOF. Follow existing repository machine-readable outcome conventions if available; do not invent an OS ABI solely for CRC.

## 13. Implementation constraints and focused acceptance

Use bounded buffers and private FCBs. Restore the caller drive/user, DMA and return state on every handled exit. No component revision is advanced solely by rebuilds. Sorting/discovery must work with the supported directory size or explicitly diagnose insufficient workspace; no truncation, omitted files or falsely complete results. An extra directory or reference pass is preferable to whole-file buffering or a new external sorting framework.

Before implementation qualification, verify these directly relevant groups:

1. Independent algorithm vectors, real historical catalog anchors, record padding/high bits and files crossing 64 KiB.
2. Four-default/subset/union selection; LEGACY override in either switch order; query paths and malformed commands before mutation.
3. Shared DU grammar, caller inheritance, operand/canonical ordering, overlaps and within-DU sorting.
4. Native fixed columns, blank extension, right alignment, RECS-width expansion, omitted/reordered algorithm columns and repeated sections.
5. Exact legacy prefix/TABs/hex byte spacing/double spacing and read compatibility with CRC 5.0 or 6.4 where feasible.
6. Original CRCKLIST and SIG/M catalog parsing, rounded size filtering, comments/continuations, malformed records and no-checksum catalogs.
7. Discovery priority, ambiguity, exact local CHECK name, no cross-DU fallback and rejected CHECK/LOCAL DU qualification.
8. Missing/unlisted files, repeated names, candidate size rejection, no mixed-entry match, absent algorithms and honest aggregate results.
9. Master/local simultaneous output, one input pass, exclusions, coincident destination policy, overwrite Y/N/A and cancellation/recovery.
10. /40 screen fit, normal file layout unaffected, state restoration, and focused CP/M runtime checks on cpmsim and Model 4.

Use existing native build/metadata infrastructure and focused host/runtime checks. No unrelated utility-wide regression campaign is required for a documentation-only change. Record implementation size, workspace requirements, platform results and any qualification gaps before claiming completion.

## 14. Historical evidence and provenance

Primary survey corpus: [HUMONGOUS restored SIG/M collection](http://cpmarchives.classiccmp.org/cpm/Software/UserGroups/SIGM/). Its `-CATALOG.ALL` is a modern reconstruction and must not be mistaken for an original input format.

- Volume 4 CRCK3 source and Volume 9 CRCK10/6 source establish the historical calculation; original CRCKLIST/CRCKFILE records provide the writer compatibility target.
- SIG/M CRC utility 5.0 introduced in Volume 72 retains historical CRCK; corrected CRCK 5.x is a different family. Volume 96/147 CRCK-51.A86 supplies corrected arithmetic.
- Volume 100 CRC.MAC and Volume 188 CRC.MQC show Conn's separate program/display adaptations without changing the historical calculation.
- Volume 226 NCRCK1.MAC, LCRCK11.MAC, LCHEK.DOC and LCRCK11.DOC establish historical CRCK/CHEK dual reporting and CHEK 1.5 compatibility; later ZCRCK versions are in Volumes 300/302/309.
- Volume 210 CRC-64.AQ6 explicitly preserves historical results; its parser requires the eleven-character CRCKLIST prefix. Both that reader and SIG/M CRC 5.0 accept single-spaced records, although our LEGACY writer deliberately reproduces double spacing.
- Original catalogs in the 31 cleaned-volume directories carrying separate lists (15 and 19-48) lack CRC columns. Volume 49 introduces embedded values. The original Volume 310 catalog and both listed LBR files verify the historical CRCK anchors above.

These facts support the selected compatibility scope; they do not claim every historical implementation or unrelated display transcript is accepted. No implementation, binary, disk image or release manifest is changed by this specification.
