# BetterCP/M 1.0.1

This release updates the cpmsim and TRS-80 Model 4 distributions. It preserves
the CP/M 2.2 programming model and existing extension interfaces. Package
version 1.0.1 is separate from individual utility versions and the Core OS 1.0
milestone. Use matching System and Utilities packages from this release.

## Changes

- Resident commands have implementation-specific help and identities, distinct
  from their transient counterparts, with query precedence and malformed-tail
  checks across all nine commands.
- RSX companions can be loaded from explicit drive/user locations. Per-RSX A0
  cache files retain the carrier data needed for later set changes without
  requiring the original disk. Warm boots preserve the loaded chain. The cache
  implementation adds 256 resident bytes per provider compared with the old
  loader; no-RSX TPA is unchanged. Keep R3PACK.RSX and R3CACHE.RSX matched with
  the System image and use writable A0 for cache operations.
- XSUB can load BATCHIO from the Utilities Disk, with submitted input and
  warm-boot reconstruction preserved.
- FDB restores Specification 209's version heading and grouped main menu while
  retaining command mappings, resume and exit decisions. Use its matching
  FDBVIEW.OVL.
- Transient DIR matches lowercase and mixed-case filespecs, including
  `:DIR *.com`, without modifying the caller's command tail.
- cpmsim's generated RAM/ROM launchers check the real host terminal and refuse
  launch below 80 columns or 24 rows, explaining how to enlarge it and retry.
  The fresh-kit instructions use the same standalone guard. This host check
  uses no CP/M memory; redirected automation remains available.
- PIP accepts expanded source drive/user selectors, including multi-user
  source sets, under its documented collision and destination rules.

## Optional format supplement

The System catalogue retains 108 definitions. The Utilities Disk supplies
SUPPDISK.FDF, SUPPDISK.FDB and SUPPDISK.TXT with four additional definitions:
CPC System, CPC Data, PCW 180K and Bondwell 14. Importing all four gives
112 catalogue entries. These use the existing checksum capacity and BIOS layout.

CPC and PCW have cpmsim and Model 4 file-interchange coverage. Bondwell has
passed all nine original-image trials on both backends, with FDF.RSX loaded
first in the Model 4 RSX chain. See the [supplement instructions and scope](../../metadata/supplemental/README.md).
ATONSS, ATONDS and PT2SS are deferred to 1.1 consideration: their larger
checksum tables and BIOS-space allocation are outside this maintenance release.
Physical media and historical boot/application execution are not implied.

## Installation and limits

Preserve original images and run writable copies. Cold boot the new System;
do not combine its protected loader/stream with older RSX runtime files.
The patched cpmsim reconstruction kit and platform installation guides remain
the supported routes. Direct cpmsim invocation bypasses the terminal guard.
The guard checks launch only: keep the window at least 80x24, and after a
shrink, exit the affected utility, enlarge the terminal and restart the utility
to redraw. Smaller-screen rendering and Model 4 40-column behavior are not
changed. The unidentified FDB exit report remains unreproduced.

The six downloads provide separate System packages, Utilities packages, Source
and four-manual Documentation. Component identities, image/member checksums,
source provenance and final package acceptance are recorded separately. The
published 1.0 packages remain unchanged. Unrelated 1.1 work is outside this cut.
