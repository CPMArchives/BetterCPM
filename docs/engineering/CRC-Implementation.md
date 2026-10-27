# CRCKSUM 1.0 development implementation

Date: 2026-10-28. Implements PR #528 plus the subsequent maintainer-approved
CRCKSUM rename and SUM8/SUM16/KERM6/KERM12 additions. This is a
development candidate, not a Utilities Disk release or completed paired-platform
acceptance. CRCKSUM is integrated in newly built paired candidate images. The
controlling design is [CRC-Specification.md](CRC-Specification.md).

## Source and build

`src/utilities/crc.mac` composes modules for command validation, sorted DU
traversal, eight streaming integrity values, display, reference parsing and output
transactions. The builder reuses the existing shared DU/filespec/attribute parser
and RCP FCB builder. The component registry assigns CRCKSUM 1.0 revision 005; without
a qualified baseline the displayed identity remains `CRCKSUM 1.0 (005-dev)`.

```sh
python3 tools/build_crc.py
python3 tools/test_crc.py
python3 tools/build_native_crc.py
```

The collection and Utilities Disk builders include CRCKSUM. `build/utilities/CRCKSUM.COM`, the prepared
`CRCKSUM-NATIVE.MAC`, native-source hash record and component build report are
development outputs. No release disk image, manifest, acceptance receipt or
qualified baseline is promoted by this change. The package carries CRCKSUM's native
source and build provenance alongside the existing full corresponding-source
archive. Its input closure is checked against that archive. The 25-file 332K
candidate retains 20K free after allocating 22K to CRCKSUM. The Model 4 candidate
uses the existing 800K data format.

The current COM image has SHA-256
`d91d9f2b6abf6eecc221271cd94b12fd1aa9d292824ca2475213cd3b2efc36bd`.
It occupies 22,142 bytes, including private data and its
512-byte stack; it loads at 0100h and ends at 577Eh. Storage is bounded by
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

SUM8 and SUM16 are the byte sum modulo 256 and 65536. KERM6 derives the
six-bit Kermit fold from SUM8; KERM12 is SUM16 masked to twelve bits. These
are whole-file numeric values, not packet framing, quoting or printable wire
encoding. The native reader now permits eleven columns, tracks their identities
in two bytes, and accepts the new widths/ranges in any order. The algorithm
selection mask uses all eight bits. Explicit selections append ordered field
descriptors on first occurrence; duplicate switches retain their original
position. Default selection uses canonical order. The same descriptors drive
wide/narrow display, saved lists and verification reports. Earlier four-algorithm lists remain readable;
`/LEGACY` still selects historical CRCK alone.

The public executable and component identity are CRCKSUM. Internal `crc` source
paths, builder entry points, `--crc-acceptance`, receipt schema keys, native list
comment and reference discovery names remain stable. CRC.LST is still the first
automatically discovered reference; the rename does not change user filenames.
Old CRC development evidence does not qualify the changed binary. The manual
Model 4 disks prepared before this extension contain the earlier CRC binary.

The console prints a single compact combined summary, omits zero secondary
counts and per-DU blocks, and retains failure/incomplete/cancellation status.
The unused per-DU snapshot storage is removed. Saved lists and checksum
calculations are unchanged. Revision 003 manual disks remain intact; revision
004 replacements contain the updated B: executable and D: native source.

Revision 005 fixes a console-only `/LEGACY` formatting defect: saved lists already
used historical rows, but the console still rendered a native CRCK table. Both
destinations now use historical rows, including the prefix and double spacing.
Regression assertions cover console-only and saved-list commands with mixed
algorithm switches. The Model 4 waiver remains in effect; no new Model 4 pass
is claimed.

## Focused results

Revision 005 passes the compiled fixtures and native byte-parity/command checks.
The historical corpus and disposable packaged-media results below were recorded
for revision 004; those broader campaigns were not repeated for this display fix.

- 129 compiled routine and command fixtures pass. They cover the independent algorithm vectors,
  all eight defaults/subsets, queries before DU services, shared selectors,
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
  successfully verifies a `/LEGACY` list produced by CRCKSUM.
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

## Qualification disposition

The maintainer explicitly waived the remaining Model 4 validation for PR #529
finalization. This waiver does not constitute a Model 4 pass, a qualified baseline
or paired release acceptance. No acceptance receipt is fabricated or promoted.

Limited manual Model 4 evidence from revision 003 shows version/help output and
generation of a native list with all eight expected values for the one-record
fixture. Native linking reported `NO FILE` and was not completed. The current
revision 004 compact-output build has not completed Model 4 qualification.

Automated Model 4 execution was attempted using the existing disposable-media harness.
LaunchServices failed before emulator startup (`kLSNoExecutableErr`); direct
launch aborted before boot. Therefore **no Model 4 runtime pass is claimed**.
The checked-in media test includes the Model 4 historical-anchor, large-file,
legacy-list and user-31 fixtures for execution in a working emulator session.

Subsequent candidate-image integration checks pass on cpmsim with CRCKSUM and
ZSM4/LINK invoked from the exact Utilities B: image. Native assembly uses
disposable C:/D: workspace, produces a byte-identical CRCKSUM, and leaves Utilities
B: unchanged. The package test checks both image inventories, CRCKSUM native-source
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
The remaining Model 4 runtime checks are waived for this PR; exact paired
release acceptance is not asserted. Fixtures remain available for future testing.
