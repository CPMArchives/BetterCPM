# Altair Z80 / Tarbell installation

This platform uses BetterCP/M 1.3 from the shared codebase. It requires a Z80,
64 KiB flat RAM, an 88-2SIO channel A console and a Tarbell 1011D single-density
controller. Qualification covers the pinned serial-only z80pack emulator.
Physical Altair hardware, 8080 operation and other controllers remain unvalidated.

## Media and drives

| Volume | Mount | Use |
| --- | --- | --- |
| System | A | Boot, configuration, installation and ordinary commands |
| Work | B | Writable files; create with the supplied preparation tool |
| Utilities-1 | C initially | HELP, FDB, NOAH and ANSI/ADM3A modules |
| Utilities-2 | D initially | Additional commands, analysis and development tools |
| Utilities-3 | Swap into C or D | Remaining tools and VT52 module |

Every image is a 256,256-byte raw image with 77 tracks, 26 sectors per track,
128-byte sectors, IDs 1–26 and no skew. ALTRB77 reserves eight tracks. Its 224
one-KiB allocation blocks include two directory blocks; there are 64 directory
entries. The final two physical records are outside the allocation area.
Do not use cpmsim's disk geometry or a historical Altair CP/M image definition.

The supplied cpmtools `diskdefs` presents the same byte layout as 2,002 logical
one-record tracks with 208 reserved records. This avoids LibDsk rounding 77
physical tracks down to 76. Use `cpmcp -T raw -f bettercpm-altair ...` from the
folder containing this diskdefs. No on-disk geometry is changed by this host view.

## Build and start offline

The matching Source archive contains the scripts, selected source manifest,
licenses and pinned upstream emulator/assembler sources. Python 3.9+, a C
compiler and make are required. The media builder additionally uses z80asm 2.1
and cpmtools (`cpmcp`, `cpmls`, `fsck.cpm`).

From the extracted source root:

```sh
python3 tools/prepare_altair_emulator.py --output build/altair-emulator
```

The default input is the bundled, hash-verified upstream source archive at
`third_party/z80pack/altair-offline.tar.gz`. It contains the required z80pack
sources at commit `91fd28eb04e675c2127df88ed3f40675e15282e2` and the upstream
z80asm source. The preparation script applies the included serial-only changes
and records the resulting binary and patched source hashes. It needs no X11.
Graphics, front panels and auxiliary serial endpoints are absent.

The media package includes the required emulator source and build helper. From
its extracted root, start in a real terminal:

```sh
python3 Run-Altair.py
```

On the first run it builds the pinned serial emulator with the host C compiler
and make. Later runs reuse that executable. A/B working images persist under
`Session`; C/D are copied from the selected immutable Utilities masters at each
launch. Use `--session /path/to/new-session` for an independent environment.
Use `--c Utilities-2 --d Utilities-3` to mount the native development tools,
or `--emulator /path/to/altairsim` to select an already built compatible emulator.
Stop the emulator before opening another process on the same session.

 The emulator command must include `-z -R -M1 -f0`:
Z80 selection, internal Tarbell ROM, full memory and unlimited CPU speed.
The package supplies `system.conf`; console input remains case-sensitive.

The emulator preparation also extracts the pinned assembler source. Build it
with `make -C build/altair-emulator/z80asm`, then use
`make -C build/altair-emulator/z80asm install` to install it in `~/bin`.
Assembler executable hashes are part of the recorded build identity; another
host's compiler may produce a different executable identity and private binding.

To rebuild media from the source archive, install z80asm 2.1 at `~/bin/z80asm`
(or use `--assembler` with the identity-selected binary) and run:

```sh
python3 tools/build_altair.py --release --work build/altair-release
```

Generated images and their file-by-file SHA-256 ledger are in
`build/altair-release/profiles/altair-fullram/altair/build/altair/release`.
The engineering image made without `--release` includes diagnostics; distribute
the manifest-selected release images instead.

## Operation

STARTUP.SUB sets `PATH C0: D0:` and prints the banner. A remains the boot/system
drive; keep it writable because SUBMIT and RSX operations create temporary files.
Change mounted images while the emulator is stopped, then restart. Keep master
images separate from working copies. Overlays and their programs are stored on
the same Utilities volume; keep that volume mounted while the program runs.
Mount Utilities-2 and Utilities-3 together for the ZSM4/LINK toolchain.

The default maximum complete-record COM is 57,344 bytes. `STAT MEM` reports the
live limit. `CONFIG` saves cold-boot settings, including STARTUP, IOBYTE and
HISTORY/MCL/VAR capacity. Optional RSXs and enabled owners have explicit memory
costs. The default console supports ordinary text; `RSX LOAD C:ANSI` enables ANSI
screen clients such as HELP when Utilities-1 is mounted. Unload ANSI to recover
its memory. ADM3A and VT52 serve applications configured for those protocols and render
to the same ANSI host terminal. Keep `sio1_baud_rate 0` for the qualified
synchronous emulator renderer.

`SYSGEN SYSTEM.SYS B:` installs the boot package while preserving the existing
filesystem on matching media. `DUP /FORMAT B:` erases the entire disk, including
reserved tracks; install again afterward if you need a bootable disk.
`DUP /COPY A: B:` overwrites and verifies the complete destination disk.
`DUP /CHECK B:` reads every sector. Confirm destructive prompts only for the
intended disposable destination. `BYE` exits with confirmation.

The controller supports this fixed format on A–D. CONFIG can inspect bindings;
setting an identical binding succeeds without changes. Different geometries,
other media sizes, optional boot-surface services and double density are not
supported. The console has one physical serial channel; IOBYTE aliases retain
the documented BIOS routing, reader EOF and punch sink behavior.

## Evidence

The [Altair release ledger](../releases/ALTAIR-1.3-READINESS.md) distinguishes
executed platform checks, reused shared-core evidence and remaining publication
gates. Existing published platform assets remain unchanged.
