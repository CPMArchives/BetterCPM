# BetterCP/M COMPARE.COM Engineering Specification

**Status:** Development implementation; component qualification incomplete  
**Target:** COMPARE 1.0, BetterCP/M Utilities Disk  
**Scope:** COMPARE 1.0 contract; implementation separately authorized by maintainer; release promotion pending  
**Reference conventions:** BetterCP/M DUMP and TYPE engineering specifications; existing utility versioning, file-selection and qualification conventions.

## 1. Purpose and boundaries

COMPARE performs a read-only, byte-for-byte comparison of **exactly two files**. It supports compact difference listing, side-by-side hexadecimal inspection, summary-only reporting, selected byte ranges, and forward-only pagination.

COMPARE is not a text DIFF, directory comparison tool, binary editor, or patch utility. No wildcard matching, directory traversal, multi-file selectors, backward paging, terminal-specific cursor control, or monitor-subsystem dependency is required for 1.0.

It shall run on the supported BetterCP/M cpmsim and Model 4 targets, using ordinary CP/M 2.2 BDOS file and console facilities wherever possible. Follow the repository's native Z80/ZSM4 and utility-versioning conventions.

## 2. Command syntax

```text
COMPARE [options] file1 file2 [options]
COMPARE /VER
COMPARE /HELP
```

Options may precede, separate, or follow file operands. Case is insignificant. Except for `/VER` (see below), validate the complete command tail before opening files.

| Option | Meaning |
|---|---|
| `/LIST` | Compact difference listing; **default** |
| `/SIDE` | Side-by-side hexadecimal view, eight byte positions per file per row |
| `/SUM`, `/SUMMARY` | Equivalent aliases for summary-only output |
| `/COUNT=n` | Maximum displayed differing-byte entries in `/LIST` (default 20) |
| `/ALL` | Remove `/LIST` display limit |
| `/FROM=hex[H]` | Starting byte offset in file 1 and, unless overridden, file 2 |
| `/FROM2=hex[H]` | Override starting byte offset in file 2 |
| `/LEN=hex[H]` | Maximum number of *comparison positions* |
| `/P` | Forward-only paginated display |
| `/40` | Four byte positions per file per row in `/SIDE` |
| `/VER` | Version/build/revision identification, using existing BetterCP/M convention |
| `/HELP` | Command help |

`hex[H]` denotes one to eight hexadecimal digits with optional trailing `H` or `h`. A missing suffix **does not** imply decimal. Reject signs, missing digits, invalid characters and numeric overflow; never truncate or wrap.

`/COUNT=n` is a decimal display-entry count from 1 through 65,535 (the only decimal numeric switch). Reject zero, signs, nondecimal characters and values above 65,535 without truncation or wrap. `/ALL` removes the display limit.

### 2.1 File operands

Require exactly two file operands. Identical specifications and operands naming the same underlying file are valid. Wildcards (`*`, `?`), DU lists/ranges (for example `A[3,5-9]:`), additional file operands and directory-wide comparisons are rejected.

Support ordinary `FILE.EXT`, `A:FILE.EXT`, and the project's exact single-DU form such as `A3:FILE.EXT`, subject to the existing single-DU parsing contract. An omitted drive or user inherits the caller's current selection. The operands may name different drives/user areas. Comparing a file with itself is valid. Restore caller drive/user on every handled exit.

Both inputs are read-only. Do not modify file contents, directory entries, file attributes, or allocation metadata.

### 2.2 Option interactions

- `/LIST`, `/SIDE`, `/SUM` or `/SUMMARY` are mutually exclusive modes; `/SUM` and `/SUMMARY` are aliases.
- `/COUNT=n` and `/ALL` apply **only to `/LIST`** and conflict with one another.
- `/P` is valid with `/LIST` and `/SIDE`, but not summary-only mode.
- `/40` is valid with `/SIDE` only.
- `/FROM=`, `/FROM2=`, `/LEN=` are valid in every display mode.
- Identical repeated boolean switches are harmless. Reject conflicting modes and invalid combinations explicitly. Value switches follow DUMP: every occurrence must be valid, and the last valid value wins.
- `/VER` is an exact case-insensitive token that takes precedence over other arguments, as in DUMP, and must perform no file access. Otherwise, an exact case-insensitive `/HELP` token anywhere in the tail displays help and ignores other arguments, including malformed combinations, without file access. `/VER` wins when both query tokens are present. Longer tokens such as `/HELPER` are not help queries.

## 3. Comparison range and pairing

Define starting offsets:

```text
start1 = FROM if present, else 0
start2 = FROM2 if present, else start1
```

Thus `/FROM2=0300` alone compares file 1 from zero against file 2 from `0300H`. Option order does not matter.

For each nonnegative comparison position `k`, compare file 1 at `start1+k` with file 2 at `start2+k`. If `/LEN=` is present, consider at most `LEN` positions; otherwise continue until neither file has remaining bytes. `LEN=0` is a valid empty comparison. Offsets beyond EOF are valid; the absent side is EOF. Do not create fictitious bytes past both EOFs or scan indefinitely.

The requested range is bounded by actual data availability and optional LEN, not by the physical maximum representable offset. Reject arithmetic overflow instead of wrapping. Report the number of positions actually considered, distinguishing positions containing two bytes from positions with a byte on only one side where useful.

A difference is either:
- **Byte mismatch:** both files have a byte at a position, but values differ.
- **Additional byte:** one file has a byte and the other is at EOF.

Count these categories separately. Additional bytes are counted **only within the selected comparison range**. Report both complete file lengths independently of range selection.

### 3.1 CP/M logical lengths

The file's byte length is its complete sequence of 128-byte logical records. `1Ah` and final-record padding are ordinary bytes, not inferred EOF. Do not strip high bits, translate text, or normalize contents. Use sufficiently wide file offsets, lengths and counters to handle files exceeding 64 KiB and the supported CP/M 2.2 record range without wrap.

## 4. Results and summaries

A completed comparison always reports:
- both filenames and **full** logical-record file lengths (decimal bytes);
- selected comparison start offsets and length restriction when applicable;
- count of unequal byte pairs;
- count of additional bytes within the selected range, and which file contains them;
- a clear final result.

Use `FILES IDENTICAL` only when the operation has established equality of the **entire files** (full coverage, same lengths, no mismatches). For bounded or independently offset comparisons, report `SELECTED RANGES IDENTICAL` when no differences occur, without implying the entire files are identical. Independently offset comparisons always use selected-range results, even if the selected range happens to cover all available bytes. If selected regions differ, report `SELECTED RANGES DIFFER` or `FILES DIFFER` with clear context. When full file lengths differ outside the compared range, report that separately.

An empty selected range is not evidence of full-file identity. If `/FROM` is beyond EOF for both, report that no bytes were available in the selected range. If `/LEN=0`, report zero positions examined.

Example (illustrative):
```text
A>COMPARE /LEN=0200 FILE1.BIN FILE2.BIN /SUMMARY
512 POSITIONS EXAMINED
0 DIFFERING BYTES
0 ADDITIONAL BYTES

FILE LENGTHS:
  FILE1.BIN   1,024 BYTES
  FILE2.BIN   2,048 BYTES

SELECTED RANGES IDENTICAL
FULL FILE LENGTHS DIFFER
```

## 5. `/LIST` mode

The default mode lists differing *byte positions*, not matching bytes. Show up to **20** entries by default, then continue comparing silently and print complete totals. `/COUNT=n` changes the number displayed, not the number examined; `/ALL` lists every differing entry. EOF-versus-byte entries participate in the display limit, but remain a separate summary count.

Use eight uppercase hexadecimal digits for absolute offsets and two digits for byte values. When starting offsets differ, list **both** absolute file offsets for each compared position; a single shared offset is insufficient. Render a missing byte as `---- EOF ----`. Keep file labels unambiguous. A display limit never truncates the underlying comparison.

## 6. `/SIDE` mode

Display the two files in parallel with two absolute row-base offset columns, eight hexadecimal byte slots per side, and a fixed-width central marker. Show matching rows as well as differing rows. Use `<>` on a row containing any byte mismatch or byte-versus-EOF difference. No marker for a fully matching row.

**File 1 controls row boundaries:** row bases are multiples of eight, including the first partial row when `/FROM=` is unaligned. File 2 is laid out by comparison pairing: corresponding bytes occupy the same visual slots, even when its absolute offsets are not eight-byte aligned. Blank slots before the first selected byte and after the final selected byte are not compared or displayed.

For each row with file 1 base `b`, the conceptual file 2 row base is `b + (start2 - start1)`. Show that row base as eight hexadecimal digits when nonnegative. When it is negative, show exactly `--------`. This is a **row-base placeholder**, not an EOF indicator. The row-base address corresponds to visual slot zero, even if that slot is blank.

Approved illustrative alignment:
```text
COMPARE /FROM=0007 /FROM2=0000 /SIDE

              FILE1.BIN                       FILE2.BIN

00000000                       54    --------                       20
00000008  2C 20 44 49 47 49 54 41    00000001  44 49 47 49 54 41 4C 20
00000010  4C 20 52 45 53 45 41 52    00000009  52 45 53 45 41 52 44 44
```

The values are illustrative. The actual implementation must ensure the two compared bytes occupy corresponding visual slots. The marker and both offset columns must never shift the byte fields.

For a file reaching EOF, show `---- EOF ----` in its column on the first row where that side has no bytes while the other side still has data, then leave its column blank on subsequent rows. If the other file has data on only part of the row, display those bytes in their proper slots. Do not substitute an EOF banner for bytes that still exist. A partially populated EOF row preserves its bytes and leaves its remaining slots blank; the banner appears only on the first fully absent row while the other file still has data.

### 6.1 `/40`

`/40` uses **four slots per file per row**, with file 1 row bases aligned to multiples of four. Pairing, partial-row and negative-row-base rules are unchanged. Each byte occupies two adjacent hexadecimal characters, without spaces between bytes. Each unavailable range-edge slot occupies two spaces.

The approved data-row layout is exactly **38 columns**:

| Columns | Field |
| --- | --- |
| 1–8 | File 1 row base |
| 9–10 | Two spaces |
| 11–18 | Four compact byte slots |
| 19–20 | `<>` or two spaces |
| 21–28 | File 2 row base |
| 29–30 | Two spaces |
| 31–38 | Four compact byte slots |

```text
00000004        54<>--------        20
00000008  47495441<>00000001  54414C20
```

On the first fully exhausted row while the other side still has data, use `EOF` left-aligned and space-padded within that side's eight-character byte field, instead of `---- EOF ----`. Subsequent exhausted fields remain blank. Preserve actual bytes on partial rows; do not overlay them with the EOF label. Both offset columns and the marker retain their fixed positions. File headings must also fit within 40 columns.

## 7. Pagination and interruption

`/P` enables **forward-only** paging in `/LIST` or `/SIDE`. Reserve the bottom display row for the prompt: on a 24-row console, 23 rows are available for content. Page boundaries are measured in **rendered display rows**, not source bytes or mismatch counts.

At the prompt:
- `Space` or `Enter`: advance one page.
- `Ctrl-C`: suppress all further detailed output and prompts; **continue comparing to completion** and print the complete final summary.
- `Q` or `Esc`: the same display-stop action as Ctrl-C; continue comparison and print complete totals.

On any of these display-stop keys at the paging prompt, print:
```text
DISPLAY INTERRUPTED
COMPARISON CONTINUING...
```
Then finish the single-pass comparison silently and report full totals. Do **not** print `COMPARISON INTERRUPTED`, because the calculation continues. No second pass or stored difference list is required. There is no backward paging, terminal-specific cursor positioning, or screen repainting in 1.0.

A genuine read error is different: abort with an error and do not claim a completed comparison. Ctrl-C during non-paged output cancels the operation cleanly: close files, restore caller state, explicitly report `COMPARISON INCOMPLETE`, and omit any completed-comparison result. Any partial statistics must be clearly labelled incomplete.

## 8. Errors, state, and implementation constraints

Reject malformed commands before file access. Identify the offending switch or operand. For file-open errors, name the specific file that could not be opened. Detect read failures distinctly from normal EOF and terminate without a success summary.

Use bounded memory, ordinary BDOS file access, and no whole-file or whole-difference-list buffering. A streaming, single-pass comparison with small record buffers and wide counters is sufficient. Support the existing BetterCP/M single-DU syntax without changing the BDOS/BIOS/CCP/CPX/RSX contracts. Avoid new monitor dependencies or terminal-specific screen-control sequences.

Close both files, restore drive/user and other owned process state, and return cleanly on handled errors and normal completion. Do not assume every CP/M implementation supplies Unix-like exit status; any batch-readable status extension requires separate approval.

`/VER` and `/HELP` must not alter input files or allocate output files. Follow the existing utility metadata and version/revision conventions; do not invent an independent build counter.

## 9. Qualification and acceptance

Before claiming component qualification, verify at least:

1. Exact two-file syntax, single DU, no wildcards/ranges, option ordering and conflicts.
2. Identical, different, empty and same-file operands.
3. Byte differences at first/last positions, across record and 64-KiB boundaries.
4. Full 128-byte records, including `1Ah` and padding.
5. Unequal lengths and byte-versus-EOF rendering, including both EOF before FROM.
6. `/FROM`, `/FROM2` with and without `/FROM`, differing modulo-eight/four alignments, negative conceptual row base.
7. `/LEN=0`, partial first/last rows, selected-range equality and unequal full lengths.
8. `/LIST` default 20, `/COUNT=n`, `/ALL`, `/SUMMARY`, and accurate totals beyond display limits.
9. `/SIDE` and `/40` exact rendered columns, marker placement and row-base labels.
10. `/P` page accounting, Enter/Space, Ctrl-C/Q/Esc display interruption followed by complete calculation; non-paged Ctrl-C cancellation with an incomplete result.
11. Open/read errors, numeric overflow, caller-DU restoration, and read-only guarantees.
12. Native ZSM4/LINK build parity and execution on cpmsim and Model 4, using disposable test media.

Preserve an explicit distinction between component qualification and final Utilities Disk acceptance. Implementation was separately authorized by the maintainer after the §10 decisions were approved. This specification does not assert qualification or authorize release promotion. See [COMPARE Implementation Qualification](COMPARE%20Implementation%20Qualification.md) for current evidence.

## 10. Settled review decisions

The maintainer approved the following decisions before implementation:

- `/COUNT` is decimal, 1–65,535; `/ALL` removes the display limit.
- At a paging prompt, Ctrl-C, Q and Esc stop detailed display while comparison continues to completion.
- Non-paged Ctrl-C cancels cleanly and explicitly reports incomplete comparison, without a completed-result claim.
- Exact `/VER` takes precedence; otherwise exact `/HELP` displays help without file access and ignores other arguments.
- `/40` uses the approved 38-column compact layout and short EOF label in §6.1.
- EOF banners appear only on the first fully absent row; partial rows preserve available bytes.
- Independently offset comparisons always report selected-range results.
- Exactly two file operands are required; identical operands are allowed.

These decisions settle the listed review points. Implementation is separately authorized; qualification and release promotion remain separate steps.
