# COMPARE implementation and qualification

Status: development candidate, COMPARE 1.0 revision 001-dev. Component qualification
and final Utilities Disk acceptance are incomplete. Implementation was authorized
by the maintainer after settling the review points in the engineering specification.

The utility is implemented in native Z80 assembly. It uses the existing single-DU
lexer and exact filename validator, two 128-byte record caches, 32-bit byte offsets
and statistics, and ordinary CP/M 2.2 BDOS services. It has no monitor or screen
backend dependency. The normal utility collection builder includes COMPARE;
release disk builders deliberately do not include it yet.

## Evidence

The [committed evidence summary](COMPARE-Qualification.json) records the executable
hash, test results and explicit qualification limits.

- `python3 tools/build_compare.py`: cross-assembles the executable and records its
  component identity, selected inputs, byte size and hash in
  `build/utilities/COMPARE-build-report.json`.
- `python3 tools/build_native_compare.py`: ZSM4/LINK on disposable stock CP/M
  cpmsim media produces byte-identical executable bytes. Native linker record
  padding is excluded. Transcript: `build/compare-development/NATIVE-COMPARE-BUILD.LOG`.
- `python3 tools/test_compare.py`: runs the actual compiled COM under a hostile
  public-BDOS fixture. An independent oracle checks comparison statistics and
  complete side-by-side rows. Coverage includes command validation, query
  precedence, selected ranges, record/64-KiB boundaries, counters beyond 64 KiB,
  24-bit record-length conversion, same-file and cross-user operands, EOF,
  display limits, every paging key, cancellation, read errors, direct return,
  and caller-state restoration. Results: `build/utilities/compare-tests.json`.
- `python3 tools/test_compare_media.py --image-dir <existing-cpmsim-image-dir>
  --target cpmsim --report <new-evidence-directory>`: disposable BetterCP/M
  execution checks version queries, cross-user comparison, narrow unaligned
  display, Ctrl-C display-stop followed by complete statistics, and whole-disk
  immutability. Current evidence: `build/compare-development/media-cpmsim-final/`.

The BDOS fixture gained support for the real Z80 `SBC A,(HL)` instruction used by
wide subtraction; production code is not patched or bypassed by the tests.

## Remaining qualification

Model 4 runtime testing has not passed. The macOS application launch failed with
LaunchServices error -10827, and a direct trs80gp launch aborted with SIGABRT
before producing guest captures. These are host execution failures, not evidence
of a guest program defect or a successful Model 4 run. The prepared disposable
media and invocation are retained under `build/compare-development/media-model4-*`.
The media test supports `--target model4` and `--model4-image` for resuming this
check with a working emulator.

Focused cpmsim runtime checks and fixture coverage are not a substitute for the
complete platform qualification matrix in §9. In particular, Model 4 execution,
platform console interruption behavior, and final disk packaging/acceptance must
be completed before release promotion.
