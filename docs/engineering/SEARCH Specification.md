# BetterCP/M SEARCH.COM Engineering Specification

**Target:** SEARCH 1.0  
**Status:** Consolidated SEARCH 1.0 engineering design; implementation details noted separately; no implementation or qualification claimed  
**Date:** 2026-10-26  
**Scope:** Read-only file-content search, streaming results and optional forward-only pagination

## 1. Authority, references and status

This document consolidates the maintainer-approved SEARCH 1.0 decisions from BetterCP/M Utilities Discussion (2), together with the subsequent specification review. The design requirements below are normative; engineering implementation details not explicitly decided remain subject to repository conventions and focused review. This document does not authorize implementation or claim qualification.

Repository references, named relative to the BetterCPM repository root:

- `docs/engineering/208 Extended DU Syntax.md`: controlling DU grammar, normalization, inheritance and shared parser model.
- `docs/engineering/DUMP Specification.md`: byte representation, bounded memory, caller restoration and qualification conventions.
- `docs/engineering/COMPARE Specification.md`: closely related read-only utility and forward-only pagination conventions.
- `docs/engineering/DIR WHEREIS Specification.md`: namespace traversal and honest incomplete-search reporting; WHEREIS-specific global defaults and private BIOS adapter are not automatically SEARCH requirements.
- `specifications/UTILITY-VERSIONING.md`, `specifications/COMPONENT-REVISION-TRACKING.md`, `specifications/UTILITY-HELP.md` and `specifications/VISUAL-IDENTITY.md`: utility metadata, queries and presentation conventions, subject to the integration decisions in Section 15.

These are repository references rather than bundled attachments. No existing binary is qualified by this document.

## 2. Purpose and boundaries

SEARCH searches the contents of files selected by a CP/M filespec and an extended drive/user selector. Each selected logical file is processed as a stream. SEARCH shall independently search for literal TEXT and, when valid and enabled, decoded HEX bytes from the same supplied pattern.

SEARCH shall not modify files, attributes, directories, allocation metadata or media. It shall not create a temporary disk file merely to buffer input or results. It is a separate content-search utility; DIR /WHEREIS remains a filename locator.

Regular expressions, wildcard interpretation inside the content pattern, replacements, backward paging, stored match indexes, recursive host directories, archive-member searching and whole-file buffering are outside the approved 1.0 scope. Filename wildcards remain supported through the common filespec grammar.

## 3. Command syntax and lexical boundary

The invocation requires one quoted pattern, one filespec and zero or more approved options:

```text
SEARCH [options] "pattern" filespec [options]

options: /NOHEX /NOTEXT /NOCASE /P
```

Require one quoted content pattern followed by one filespec; switches may occur before the pattern or after the filespec. The quoted pattern preserves internal spaces and letter case, and the quotation marks are delimiters, not pattern bytes. A pattern beginning with `/` remains pattern data when quoted. Do not reverse the established pattern-first operand order. Handling literal embedded double-quote bytes and TABs within a pattern is an implementation-level lexical detail to be resolved without changing the required examples.

The finalized lexer shall preserve literal pattern bytes, including letter case and significant spaces. It must distinguish literal pattern data from option/query tokens. It must not uppercase the pattern as part of case-insensitive filename or option handling. If a host CCP changes command-tail case before launch, SEARCH cannot reconstruct the original spelling; document and test that environment limitation rather than promising recovery.

Parse the bounded command tail itself and construct private FCBs; do not assume CCP-prepared default FCBs describe the intended filespec. Copy or finish parsing the tail before a file DMA operation can overwrite `0080h`.

### 3.1 Command-tail and pattern limits

The existing CP/M command-tail limit remains **127 bytes**. The filespec, selector, delimiters, separators and switches all consume that budget. SEARCH shall not add an extended command-input mechanism or silently truncate input.

Each enabled search representation is limited to **64 decoded bytes**. For TEXT, decoded bytes are the literal pattern after lexical delimiter handling, with no implied escapes. For HEX, they are the bytes produced by hex decoding. A valid enabled representation exceeding its supported limit must be diagnosed before file access, not shortened.

The semantic 64-byte limit does not guarantee that every such pattern can be expressed in one invocation: contiguous HEX for 64 bytes requires 128 hex characters before any other arguments, already exceeding the command-tail limit. Space-separated bytes require still more characters. Test the actual command-tail budget, not an assumed 64-byte HEX command-line capability.

Reject an empty pattern. Apply the 64-byte limit to each **enabled** interpretation. The literal TEXT pattern may contain at most 64 bytes when TEXT is enabled. A valid hexadecimal interpretation of a TEXT pattern of at most 64 characters can decode to at most 32 bytes, so it cannot independently overflow the 64-byte HEX limit. When `/NOTEXT` disables TEXT, HEX input is still bounded by the command tail and the decoded 64-byte capacity. `/NOHEX` disables HEX parsing and its limits. Never truncate input.

### 3.2 Validation before traversal

Validate the entire invocation before directory traversal or opening a file. Diagnose missing/extra operands, malformed selectors or filenames, unsupported options, invalid combinations, malformed lexical delimiters, exceeded limits and a request with no enabled interpretation. Do not begin a partial search for an invalid invocation.

`/NOHEX /NOTEXT` disables both search interpretations and is invalid. `/NOTEXT` with an invalid HEX pattern is an error. Invalid HEX otherwise produces no diagnostic and does not disable a valid TEXT search. A malformed command or invalid TEXT length is not an invalid-HEX condition that may be silently ignored.

Option names are case-insensitive; repeated identical flags are harmless. Unknown or incompatible options cause a diagnostic before file access. Exact wording follows repository utility conventions.

## 4. Filespec and extended DU selection

SEARCH shall use the shared extended DU/filespec parser and canonical iterator rather than introduce a second selector grammar. The selected domain is drives A–P and users 0–31, represented by a **512-bit / 64-byte bitmap**. This is a syntax domain, not a promise that all locations exist on every target.

```text
filespec        = [scope ':'] filename-pattern
scope           = du-term | compound-list
compound-list   = '[' du-term (',' du-term)* ']'
du-term         = drive [user-number | user-list] | user-number
user-list       = '[' user-item (',' user-item)* ']'
user-item       = user-number | user-range
user-range      = [user-number] '-' [user-number]
drive           = A through P, case-insensitive
user-number     = one or two decimal digits, value 0 through 31
```

Selectors contain no spaces. Leading zeros in valid user numbers are allowed. Ranges include both endpoints; missing lower/upper endpoints mean 0/31. Descending explicit endpoints normalize to their minimum and maximum. Duplicate terms and overlapping ranges form a set and never cause repeated searching.

Examples:

```text
B7:*.TXT
B[3,5-8,11]:*.COM
B[-]:*.*
[A0,B[3-7],D[-]]:*.DAT
[C7,A0,B[9-3],5]:FOO.*
```

Capture caller drive and user once before resolving inheritance. A bare drive inherits the original user; a bare user inherits the original drive. Neither inherits from a preceding selector term. An absent qualifier has the shared parser's current-DU interpretation. Unqualified filespecs use the caller's current DU; do not import WHEREIS-specific global search defaults.

Enumerate selected DUs once each in drive-major, user-minor order. Input order is immaterial. The bitmap uses byte `4*d + floor(u/8)`, bit `u mod 8`, where A has drive index zero.

Reject empty lists/items, trailing commas, unbalanced brackets, users above 31, invalid drives, nested compound lists, nested user lists and retired `[*]` user syntax. Only per-drive user lists may appear inside a compound list. Thus `[A0,B[3-7]]:` is valid and `[[A0,B0],C0]:` is invalid. Clear the bitmap on parse failure and never consume an unsuccessful partial result.

The filename pattern follows the common bounded CP/M 8.3 rules: `?` consumes a field position; terminal star runs fill the rest of that field; characters after a star run within a field are invalid. Name and extension are independent. Content patterns do not use this wildcard interpretation.

Directory extent entries shall not cause duplicate logical-file searches. A logical file is identified by DU plus canonical 8.3 name. Require exactly one filespec. Apply existing shared filename/attribute selection conventions; do not invent a SEARCH-only SYS-file policy. No matching files is a completed zero-file search unless directory access failed. Within-DU ordering follows native directory order, as in DIR /WHEREIS; the shared DU iterator governs location order; exact error-continuation behavior is specified in Section 9.

## 5. TEXT and HEX interpretation

Let `P` be the literal pattern after lexical delimiter handling. TEXT compares the bytes of `P`; it does not hex-decode, interpret backslashes, expand wildcard characters or apply regular expressions.

HEX is eligible only if the entire `P` matches one of these forms, subject to the optional multiple-space extension below:

```text
hex-digit       = '0'..'9' | 'A'..'F' | 'a'..'f'
byte-pair       = hex-digit hex-digit
contiguous-hex  = byte-pair {byte-pair}
spaced-hex      = byte-pair (' ' byte-pair)+
```

This states the approved contiguous-even-digit and space-separated-byte-pair forms. For HEX interpretation, accept contiguous even-length hexadecimal digits or complete byte pairs separated by spaces. Multiple separator spaces may be accepted as a parser convenience provided they do not change literal TEXT interpretation; reject incomplete pairs. No implicit TAB or punctuation separators are required.

No approved HEX prefixes, suffixes, commas, signs, nibble wildcards or mixed token widths exist. For example, `4142` and `41 42` decode to bytes `41h 42h`; `4`, `41 4`, `0x41`, `41,42` and `41H` do not satisfy the specified forms. Hex letter case has no effect on decoding: `4a`, `4A` both mean byte `4Ah`.

| Invocation mode | TEXT | HEX |
| --- | --- | --- |
| Default, valid HEX pattern | Literal P | Decoded P |
| Default, invalid HEX pattern | Literal P | Silently absent |
| `/NOHEX` | Literal P | Disabled |
| `/NOTEXT`, valid HEX pattern | Disabled | Decoded P |
| `/NOTEXT`, invalid HEX pattern | Disabled | Validation error |
| `/NOHEX /NOTEXT` | Disabled | Validation error: no search mode |

TEXT is case-sensitive by default. `/NOCASE` enables case-insensitive TEXT comparison and shall not alter HEX decoding, file bytes, offsets or displayed source text. With `/NOCASE`, fold ASCII `A`–`Z` and `a`–`z` only. High-bit bytes are never folded. `/NOCASE` with `/NOTEXT` is harmless but has no effect on HEX matching.

HEX case-insensitivity refers to pattern notation, not a case-insensitive byte search: bytes `41h` and `61h` remain different in HEX even under `/NOCASE`.

## 6. File representation and streaming matching

Search every byte of every successfully read **128-byte CP/M logical record**, including final-record padding. `1Ah` is ordinary searchable data in both modes, not a TEXT EOF marker. Do not infer a byte length from padding, remove high bits, normalize line endings or translate the input stream.

Maintain matching state across record and extent boundaries. A match beginning near the end of one record and ending in the next counts exactly as if the bytes were contiguous in memory. Never carry partial-match state from one file into another. Only complete patterns wholly contained in successfully read bytes are matches; EOF is not synthetic padding beyond the last record.

Streaming means bounded memory independent of file size and number of matches. A file, all matching lines or a complete match list need not fit in RAM. Independent TEXT and HEX matchers operate on the same unchanged stream. Buffer overlap or incremental automata are implementation choices; record boundaries must be invisible to matching semantics.

Count **all occurrences**, rather than stopping at the first occurrence or counting only displayed rows. To satisfy the ordinary meaning of all occurrences, the acceptance oracle enumerates every possible starting byte, including overlapping matches (for example `AAA` occurs twice in `AAAA`). Count overlapping matches independently: each matching start position is an occurrence.

TEXT line numbers begin at 1. CR/LF is one line break; bare CR or bare LF is also a line break. An unterminated final line is valid. TEXT matching is literal and contiguous: line breaks are never replaced by spaces. For presentation, a match spanning line terminators is attributed to the line containing its first byte; line numbers and counts must remain accurate. HEX matches can cross line boundaries.

## 7. Independent reporting and totals

A TEXT result identifies the file, text line number and matching source line. Display that line once for TEXT even when it contains several occurrences. The TEXT occurrence counter still increases by every match on that line. Do not replace occurrence counts with matching-line counts.

A HEX result identifies the file and the byte offset of the match. It shall be visibly distinguishable from a TEXT result. HEX results use zero-based, eight-digit uppercase hexadecimal byte offsets. Each result identifies the filename and `[HEX]`; TEXT results identify the filename, `[TEXT]`, one-based line number and matching line or bounded excerpt. Exact punctuation may follow existing utility visual conventions.

TEXT and HEX reporting is independent. If both interpretations match the same file or even the same starting byte, retain both results and both occurrence counts. Do not suppress one because the other matched. Files matched counts the union of files with either kind of occurrence, once per logical file.

After the full search, always report these five totals, including zero values:

1. Files searched.
2. Files matched.
3. TEXT matches.
4. HEX matches.
5. Total matches, equal to TEXT matches plus HEX matches.

Disabling a mode gives that mode zero matches; it does not remove the corresponding summary field. Detail suppression does not reduce any count. No-match is a normal completed result when coverage is complete.

Count as **files searched** each logical file successfully opened and subjected to scanning, including empty and partially read files. Count files with any observed match once. Report failures and incomplete coverage separately; never imply a partially read file was completely searched.

TEXT result display shall be bounded in memory. For ordinary lines display the matching line. For lines too long to display or buffer safely, show a bounded excerpt **containing the match**, with an explicit truncation indicator at omitted edges. Match finding and counts must continue across the entire line; a long line does not truncate the search. Rendering must escape or visibly substitute control bytes, preserve the source data unchanged, and count wrapped output rows for paging. The precise excerpt width and punctuation may be set by the implementation's qualified 40/80-column output layout. Do not require unbounded line storage or a whole-file replay framework.

Never emit arbitrary binary control sequences to the terminal as an accidental consequence of reporting a source line. Agree a deterministic visible-byte rendering contract. Rendering must not change searched bytes or occurrence counts.

## 8. Pagination and Ctrl-C

Without `/P`, details stream in the ordinary forward direction. With `/P`, output pauses at forward-only paging prompts. No reverse navigation, redraw history or match index is required.

At a paging prompt:

| Key | Approved action |
| --- | --- |
| Space | Continue forward |
| Enter | Continue forward |
| Ctrl-C (`03h`) | Suppress all subsequent match detail; continue the full search and print final totals |

Ctrl-C is not a request to terminate scanning. Consume the key so it does not remain pending at the caller prompt. Once detail is suppressed, do not show additional paging prompts. Continue every remaining selected file and both enabled matchers, retain complete counts, and emit final totals. Essential error/incomplete-coverage reporting must remain available so totals are not misleading.

Reserve the bottom display row for the paging prompt (23 content rows on a 24-row display). Space and Enter each advance **one page**, not one line. Count actual rendered rows, including wrapped excerpts. The final totals must remain available after display suppression. Prompt wording and unknown-key behavior may follow the shared simple paging convention; no monitor/provider dependency or cursor controls are authorized.

Ctrl-C at a `/P` prompt suppresses detailed output, prints `DISPLAY INTERRUPTED` and `SEARCH CONTINUING...`, then finishes the search and reports totals. Handling Ctrl-C during unpaged streaming must respect ordinary console behavior; it is not permitted to label incomplete coverage as a completed search.

## 9. Errors, incomplete coverage and cleanup

A distinguishable open, directory or read failure shall be diagnosed honestly. Do not call an error EOF, reuse a stale DMA record, fabricate missing bytes, or describe an incomplete scan as exhaustive. Include the affected DU/file and the failed position where available.

Successfully established matches remain valid after an error. Totals from incomplete coverage are observed totals, not complete totals. Print an explicit incomplete-search indication alongside the final accounting whenever SEARCH detects omitted coverage. Zero observed matches after an error must not imply that every selected byte was searched.

Continue elsewhere only where the underlying BDOS behavior and saved enumeration state permit safe recovery. After a recoverable file-open or read error, report the affected file, mark coverage incomplete, and continue with the next selected file when safe. For directory enumeration errors, continue only if the existing iterator can safely resume; otherwise stop the affected traversal and report incomplete coverage. Do not add BIOS interception or a new OS service.

CP/M 2.2 implementations may handle some physical errors by prompts or nonreturning warm boots. SEARCH cannot promise recovery, final totals or caller-state restoration after an external path that never returns. Document observed platform limitations precisely. This exception does not excuse mishandling errors that do return to SEARCH.

Preserve the caller's original drive and user on every SEARCH-handled success, no-match, validation failure, error and suppression/completion path. Save entry SP, provide a private bounded stack, release file/search resources and restore the entry stack before direct return. Avoid intentional warm boot as ordinary cleanup. DMA and directory-enumeration workspace ownership must be documented; do not allow nested file reads to corrupt the directory search state.

No new numeric process exit-status API is specified; ordinary CP/M 2.2 does not supply a portable one.

## 10. CP/M portability, memory and build constraints

Follow repository native Z80 assembly and ZSM4/LINK build conventions. CP/M 2.2 portability here concerns operating-system services; it does not establish an additional Intel 8080 CPU target. Use ordinary CP/M 2.2 BDOS file, user/drive and console services. No new resident service, BDOS/BIOS/CCP change, required RSX, monitor provider or terminal-specific escape sequence is part of SEARCH 1.0.

The extended selector is a utility-side linked parser, not a demand that the CCP expand operands. For a CP/M 2.2 target with fewer supported users or drives than the parser's logical domain, distinguish syntactically valid selections from executable locations. A syntactically valid but unavailable drive/user area must be reported as unavailable; continue other selected locations when safe. Never silently alias, mask or wrap an unsupported user into another area. Platform-specific inability to return from a BDOS/BIOS failure remains an explicit qualification limitation.

Memory use shall be bounded independently of file length, number of occurrences and line length. Account for code, FCBs, directory enumeration state, 64-byte DU bitmap, command-tail copy, enabled patterns, matcher state, record/carry buffers, line reporting, counters and private stack. Ensure command input and file DMA do not overlap live state.

Use offsets and counters wide enough for supported CP/M file positions and aggregate counts. Crossing 64 KiB must not wrap offsets, line numbers or counts. Totals across many files can exceed a single-file range. Measure TPA and executable size during implementation; use counters wide enough for supported files and aggregate occurrences, and diagnose rather than silently wrap on overflow. Do not invent a memory ceiling without measurements.

Build preparation must use authoritative utility metadata for version/revision rather than a separately hard-coded identity. Require reproducible native and host builds and byte comparison under repository practice. No implementation, source edits, metadata entry, build script or distribution-manifest change is authorized or delivered by this specification-only task.

## 11. Illustrative commands and output

The following demonstrate approved semantic outcomes. Exact punctuation and screen layout are subject to the qualified implementation.

### 11.1 Literal TEXT with default HEX eligibility

```text
SEARCH "4142" A0:NOTES.TXT
```

For a fixture whose first line is `4142 AB 4142` followed by CR/LF and nonmatching record padding, the literal TEXT has two occurrences on one line. Decoded HEX `41 42` has one occurrence at byte offset 5:

```text
A0:NOTES.TXT [TEXT] line 1: 4142 AB 4142
A0:NOTES.TXT [HEX] offset 00000005
Files searched: 1
Files matched: 1
Text matches: 2
Hex matches: 1
Total matches: 3
```

Line 1 appears once despite its two TEXT occurrences. Line numbers are one-based and HEX offsets are zero-based, as required.

### 11.2 Mode switches

```text
SEARCH "4142" A0:NOTES.TXT /NOHEX
SEARCH "41 42" A0:NOTES.TXT /NOTEXT
SEARCH "Error" B[3-7]:*.TXT /NOCASE /NOHEX
SEARCH "4a00" [A0,B[-],C[4,7-9]]:*.COM /NOTEXT /P
```

The first searches literal `4142` only. The second searches bytes `41h 42h` only. The third requests case-insensitive literal TEXT using ASCII-only folding. The fourth searches bytes `4Ah 00h`, not `6Ah 00h`, and pages details forward.

```text
SEARCH "hello" A0:NOTES.TXT
```

`hello` is invalid HEX, so default behavior is ordinary literal TEXT search without an invalid-HEX warning. Adding `/NOTEXT` makes that same pattern a validation error before file access.

### 11.3 Suppressed detail and incomplete coverage

After Ctrl-C at a paging prompt, subsequent detail and paging prompts disappear; the illustrative completed summary can still be:

```text
Files searched: 12
Files matched: 4
Text matches: 23
Hex matches: 7
Total matches: 30
```

With a detected read failure, output must clearly qualify coverage, for example:

```text
SEARCH: B7:BAD.DAT: Read error at 00000100
Files searched: 12
Files matched: 4
Text matches: 23
Hex matches: 7
Total matches: 30
Search incomplete; totals cover successfully searched data only.
```

The example reports observed totals and separately identifies incomplete coverage; partially read files are included in files searched as defined in Section 7.

## 12. Validation and test matrix

Tests shall use independently specified byte fixtures and expected occurrences, rather than deriving expectations from SEARCH's matcher. Preserve exact binaries, fixture generation descriptions, media hashes and console transcripts for qualification.

| Area | Required cases and acceptance evidence |
| --- | --- |
| Invocation | Missing and extra operands; unknown switches; malformed delimiters; complete validation before directory/file access; patterns resembling switches and queries remain data. |
| Tail budget | Valid bounded tails at the limit; malformed over-limit declared input handled safely; quotes/options/selectors included in length; no buffer overrun or silent truncation. |
| Pattern limits | 1-byte and 64-byte enabled patterns; 65-byte rejection; independently exercise HEX decoder's 64-byte boundary even though it cannot be fully expressed as a 127-byte invocation. Reject empty patterns. |
| HEX syntax | Upper/lower/mixed hex digits; contiguous even digits; spaced pairs; odd digits, nonhex characters, prefix/suffix notation, mixed-width tokens and separator edge cases. |
| Mode matrix | Every row of Section 5; invalid HEX silent by default; invalid HEX fatal with /NOTEXT; both modes disabled rejected before access; /NOCASE never changes HEX bytes. |
| TEXT | Case-sensitive default; approved folding under /NOCASE; literal punctuation; multiple occurrences on one line; one displayed line and full occurrence count; line endings and unterminated lines. |
| Occurrences | Adjacent occurrences; overlapping occurrences; pattern longer than file; match at first and final available byte positions; no matches fabricated after EOF. |
| Byte representation | 1Ah in middle and final record; final padding searched; NUL and high-bit bytes; CR/LF remain raw HEX bytes; all successfully read record bytes included. |
| Boundaries | Each possible split of a maximum pattern across 128-byte records; extent transitions; positions before/at/after 64 KiB; matcher reset between files. |
| Dual reporting | Both modes match one file; both match the same position where representable under final lexer; each counter independent; file matched once; total equals sum. |
| DU grammar | Bare-drive/user inheritance from captured caller; open and descending ranges; duplicates and overlaps; canonical ordering; all malformed examples in shared specification; no partial traversal on parser failure. |
| File selection | Exact and wildcard 8.3 selection; extent collapse; multiple DUs; same filename in different DUs counted separately; unavailable selections; attributes. |
| Streaming | File larger than available TPA; many files/matches; an extremely long line with a match near its end; no whole-file/match-list allocation; bounded line reporting. |
| Paging | Space and Enter; no backward behavior; Ctrl-C early/middle/last prompt; full remaining scan, identical totals to unsuppressed run, no later detail/prompts and consumed key. |
| Errors | Failed open, directory failure, failure after partial data, failure during line reread if used; no stale-record matches; error distinct from EOF; incomplete coverage visible even after detail suppression. |
| Accounting | Zero selected files; empty files; zero matches; many occurrences per line; partial files; disabled-mode zero; wide counters and approved overflow behavior. |
| Cleanup | Nonzero entry DU restored after each handled path; stack guards and entry SP intact; file/FCB lifecycle correct; DMA/search state safe; no intentional warm boot. |
| Read-only | Media before/after identical; no file writes, attribute changes or allocation operations; observe allowed reads/console activity with instrumentation. |
| Platforms/build | Native ZSM4/LINK and host-build parity; BetterCP/M cpmsim and Model 4 runs; separate stock CP/M 2.2 BDOS qualification; stated TPA minimum and service/console limitations recorded. |

Calculate expected line numbers using the one-based CR/LF, bare-CR and bare-LF rules in Section 6. Do not treat arbitrary behavior of an initial implementation as the acceptance oracle.

## 13. Release acceptance criteria

SEARCH 1.0 is acceptable only when:

1. Implementation-specific presentation and resource choices have been documented and tested without changing approved behavior.
2. Default literal TEXT and eligible HEX searches, all three mode/case switches and independent counts meet Sections 3–7.
3. Full-record semantics, 1Ah treatment, cross-record matching and positions beyond 64 KiB pass independent fixtures.
4. Every matching text line is reported once with its line number; every occurrence contributes to totals including overlaps. HEX results carry correct byte offsets.
5. Extended DU selection conforms to the shared parser grammar and canonical set semantics, with no duplicate file scans from selector overlap or directory extents.
6. Paging is forward-only. Ctrl-C at a paging prompt suppresses remaining detail while preserving full coverage, final totals and essential diagnostics.
7. Detected failures never appear as ordinary EOF or a complete negative result; partial coverage is explicit.
8. Caller state and read-only guarantees pass on all returning paths. Nonreturning platform error limits are recorded without overstating recovery.
9. Bounded memory, long-line handling, stack reserve, minimum TPA, numeric ranges and overflow policy are measured and qualified.
10. Reproducible build parity and required platform execution attach to identified release artifacts; no tests or implementation are claimed by this document alone.

## 14. Implementation details requiring verification

The following are implementation-level details, **not** reopened decisions about the SEARCH design:

- Lexer details for embedded quote bytes and TAB characters in patterns; keep the required quoted, pattern-first syntax.
- Exact punctuation, prompt styling, line-excerpt width and visual substitution for nonprinting bytes; preserve the approved reporting semantics.
- Exact per-target screen dimensions and error recovery limits; do not claim nonreturning BDOS/BIOS failures can be caught.
- Measured minimum TPA, stack reserve, executable footprint and aggregate counter widths.
- `/HELP` and `/VER` integration: use the repository's actual shared query precedence, but never treat a quoted literal `/VER` as a query.

Any implementation choice that materially changes observable behavior must return for maintainer approval before coding.

## 15. Utility identity and integration handoff

Use the repository's current utility metadata and component revision policy when SEARCH is implemented. Do not assign an executable revision or distribution slot in this document. SEARCH 1.0 is a target version, not evidence of a release.

Adopt `/VER` and `/HELP` using existing BetterCP/M metadata and utility-query conventions. Query recognition must respect quoted literal pattern boundaries, so searching for the literal text `/VER` remains possible. Follow `specifications/UTILITY-HELP.md` and `specifications/UTILITY-VERSIONING.md`: exact case-insensitive `/HELP` takes precedence over `/VER`, outside quoted pattern data. Queries ignore other arguments and return before file operations, drive/user inquiry or changes, DMA changes or terminal initialization. COMPARE Section 2.2 still states `/VER` precedence; that older utility-specific wording is inconsistent with the common policy and is not adopted by SEARCH. Identification follows `specifications/COMPONENT-REVISION-TRACKING.md` where it supersedes older build-counter terminology; no revision is assigned by this document.

The implementation handoff shall verify the details in Section 14, audit shared parser and directory enumeration reuse, establish a bounded line-reporting method, freeze memory/counter budgets and then implement against independently prepared fixtures. It shall not change the approved default dual interpretation, full-record model, independent counts, or paging-prompt Ctrl-C semantics to simplify implementation.
