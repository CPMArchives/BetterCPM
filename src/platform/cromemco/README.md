# Cromemco Z-1 / z80pack engineering port

Status, 28 November 2026: **qualified emulator candidate; package reproduction and publication are separate gates**.
Built from the common BetterCP/M 1.3 source tree, starting at
`90a766a29fe210b1f4082c8b6449ea4c705813a6`. No separate BDOS or CCP fork.
The initial implementation targets the pinned z80pack Cromemco emulator,
not physical Cromemco hardware.

## Target sheet

| Component | Initial configuration |
| --- | --- |
| Emulator | `cromemcosim`, z80pack `91fd28eb04e675c2127df88ed3f40675e15282e2` |
| CPU | Z80 |
| Memory | Bank zero, 64 KiB; additional banks unused |
| Firmware | Upstream RDOS 2.52 at C000h; loads first sector at 0080h |
| ROM removal | Bootstrap writes 01h to bank-select port 40h |
| Console | FDC UART: status/baud 00h, data 01h, command 02h |
| UART status | Receive-ready bit 6; transmitter-empty bit 7 |
| Controller | 16FDC: command/status 30h, track 31h, sector 32h, data 33h, control 34h; auxiliary 04h |
| Media | Four 8-inch SSSD images, 77 tracks × 26 sectors × 128 bytes |
| Filesystem | CRMF77, identity sector order; eight reserved tracks, 1 KiB blocks, 224 allocation blocks, 64 directory entries |
| Image length | 256,256 bytes |
| Unloaded COM capacity | 57,344 bytes, using the shared `cromemco-fullram` profile |
| Optional services | Basic console; optional integrated ADM3A/VT52/ANSI; no clock provider |

The banked ROM is removed before stage two runs. Hardware diagnostics write
and read 55h and AAh throughout C000h–FFFFh. The OS uses the common checked
command/RSX/package carriers and a distinct private build identity. Cromemco
uses MCON backend bit 16; other platform display modules are rejected. Bound
renderers call CM_TXA, a register/flag-preserving transmit-ready leaf, and the
fixed raw-input vector without monitor recursion.

`boot.mac` is a 128-byte sector assembled at 0080h. The diagnostic form reads
sectors 2–9 to 1000h; the system builder reads sectors 5–8 instead. Stage two
loads the shared resident image from package records 8–59. The common package
layout, reconstruction and RSX machinery remain in use.

`fdc.inc` validates A–D, tracks 0–76 and sectors 1–26 before transfer. It
selects side zero, restores/seeks every request, bounds status polling, and
checks transfer completion/errors. No cpmsim DMA or host filesystem shortcut
implements disk I/O. The disk service stages reads before publishing bytes
to caller DMA. Fixed-format discovery, validation, identical binding setters
and E5 data-track initialization are implemented; geometry changes and
optional physical boot-surface operations return unsupported. A is protected
from formatting.

## Reproduce

Use fresh output directories and a local checkout of the exact z80pack revision:

```sh
python3 tools/prepare_cromemco_emulator.py \
  --source /path/to/z80pack --output build/cromemco-emulator-final
python3 tools/test_cromemco_hardware.py \
  --simulator build/cromemco-emulator-final/cromemcosim/cromemcosim \
  --output build/cromemco-hardware-final
python3 tools/build_cromemco.py --work build/cromemco-engineering
python3 tools/test_cromemco_system.py \
  --image-dir build/cromemco-engineering/profiles/cromemco-fullram/cromemco/build/cromemco \
  --simulator build/cromemco-emulator-final/cromemcosim/cromemcosim \
  --output build/cromemco-system-final
```

The assembler defaults to `~/bin/z80asm`; build identity verifies its hash.
The emulator preparer archives committed sources without changing the user's
checkout. It disables optional web/modem services and auxiliary TCP listeners,
builds without graphics/front-panel libraries, and replaces absent video with
a shim that fails on video access. CPU, memory mapping, ROM and FDC
retain their pinned upstream implementations. The diagnostic shutdown port
is only used to end tests. Firmware is read from the staged upstream ROM folder.
The host HAL serial reader has a targeted correction: its one-byte read uses
a byte-sized object instead of an uninitialized integer. Otherwise valid
keystrokes can be misclassified as negative "no character" results depending
on host stack contents and launch path. `test_cromemco_uart_input.py` reproduces
the original failure with poisoned stack locals and checks the corrected reader.

Launch the engineering image in an interactive terminal:

```sh
./Run-Cromemco.command
```

Or use `tools/launch_cromemco.py` with explicit `--image-dir` and `--simulator`.
Media are writable. `BYE` ends emulation. The emulator's UART is timed, and
the basic CCP redraws the input line; automated input is deliberately paced.
The standalone hardware probe only needs one lowercase `a`.

Cold boot runs `SUBMIT STARTUP`; `STARTUP.SUB` invokes `:VER /BANNER` from
the included VER.COM. The banner identifies BetterCP/M and Cromemco. To show
it again, enter `:VER /BANNER`. The colon forces the transient command; the
resident VER deliberately omits the larger banner feature. Warm boot does
not rerun the startup script.

## Executed checks and next gates

### Deferred feature: WDI-II hard disks

Explicitly deferred by the user on 28 November 2026. Keep the current work
focused on testing the initial floppy-based port. Future work may expose the
emulator's `hd0.hdd`–`hd2.hdd` images through a WDI-II BIOS driver, 512-byte
sector buffering, and suitable logical volume layouts. Begin with floppy boot
and hard-disk data storage; investigate hard-disk boot separately. Preserve the
56 KiB unloaded TPA floor and qualify controller errors and data integrity.
This is not a requirement for the initial testing milestone.

Hardware checks include ROM cold boot, recovered upper 16 KiB, console input
and output, distinct sectors at both ends of A–D, one write/readback per drive,
whole-image equality, invalid addresses, and missing/malformed/read-only B.
Read-only testing requires file permissions to be enforced for the test user.

OS integration checks include cold/warm boot, VER/DIR/STAT MEM, geometry API,
140-record files on B–D crossing extents with independent cpmtools extraction,
destructive transient-area overwrite/reconstruction, ECHO load/call/unload,
56 KiB restoration, preservation of B after warm boot, system tracks/active
files unchanged, and rejection of damaged or foreign command carriers.

Exact results, transcripts and reproduction artifacts are retained under
[`docs/engineering/evidence/cromemco`](../../../docs/engineering/evidence/cromemco).
These original checks qualify the bounded engineering collection. The complete
System/three-Utilities collection has additionally passed the focused gates in
the [release ledger](../../../docs/releases/CROMEMCO-1.3-READINESS.md), including
saved settings, installation, disk management, integrated displays, utilities
and 269 independent compatibility assertions. Final package reproduction,
review and publication are separate gates.
5.25-inch, double-density, double-sided, hard-disk, banked-service, auxiliary
serial, graphics and physical-hardware configurations remain unqualified.

## Complete release candidate

Build with `python3 tools/build_cromemco.py --release --work build/cromemco-release`.
The four manifest-selected volumes are under the prepared profile's
`build/cromemco/release`, separate from the engineering fixture disks. Run
`tools/qualify_cromemco_release.py` with `--build-root`, `--simulator`, `--suite`
and a fresh `--output` to reproduce focused acceptance. See the
[installation guide](../../../docs/platform/CROMEMCO-INSTALLATION.md) for the
self-contained native Mac launcher, utility mounts and offline source build.
