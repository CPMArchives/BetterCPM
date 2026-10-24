# BYE build-record integration

This increment builds on the selected-input pilot in PR #490. BYE's builder now
writes `build-report.json` beside BYE.COM. It binds the actual artifact size and
SHA-256 to its version/revision, selected input record, assembler hash and the
available repository HEAD. A checkout without Git provenance records null HEAD;
it never invents a source commit or asserts a globally clean working tree.

The builder hashes selected inputs before and after assembly and refuses a
report if they change. It also verifies the returned image against output bytes.
A failed rebuild removes an older report so it cannot appear to certify the
new attempt. As with ordinary builds, callers must not build concurrently into
the same output directory; an isolated output directory is required for each
concurrent build. Reports are build receipts, not execution qualification.

`--baseline FILE` optionally supplies the pilot's raw input-record object. It
does not accept a whole build report, assign a revision or install a publication
baseline. Without a reference the receipt records unknown; an equal explicit
reference records unchanged. Unsupported capture, including checked profiles,
also records unknown while preserving the existing assembler/build path and its
runtime compatibility validation. Capturing an unsupported profile does not
assert complete input provenance. Input changes during an otherwise supported
build instead fail receipt generation.

No executable title/query text, assembler input or numeric assignment changes.
Freshly prepared checked compatibility contracts still include the changed host
builder in their broad input closure; their artifacts are not claimed unchanged
or requalified here. Default BYE bytes are compared against the previous builder.
`-dev` embedding, revision acceptance, native tooling and disk manifests remain
subsequent migration work.

Four integration tests use the real host assembler to check artifact binding,
identical rebuild/reference classification, failed-build receipt removal,
source-race refusal and unsupported-capture fallback. The 20 registry/input
tests and registry projection check remain applicable. No emulator execution
is claimed by these build-record checks.

```sh
python3 tools/test_bye_build_record.py
python3 tools/build_z80pack_bye.py --output /path/to/isolated-output
```
