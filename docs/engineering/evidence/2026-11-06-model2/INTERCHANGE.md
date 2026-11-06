# ATON/Lifeboat file interchange on cpmsim

The approved bounded implementation qualifies **ATONSS** (single-sided ATON
and Lifeboat) and **ATONDS** (double-sided ATON) on the updated **cpmsim RAM
backend through the canonical raw adapter**. All five valid originals passed
independent parallel guest trials. The malformed ATN225BS original remains a
rejection fixture. Historical system booting, formatting, Model 4, ROM and
physical-media interchange are not qualified.

| Original | Files recovered unchanged | Probe written and read | Final block |
|---|---:|---:|---:|
| ATN223IS.IMD | 19 | 473,088 bytes | 299 |
| ATN225BD.IMD | 31 | 954,368 bytes | 607 |
| LB224A.IMD | 52 | 24,576 bytes | 299 |
| LB225D.IMD | 39 | 274,432 bytes | 299 |
| LB225DF80.IMD | 7 | 503,808 bytes | 299 |

The five workers own separate A/B/C/D images. Each recovers all original
files, fills the target's free allocation blocks, and reads the entire probe
back to another disk. The Python word-pointer CP/M reader and POSIX cpmtools
independently verify every resulting file. All original directory entries,
11,520 reserved bytes, IMD headers, sector order and image bounds survive.
The final parallel run's longest worker took 47.853 seconds.

[Guest receipt](cpmsim-results.json) · [CPC regression](cpc-regression.json) ·
[PCW regression](pcw-regression.json) · [Build/test checks](implementation-checks.json)

## Use the adapter

Keep the original IMD. From the repository root, convert to a **new** raw file:

```sh
python3 docs/engineering/evidence/2026-11-06-model2/adapt.py \
  to-raw /path/to/ATN223IS.IMD /path/to/private.raw
```

Mount private.raw as cpmsim physical drive 1. Place SUPPDISK.FDB on a work disk
as DISK.FDB; with that work disk current in C:

```text
A:CONFIG /PHYSICAL=1 /TRACKS=77 /SIDES=1 /STEP=6
A:CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="ATON/Lifeboat Model II SS"
A:
DIR B:
```

For the double-sided image use SIDES=2 and FORMAT="ATON Model II DS".
Use the rebuilt RAM System and matching CONFIG. A new utility refuses an old
BIOS rather than treating the exceptional first surface as uniform media.
The old native FDB reader marks the required extension unsupported.

After guest use, reconstruct a **new** IMD against the original template:

```sh
python3 docs/engineering/evidence/2026-11-06-model2/adapt.py \
  to-imd /path/to/ATN223IS.IMD /path/to/private.raw /path/to/written.IMD
```

The adapter validates the observed 77-cylinder layouts and refuses ambiguous
sectors, wrong lengths, altered boot padding, or altered reserved bytes. It
never overwrites an existing output. The unchanged original remains the
source of container metadata. The initial 3,328-byte FM surface occupies an
8,192-byte canonical slot; the added zeros are representation, not media.
Never mount the unpadded 625,920/1,256,704-byte raw stream directly in cpmsim.

## Runtime and memory contract

Required FDB extension 83h describes C0/H0. Binding byte 61 carries its adapter
requirement. BDOS 181 operation 6 returns B301h only for the supporting RAM
backend. CONFIG and FDB check that token before operation 4. Guest reads and
writes of linear surface zero fail before port access. All formatting of a
marked binding is refused, including data surfaces. Model 4 rejects the marker;
ROM retains its 32-byte checksum bound and does not advertise the capability.

Four 48-byte CSVs retain full CKS 48 coverage. A/B use 96 bytes of the existing
128-byte CSV region; C/D use an explicitly initialized 96-byte region immediately
before the file loader. The BIOS ends 38 bytes before that region. TPA, history,
ALV size and the resident carrier span are unchanged. The build checks all
bounds and records the layout. The machine-code test checks every CSV slot,
independent vectors, final-record media-change protection, BIOS/ALV preservation
and cold zeros. SYSGEN also preserves a populated filesystem and cold-boots the
installed target with these carriers.

Native FDB compiles and exports the new fields and preserves the complete boot
profile while editing a loaded entry. Capture from an active marked binding is
refused because the binding omits original boot IDs. Boot metadata is edited in
FDF text; ordinary workbench edits preserve it. Viewer byte offsets explicitly
refer to canonical slots. Existing catalogue output remains byte-identical.
Repeated scalar output was factored to fit native FDB's existing arenas. Its
private stack is 128 bytes; CONFIG's is 256 bytes. Measured margins are in the
check receipt. No catalogue arena or system TPA was reduced.

## Reproduce

Build the normal component prerequisites from this checkout, then a new RAM
carrier set. The complete-system builder supplies the shared utility/bootstrap
metadata needed by the cpmsim builder. Use a fresh output directory:

```sh
python3 -B tools/build_complete_system.py
python3 -B tools/build_z80pack_image.py --ram-only --system-tracks-only \
  --output build/model2-ram
python3 -B docs/engineering/evidence/2026-11-06-model2/prepare_system.py \
  --base-system /path/to/baseline-332K-System.dsk \
  --runtime-build build/model2-ram --config build/utilities/CONFIG.COM \
  --catalogue docs/engineering/evidence/2026-11-06-model2/qualification-catalogue.FDF \
  --cpmtools /path/to/POSIX-cpmtools --output build/model2-private-system
python3 -B docs/engineering/evidence/2026-11-06-model2/qualify.py \
  --images /path/to/originals --system build/model2-private-system/system.dsk \
  --catalogue docs/engineering/evidence/2026-11-06-model2/qualification-catalogue.FDF \
  --simulator /path/to/patched/cpmsim --cpmtools /path/to/POSIX-cpmtools \
  --output /path/to/new-results --jobs 5
```

The scratch-only M2WORK definition provides space for the 954,368-byte probe
and all original files, with CKS 48 on both work/return drives. It is not an
additional historical format or a supplemental catalogue entry. The qualified
source images and pinned cpmtools revision remain in [sources.json](sources.json).
Use the POSIX cpmtools build for offset-11,520 historical raw extraction; the
libdsk-backed offset path requires sector alignment and cannot represent it.

## Pickles & Trout follow-up

The same adapter now also accepts the observed single-sided 16 × 512-byte
data-track profile. See the [P&T qualification](../2026-11-06-pickles-trout/README.md)
for PT2SS, its three originals and the separate sequential/random-record checks.
The adapter still rejects other geometry and never overwrites existing output.
