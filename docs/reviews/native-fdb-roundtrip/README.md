# Native FDB round-trip milestone

Review baseline: main `48a1ab71403172956a2b7a82070d8bbb413f85c4`, the merge
of PR #593. This implements only the first implementation stage of
[specification 209](../../engineering/209%20Native%20FDB%20Catalogue%20Workbench.md).
The BetterCP/M 1.0 package freeze remains on hold. No release manifest,
candidate, or synced project reference is changed.

## Reviewable behavior

Build with `python3 tools/build_fdb.py`. The result is `build/fdb/FDB.COM`.
Run these commands inside CP/M, using new destination filenames:

```
FDB DISK.FDB ROUND.FDF
FDB ROUND.FDF ROUND.FDB
```

The extension selects export or compilation. Both directions run natively;
there is no host converter embedded in the executable. Text is streamed in
128-byte records; descriptors and pool objects are kept in bounded memory.
The compiler accepts FDF v1 fields, optional derived BLM/EXM and description,
case-insensitive keywords/enums, comments, decimal/hex numbers, and CRLF/LF.
The initial version statement is `FDF_VERSION 1` with one intervening space.
It supports up to 128 definitions and a bounded pool, with explicit refusal
when workspace is insufficient. This is a command-line foundation, not the
specification's finished session UI.

FDB.COM reuses CONFIG's native framing, CRC, ownership and extension validator
without modifying it. Additional checks cover geometry, DPB masks, directory
allocation, 32-bit capacity calculations, topology and duplicate IDs.
An existing destination is refused. Errors and BREAK attempt to close and
remove a newly created incomplete destination; failure to remove it is reported.
A power interruption can leave a partial new file. There is no replacement
or backup/rename protocol in this milestone.

## Acceptance evidence

| Check | cpmsim | Model 4 / trs80gp |
| --- | --- | --- |
| Native stock binary → FDF → binary | PASS | PASS |
| Host compiler accepts native export and reproduces stock bytes | PASS | PASS |
| Native compiler accepts host-decompiled stock text | PASS | PASS |
| Source DISK.FDB preserved | PASS | PASS |
| Entries | 108 | 108 |
| Stock/rebuilt binary bytes | 8,448 | 8,448 |
| Native exported text, including record padding | 40,576 | 40,576 |

Every stock entry is represented losslessly, including the mixed-sector and
cylinder logical-track definitions. Original and rebuilt binaries have SHA-256:

```
06e2d88e30c38bebe4eaf0975a3e302086874e719109dc3898bb72a0f7ded6a5
```

Both emulators ran the same 9,507-byte executable, SHA-256:

```
f8a4fe79c70161758a5a4c54a9119ef808f8ecff360e3fa5432d941805ccaca4
```

The platform system tracks were freshly built from the baseline above, in
private build directories. Each Model 4 command was cold-booted separately to
prevent matching a previous command's completion text. The JSON evidence
records emulator identities and all output hashes; the three Model 4 screen
captures are retained alongside it. Outputs were extracted from the actual
modified guest disks and compared on the host, rather than inferred from the
success messages.

## Resource use

| Resource | Measurement / bound |
| --- | --- |
| COM size, both targets | 9,507 bytes |
| Required address span | 0100h–C7FFh, 50,944 bytes (49.75 KiB) |
| Standard TPA | 54,272 bytes (53 KiB) |
| TPA margin, both targets | 3,328 bytes (3.25 KiB) |
| Catalogue/pool/validator workspace | 8000h–C7FFh, 18 KiB |
| Private stack | 512 bytes, included in COM image |
| Peak private stack in the instrumented full Z80 core | 32 bytes; 480-byte margin |
| Temporary scratch-disk files | None |
| New round-trip outputs, before filesystem allocation rounding | 49,024 bytes total |

The span is a conservative reservation including the unused gap between the
executable and workspace; it is not a claim that every byte is live data.
The identical fixed addresses establish the TPA bound on both targets. Stack
high-water instrumentation was performed on the independent CPU core, not
inside the two emulator builds.

## Lossless-export refusal

There are no unrepresentable stock formats. For other catalogues, export
refuses unknown required **and optional** TLVs, nonzero minor versions,
noncanonical header/descriptor widths, reordered or noncanonical pool layouts,
redundant uniform mixed-size extensions, empty extension lists, and descriptions
containing a double quote. These may contain bytes that FDF v1 cannot preserve,
or encodings the deterministic host serializer would normalize. Invalid CRCs,
objects, geometry and duplicate IDs are rejected before destination creation.
This conservative policy can refuse an otherwise readable FDB; it never silently
drops extension bytes.

## Reproduce

```
python3 tools/test_fdb_roundtrip.py
python3 tools/test_native_fdb_reader.py
python3 tools/test_fdf_v1_compiler.py
python3 tools/test_fdb_v1_reader.py
```

The focused 37-case test executes the assembled COM on the independent full
Z80 core with register-clobbering, record-level BDOS. It includes stock cross
checks, malformed values, duplicate fields and identities, geometry and capacity
failures, unknown optional/required extensions, collisions, open/read/make/write/
close failures, cancellation, cleanup failure, both semantic TLVs in one format,
and a 255-sector mixed-size list.

For platform runs, prepare isolated current-main platform builds using the
existing complete-system builder and the cpmsim system-tracks builder. Then:

```
python3 tools/qualify_fdb_roundtrip.py --target z80pack \
  --build-root BUILD_ROOT --output NEW_OUTPUT --simulator CPMSIM
python3 tools/qualify_fdb_roundtrip.py --target trs80gp \
  --build-root BUILD_ROOT --output NEW_OUTPUT
```

The qualifier constructs a small private filesystem around the supplied system
tracks. It never modifies the build tree or existing release media. Use a fresh
output directory. On macOS, launch through the repository's LaunchServices
wrapper or set `BETTERCPM_TRS80GP_DIRECT=1` from a permitted application context.

The existing unrelated `test_fdf_workflow.py` was also attempted, but its probe
assembly fails because it leaves `INCLUDE disk/fdbread.inc` unresolved in its
temporary directory. That live disk-format workflow is not counted as a pass.
The shared native reader and host compiler/reader regression tests pass.

## Next stages, unchanged from specification 209

1. Introduce separate working-catalogue and working-format objects, including
   modified state, default filename, import staging, duplicate resolution and
   preservation of unrelated destination entries. Use file backing if required
   to lift the initial in-memory catalogue limit.
2. Implement validation, temporary-file readback and a recoverable CP/M
   backup/rename protocol before enabling replacement or the S/O workflows.
   Exercise disk-full and interrupted replacement against actual files.
3. Reuse CONFIG's editor conventions and validated binding operation for the
   three-page editor and B–D drive workflow; preserve A and cold-boot defaults.
4. Add the specified inspection/comparison pages, one/whole-catalogue exchange,
   pending-work prompts and the remaining acceptance gates, including the 109th
   definition selected by CONFIG and read through its drive binding.

Do not add this milestone to the six 1.0 candidates or unfreeze packaging.
