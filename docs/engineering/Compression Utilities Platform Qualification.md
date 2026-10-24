# Compression Utilities Disk Platform Qualification

## Verdict

**PASS for the six compression command components on both recorded platforms.**
SQ, USQ, CR, UNCR, LZH and UNLZH Build 004 run from private Utilities B:
alongside BetterCP/M System A: on z80pack/cpmsim and trs80gp/Model 4. Each
platform passes 27 round trips, including drive defaults, user area 7, collision
refusal, malformed/checksum cases, cleanup and unchanged source files. Model 4
also retains pre-existing output files through the large SQ/USQ case. Exact
command, System and Utilities image hashes are in the machine-readable record.

The initial Model 4 data-loss finding came from host-side test media preparation.
LibDsk inferred disk geometry from arbitrary CP/M directory bytes when reading
and writing the raw data disk. A large first file made later host operations map
to incorrect sectors. This caused the harness to seed damaged DEFAULT.TXT and
temporary sentinels before the emulator ran. It was not a guest SQ/USQ data
corruption defect. The original failure record remains in the evidence bundle
and is superseded by the corrected run.

The fix pins LibDsk to the disk's explicit PCW 800K geometry. The harness also
reads selected files directly from the raw image using the FDF sector map,
independently of cpmtools/LibDsk, before boot and after execution. A focused
regression reproduces the incorrect physical readback without the geometry pin
and passes for all seeded files with it.

The [machine-readable qualification](Compression-Utilities-Platform-evidence.json)
and [console, VRAM and audit bundle](Compression-Utilities-Platform-evidence.tar.gz)
bind the tested COM files, System and Utilities images, emulator identities,
command captures, seed/output image hashes, file readbacks and geometry
regression. Historical interoperability also passes for these same binaries.
The wider forgiving /HELP and /VER contract is qualified in
[Common Utility Query Qualification](Utility%20Query%20Qualification.md).

| Platform | Commands | Round trips | Result |
| --- | ---: | ---: | --- |
| z80pack/cpmsim | 85 | 27 | PASS |
| trs80gp/Model 4 | 88 | 27 | PASS |

The Model 4 adds a TYPE C:DEFAULT.TXT check immediately before codec queries
and execution. Each Model 4 pair uses private images. The large SQ case copies
the original 70,001-byte source onto C: to avoid repeated drive switching,
renames that copy to SAVED.BIN after encoding, and restores BIG.BIN on C:.
Both copies and the original A: source are checked. The other six regular
fixtures cover empty/binary data, 127/128/129-byte boundaries, a 17,001-byte
extent crossing and the 70,001-byte/64-KiB crossing, with physical CP/M record
padding. Each family adds a logged-drive default case and a user-7 case.

## Release boundary

These are component results for the exact recorded images. The Utilities disk
as a whole remains **PROVISIONAL**. [Native ZSM4/LINK qualification](Compression%20Native%20Build%20Qualification.md)
now passes with identical Build 004 bytes. [Pinned cpmsim reconstruction and
compression requalification](CPMSIM%20Reconstruction%20Qualification.md) also pass.
Remaining Utilities selections, relevant
final-artifact acceptance for other utilities changed by the shared /VER
revision and final whole-image checks remain open. A changed executable or
image requires relevant reacceptance.

## Reproduction

Build isolated System generations with tools/build_distribution.py --target all,
build the six compression commands into the artifacts tree, then run:

```sh
python3 tools/test_codec_utilities_platforms.py \
  --system /private/tmp/codec-system/release-GENERATION \
  --artifacts /private/tmp/codec-build/z80pack \
  --output /private/tmp/codec-platform-campaign
```

Use fresh disposable directories and disks. The campaign requires cpmtools, the
existing local cpmsim and trs80gp executables. Emulator hashes are recorded;
this does not establish a clean pinned cpmsim reconstruction.

The later pinned-runtime receipt passes 86 commands and 27 round trips on the
same System/Utilities images. This original platform receipt remains unchanged;
its local-emulator provenance is superseded by the linked reconstruction record.
