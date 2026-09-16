# Engineering Specification 139: Native System Build

## Status

Implemented. BetterCP/M now supplies an ordered CP/M-native build that creates
all inputs to `SYSBUILD` and produces the canonical `SYSTEM.SYS` artifact.

## Build roles

- ZSM4 and LINK compile and link the individual system modules.
- `RLMBUILD` compares three native CCP links and constructs the versioned CCP
  relocation carrier.
- `RESPACK` composes the fixed-layout, 52-record `RESIDENT.BIN` from its seven
  resident modules.
- `SYSBUILD` combines the eleven package inputs, records the built A: binding,
  creates `SYSTEM.SYS`, and verifies all 161 records.
- `SYSGEN SYSTEM.SYS C:` installs only the reserved system area of a prepared
  destination and verifies it.
- `SYSGEN A: C:` retains the traditional installed-system copy operation.

`BUILD.SUB` deletes stale products, selects the build disk, builds components
in dependency order, removes temporary REL files, invokes `RESPACK`, and then
invokes `SYSBUILD`. The supported entry command is `SUBMIT B:BUILD` from the
booted A: system so BetterCP/M's batch RSX and pending command file remain
available across warm boots.

## Generated symbol snapshot

Some fixed resident modules consume addresses exported by modules built before
them. The source-disk generator first performs one coherent host build, extracts
those addresses, and writes CP/M-compatible `CORE.INC`, `BIOSLINK.INC`,
`DISKLINK.INC`, and `CPXLINK.INC` files to the native build disk. Sources on
that disk are rewritten only where a host include stem exceeds CP/M's 8.3
limit. The snapshot and sources therefore describe the same layout;
mixing generated symbols from another build is unsupported.

## Disk split

The complete current `src/` tree, native tools, license, maps, and build helpers
exceed the 398 usable 2 KiB blocks of the 800K DATA format. The generator now
produces two deterministic images:

- the build disk, containing every input needed by `SUBMIT B:BUILD`; and
- the complete-source disk, containing every non-hidden file under `src/` and
  a path-to-8.3 map.

Both images are independently read back through the CP/M directory parser and
their DMK structures and sector CRCs are verified. The generator also emits
byte-identical raw `.dsk` forms for z80pack, where BetterCP/M accesses them
through its MM 80T DS DATA format definition.
