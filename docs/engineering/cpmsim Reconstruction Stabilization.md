# cpmsim reconstruction stabilization

During the 1.0 release pass, reconstruction into `build/` beneath a Git checkout
compiled successfully but failed the existing geometry-interface assertion in
`test_qualified_cpmsim.py`. `git apply --verbose` reported both runtime patch
paths as skipped: Git had discovered the surrounding BetterCP/M repository and
interpreted the archive directory as a repository subdirectory.

The builder now isolates Git discovery during patch checks and application by
setting `GIT_CEILING_DIRECTORIES` to the private output parent and removing
inherited GIT_DIR, GIT_WORK_TREE and GIT_INDEX_FILE overrides from that operation.
The extracted upstream archive remains standalone. Missing/mismatched patches
still fail normally. This changes emulator reconstruction, not guest binaries
or the patch set.

Validation uses the existing integration campaign with output beneath the
BetterCP/M checkout: reconstruct runtime and qualification profiles, verify all
recorded input and executable hashes, rebuild from a poisoned working tree and
compare executables, execute seven ROM-guard primitives and query the runtime
geometry port for version 2. A build-only receipt from the failed reconstruction
is not runtime evidence. Earlier macOS results have not been reclassified.

Reproduce from the source root, using absolute paths for the probe runner:

```sh
python3 tools/build_qualified_cpmsim.py --source /path/to/z80pack \
  --output "$PWD/build/cpmsim-runtime" --profile runtime
python3 tools/build_qualified_cpmsim.py --source /path/to/z80pack \
  --output "$PWD/build/cpmsim-qualification" --profile qualification
python3 tools/test_qualified_cpmsim.py --source /path/to/z80pack \
  --runtime "$PWD/build/cpmsim-runtime" \
  --qualification "$PWD/build/cpmsim-qualification" \
  --output "$PWD/build/cpmsim-primitives"
```

Use new output directories. Retain both environment.json files, compiler logs,
probe transcripts and report.json. The primitive campaign does not replace the
final guest conformance pass or fresh-package installation test.
