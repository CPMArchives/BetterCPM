# Private native-reference package evidence

This evidence belongs to the isolated OFF=3 / XTNP Model 4 reference package.
It does not accept a production TCAP profile or allocate the public request ABI.

- `integration-report.json`: source closure, matching build identity, toolchain,
  emulator provenance and the preceding 516 CPU/manager/native-path checks.
- `integration-manifest.json`: resident and required-role artifact hashes.
- `integrated-core.patch`, `manager-context.patch`: generated private source diffs;
  the permanent reservation remains 1 KiB.
- `package-manifest.json`: generated files and complete protected package hashes.
- `configuration-verification.json`, `production-system-build.txt`: the companion
  Model 4 destination-admission fix, two sets of 32 regression cases, and the
  unchanged production resident/overlay sizes.
- `qualification.json`: final full-machine qualification and transcript hashes.
- `transcripts/`: guest screen captures as JSON row arrays, including the source
  workflow, actual installation, installed-system workflow and damaged-media cases.

Reproduce with the commands in the [package report](../../TCAP-Native-Package-Results.md).
Generated executables and disk images remain under `build/`; they are not
committed distribution artifacts. The qualification uses disposable filesystems
already formatted with OFF=3 and does not convert existing OFF=2 disks.

Each transcript preserves all 24 normalized screen rows, including blank rows.
Join its `rows` with newline characters, with no additional final newline, to
reproduce `normalized_screen_sha256` and the workflow hashes in the report.
