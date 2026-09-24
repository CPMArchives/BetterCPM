# BetterCP/M build disk

`tools/build_source_disk.py` creates a self-hosting build disk and companion
complete-source volumes. The build disk contains the canonical native source set,
generated link-symbol snapshot, ZSM4, Digital Research LINK, `SUBMIT`,
`RESPACK`, `SYSBUILD`, `SYSGEN`, and build instructions. The source disk
volumes together preserve the complete `src/` tree. All use the Montezuma Micro 80-track,
double-sided DATA geometry: 800 KiB,
512-byte sectors, 2 KiB allocation blocks, 128 directory entries, and no
reserved system tracks.

```sh
python3 tools/build_source_disk.py
```

The generated artifacts are:

- `build/trs80/BetterCPM-Build-80T-DS-800K.dmk` for trs80gp;
- `build/trs80/BetterCPM-Build-80T-DS-800K.img` as a flat logical-sector
  image for cpmtools;
- `build/trs80/BetterCPM-Build-80T-DS-800K.dsk` as the same raw 800K image
  named for direct mounting in z80pack;
- `build/trs80/BetterCPM-Build-80T-DS-800K.json`, which records every source
  mapping and the finished image hash;
- `build/trs80/BetterCPM-Sources-1-80T-DS-800K.dmk` and
  `BetterCPM-Sources-2-80T-DS-800K.dmk`, with matching `.img` and `.dsk`
  forms. The two volumes hold the complete source archive. Each contains the
  same `SOURCES.DOC` map identifying the volume for every source file;
- `build/trs80/diskdefs-build`, a cpmtools definition for the flat image. It
  deliberately presents the image as one 1,600-sector linear track; this
  prevents libdsk from imposing a double-sided track order on data that is
  already in logical order.

The builder searches the compatibility-suite build tools in the two known
local checkout locations. A different tool directory can be supplied with
`--tools`. It reads every file back through a separate CP/M directory parser,
then verifies the complete DMK structure and sector CRCs.

For z80pack, mount a generated `.dsk` file in a raw-image physical drive. In
BetterCP/M CONFIG, define that physical drive as 5-inch, 80-track,
double-sided, then assign the logical drive the `Montezuma Micro 80T DS DATA
(80T, DS, DD, 800K)` format. The `.img` form is in logical order for the
supplied cpmtools definition. The `.dsk` form places each 512-byte sector in
the MM physical order 1,3,5,7,9,2,4,6,8,10 expected by the z80pack mapper.

## Disk organization

CP/M's 8.3 filename limit cannot preserve the source tree paths. All files
reside in user zero. `SOURCES.DOC` records the path represented by every name.
The tree and native toolchain no longer fit together in the 398 usable 2 KiB
blocks, so the reproducible build inputs and complete archive are separate.
The fully commented tree itself now spans two source volumes.

| User | Contents |
|---:|---|
| 0 | Canonical build sources and includes, `BUILD.SUB`, documentation, ZSM4, LINK, and native build tools |

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

The native build disk provides a complete ordered build. Boot the normal system
disk as A:, mount the build disk as B:, and run:

```text
A0>SUBMIT B:BUILD
```

`SUBMIT` and its resident batch service run from A:. `BUILD.SUB` selects B: and
then assembles and links every required component. Generated symbol definitions
are supplied in `CORE.INC`, `BIOSLINK.INC`, `DISKLINK.INC`, and `CPXLINK.INC`;
they are produced by the same coherent host build
that creates the disk, preventing sources and inter-module addresses from being
mixed across builds.

`RLMBUILD.COM` compares native CCP links at BB00h, BC01h, and BD37h and
constructs the versioned `CCP.RLM` with a verified relocation directory.
`RESPACK.COM` constructs the 52-record `RESIDENT.BIN` from `GATEWAY.BIN`,
`BDOS.BIN`, `EXTENS.BIN`, `DISK.BIN`, `BIOS.BIN`, `FILELOAD.BIN`, and
`TABLES.BIN`. `SYSBUILD.COM` then performs the package-level composition and
read-back verification described below.

`SYSBUILD.COM` is the native composer. It reads the standard assembled binary
products from the current drive, checks every component against its assigned
slot, constructs the 20 KiB protected-system payload, records the built A:
binding in a versioned header, and writes and rereads `SYSTEM.SYS`. The package
is 161 records: one metadata record followed by 160 payload records.

The required input names are:

```text
BOOT.BIN     STAGE1.BIN   RESIDENT.BIN CCPRELOD.BIN RSXSEL.BIN
CONFIG.BIN   RSXLOAD.BIN  RSXRESOL.BIN CCP.RLM
```

The host reference composer exports the same products and package with:

```sh
python3 tools/build_system_package.py
```

It also proves that the package payload exactly matches the protected area of
the generated boot disk. Installation is the separate SYSGEN operation, so a
failed composition cannot touch a target disk.

After `SYSTEM.SYS created and verified` appears, prepare the destination with
DUP and CONFIG, then install it without changing the destination filesystem:

```text
B0>SYSGEN SYSTEM.SYS C:
```

Move that disk to the boot drive and cold boot it. `SYSGEN A: C:` remains the
traditional operation that copies an already installed system from A:.
