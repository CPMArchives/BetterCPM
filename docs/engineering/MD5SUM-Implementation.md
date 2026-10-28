# MD5SUM 1.0 development implementation

Date: 2026-10-28. Implements the design merged in PR #532 and the maintainer's
subsequent implementation authorization. MD5SUM is an implemented development
candidate, integrated in newly generated paired Utilities images. Model 4
execution and paired release acceptance remain pending. The controlling contract
is [MD5SUM-Specification.md](MD5SUM-Specification.md).

## Source and build

MD5SUM has its own executable, algorithm, command dispatch, conventional list
parser, rendering and reference-candidate routines under `src/utilities/md5sum`.
`tools/build_md5sum.py` composes these with labelled routines from CRCKSUM's
command, traversal, reference streaming, transaction and support modules. It
omits CRC-specific selection, native/historical formatting and discovery tiers.
CRCKSUM's executable sources and behavior are unchanged. The test BDOS model is
also shared, selecting its executable through an optional argument.

The input map records the shared source dependencies. Changes to relevant shared
routines must be reviewed for both utilities. The builder assembles the complete
prepared source; an absent routine boundary is a build failure. Corresponding
source includes the composition tool as well as every source fragment. This
avoids maintaining independent copies of the file engine while leaving the two
user interfaces separate.

```sh
python3 tools/build_md5sum.py
python3 tools/test_md5sum.py
python3 tools/build_native_md5sum.py
```

The registry assigns MD5SUM version 1.0, revision 001. Without a qualified
baseline, identification displays `MD5SUM 1.0 (001-dev)`. The current COM is
18,397 bytes, including fixed working storage and a 512-byte private stack. It
loads at 0100h and ends at 48DDh (exclusive). SHA-256:

```text
dc96564312b1fbf18c0114c295febfea27a521dea369f2358c96f9b533e6f9a4
```

MD5 uses a 64-byte block, sixteen-byte state, four-byte step temporary and
64-bit input-bit count. The rotation/index/constants schedule is generated at
build time; the guest does no floating-point work. Update preserves IX, which
is the shared stream's current byte pointer. File/summary accounting remains
32-bit, and each stored logical record contributes all 128 bytes.

The rest of storage is bounded by the existing 127-byte command-tail grammar:
up to 64 operands, 512 DU identities, fixed reference/record buffers and two
output streams. Directory and list replay avoid fixed entry-count arrays.
Sorting and repeated reference scans trade disk operations for bounded memory.
The parser accepts ordinary starred/two-space entries and reports malformed,
unsupported, embedded-NUL/high-bit, invalid-filename and overlong records.
Reference line numbers include malformed physical lines. Input mode markers
never enable target text conversion.

A checked-in [qualification summary](MD5SUM-Qualification.json) binds these
results to the current binary, native source and cpmsim Utilities image.

## Focused evidence

- 87 compiled command/routine fixtures pass against independent Python hashlib
  results and the hostile BDOS model. They cover RFC examples, split update and
  finalization boundaries, padded/high-bit files, a 65,792-byte stream, bit-length
  carry, queries, command errors, both list entry forms, case/line-ending rules,
  malformed input, duplicate alternatives, missing/unlisted files, local-only
  discovery, 40-column output and simultaneous master/local streams.
- Overwrite Y/N/A, cancellation and injected create/write/close/rename failures
  preserve the old final list. The model clobbers public BDOS scratch registers
  and reuses directory DMA; every command checks caller DU/DMA/stack restoration
  and the untouched bottom stack guard.
- ZSM4/LINK on stock CP/M 2.2 produces a byte-identical COM. Native version/help,
  one-record calculation/list generation and local verification commands pass.
- The packaged BetterCP/M cpmsim campaign runs MD5SUM and ZSM4/LINK from exact
  Utilities B:, builds on disposable C:/D:, and checks native/cross parity. It
  exercises user 31, padded and >64K fixtures, native list generation/checking,
  simultaneous master/local output, a negative digest check and `/40`. Fixture
  bytes and the entire Utilities B: image remain unchanged.
- Host md5sum verifies the exact stored fixture bytes using a two-space/LF
  copy of the conventional list. Only the reference presentation is converted;
  checked target bytes remain unchanged.
- Paired disk construction validates file readback, filesystem integrity and
  the Model 4 DMK/raw round trip. Package tests check MD5SUM's executable/native
  identities, complete corresponding-source closure, pending acceptance and
  refusal of incomplete or mismatched acceptance proofs.
- The reused command harness still passes all 129 CRCKSUM fixtures. Registry
  projections, metadata checks, Python syntax and whitespace checks pass.

Development evidence is written under `build/md5sum-development`:
`HOST-MD5SUM-CHECKS.json`, `NATIVE-MD5SUM-BUILD.LOG` and the packaged campaign's
`evidence.json` and `transcript.txt`. These are development results, not an
assertion that both release platforms passed.

## Candidate disk integration

The collection and Utilities builders include MD5SUM. Prepared native source,
build provenance and a native-build README accompany the shared full source
archive. `--md5sum-acceptance` can bind a separately supplied complete receipt to
the exact executable, native source and paired media; no PASS receipt is created
by the implementation or packaging build.

```sh
python3 tools/build_utilities_disk.py --build --output build/md5sum-utilities-candidate
python3 tools/test_md5sum_distribution.py --package build/md5sum-utilities-candidate
python3 tools/test_md5sum_media.py \
  --image-dir /path/to/BetterCPM/build/z80pack \
  --utilities build/md5sum-utilities-candidate \
  --report build/md5sum-development/packaged-cpmsim
```

The 26-file primary 332K candidate allocates 18K to MD5SUM and has 2K free.
The Model 4 primary uses the existing 800K data format. NOAH remains on its
existing companion volume. Use writable target/workspace disks for lists and
native build products; the primary cpmsim Utilities disk has very little spare
capacity. Further additions require another capacity assessment.

## Remaining qualification

Model 4 execution is pending, including native linking, actual console display,
large-file processing, local lists and input/state preservation on that target.
The earlier CRCKSUM-only waiver is not applied to MD5SUM. No automatic GUI run
was attempted in the previously unreliable trs80gp environment, and no Model 4
runtime pass or paired release acceptance is claimed. The prepared native source
can be copied as MD5SUM.MAC to a disposable work disk and built with:

```text
B:ZSM4 MD5SUM=MD5SUM
B:LINK MD5SUM[A]
```

A minimal manual one-record check uses the existing A31:FIX.DAT fixture:

```text
B:MD5SUM /VER
B:MD5SUM /HELP
B:MD5SUM A31:FIX.DAT /LOCAL=MD5SUM.LST
B:MD5SUM /CHECK A31:FIX.DAT
B:MD5SUM A31:FIX.DAT /40
```

Expected digest: `b42a83d49df3489b2324811d5ed28d76`. This short check alone
would not complete the full Model 4 campaign. Stack guards are not a physical
interrupt worst-case stack proof; maximum directory sizes and all 512 DUs have
not been exhaustively run on hardware. No qualified baseline, frozen disk
release or whole-disk acceptance is promoted here.
