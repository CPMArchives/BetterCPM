# BetterCP/M build disk

`tools/build_source_disk.py` creates a companion development disk containing
the complete `src/` tree, ZSM4, Digital Research LINK, and build instructions.
It uses the Montezuma Micro 80-track, double-sided DATA geometry: 800 KiB,
512-byte sectors, 2 KiB allocation blocks, 128 directory entries, and no
reserved system tracks.

```sh
python3 tools/build_source_disk.py
```

The generated artifacts are:

- `build/trs80/BetterCPM-Build-80T-DS-800K.dmk` for trs80gp;
- `build/trs80/BetterCPM-Build-80T-DS-800K.img` as a flat logical-sector
  image for cpmtools;
- `build/trs80/BetterCPM-Build-80T-DS-800K.json`, which records every source
  mapping and the finished image hash;
- `build/trs80/diskdefs-build`, a cpmtools definition for the flat image.

The builder searches the compatibility-suite build tools in the two known
local checkout locations. A different tool directory can be supplied with
`--tools`. It reads every file back through a separate CP/M directory parser,
then verifies the complete DMK structure and sector CRCs.

## Disk organization

CP/M's 8.3 filename limit cannot preserve the source tree paths. All source,
tools, maps, and instructions reside in user zero. Colliding source names are
assigned stable short names and recorded in `SOURCES.DOC`.

| User | Contents |
|---:|---|
| 0 | All sources, `BUILD.DOC`, `SOURCES.DOC`, ZSM4, and LINK |

`SOURCES.DOC` is the canonical path-to-disk-name map. The JSON manifest is
the machine-readable equivalent.

## Building and installing

An ordinary transient can be assembled and linked natively. With the build
disk mounted as B:, ERA is one example:

```text
B0:
B0:ZSM4 B:ERA=B:ERA
B0:LINK B:ERA[A]
```

Building a bootable operating system requires another stage. The separate
linked components must be composed at their assigned offsets into the boot
sector, stage-one loader, packed resident image, reloader, control overlay,
RSX manager, and relocatable CCP carriers. The host build currently performs
that job:

```sh
python3 tools/build_complete_system.py
```

The resulting bootable DMK already has those carriers installed. The current
`SYSGEN.COM` can copy and verify the complete 20 KiB protected system area
from the running A: disk onto a prepared, compatible SYSTEM disk without
altering its CP/M filesystem.

The build is therefore source-complete but not yet fully self-hosting. A
native GENSYS-style composer and a SYSGEN input-image mode are still needed
to turn newly assembled resident components into system tracks entirely
under BetterCP/M. Until those exist, use the host composer to make the first
boot disk and SYSGEN to install or duplicate that built system.
