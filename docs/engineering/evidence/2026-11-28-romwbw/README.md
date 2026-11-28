# RomWBW initial engineering acceptance, 28 November 2026

PASS on macOS ARM64 with the source pins and exact ROM described in the
[port target sheet](../../../../src/platform/romwbw/README.md).

- `result.json`: 15 completed checks, ROM/executable/image/file checksums.
- `session-1.txt`: cold boot, DIR, transient, 140-record file I/O, direct BIOS
  boundary tests, TPA overwrite/WBOOT, ECHO lifecycle and reconstruction.
- `session-2.txt`: a new emulator process sees the generated file and executes
  HELLO. `cpmcp` independently extracted all 17,920 guest file bytes and matched
  every byte to the generated pattern. The 128 KiB system area was unchanged.
- `rejected-geometry.txt`: truncating the candidate to a valid 8 MiB hd1k image
  still lets the ROM loader reach our bootstrap; its capacity check rejects
  the different geometry before BetterCP/M entry.
- `build.json`: prepared layout, private source hashes, component bounds and
  file inventory. Base revision is provenance; private input hashes identify
  the changed engineering sources. No frozen release or published kit is claimed.

Retained text transcripts normalize line endings, trailing whitespace and
workspace paths; the test output directory preserves raw PTY bytes.

All guest checks run with `--strict-io`. The emulator was rebuilt by the pinned
source preparer, rather than taken from an unverified installed executable.
The unchanged shared profiles plus the RomWBW ceiling/floor pass the 11-test
`tools/test_build_profiles.py` suite.

This evidence covers a single fixed hd512 emulator target. CONFIG/SYSGEN/DUP,
full compatibility and utility collections, terminal personalities, alternative
firmware/boards/slices, HBIOS fault injection and release packaging remain work.
Banked RSX execution is a separate future project. Real RomWBW drivers are not
executed by this emulator's C++ HBIOS implementation.
