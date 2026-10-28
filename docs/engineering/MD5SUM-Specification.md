# BetterCP/M MD5SUM.COM Engineering Specification

**Target:** MD5SUM 1.0, BetterCP/M Utilities Disk\
**Status:** Implemented development candidate; native/cross and cpmsim checks pass; Model 4 execution and paired release acceptance pending\
**Date:** 2026-10-28\
**Authority:** Maintainer decisions in the CRC, CHECKSUM and HASH discussion. Implementation was authorized after PR #532 merged. See [implementation and qualification notes](MD5SUM-Implementation.md) for measured results and remaining qualification.

## 1. Purpose and controlling contracts

MD5SUM calculates MD5 file digests, writes conventional md5sum lists, and verifies files against those lists. It replaces the provisional HASH.COM name for this work. MD5 is the sole algorithm; there are no algorithm-selection switches, SHA-256 mode, historical CRC readers or `/LEGACY` option.

Follow [CRCKSUM's specification](CRC-Specification.md) for applicable command, selection, traversal, output-transaction and reporting behavior. The explicit MD5SUM rules below take precedence where the algorithms or formats differ. Do not copy CRCKSUM's native tables, historical-list discovery tiers, size fields or repeated saved headers.

Controlling common contracts are [extended DU syntax](208%20Extended%20DU%20Syntax.md), [utility help](../../specifications/UTILITY-HELP.md), [utility versioning](../../specifications/UTILITY-VERSIONING.md), [component revision tracking](../../specifications/COMPONENT-REVISION-TRACKING.md) and [visual identity](../../specifications/VISUAL-IDENTITY.md). Use existing shared parsing and build conventions; do not create another DU grammar or OS interface.

The target is a streaming Z80 transient using ordinary CP/M 2.2 BDOS services, suitable for BetterCP/M cpmsim and TRS-80 Model 4. Input files and reference lists remain read-only. Archive members, recursive host paths, standard-input hashing, hash-based authentication and automatic file repair are outside scope. MD5 is used for file identification and accidental-corruption checks, not as protection against deliberate collision construction.

## 2. Command contract

```text
MD5SUM [options] [filespec ...] [options]

/FILE=filespec  /LOCAL=filename  /CHECK[=filename]
/40  /HELP  /VER
```

| Option | Required behavior |
| --- | --- |
| `/FILE=filespec` | Write one master list. An explicit single-DU destination is allowed; otherwise use the caller's original logged DU. |
| `/LOCAL=filename` | Write this list name separately in each target DU. Accept only an unqualified filename. |
| `/CHECK` | Verify against MD5SUM.LST in each target DU. |
| `/CHECK=filename` | Verify against this exact unqualified list name in each target DU. |
| `/40` | Fit console presentation within 40 columns; saved lists are unchanged. |
| `/HELP` | Common metadata-only help query. |
| `/VER` | Common metadata-only identification query. |

Option names are case-insensitive; options may precede, separate or follow operands. There is no `/MD5`, `/LEGACY`, text-conversion switch or alternate output-format switch. Unknown options are errors.

No operands means `*.*` in the caller's original logged DU. A bare DU likewise means `*.*` there. Accept multiple filespec operands, wildcards, extended DU sets and user ranges. Query precedence is the common contract: exact `/HELP` or `/VER` ignores other arguments, `/HELP` wins, and the query returns before file access, DU inquiries/changes or DMA changes.

`/FILE=` and `/LOCAL=` may be combined. `/CHECK` cannot be combined with either generation option. Value options require exact legal CP/M 8.3 filenames without wildcards; FILE permits one destination DU, never a DU set. A DU qualifier on LOCAL or CHECK is an explicit error and aborts before operations. Validate every repeated value option; use the last valid value. A later bare `/CHECK` does not erase an earlier explicit reference name. Repeated flag options are harmless.

Privately parse the bounded 127-byte command tail before DMA reads. Reject malformed filespecs, missing option values, incompatible modes and silent truncation before traversal or output creation. Ordinary query precedence is the only exception to complete invocation validation.

## 3. Selection and processing order

Capture the original drive/user once. Omitted selector components inherit the caller's original values, not the previous operand. Use the shared A-P, user 0-31 selection domain and bitmap, wildcard rules and normal system-file selection policy; actual drive availability remains a runtime matter.

Process separate operands in order. Assign a DU to its first encounter; within an extended selector use shared canonical drive/user enumeration. Union selections for that DU and deduplicate overlapping operands and multiple extents. Sort within each DU by canonical eight-character basename, then three-character extension. Process each selected logical file once, regardless of overlapping patterns.

Files with identical names in different DUs remain separate results. DU plus canonical filename identifies a source internally, even though saved entries contain only filenames. Console DU context and diagnostics identify actual locations. No location or directory tree is inferred from saved-list position.

## 4. Stored-byte coverage and length

Hash every byte of every 128-byte logical record through BDOS logical EOF, including embedded `1Ah`, high-bit bytes and final-record padding. Do not strip parity, translate line endings, infer a byte EOF, stop at Ctrl-Z or decompress inputs. An empty logical file hashes the empty byte stream.

Stream files larger than 64 KiB without buffering whole files. Maintain at least 32-bit record and byte accounting, plus MD5's 64-bit bit-length accumulator. Detect operational counter overflow; no silent 16-bit wrap. A BDOS size preflight may detect input-size changes, but md5sum lists contain no expected size. There is no reference-size shortcut comparable to CRCKSUM's RECS/K filtering. Detect disagreement between the preflight record count and streamed count before publishing the result. Same-size concurrent changes are not guaranteed to be detected.

Read each target once for calculation, even when both master and local outputs are requested. Reuse the calculated digest for duplicate reference candidates. Extra directory or list passes are permitted to keep memory bounded.

CP/M record padding is part of the input message. MD5's own final padding is separate internal algorithm processing, never written to the input file or counted as stored records. A host program agrees only when it hashes exactly the same stored bytes. Conventional list syntax alone does not reconcile stripped padding or translated text.

## 5. Exact MD5 algorithm and vectors

Implement MD5 as defined by [RFC 1321](https://www.rfc-editor.org/rfc/rfc1321). Use its full 64-operation compression, constants, word ordering and finalization; do not substitute MD4, truncated MD5 or a configurable variant. Internal words and additions are 32-bit, with addition modulo 2^32. Decode each 64-byte block into little-endian words. Initial numeric state is A=67452301h, B=EFCDAB89h, C=98BADCFEh, D=10325476h.

Finalize with byte 80h, enough zero bytes to reach offset 56 modulo 64, and the original bit length as eight little-endian bytes. Serialize the final A, B, C, D words least-significant byte first. Print those 16 bytes in order as 32 lowercase hexadecimal characters, with leading zeros. Do not print each internal word in ordinary numeric order. No filename or mode marker participates in the digest.

Independent routine vectors:

| Exact input bytes | MD5 |
| --- | --- |
| Empty | `d41d8cd98f00b204e9800998ecf8427e` |
| ASCII `a` | `0cc175b9c0f1b6a831c399e269772661` |
| ASCII `abc` | `900150983cd24fb0d6963f7d28e17f72` |
| ASCII `123456789` | `25f9e794323b453885f5181f1b624d0b` |

Stored-file fixtures, independently calculated with host MD5:

| Exact stored bytes | Records | MD5 |
| --- | --- | --- |
| `123456789` followed by 119 bytes of 1Ah | 1 | `b42a83d49df3489b2324811d5ed28d76` |
| Bytes 00h through FFh, once | 2 | `e2c865db4162bed963bfaa9ef6ac18f0` |
| Bytes 00h through FFh, repeated 257 times | 514 | `c8bdfda91d6d23e412dbbef4b6d40f8b` |

The short routine vectors do not imply arbitrary byte-sized CP/M files. Exercise update boundaries and finalization separately, including message lengths 55, 56, 63, 64 and 65 bytes, as well as the record-sized command fixtures. Follow the algorithm definition rather than RFC 1321's superseded security claims; see [RFC 6151](https://www.rfc-editor.org/rfc/rfc6151) for the later security assessment.

## 6. Conventional saved-list format

Use the conventional untagged [GNU md5sum format](https://www.gnu.org/software/coreutils/manual/html_node/cksum-output-modes.html):

```text
b42a83d49df3489b2324811d5ed28d76 *TEST.DAT
```

Each record is exactly 32 lowercase hex digits, one ASCII space, `*`, then the unqualified canonical uppercase filename. Use an ordinary dot between basename and nonempty extension. Extensionless names have no trailing dot. Do not include FCB padding inside the filename. Terminate each entry with CRLF. Empty input files use the ordinary empty-message digest.

Write no title, column names, separators, size, algorithm label, DU heading, comments or blank section delimiters. Master output is one uninterrupted sequence of the same entries written locally, in traversal order. Identical filenames from different DUs are retained as separate entries. Saved files use ASCII text and CP/M `1Ah` final-record padding. No summary or diagnostic is written into a list.

The reader accepts exactly these two entry forms, with either case of hex digits:

```text
b42a83d49df3489b2324811d5ed28d76 *TEST.DAT
b42a83d49df3489b2324811d5ed28d76  TEST.DAT
```

The second form has two spaces after the digest. Both hash the same complete stored bytes; the input marker does not enable text translation. Accept lowercase filename letters and normalize for CP/M lookup. Accept CRLF or LF and a final complete line without a newline. Stop list text at `1Ah`; this text-reader rule never applies to target data. Ignore blank lines. Require exactly 32 hex digits and the conventional separator/mode positions; do not split the whole line on arbitrary whitespace.

The remainder must be a legal, unqualified CP/M 8.3 filename, without wildcards, embedded whitespace or trailing garbage. Do not strip host directories or DU qualifiers and then guess a target. Tagged `MD5 (name) = ...` output, GNU escaped filenames, NUL-delimited lists, host pathnames and other algorithms are outside the accepted format. Report unsupported or malformed nonblank lines with their reference identity and line number; do not silently skip them. Bounded line buffers must detect overlong lines and drain them safely rather than parse a truncated prefix. A list without a valid digest entry is unusable.

The file bytes of a CP/M list may include trailing 1Ah padding that a host reader does not accept. When necessary, remove only that trailing list padding from the host copy before passing it to host md5sum. Do not remove padding from the target files. A host reader may also require LF line endings or the conventional two-space input marker; converting those list details does not change a digest. Host filename case must also agree with the exported names. The interoperability promise is the ordinary supported entry syntax and identical digest for identical target bytes, not every GNU command-line or filename feature.

## 7. Master/local output and replacement

Follow CRCKSUM's output transaction policy. FILE writes one master and LOCAL one list per target DU. Both may be active, feeding from the same completed target digest. The master concatenates entry streams, with no repeated headers or separators. Local lists remain portable with their files; masters contain no saved source-DU mapping.

Exclude every resolved output identity, existing or newly created, and every transaction file from input selection. Declining replacement does not make an old output list eligible for hashing. Protect source files from explicit output-name collisions before overwrite. If master and local name the same physical file, prompt/open/write once and give that destination the complete master stream; other locals remain local subsets.

Before replacing an existing output, identify its full DU/name:

```text
B3:MD5SUM.LST exists. Overwrite? (Y/n/a)
```

Y or Enter replaces it; N leaves it unchanged and continues other destinations and screen output; A authorizes this and later replacements for this invocation. Accept either case. Ctrl-C cancels. Count declined outputs separately from completed outputs.

Stage output in private temporary files, close and validate before promotion, and preserve old completed lists on handled failure or cancellation. Use established backup/rename recovery; do not promise power-fail atomicity. Name surviving recovery files if restoration fails. Master/local outputs complete independently. A source failure invalidates affected pending lists, including the master; it does not erase completed independent locals. Never install an incomplete master as a complete final list. Continue unaffected DU jobs where possible.

## 8. Local reference discovery and verification

Bare CHECK selects only MD5SUM.LST in each target DU. There are no wildcard name tiers and no search of the caller's original DU as fallback. If absent, report `No MD5 list found` for that DU and continue other targets. CHECK=name selects exactly that name locally. Report the reference chosen. A malformed, unreadable or empty reference does not trigger a different-name search.

Targets, not the option value, select the files being verified. Apply their exact names/wildcards to both existing directory files and reference names. Report selected existing files not listed and selected reference names whose files are missing. Exclude the selected reference itself from wildcard targets; a literal request may check it if a reference entry exists. Files outside the requested pattern are not failures. Malformed list records remain list errors even if some selected files match.

Keep all entries for repeated names. Compare one target digest against every applicable candidate of that name in the selected list. One matching digest verifies the file; identify differing alternatives without declaring that file failed solely because an alternative differs. If none agrees, report MD5 mismatch. Count each physical target once, not once per candidate. Never consult a second list for authority, map anonymous master entries back to source DUs, or require all duplicate alternatives to agree. The user is responsible for distinguishing unrelated versions of identical filenames in a location-free master.

There is no algorithm-selection skip case and no reference-size comparison. A recorded MD5 entry always participates. Missing entries, missing files, read/list errors and a run checking zero files must not be reported as complete success.

## 9. Console, cancellation and outcomes

Normal calculation rows use exactly the saved entry spelling. Identify each active DU separately on the console, as CRCKSUM does, and show full identities in diagnostics. Saved lists contain only entries. Normal console summaries and context mean that console capture is not a substitute for FILE or LOCAL.

A full digest/name entry can exceed 40 columns. With `/40`, show the filename on one line and its intact 32-digit digest on the next; wrap context, prompts and diagnostics within 40 columns. This is only a narrow-screen presentation, not a new saved-list format. No paging, cursor addressing, terminal negotiation or extra P switch is required.

Verification reports one outcome per selected target with enough candidate detail to explain alternatives and mismatches. Distinguish MATCH, MD5 MISMATCH, FILE NOT FOUND, FILE NOT LISTED, READ ERROR, LIST ERROR and missing reference. Identify the reference line where useful. Do not invent SIZE MISMATCH or algorithm-skip reports for size-free MD5 entries.

Print one compact combined summary after all DUs, using CRCKSUM's conventions. For example, `1 file calculated; 1 list written.` or `12 verified; 1 failed; 2 missing; incomplete.` Omit zero secondary counters, unrelated counters, per-DU counter blocks and duplicate success banners. Use correct singular/plural forms. With zero primary results, say `No files calculated` or `No files verified`; zero verification is incomplete. Include nonzero list/DU error and declined-output counts where applicable.

Retain detailed errors beside affected files. Any verification failure, omission or list error prevents aggregate success even if another file matches. Cancellation adds `; cancelled`, closes files, discards uncommitted output, restores caller state and reports incompleteness. Completed independent lists remain completed. Continue independent jobs after recoverable errors; distinguish BDOS read errors from logical EOF. Follow existing machine-readable outcome conventions if present, without inventing a new OS ABI.

## 10. Implementation boundaries and acceptance

Implementation follows this contract; current evidence and limitations are recorded in the linked implementation notes. Source sharing with CRCKSUM is an engineering choice; it must preserve CRCKSUM behavior and must not require architectural consolidation of the executables. Use bounded buffers, private FCBs and stack space; restore caller drive/user, DMA and return state on all handled exits. Do not impose an undocumented directory/reference-entry count limit. Additional passes are preferable to unbounded storage.

On implementation, register MD5SUM's own version/revision, integrate the existing cross/native builders and corresponding-source packaging, and measure executable size, working memory and disk capacity before claiming inclusion. Rebuilding identical source does not advance the revision. The implementation assigns its own registry identity and candidate artifacts; this specification does not itself qualify or promote them.

Focused acceptance must cover:

1. Independent MD5 vectors, split-update/finalization boundaries, empty and padded records, high-bit input, a file over 64 KiB and length carry handling.
2. Actual saved bytes: lowercase digest, one space plus star, canonical dotted/extensionless names, CRLF and list-only padding; no headers, sizes, DU markers or summaries.
3. Both input markers, uppercase digest acceptance, lowercase names, LF/CRLF, final unterminated line, blank lines and safe handling of malformed, unsupported or overlong records.
4. Shared selectors, original-DU inheritance, overlapping patterns, sorted traversal, independent local discovery, no fallback, and rejected CHECK/LOCAL DU qualifiers.
5. Repeated names with equal and differing alternatives, absent/unlisted files, exact target filtering, reference exclusion, errors after matches and zero-file incompleteness.
6. Simultaneous master/local output, one target read, uninterrupted master concatenation, coincident destinations, output exclusions, overwrite Y/N/A, cancellation and injected write/close/rename/recovery failures.
7. Default rows and 40-column console fit, compact summaries, query-before-services behavior and state restoration.
8. Byte-identical native/cross builds and focused runtime checks on cpmsim and Model 4, with actual evidence or explicitly documented qualification disposition. CRCKSUM's waiver is not automatically a qualification waiver for MD5SUM.
9. Host interoperability using the exact stored target bytes and supported entry syntax; remove only list-file padding when the host reader requires it. Recheck Utilities capacity and package readback when integration occurs.

Document measured results and remaining limitations. This specification makes no implementation or release-acceptance claim.
