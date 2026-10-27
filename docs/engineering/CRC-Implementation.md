# CRC 1.0 development implementation

Date: 2026-10-27. Implements the interface approved in PR #528. This is a
development candidate, not a Utilities Disk release or completed paired-platform
acceptance. CRC is integrated in newly built paired candidate images. The
controlling design is [CRC-Specification.md](CRC-Specification.md).

## Source and build

`src/utilities/crc.mac` composes modules for command validation, sorted DU
traversal, four streaming accumulators, display, reference parsing and output
transactions. The builder reuses the existing shared DU/filespec/attribute parser
and RCP FCB builder. The component registry assigns CRC 1.0 revision 001; without
a qualified baseline the displayed identity remains `CRC 1.0 (001-dev)`.

```sh
python3 tools/build_crc.py
python3 tools/test_crc.py
python3 tools/build_native_crc.py
```

The collection and Utilities Disk builders include CRC. `build/utilities/CRC.COM`, the prepared
`CRC-NATIVE.MAC`, native-source hash record and component build report are
development outputs. No release disk image, manifest, acceptance receipt or
qualified baseline is promoted by this change. The package carries CRC's native
source and build provenance alongside the existing full corresponding-source
archive. Its input closure is checked against that archive. The 25-file 332K
candidate retains 20K free after allocating 22K to CRC. The Model 4 candidate
uses the existing 800K data format.

The current COM image has SHA-256
`039a91f2ce19a233162d92321a9171e1a7a45f744afc1425c7e32a19ded595bb`.
It occupies 21,508 bytes, including private data and its
512-byte stack; it loads at 0100h and ends at 5504h. Storage is bounded by
the 127-byte command tail: at most 64 operand tokens, 512 selected DUs, 64
active filename patterns, fixed line/record buffers and two output streams.
There is no fixed directory-entry or reference-entry array. Alphabetical
directory replay and repeated reference passes trade additional disk operations
for bounded memory. Files are streamed through 128-byte records. Record counts
and totals use 32-bit arithmetic; BDOS size queries supply the public CP/M
24-bit logical-record value.

Master/local destinations use separate temporary files and unused recovery
names. Existing final files remain intact until the temporary is closed. Failed
promotion restores the old name where possible; failed recovery reports the
recovery filename. This handles reported failures, not sudden power loss.

## Focused results

- 84 compiled routine and command fixtures pass. They cover the independent algorithm vectors,
  all four defaults/subsets, queries before DU services, shared selectors,
  overlapping operands, sorting, fixed-column native lists, reordered algorithm
  columns, blank extensions, legacy bytes, repeated sections and duplicate
  candidates, rounded sizes, discovery/locality, and simultaneous output.
- Injected create/write/rename/recovery errors, cancellation and overwrite
  choices preserve the previous final list or identify its surviving backup.
  A simulated size change rejects publication; a five-digit preflight count
  expands RECS. Incompatible reference sizes reject before target data reads.
  Hostile BDOS fixtures clobber scratch registers and reuse DMA. Caller state
  and an untouched bottom stack guard are checked on every fixture.
- The original survey corpus parses successfully: 139 original SIG/M
  catalogs/lists, 1,944 checksum-bearing entries. Pre-CRC catalogs contribute
  no checksum entries. Volume 51's CRC-before-size ordering is accepted as well
  as the usual size-before-CRC form. Volume 310 yields `136B` and `B06D`.
- ZSM4/LINK under stock CP/M 2.2 produces a byte-identical COM. Native query,
  generate and check commands pass. The original SIG/M CRC 5.0 executable
  successfully verifies a `/LEGACY` list produced by the new CRC.
- Disposable BetterCP/M full-RAM cpmsim media pass calculation and verification
  of both real Volume 310 LBR files, including all four specified anchor values;
  original catalog verification; a 65,792-byte/high-bit fixture crossing 64 KiB;
  native and legacy list round trips; user 31 selection; and unchanged input
  payloads.

Reproduce historical checks with independently obtained original archive files:

```sh
python3 tools/test_crc_history.py --corpus /path/to/original-sigm-survey
python3 tools/build_native_crc.py --legacy-reader /path/to/vol310/CRC.COM
python3 tools/test_crc_media.py \
  --image-dir /path/to/BetterCPM/build/z80pack \
  --model4-image /path/to/BetterCPM-System.dmk \
  --historical-volume /path/to/vol310 \
  --report build/crc-media-checks
```

The corpus directory contains `sigmvNNN` subdirectories. The Volume 310
directory supplies `-CATALOG.310`, `ZMD146.LBR` and `ZMDOVL2.LBR`. Historical
material is not fetched or modified by these tests. Reports record sample
SHA-256 identities. Reconstructed `-CATALOG.ALL` is not a substitute.

## Remaining qualification

Model 4 execution was attempted using the existing disposable-media harness.
LaunchServices failed before emulator startup (`kLSNoExecutableErr`); direct
launch aborted before boot. Therefore **no Model 4 runtime pass is claimed**.
The checked-in media test includes the Model 4 historical-anchor, large-file,
legacy-list and user-31 fixtures for execution in a working emulator session.

Subsequent candidate-image integration checks pass on cpmsim with CRC and
ZSM4/LINK invoked from the exact Utilities B: image. Native assembly uses
disposable C:/D: workspace, produces a byte-identical CRC, and leaves Utilities
B: unchanged. The package test checks both image inventories, CRC native-source
and executable hashes, the complete corresponding-source closure, and refusal
of incomplete or mismatched acceptance evidence:

```sh
python3 tools/build_utilities_disk.py --build --output build/crc-utilities-candidate
python3 tools/test_crc_distribution.py --package build/crc-utilities-candidate
# Add this to test_crc_media.py's arguments to exercise packaged B: tools:
# --utilities build/crc-utilities-candidate
```

The sandbox's permission policy rejects an out-of-sandbox emulator launch.
Desktop automation briefly connected but then lost window/capture access;
it did not produce a Model 4 execution result. A normal local Terminal session
can run the checked-in media harness without changing the test contract.

Stack guard checks are not a physical-interrupt worst-case stack proof. The
directory replay design has no entry-count truncation, but a maximum-size
physical directory and all 512 DUs were not exercised on hardware. Paired disk
placement, capacity, readback and corresponding-source packaging now pass;
Model 4 runtime and exact paired release acceptance remain pending.
