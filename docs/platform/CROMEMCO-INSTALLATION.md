# BetterCP/M 1.3 — Cromemco Z-1 / z80pack

This platform uses the pinned serial-only z80pack `cromemcosim`, a Z80, bank-zero
64 KiB RAM, the FDC UART and four 8-inch single-sided single-density floppies.
The unloaded maximum COM capacity is **57,344 bytes**. Hard disks, other floppy
geometries, banked services, graphics, auxiliary serial and physical hardware
remain outside this first release. This is an additional platform for OS 1.3.

## Start on an Apple Silicon Mac

1. Extract the entire `BetterCPM-1.3-Cromemco.zip` into a folder of your choice.
2. Open that folder and double-click **Run-Cromemco.command**. The bundled native
   emulator runs without Python, a compiler or a network connection.
3. RDOS loads the system and the BetterCP/M 1.3 — Cromemco banner appears.
   Enter `DIR`, `STAT MEM` or `:VER /BANNER`. Use `BYE /Y` to exit.

The launcher finds its own files regardless of Terminal's starting directory.
On first launch it creates `Session/disks` with System on A, writable Work on B,
Utilities-1 on C and Utilities-2 on D. Subsequent native launches preserve all
four images. Disk changes persist there. `Media` contains the original templates.
Close the emulator before replacing or resetting a session's images. A fresh
session is created by moving the existing Session folder aside and relaunching.

The default startup script runs `PATH C0: D0:` and `:VER /BANNER`. The colon
forces the transient VER.COM, which implements the banner. Cold startup does
not repeat when transients return or after warm boot.

## Utilities and screens

There is one System volume and three Utilities volumes. Keep HELP.COM/HELP.LBR,
FDB.COM/FDBVIEW.OVL and NOAH.COM/NOAH.OVL together. Use `Media/collection.json`
for the exact contents of each volume and its checksums. PATH can find an overlay
only on a disk actually mounted; it does not swap media automatically.

ANSI, ADM3A and VT52 are integrated TCAP 2.0 display modules for the host's
80×24 ANSI-compatible terminal. They use Cromemco's transmit-ready polling and
private BIOS binding. For HELP, load a personality from the mounted utility disk:

```text
RSX LOAD C:ANSI
HELP PIP
RSX UNLOAD ANSI
STAT MEM
```

Unloading restores the unloaded TPA. These modules are optional; basic console
startup leaves the complete 56 KiB TPA available. Do not substitute modules from
another platform or a differently bound build.

To select a different pair of utility volumes, run the Python launcher, for example:

```sh
python3 Run-Cromemco.py --c Utilities-2 --d Utilities-3
```

This preserves A/B and explicitly replaces C/D with the selected templates.
Alternatively, with the emulator stopped, copy a selected template over the
corresponding Session disk image, keeping its drive filename. Reset logged disks
with the appropriate CP/M reset/warm-boot operation after any live media change.

## Rebuild or run without the bundled native executable

Python 3, make and a C99 compiler can build the serial emulator entirely offline.
The source archive includes z80asm and the emulator prerequisites; no graphics,
front-panel, web-server or modem libraries are required. The Python launcher
builds `Host/build/cromemco` automatically when a suitable executable is absent.
Host platforms other than the tested macOS arm64 build require their own host
validation; the emulated machine and disk images remain the same.

From the matching Source archive:

```sh
python3 tools/prepare_cromemco_emulator.py --output build/cromemco-emulator
make -C build/cromemco-emulator/z80asm
```

The default archive and manifest under `third_party/z80pack` pin upstream
`91fd28eb04e675c2127df88ed3f40675e15282e2`. The preparer applies the retained
host serial-input correction, disables optional network listeners and builds
the serial target. RDOS 2.52 firmware and its upstream disassembly accompany
the image; original third-party notices and terms are retained.

The guest builder expects z80asm 2.1 at `~/bin/z80asm` and cpmtools on PATH.
Assembler executable hashes are part of the exact build identity. Rebuild media:

```sh
python3 tools/build_cromemco.py --release --work build/cromemco-release
```

Outputs are under
`build/cromemco-release/profiles/cromemco-fullram/cromemco/build/cromemco/release`.
The exported source has its own explicit source identity and selected-file
manifest; its build must reproduce all four published image hashes.

## Install and qualify

SYSGEN installs the checked SYSTEM.SYS package onto compatible Cromemco media
without replacing its populated filesystem. CONFIG saves supported startup,
IOBYTE and PDS choices; geometry changes outside CRMF77 remain unsupported.
DUP supports the qualified fixed-format erase/check/copy path. A is protected
from formatting. Review destructive-operation prompts before confirming them.

The focused acceptance suite covers installation/cold boot, saved settings,
MCL/VAR/NDR/PATH, disk errors and media resets, all 256 IOBYTE routes, shipped
utility queries, screen/overlay integration, native tools and 269 independent
automatic compatibility assertions. Matching shared-core evidence is reused
only for identical executable bodies. This is not a new 627-card campaign.
See the [release ledger](../releases/CROMEMCO-1.3-READINESS.md).
