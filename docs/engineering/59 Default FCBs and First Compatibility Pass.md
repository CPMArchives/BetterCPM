# Engineering Specification 59: Default FCBs and First Compatibility Pass

## Milestone

BetterCP/M now constructs ordinary first and second default FCBs for transient
arguments, installs arbitrary multi-extent CP/M files in generated DMKs, and
runs the independent CP/M 2.2 Compatibility Suite's `ENTRYTST.COM` plus the
original Montezuma Micro `MDIR.COM` under `trs80gp`.

## Default FCBs

Before transient entry, the CCP clears page zero `005Ch` through `007Fh` and
parses the first two space-separated operands into drive-zero, uppercase,
space-padded 8.3 FCBs at `005Ch` and `006Ch`. The second FCB intentionally ends
before the command tail at `0080h`.

This increment establishes ordinary 8.3 operands. Drive prefixes and CP/M
wildcard expansion remain required follow-up work and are reported honestly by
the selected `ENTRYTST` procedures rather than claimed complete.

Patch history: the first argument-bearing loader rejected every command because
the `CP ' '` zero flag survived a subsequent `LD A,C`; the empty-name branch
therefore saw stale Z even though A held a nonzero length. An explicit `OR A`
now tests the restored length. Focused tests retain both `HELLO WORLD` and the
eight-character boundary `MINRET22 X`.

## General disk installation

`build_trs80_boot.py` now accepts repeatable `--include` inputs and installs
arbitrary user-zero files with 2K blocks, 16-bit allocation entries, and as many
128-record extents as required. `build_compatibility_disk.py` uses this path to
install `ENTRYTST.COM` and `MDIR.COM` without changing the small standard disk.
Independent recovery from the resulting DMK proved `ENTRYTST.COM` byte-identical
at 16,768 bytes.

## First compatibility evidence

`ENTRYTST /VER` runs and reports `ENTRYTST 0.1.0-dev16`. The first visible SAFE
block reports ten passes and no failures:

- program entry and TPA lower boundary at `0100h`;
- warm-start and BDOS page-zero vectors;
- IOBYTE location and page-zero gateway roles;
- first-default-FCB address;
- command-tail count and leading separator;
- entry DMA at `0080h` and its required overlap with the command tail.

The first monolithic physical `/SAFE` run filled the 24-row display while the
bring-up console still lacked scrolling. Subsequent output advanced beyond
Model 4 video RAM, so that run is invalid beyond its first visible block; it was
not evidence of a slow or nonreturning test. Individual item `0001` completes
with one pass and zero failures. Engineering Specification 60 corrects the
console boundary before the complete compatibility run is resumed.

## MDIR

The requested `MDIR.COM` was reconstructed from `MMCPM.dmk` using its 16-bit
allocation blocks and Montezuma logical-sector skew. The first physical-order
extraction was deliberately rejected after producing corrupt output. The
correct binary has SHA-256
`6ba323d6b9df4ef903cc8916e231f4d554e11cb01a016483969a4dda8e31488b`.

Running it on BetterCP/M correctly lists `ENTRYTST.COM`, `HELLO.COM`, and
`MDIR.COM`, reports three files occupying 24K, and returns to `A>`.
