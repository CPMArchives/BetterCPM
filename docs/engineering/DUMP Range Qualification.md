# DUMP exact range qualification — revision 006

DUMP 1.0 (006) implements the exact-byte `/FROM=` and maximum-count `/LEN=`
contract in [DUMP Specification](DUMP%20Specification.md), Section 6.1.
The Utilities Manual and `docs/user/DUMP.md` describe the same behavior.
This record supersedes older DUMP evidence only for this candidate; historical
Build 001/002 records and frozen System/Utilities releases remain unchanged.

## Decisions and implementation

- `/LEN=` uses the existing hexadecimal parser: one through eight digits,
  optional H/h suffix, every occurrence validated, last valid value wins.
  `/BARE` rejects it; the historical display loop is unchanged.
- `/FROM=` clips the initial display at the exact byte, retaining aligned
  addresses, columns, separators and ASCII positions in both layouts.
- `/LEN=` defines a fixed interval, starting at the final `/FROM=` or zero,
  ending at the smaller of mathematical start-plus-count and CP/M record EOF.
  Counts past EOF, including addition carry, stop at EOF without wrapping.
  Zero count produces no data reads or viewer, after ordinary file checks.
- In `/P /LEN=`, paging clamps to the interval, Go To must be inside it and
  does not restart the count, and a complete Find match must fit within it.
  Existing boundary messages denote range boundaries. Without `/LEN=`, `/FROM=`
  remains an initial position and navigation can still access the whole file.
  Go To and Find retain their existing containing-row display.
- Candidate lower bounds are staged with page bytes and committed only on a
  successful read. Failed movement preserves the page and continuation state.
  Excluded cells do not read uninitialized buffer contents or issue byte reads;
  the underlying BDOS record cache still reads whole 128-byte records.
- Memory stays bounded: existing two 4,064-byte page buffers and 512-byte private
  stack, plus 25 state bytes. No resident/core, DU lexer or shared UI changes.

The program is 14,537 bytes, SHA-256
`3734f5fe0750a52328cc9cf02be502076f0c29f6b7279d0b7789d8596bbf9576`.
Native ZSM4/LINK matches every cross-built byte. The preceding main revision 005
is 14,128 bytes, SHA-256
`e8b8263d528329542f3315f0c223d2fe34c784d7776c8d961240c17256779095`.
The reference and changed candidate were compared at the same identity 005
before assigning 006. Both cross-target input baselines and explicit assignment
receipts are recorded in `metadata/component-baselines.json` and
[DUMP-Range-Revision-Assignment.json](DUMP-Range-Revision-Assignment.json).
Compilation itself does not advance the revision. This identity assignment is
separate from execution qualification.

## Results

- **PASS — compiled enhanced:** 174 cases using the actual Z80 executable,
  hostile public BDOS returns and independent screen cells. Exact full output
  comparisons cover unaligned starts, 0/1-byte counts, both partial row edges,
  row/record/page boundaries, EOF, large counts and addition carry, >64K offsets,
  both layouts, `/P`, fixed range navigation/Go To/Find, malformed and repeated
  options, `/BARE` conflicts and `/VER` precedence. Existing DU, editor, search,
  interruption, transactional failure and direct-return checks also pass.
- **PASS — historical/version:** 19 cases, including differential DRI `/BARE`
  output, 64K wrap, EOF/status behavior, pending-character preservation, direct
  return and current numeric identification. The test's obsolete literal
  `Build nnn` expectation was corrected to the already-shipped numeric format.
- **PASS — native build:** native ZSM4 and LINK under CP/M produce all 14,537
  identical bytes. No cross-only assembly or test-only production path.
- **PASS — cpmsim:** real BDOS streaming, empty/missing files, version and
  cross-user invocation, plus independent pyte screen captures for both layouts,
  paging, Go To, Find and cancellation. New wide-range captures verify partial
  edge rows, range BOF/EOF, Page Up/Down and Go To without changing the count;
  compact-range captures verify two partial rows and cleared following rows.
  The same screen campaign passes with the executable on the packaged Utilities
  disk. Input readback, reference-image immutability and filesystem checks pass.
- **PASS — Model 4:** actual trs80gp with shipped M4SCRN/ADM3A, 17 keyboard/screen
  stages, including both new range layouts and boundary navigation alongside
  existing editing, software cursor, forward/backward Find, physical CLEAR and
  queued-command return checks. The same 17 stages also pass with DUMP loaded
  from the newly packaged native Utilities disk. Input directory/attributes and allocated bytes
  remain unchanged; independent filesystem checks pass.
- **PASS — provisional media:** both Utilities images contain this exact DUMP;
  complete file readback and filesystem checks pass, as does native DMK/raw
  round-trip verification. Other Utilities artifacts are reused from the local
  current build set. This is not full Utilities release acceptance.
- **PASS — metadata:** registry projections, nine registry tests and fourteen
  revision-assignment tests. Both DUMP cross variants select unchanged assigned
  inputs after the explicit baseline update.

Live System input identities are recorded in the machine-readable results.
The Model 4 input is SHA-256
`40e7ddeccf2bc0720179045785ed56fd41658c0ab1d6b957e178fdf1e813f72f`.
These are private test copies; daily disks and running daily emulators were not
used. Initial sandboxed macOS launch attempts failed before guest execution.
The normal application launcher outside that sandbox completed the campaign;
failed attempts are not passing evidence. This is emulated platform evidence,
not physical Model 4 certification. Unsupported physical disk faults are not
claimed; distinguishable read failures are covered by the compiled fixture.

## Reproduction

```text
python3 tools/build_dump.py
python3 tools/test_dump.py
python3 tools/test_dump_enhanced.py
python3 tools/build_native_dump.py
python3 tools/component_registry.py --check
python3 -m unittest discover -s tools -p test_component_registry.py
python3 -m unittest discover -s tools -p test_component_revision.py
python3 tools/test_dump_live.py --baseline <hash-identified-cpmsim-system>
python3 tools/test_dump_view_live.py --baseline <hash-identified-cpmsim-system> --output <fresh-directory>
python3 tools/test_dump_model4.py --image <matching-System.dmk> --output <fresh-directory>
python3 tools/build_utilities_disk.py --output <fresh-utilities-directory>
```

Live viewer tests require `tools/requirements-monitor-tests.txt`. Use the live
runners' `--utilities` option to invoke the candidate from each provisional
Utilities image. The media builder also requires the other selected component
artifacts and source companions; it does not infer their release acceptance.
No outstanding design decision remains for this increment.

## Retained evidence

Machine-readable results: [DUMP-Range-Qualification.json](DUMP-Range-Qualification.json).
The local CP/M project retains `validation-evidence/BetterCPM-DUMP-006-range-evidence.tar.gz`
with SHA-256 `b317bf4dcc0dc71aaebacfc0cf38559fc0394874a7d6c677071a1f67ed292fd3`. All 237 members were reopened and
verified against its manifest. It includes exact cross/native binaries, source,
revision comparison receipts, test reports, both platforms’ captures and provisional
Utilities images. The external qualification prose and archive checksum are not
inputs to the executable or its component baseline.
