# Supplemental disk formats

Use [SUPPDISK.FDF](SUPPDISK.FDF) as the editable source and [SUPPDISK.FDB](SUPPDISK.FDB) as the compiled catalogue. Each row gives the scope of the guest test that admitted the entry.

| ID | CONFIG display name | Qualified for | Pending |
|---|---|---|---|
| CPCSYS | Amstrad CPC System | cpmsim and trs80gp (CPC464 disk 1) file reads and writes through allocation block 170 | CPC664 disk 2 on trs80gp, physical media |
| CPCDATA | Amstrad CPC Data | cpmsim file reads and writes through allocation block 179 | Model 4 guest I/O, physical media |

To use the supplement on cpmsim, put a copy of `SUPPDISK.FDB` on a separate work disk under the guest name `DISK.FDB`. Keep the production catalogue on system drive A. With that work disk in C and a CPC raw image in physical drive 1, run the following. Select `Amstrad CPC Data` in the CONFIG command for a Data disk.

```text
C:
A:CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="Amstrad CPC System"
A:
DIR B:
```

A CPCEMU/Extended DSK contains track headers. Convert its sector payloads to raw for cpmsim or an ID-preserving DMK for the Model 4 trial. The qualification runner performs both conversions.

For each addition, seek a nonempty disk image from an independent online collection or software distribution. Record the URL, revision where available, image hash, physical sector IDs and logical order. Compare original file bytes with an independent reader. On disposable media, write through the highest allocation block, read it back and verify existing files and reserved tracks. Record each tested backend separately and identify synthetic fixtures explicitly. See the [CPC test and source images](../../docs/engineering/evidence/2026-11-05-cpc/README.md).

Rebuild from the repository root.

```sh
python3 tools/fdfcomp.py metadata/supplemental/SUPPDISK.FDF metadata/supplemental/SUPPDISK.FDB
```
