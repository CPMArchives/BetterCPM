# Supplemental disk formats

## Release 1.0.1

The release supplement is [1.0.1/SUPPDISK.FDF](1.0.1/SUPPDISK.FDF) and
[1.0.1/SUPPDISK.FDB](1.0.1/SUPPDISK.FDB): CPCSYS, CPCDATA, PCW and BW14.
Importing these four into the standard 108-entry catalogue gives 112 entries.
It retains the existing 32-byte checksum capacity and BIOS layout. ATONSS,
ATONDS and PT2SS require expanded checksum storage; that expansion is deferred
to 1.1 consideration. They are not supplied on the 1.0.1 Utilities disks.

## Full experimental collection and qualification history

Use [SUPPDISK.FDF](SUPPDISK.FDF) as the editable source and [SUPPDISK.FDB](SUPPDISK.FDB) as the compiled catalogue. Each row gives the scope of the guest test that admitted the entry.

| ID | CONFIG display name | Qualified for | Pending |
|---|---|---|---|
| CPCSYS | Amstrad CPC System | cpmsim and trs80gp (CPC464 disk 1 and CPC664 disk 2) file reads and writes through allocation block 170 | physical media |
| CPCDATA | Amstrad CPC Data | cpmsim and trs80gp (CPC6128 disk 3 and Booster) file reads and writes through allocation block 179 | physical media |
| PCW | Amstrad PCW 180K | cpmsim and trs80gp file reads and writes through allocation block 174 | physical media |
| ATONSS | ATON/Lifeboat Model II SS | cpmsim RAM canonical adapter; four originals, all files and block 299 read/write | Model 4 and ROM unsupported; physical media untested |
| ATONDS | ATON Model II DS | cpmsim RAM canonical adapter; one original, all files and block 607 read/write | Model 4 and ROM unsupported; physical media untested |
| PT2SS | Pickles & Trout M2 SS | cpmsim RAM canonical adapter; three originals, sequential files plus random tail records, block 299 read/write | Model 4 and ROM unsupported; physical media untested |
| BW14 | Bondwell 14 40T DS | cpmsim RAM and trs80gp with FDF.RSX loaded first; nine originals, all 152 files and block 174 read/write; identical written images | ROM and physical media untested |

To use the supplement on cpmsim, put a copy of `SUPPDISK.FDB` on a separate work disk under the guest name `DISK.FDB`. Keep the production catalogue on system drive A. With that work disk in C and a CPC raw image in physical drive 1, run the following. Select `Amstrad CPC Data` in the CONFIG command for a Data disk.

```text
C:
A:CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="Amstrad CPC System"
A:
DIR B:
```

A CPCEMU/Extended DSK contains track headers. Convert its sector payloads to raw for cpmsim or an ID-preserving DMK for the Model 4 trial. The qualification runner performs both conversions. See the [PCW qualification](../../docs/engineering/evidence/2026-11-06-pcw/README.md) for the one-reserved-track PCW 180K layout.

For each addition, seek a nonempty disk image from an independent online collection or software distribution. Record the URL, revision where available, image hash, physical sector IDs and logical order. Compare original file bytes with an independent reader. On disposable media, write through the highest allocation block, read it back and verify existing files and reserved tracks. Record each tested backend separately and identify synthetic fixtures explicitly. See the [CPC test and source images](../../docs/engineering/evidence/2026-11-05-cpc/README.md).

Rebuild from the repository root.

```sh
python3 tools/fdfcomp.py metadata/supplemental/SUPPDISK.FDF metadata/supplemental/SUPPDISK.FDB
```

Pristine images, expected file hashes, archive identities, and collection admission instructions are indexed in the [disk-image reference collection](../disk-image-reference/README.md).

ATON/Lifeboat requires the updated RAM BIOS and CONFIG together. This experimental RAM configuration is not selected for 1.0.1;
ATON/Lifeboat and Pickles & Trout are deferred to 1.1 consideration. The required
boot-surface extension prevents older catalogue readers from binding these
entries; the capability query prevents a new utility from applying them to an
older BIOS. Use the [Model II adapter and qualification procedure](../../docs/engineering/evidence/2026-11-06-model2/INTERCHANGE.md).
The original IMD or variable-length raw file is not a directly mountable cpmsim
image. Historical booting and formatting are outside the support claim.

Pickles & Trout uses the same boot adapter with 16 × 512-byte data sectors.
See the [P&T qualification and master-disk EOF detail](../../docs/engineering/evidence/2026-11-06-pickles-trout/README.md).

Bondwell 14 uses ordinary uniform media with side-major filesystem order. Load
`FDF.RSX` before other RSXs and before binding BW14; an earlier chaining RSX
can overwrite the private mapper input register. Its CopyQM `.IMG` originals require conversion
to canonical C/H/ascending-ID raw images; do not mount the container itself.
See the [BW14 qualification](../../docs/engineering/evidence/2026-11-06-bondwell14/README.md).
