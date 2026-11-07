# BetterCP/M 1.1 cpmsim default RAM layout

The normal distribution build selects `cpmsim-fullram` for z80pack, including
when building all targets. The standard System Disk filename is unchanged.
Its checked `SYSTEM.SYS` contains the same reserved tracks, including the
shipped startup command. SYSGEN verifies the destination's RCP.CPX, R3PACK.RSX
and R3CACHE.RSX before installing. The cpmsim Utilities disk carries BATCHIO.RSX
built against the same layout and private component identity.

| Configuration | Maximum loadable COM |
| --- | ---: |
| Shipped startup and unloaded base | 57,344 bytes |
| ANSISCRN | 54,528 bytes |
| ANSISCRN and ADM3A | 53,760 bytes |
| After unloading both | 57,344 bytes |

The earlier checked profile measurement of 54,272 bytes with both providers
predates the [RSX disk cache](RSX-Disk-Cache-Implementation.md). The manager
uses 1,024 bytes. ANSISCRN and ADM3A reserve 1,536 and 512 bytes, respectively,
plus one 256-byte cache bookkeeping page per installed provider.

The checked BIOS uses the four 32-byte directory checksum vectors from the
shipped 1.0.1 disk layout. The separate 48-byte-vector experiment occupies
space used by the checked BIOS. The CCP keeps its full 128-byte runtime stack
allocation. Its checked disk carrier omits the trailing uninitialized stack
storage, so the complete module and its binding fit in the existing 52 records.

## Reproduction

Use the [distribution build instructions](../releases/DISTRIBUTION-BUILD.md)
with a qualified cpmsim binary. The normal System build runs the exact-fit and
one-record-oversize COM cases, warm returns, stateful RSX reconstruction,
carrier rejection, installation, export and recovery. Each generation includes
the transcripts and the measured unloaded, shipped-startup and screen-pair TPA.
The Utilities check uses the unchanged distributed XSUB and BATCHIO on B0 to
supply a submitted input line, unload the provider and recover the unloaded TPA.

```sh
python3 tools/build_distribution.py --target z80pack --work /tmp/bcpm-system --simulator "$simulator"
python3 tools/build_utilities_disk.py --build
python3 tools/qualify_cpmsim_utilities_pair.py --system "$generation/z80pack" \
  --utilities build/utilities-disks/BetterCPM-Utilities-z80pack-332K.dsk \
  --simulator "$simulator" --output /tmp/bcpm-utilities-check
```

For mixed-profile testing, prepare `cpmsim-legacy-checked` with the distribution
builder's `--prepare-profile` option. In that staged tree run
`tools/build_checked_distribution.py` with `BETTERCPM_BUILD_CONTEXT` set to
its absolute `build/profile/context.json` path. Use
`tools/test_checked_cross_profile.py` in each staged tree with the other
tree and its disk as the foreign inputs.

## Qualification on 7 November 2026

The [qualification record](CPMSIM-1.1-DEFAULT.json) identifies the tested source
commit, simulator and SHA-256 sums of the 37-file System Disk, its matching
installation package and the Utilities disk. A second default build using
`--reuse-work` verified and reused the same generation.

The 57,344-byte patterned program ran twice and checked its contents. The
57,472-byte program returned to the prompt without executing. All 23 System
media cases passed, including filesystem preservation on both installation
paths, installed-system boot and exact package export. Six mixed-profile
campaigns passed in each direction. The paired Utilities disk supplied XSUB
and BATCHIO for a submitted Function 10 input test.

The required CCP, transient-entry and BDOS compatibility groups produced
12, 25 and 56 passes respectively, with zero failure or error rows. The
ANSI scroll-region/reverse-video disk-error paths for Ignore and Abort
each used 38 of the 40 BDOS stack bytes. Both returned correctly on ordinary
cpmsim. Two bytes is the smallest margin observed in these workloads.
