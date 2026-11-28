# Altair Z80 / Tarbell platform

Status, 28 November 2026: **release integration in progress for BetterCP/M 1.3**.
The shared source baseline is published mainline commit
`55612e001027bce02978d1cd010ee56e63549402` plus this platform adapter.
See the [release ledger](../../../docs/releases/ALTAIR-1.3-READINESS.md) for
executed gates and publication status, and the
[installation guide](../../../docs/platform/ALTAIR-INSTALLATION.md) for operation.

The initial target uses a Z80 CPU, 64 KiB RAM, an Altair 88-2SIO channel A
serial console, and a Tarbell 1011D single-density floppy controller. It is
explicitly a Z80-equipped Altair configuration, not an 8080 port.

## Hardware boundary

| Component | Initial configuration |
| --- | --- |
| CPU | Z80; launch with `-z`, since altairsim defaults to 8080 |
| RAM | 0000h–FFFFh, nonbanked |
| Bootstrap | Tarbell internal 32-byte ROM, enabled with `-R` |
| Boot entry | Firmware loads track 0, sector 1 at 0000h and enters 007Dh |
| Console | 88-2SIO channel A, status/control 10h, data 11h |
| Disk | Tarbell status/command F8h, track F9h, sector FAh, data FBh, select/wait FCh |
| Drives | A–D; 77 tracks, 26 sectors/track, 128 bytes/sector |
| Raw image | 256,256 bytes, track-major ascending sector IDs 1–26 |

The internal ROM is overlaid at reset and disables itself after an access
above 001Fh. It does not permanently occupy FC00h–FFFFh. This avoids the
permanent top-of-memory reservation in upstream's external-ROM CP/M example.
The supplied diagnostic writes and reads both 55h and AAh at every address
FC00h–FFFFh after disk boot. The OS reports **57,344 bytes maximum loadable COM**
with no optional RSX loaded. A guest fixture verifies its page-zero boundary,
writes and checks the transient region from 2000h to that boundary, and then
warm-boots successfully after overwriting the former CCP/CPX allocation.

`boot.mac` is a 128-byte first sector with a jump at 007Dh. It loads sectors
2–9 at 1000h for the controller diagnostic. The system builder selects sectors
5–8 instead, loading `systemboot.mac` from package records 4–7. That stage reads
the common resident image from records 8–59 and enters the shared BIOS. Checked
command, control and RSX carriers retain the common package record allocation.

`console.inc` supplies polling serial status/input/output.
`tarbell.inc` supplies bounded single-sector read and write operations,
validates drive/track/sector before transfer, checks completion status, and
returns a nonzero error on premature completion. It restores and seeks each
request; per-drive head tracking is a later optimization. No cpmsim disk DMA,
geometry extension, or host filesystem hook is used for these transfers.
The diagnostic uses altairsim's virtual shutdown port solely to end a test.

## Reproduce hardware checks

From the repository root, supply a local checkout containing z80pack commit
`91fd28eb04e675c2127df88ed3f40675e15282e2` at HEAD:

```sh
python3 tools/prepare_altair_emulator.py \
  --source /path/to/z80pack --output build/altair-emulator
python3 tools/test_altair_hardware.py \
  --simulator build/altair-emulator/altairsim/altairsim \
  --assembler /path/to/z80asm --output build/altair-hardware
```

Both commands require fresh output directories. The preparation tool archives
committed emulator sources, so it does not copy uncommitted local modifications.
It builds without the front panel or graphics dependencies. A small host shim
marks graphics cards absent, and a generated `simio.c` patch removes unused
auxiliary socket initialization and traps accesses to those endpoints. The CPU,
memory, Tarbell controller, boot ROM, and console emulation retain their pinned
upstream implementations. This serial-console configuration does not qualify
VDM, Dazzler, front-panel, auxiliary-serial, or modem functionality.

The test generates private images, assembles the first sector and diagnostic,
cold-boots through the actual Tarbell ROM, supplies lowercase serial input,
and verifies:

- Writable upper 1 KiB after the ROM has switched out.
- Console input and output on the configured serial channel.
- Distinct known data from track 2/sector 1 and track 76/sector 26 on A–D.
- Write, clear RAM buffer, and read-back on all four drives.
- Whole-image equality against independently constructed expected images,
  allowing exactly one 128-byte write per drive.
- Rejection of drive 4, track 77, sector 0, and sector 27.
- Separate cold boots requiring read/write errors on missing and incorrectly
  sized B media, and a successful read followed by a rejected write on
  read-only B media. Every error case leaves all media byte-identical.

Output includes assembly listings, exact images, per-case transcripts,
emulator/build identities, and `result.json`. Read-only media testing requires
an ordinary user whose file permissions enforce read-only access.

Retained controller results are under
[`docs/engineering/evidence/altair-hardware`](../../../docs/engineering/evidence/altair-hardware).

## Build and run the OS engineering image

```sh
python3 tools/build_altair.py --work build/altair-integration
python3 tools/test_altair_system.py \
  --image-dir build/altair-integration/profiles/altair-fullram/altair/build/altair \
  --simulator build/altair-emulator/altairsim/altairsim \
  --output build/altair-system-check
python3 tools/launch_altair.py \
  --image-dir build/altair-integration/profiles/altair-fullram/altair/build/altair \
  --simulator build/altair-emulator/altairsim/altairsim
```

The builder stages and hashes shared sources in an isolated `altair-fullram`
profile. It rejects stale or mixed source/assembler inputs and checks component
sizes against the resident map. Existing targets retain their own profiles.
The generated `SYSTEM.SYS` uses the common checked package schema and private
carrier binding. Native SYSGEN installs it without replacing the destination
filesystem; release qualification cold-boots the independently installed image.

All four 256,256-byte disk images use ALTRB77: eight reserved tracks, 1 KiB
allocation blocks, 224 blocks, 64 directory entries, eight-bit allocation
entries, and identity sector order. This provides a 224 KiB allocation area,
including two directory blocks; the final two physical records are unallocated.
`diskdefs` lets independent cpmtools read the same filesystem.

The image includes the shared RCP, RSX pack/cache, STAT and RSX commands, ECHO
proof module and the AFILE/ATPA/AAPI/AECHO fixtures. BYE exits the emulator.
It is deliberately a bounded engineering collection, not the final distribution
manifest or a complete utilities disk. Treat the generated media as writable;
the shared RSX manager may create and delete scratch files on A.

The disk API supports discovery, getters, validation of identical binding
setters and fixed-format E5 initialization. A is protected from formatting.
Different bindings and optional boot-surface operations return unsupported.
The public physical-read adapter stages a full record before publishing it to
DMA, so failed media reads leave the caller's buffer unchanged. DUP's Altair
builder uses the eight-inch single-density track budget. Host `diskdefs` uses
an equivalent linear record view to avoid LibDsk's odd-track truncation.

Retained [OS integration evidence](../../../docs/engineering/evidence/altair-system)
records cold/warm boot, version and directory commands, STAT memory reporting,
140-record files on B–D crossing CP/M extents with independent cpmtools byte
comparison, geometry API behavior, active system-file integrity, the destructive
TPA fixture, ECHO load/call/unload, restoration of 56 KiB afterward, drive-B
preservation on warm boot, and refusal of damaged/foreign command carriers.

## Complete release media and focused acceptance

```sh
python3 tools/build_altair.py --release --work build/altair-release
python3 tools/qualify_altair_release.py \
  --build-root build/altair-release/profiles/altair-fullram/altair \
  --simulator build/altair-emulator/altairsim/altairsim \
  --suite /path/to/rc564-conformance-suite --output build/altair-acceptance
```

The full manifest-selected collection is one System and three Utilities images.
HELP, FDB and NOAH overlays stay with their commands. The release does not
include AFILE/ATPA/AAPI/AECHO engineering fixtures. Native ZSM4 and LINK retain
their required source/license companions. `package_altair.py` requires a clean
committed source tree and passing gates bound to the exact System hash.

`prepare_altair_emulator.py` defaults to the bundled hash-verified offline
source archive. `--source` still accepts the exact pinned local Git checkout.
The serial-only build does not need graphics dependencies or a network.
Integrated ADM3A/VT52/ANSI modules use Altair MCON backend bit 8 and the exact
private binding. Their leaf renderer writes port 11h for the pinned emulator's
unthrottled, synchronous console; physical serial timing is unqualified.

Focused release gates cover populated-media installation, saved cold settings,
enabled MCL/VAR/NDR/PATH, formatting/check/copy, physical errors and DMA
preservation, media-change/reset, all IOBYTE routes, shipped utility queries,
HELP/NOAH, native assembler/linker execution and 269 automatic independent
compatibility assertions. Existing matching 1.3 core evidence is reused; these
results are not a new full 627-card campaign or physical-hardware validation.
Final package and publication records remain separate gates.
