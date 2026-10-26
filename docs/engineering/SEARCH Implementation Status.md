# SEARCH implementation and qualification status

**Status:** Runnable SEARCH 1.0 development command, 2026-10-26. Release
qualification and distribution promotion remain separate. The
[engineering specification](SEARCH%20Specification.md) controls the behavior;
the [manual](../user/utilities_manual.md#search-file-content-search) describes
the implemented interface.

## Implemented command

- Bounded, quote-aware pattern-first command parsing, literal-safe query
  recognition, `/HELP` precedence, and complete validation before file access.
  A double quote terminates a pattern; there is no embedded-quote escape. TAB
  is literal inside quotes and separates arguments outside them. Embedded NUL
  and command tails over 127 bytes are rejected without truncation.
- Literal TEXT plus valid contiguous/spaced HEX from the same pattern,
  `/NOHEX`, `/NOTEXT`, ASCII-only `/NOCASE`, and 64 decoded bytes per enabled
  mode. Multiple spaces between HEX pairs are accepted; leading/trailing
  spaces and mixed contiguous/spaced groups are not HEX. Invalid HEX silently
  falls back to enabled TEXT. Empty/no-mode requests are errors.
- Production shared DU/filespec/attribute/FCB components; canonical DU order,
  native directory order within a DU, and one scan per logical filename after
  collapsing qualifying extents. Unqualified scope is the captured caller DU.
- Full logical-record reads, including padding and 1Ah; cross-record/extent
  matching and overlapping occurrences; zero-based eight-digit HEX offsets;
  one-based TEXT attribution with CRLF, bare CR and bare LF line breaks.
- One TEXT report per matching line, chosen by its first occurrence; independent
  HEX reports. All occurrences contribute to counts, including distant matches
  outside a chosen excerpt. Nonprinting bytes use `<HH>` rather than raw
  terminal controls. Canonical filename bytes are also rendered safely.
- Forward-only `/P`: Space and Enter advance a page. Ctrl-C suppresses later
  detail/prompts while full scanning and final summaries continue. Unpaged
  Ctrl-C uses the same display-stop policy, polled at record boundaries as well
  as result boundaries. Essential diagnostics remain visible.
- Eight-byte files-searched, files-matched, TEXT, HEX and combined totals,
  including zero values. Empty/partially read files count as searched; failed
  opens do not. Returning errors identify the location/file and a failing
  offset when available, and mark the summary incomplete. Numeric overflow
  saturates counters and reports an accounting error, never a wrapped total.
- Metadata-owned `SEARCH 1.0 (001-dev)` identification and help, private stack,
  direct return, caller DU restoration and conventional DMA restoration.

`src/utilities/search.mac` supplies the entry/return path. The `search/` modules
separate parser, matcher/state, file traversal and display. Builders create local
development outputs only. Component registration starts SEARCH at revision 001
with development display because no accepted input baseline exists. No existing
component revision, distribution manifest, frozen disk or package was changed.

## Bounded display and traversal choices

The supported simple console profile is 80 columns by 24 rows. Explicit wrapping
at 79 characters avoids automatic terminal-wrap ambiguity; `/P` pauses after
23 rendered content rows, including essential error rows before suppression.
There are no cursor controls or monitor dependencies.
A different geometry/profile is not qualified by these checks.

A TEXT excerpt looks back up to 64 source bytes before its first occurrence
(also retaining a paired CR when the match begins on LF),
then displays at most 192 source bytes, ending at the first line break after the
complete match. A matched terminator remains visible as `<0D>`/`<0A>` and does
not pull an unrelated next line into the result. Ordinary lines of up to 64
bytes are shown in full; omitted edges have explicit `[...]` indicators.
The renderer uses a cloned open FCB and a private record buffer for bounded
random-read lookaround; it restores the engine's DMA before returning. A reread
failure is essential diagnostic output and qualifies the final summary, while
the primary search continues to count every successfully read record.

File I/O can invalidate BDOS directory-search state. The engine restarts and
replays directory enumeration after file operations and checks earlier qualifying
entries to collapse extents. This preserves order with constant storage and no
temporary file/catalog capacity limit, at a quadratic directory-work cost.
Earlier nonqualifying attribute entries do not hide later qualifying extents.
Concurrent directory mutation is not a snapshot contract.

Function 35 supplies record count only in the FCB; its A return is unspecified
and may be FFh on success. SEARCH does not invent an error status for it. Every
nonzero Function 33 result before the established record count is incomplete
coverage, never stale data or normal completed EOF. Returning user aliases and
drive-selection failures are diagnosed before directory/file access.

Stock BDOS may convert an underlying directory failure to its ordinary FFh
end status, or prompt/warm boot without returning. Such unobservable/nonreturning
paths cannot be reliably diagnosed or recovered by SEARCH. Recorded error tests
cover returning statuses; they do not claim interception of hidden physical
errors. Owned returning paths restore DU, entry stack and DMA to 0080h.

## Resources and identity

The current COM image is **8,044 bytes**, including its fixed buffers, **512-byte
private stack** and **16-byte lower stack guard**. The CPU command suite observed
at most **70 bytes** of that private stack, including the simulated BDOS call
frames; this is not a worst-case physical-BDOS stack measurement. Guard checks
pass on query, invalid-command, result, paging, suppression and error paths.
No allocation grows with file size, line length, match count or directory size.

The image requires 8,044 bytes of TPA payload above 0100h. Execution on a TPA
reduced to that exact minimum has not been qualified. Positions/line tags are
32-bit; aggregate counters and decimal conversion are 64-bit. Both numeric
boundaries and non-silent overflow paths have compiled-code tests.

Current candidate SHA-256:
`a771b4fcf0b0b04133f3c8d54eb3d9917f66b366a11e95d049a51dc32aa77862`.
The full selected input fingerprint and source provenance are local build-report
fields, not embedded Git identifiers or release qualification claims.

## Repeatable checks

```text
python3 tools/build_search.py
python3 tools/test_search_matcher.py
python3 tools/test_search_parser.py
python3 tools/test_search_scan.py
python3 tools/test_search.py
python3 tools/build_native_search.py --verify
python3 tools/test_component_registry.py
python3 tools/component_registry.py --check
```

The matcher/parser/scan tests execute actual assembled Z80 with independent
byte/line oracles and a hostile public-BDOS adapter. The adapter destroys search
state after every file operation, clobbers volatile registers, returns FFh on
successful Function 35, and supplies explicit faults. Coverage includes all 64
maximum-pattern record splits, binary bytes/padding, overlap/dual counts, mixed
line endings, cross-file reset, >64 KiB, shared selectors/predicates, extent
collapse, empty files, error continuation, wide counter saturation and cleanup.

The complete-command suite additionally verifies query paths use console output
only, malformed invocations perform no file/DU/DMA operations, normal and bounded
TEXT excerpts, control escaping, full uint64 decimal output, Enter/Space page
advancement, Ctrl-C display suppression with identical totals, essential errors
after suppression excerpt reread failures without losing primary counts, correct paging of
essential error rows, and unpaged Ctrl-C after the final detail.

The native builder runs ZSM4 4.7/LINK 1.3 under stock CP/M 2.2 in cpmsim and
compares every COM byte with cross output. Its command fixtures verify the full
help screen, a 513-record file spanning several extents with a late match at
byte 65,535, all five totals, and Ctrl-C at a paging prompt. The searched fixture
is read back unchanged. Native and cross program images are byte-identical; the native CP/M file
is padded to logical records, so parity compares the 8,044-byte program image.

`tools/test_search_media.py` stages disposable copies of supplied BetterCP/M
platform images. The cpmsim case passes help/query precedence, combined users
3 and 31, independent TEXT/HEX results, final totals, Ctrl-C continuation and a
whole-disk byte comparison. See `build/search-platform-final-7/cpmsim/` for the local transcript/evidence.

The Model 4 case passes user-31 TEXT/HEX results, caller-user restoration through
SUBMIT, a captured 23-row page plus bottom prompt, Ctrl-C display suppression,
and full totals for all 80 occurrences. The standard M4SCRN/ADM3A startup is used;
SEARCH itself makes only ordinary BDOS calls and does not load or require these
providers. Automated command text through the physical key matrix stalled, so
commands are supplied by startup SUBMIT and only Enter/Ctrl-C are injected.
A small HOLD probe pauses between commands to capture results reliably.
All searched fixture contents are read back unchanged. Whole-disk immutability
is not asserted for this case because startup SUBMIT writes/deletes its own spool.
Local screens and evidence are in `build/search-platform-final-7/model4/`.

| Focused qualification | Result |
| --- | --- |
| Assembled matcher, parser, traversal and complete-command CPU fixtures | PASS |
| Native ZSM4/LINK program-image parity | PASS, 8,044 bytes |
| Stock CP/M 2.2 full command, large file/extents, help and paging stop | PASS |
| BetterCP/M cpmsim users 3/31, results, paging stop, whole disk unchanged | PASS |
| BetterCP/M Model 4 user 31, captured paging/stop, fixture contents unchanged | PASS |
| Complete release acceptance, hidden/nonreturning physical faults, minimum TPA | Not claimed |

## Remaining release work

- Broaden Model 4 scripted and interactive command-entry coverage; the focused
  run verifies startup SUBMIT and the two physical paging keys.
- Broaden actual-platform error/media and large-directory performance evidence;
  CPU fault simulation alone does not qualify physical failures.
- Qualify reduced-TPA operation and the full physical-BDOS stack budget before
  declaring a minimum supported TPA or release resource ceiling.
- Review the complete command and qualification evidence, then assign an accepted
  input baseline and decide distribution separately. Current binaries remain
  development artifacts and this work does not merge or publish a release.
