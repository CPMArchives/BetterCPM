# SEARCH implementation status

**Status:** Streaming core, command parser and read-only traversal increments, 2026-10-26. No runnable SEARCH.COM,
release promotion or platform qualification is claimed.

The [SEARCH specification](SEARCH%20Specification.md) remains the authoritative
contract. The [user manual](../user/utilities_manual.md#search-file-content-search)
now describes that contract, with an explicit development notice.

## Implemented increment

`src/utilities/search/matcher.inc` and `state.inc` provide a linked Z80 core:

- Compile enabled literal TEXT and eligible HEX from one bounded literal pattern.
  Validate mode flags, empty input and enabled pattern lengths; disable both
  matchers on configuration failure. Invalid HEX falls back to TEXT by default.
  Accept multiple spaces between HEX byte pairs, but no leading/trailing spaces.
- Fold only ASCII letters for `/NOCASE`; never alter source bytes or HEX values.
- Feed one raw byte at a time, retaining a 64-byte circular history across record
  boundaries. Compare both enabled patterns independently and return every
  overlapping occurrence, including simultaneous TEXT and HEX results.
- Return zero-based 32-bit starting offsets and the one-based line of a TEXT
  match's first byte. CRLF counts once; bare CR and LF count independently.
  A CRLF pair's terminator bytes both belong to the line being ended.
- Reset per-file state explicitly; latch position/line overflow as an error.
  The consumer must report incomplete coverage rather than continue with wrapped
  positions. Successful configuration resets per-file state automatically.

The core uses 601 bytes of code and 483 bytes of fixed storage (1,084 total in
this increment). The ring retains 64 source bytes and 64 four-byte line tags.
Work per byte is bounded by the two pattern lengths, each at most 64. This is
an initial straightforward matcher, not a performance qualification. No stack
budget or minimum TPA for the complete utility has been established.

The core's raw-pattern API accepts at most 127 bytes. The 64-byte decoded HEX
capacity cannot be fully exercised through that API because its spelling alone
would need 128 digits; the largest even HEX input it admits is 126 digits.
A real command has less space because quotes, filespec and options also consume
the command tail. The TEXT capacity is 64 bytes and is exercised in full.

Entry contracts, result masks, register ownership and error codes are documented
at the top of `matcher.inc`. This module has no BDOS calls or output. Its code
and state are linked into a future consumer; it is not an independently tracked
or distributed component.

## Verification

Run:

```text
python3 tools/test_search_matcher.py
python3 tools/build_native_search_core.py
```

The first assembles the actual Z80 code and executes it in the repository CPU
harness. An independent Python oracle checks results and start-line attribution.
Fixtures cover mode failures, preserved literal input, ASCII-only folding,
NUL/1Ah/high-bit data, default independent dual interpretation, overlapping
matches, mixed CR/LF and cross-line patterns, all 64 splits of a maximum-length
pattern at a 128-byte boundary, a stream beyond 64 KiB, reset between files,
32-bit carry/overflow and a storage guard. Feeding stops at actual fixture EOF;
no synthetic final bytes are added.

The second assembles and links the same source with ZSM4 4.7 and LINK 1.3 under
stock CP/M 2.2 in cpmsim, then compares all 1,084 bytes with cross output at the
same origin. It stages copies of disks in a temporary directory. Logs and
binaries are local development outputs under `build/search-core/`; they are not
release artifacts. This checks native toolchain compatibility, not execution of
a complete SEARCH command on cpmsim or the Model 4.

## Command parser and file traversal increment

`parser.inc` adds a bounded, quote-aware parser using the production shared
DU, filespec, attribute and FCB components through `tools/search_source.py`.
It copies the tail before DMA activity, preserves literal quoted bytes, requires
pattern-first order, and accepts switches only before the pattern or after the
filespec. Quoted query names remain data. Unquoted exact `/HELP` takes precedence
over `/VER` and bypasses ordinary operand/option validation with no BDOS calls.
Embedded NUL and a tail over 127 bytes are rejected without truncation.

The lexical profile now specifies that a double quote terminates a pattern, with
no escape for embedded quotes; a TAB inside quotes is literal data, and outside
quotes is an argument separator. Text glued to a closing quote is invalid.
Case normalization applies only to unquoted tokens and `/NOCASE` comparison.

`scan.inc` traverses the selected DU bitmap and shared attribute predicate,
scans each logical filename once, and maintains eight-byte files-searched,
files-matched, TEXT, HEX and total occurrence counters. Events expose file
identity, match offsets/line attribution and errors to a future renderer.
No console renderer or SEARCH.COM front end is provided by these modules.

File reads can invalidate CP/M directory-search state. The engine therefore
restarts directory enumeration after each file operation and replays to the
next physical entry, checking earlier qualifying entries to collapse extents.
This preserves native directory order with constant memory at the cost of
quadratic directory work. Earlier extents excluded by an attribute predicate
do not hide a later qualifying extent. There is no fixed file-catalog capacity
and no temporary disk file. No concurrent-directory snapshot is promised.

The engine opens files read-only, obtains record counts with Function 35 and
reads all complete records with Function 33. It treats any nonzero read result
before the established record count as incomplete coverage, never stale data or
normal completed EOF. Empty and partially read files count as searched; failed
opens do not. Returning open, read, close, directory-status and location failures
raise error events while scanning continues elsewhere when safe. Totals are
observed counts when coverage is incomplete. Numeric overflow saturates counters
and marks coverage incomplete rather than presenting a wrapped small value.

Drive selection and user selection are checked before directory/file access;
a returned unsupported-user alias is reported rather than searched under the
aliased user. Nonreturning BIOS/BDOS media-error paths remain outside control.
A documented directory-end status of FFh cannot expose an underlying error if
the platform itself converts an error into that status. Function 35 has **no
defined A error status**; only its FCB random-record output is used. The native
probe caught and removed an incorrect FFh-as-error assumption, also discussed
in [NOAH LBR Integrity and Extraction](NOAH%20LBR%20Integrity%20and%20Extraction.md).
An unobservable Function 35 failure cannot be diagnosed through an invented
status contract. Returning paths restore caller drive/user and reset DMA to the
conventional 0080h; the eventual front end must provide its own bounded stack.

Additional verification:

```text
python3 tools/test_search_parser.py
python3 tools/test_search_scan.py
python3 tools/build_native_search_core.py --integration --execute
```

The parser suite executes the assembled code with no BDOS adapter, checks
quoted query boundaries and precedence, complete validation, shared DU and
attribute selection, source preservation and the command-tail boundary.
The scan suite uses a hostile public-BDOS adapter that destroys search state on
every file operation and clobbers volatile registers. It verifies native order,
extent deduplication, overlapping selectors, attribute bits, full records and
padding, cross-record matching, empty files, failed opens/reads/closes, returning
location aliases/directory errors, eight-byte carry/saturation and caller/DMA
restoration. It returns FFh on successful Function 35 to prevent regression.

The native command builds a small **qualification probe**, not SEARCH.COM,
with ZSM4/LINK and compares it with the same cross-assembled source. Under stock
CP/M 2.2 in cpmsim it searches a 513-record `B0:FIX.DAT` fixture across multiple directory extents,
checks all five expected totals (1, 1, 3, 1, 4), a match starting at byte 65,535
on line 2, and caller DU, and reports `SEARCH BDOS PASS`.
The fixture is read back unchanged. Probe binaries/logs stay under
`build/search-integration/`; temporary working disks are discarded. This is
one real-BDOS integration case, not full error, multi-DU or Model 4 qualification.

## Remaining implementation

1. Add the SEARCH.COM entry/return path, metadata-owned help/identity, bounded
   private stack and complete resource accounting. No identity or distribution
   slot is assigned by the current library/probe increment.
2. Add bounded line/excerpt rendering and independent HEX reporting. Document
   which excerpt is chosen for distant occurrences on one line while retaining
   one TEXT report per matching line and counting all occurrences.
3. Add forward-only paging and Ctrl-C display suppression with continued scan.
   Resolve unpaged Ctrl-C behavior without implying incomplete scans completed.
4. Render complete/incomplete summaries and essential diagnostics, then verify
   that display suppression cannot affect scanning or aggregate counts.
5. Qualify the complete utility under stock CP/M 2.2 and BetterCP/M, including
   multiple extents/DUs, terminal layouts, error recovery and native Model 4.
   Measure directory-replay performance and complete memory/stack/TPA budgets.
   No distribution changes are made here.

The common `/HELP` precedence governs SEARCH. COMPARE's older contradictory
wording remains outside this increment. The current CCP uppercases command
input, so exact lower-case bytes must ultimately be supplied through HEX-only
mode on that CCP; `/NOCASE` is appropriate for ASCII text independent of case.
