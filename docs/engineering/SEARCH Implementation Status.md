# SEARCH implementation status

**Status:** Initial streaming-core increment, 2026-10-26. No runnable SEARCH.COM,
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

The core uses 571 bytes of code and 482 bytes of fixed storage (1,053 total in
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
stock CP/M 2.2 in cpmsim, then compares all 1,053 bytes with cross output at the
same origin. It stages copies of disks in a temporary directory. Logs and
binaries are local development outputs under `build/search-core/`; they are not
release artifacts. This checks native toolchain compatibility, not execution of
a complete SEARCH command on cpmsim or the Model 4.

## Remaining implementation

1. Bounded, quote-aware command-tail lexer, literal-safe `/HELP` and `/VER`
   dispatch, and complete invocation validation before file access. Freeze the
   embedded-quote/TAB rules before exposing a command interface.
2. Reuse shared DU/filespec/attribute selection and directory enumeration.
   Collapse extents, preserve enumeration state across file reads, and diagnose
   unavailable locations without aliasing user areas.
3. Read complete logical records, distinguish EOF from returning failures, and
   continue safely where possible. Restore caller DU, DMA and stack.
4. Add bounded line/excerpt rendering and independent HEX reporting. Document
   which excerpt is chosen for distant occurrences on one line while retaining
   one TEXT report per matching line and counting all occurrences.
5. Add forward-only paging and Ctrl-C display suppression with continued scan.
   Resolve unpaged Ctrl-C behavior without implying incomplete scans completed.
6. Maintain wide aggregate totals with explicit overflow handling, including
   empty/partially read files and honest incomplete-coverage summaries.
7. Integrate component metadata/builds only with the runnable utility; establish
   full resource budgets and native/cross parity, then qualify end-to-end BDOS,
   console and Model 4 behavior. No distribution changes are made here.

The common `/HELP` precedence governs SEARCH. COMPARE's older contradictory
wording remains outside this increment. The current CCP uppercases command
input, so exact lower-case bytes must ultimately be supplied through HEX-only
mode on that CCP; `/NOCASE` is appropriate for ASCII text independent of case.
