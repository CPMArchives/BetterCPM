# Amstrad CPC System and Data interchange

Both supplemental definitions passed file interchange under the patched cpmsim using BetterCP/M System media. The guest read 47 files from four independently published, nonempty disk images. Each disk accepted a write through its highest allocation block and the guest copied the entire file back to another drive. The Model 4 DMKs passed host-side sector and file preparation. Guest I/O on trs80gp and interchange on physical equipment remain open.

| Definition | Sector IDs | Reserved tracks | DSM | Directory starts at | Space available for files on a blank disk |
|---|---|---:|---:|---:|---:|
| CPCSYS | 41h–49h | 2 | 170 | 9,216 bytes | 169 KiB |
| CPCDATA | C1h–C9h | 0 | 179 | 0 | 178 KiB |

Both have 40 single-sided MFM tracks with nine 512-byte sectors each, 36 logical 128-byte records per track, 1 KiB allocation blocks and 64 directory entries. The directory uses the first two blocks. BSH = 3, BLM = 7, EXM = 0, DRM = 63, AL0/AL1 = C0h/00h, CKS = 16. The FDF lists sector IDs in ascending **logical** order. On all 160 formatted tracks the **rotational** order relative to the first ID was 0,5,1,6,2,7,3,8,4. A raw stream in rotational order would scramble files. The three Amstrad archive EDSKs declare 43 track slots. Each has 40 formatted tracks and three zero-length trailing slots. The Booster image declares 40.

The cpmtools definitions supply the filesystem dimensions, skew, reserved tracks and a named libdsk profile. John Elliott documents each format’s absolute first sector, side count, encoding-related parameters and allocation geometry. The source images independently establish the sector IDs and recorded order. The scope here is ordinary CP/M file payloads. CP/M Plus-specific metadata handling, CPC boot execution and low-level formatting require separate evidence. [cpmtools 2.24 diskdefs](https://github.com/johnsonjh/cpmtools/blob/58e11085eb713d54fcf876f7dd7c8243b09af6ca/diskdefs) · [Amstrad disk formats](https://www.seasip.info/Cpm/amsform.html)

## Images and results

| Published image | Format | Original files verified | Guest-written probe | Highest block written |
|---|---|---:|---:|---:|
| CPC464 DDI-1 English disk 1 | CPCSYS | 26 | 50 KiB | 170 |
| CPC664 English disk 2 | CPCSYS | 3 | 128 KiB | 170 |
| CPC6128 Spanish disk 3 | CPCDATA | 17 | 8 KiB | 179 |
| Arkos Tracker CPC Booster client | CPCDATA | 1 | 176 KiB | 179 |

The first three come from the Amstrad CP/M and Logo collection. The fourth ships with the tracker tools in CPCtelera and contains an extensionless application named `CLIENT`. The pinned manifest identifies each original image by URL and SHA-256. The receipt records every recovered file hash, the pattern and raw-image hashes, the post-write EDSK hashes, emulator and system-image identities, and guest commands. [Image manifest](samples.json) · [cpmsim receipt](cpmsim-results.json)

The host read each original EDSK directly with cpmtools 2.23 and libdsk 1.4.2. The test checked the cylinder, head, sector ID, size, controller status and byte count for all 360 sectors on each disk, then indexed payloads by sector ID. As a negative control, the opposite definition rejected each image’s sector IDs. On cpmsim the 384-byte supplement was `C:DISK.FDB` and the production catalogue stayed on A. The guest selected the format by name with `A:CONFIG`, copied every original file out, filled the remaining allocation blocks with a record-specific pattern and copied the new file back out. Host checks proved that `FILL.BIN` owned DSM, every original file survived, and the System disks retained both reserved tracks byte-for-byte. Reinserting the changed sectors into a copy of each original EDSK and reopening it with libdsk recovered the same files and probe.

## Reproduce

Run with Python 3.9+ and cpmtools linked to libdsk. Supply a BetterCP/M System image for the chosen target, the project-patched cpmsim executable or the installed trs80gp executable, and a fresh output directory. The runner downloads missing fixtures from the pinned locations and checks the hashes before use. It writes only to its cache and private test directory.

```sh
python3 docs/engineering/evidence/2026-11-05-cpc/qualify.py \
  --target cpmsim --system /path/to/cpmsim-system.dsk --simulator /path/to/cpmsim \
  --images ./cpc-originals --output ./cpc-cpmsim-results

python3 docs/engineering/evidence/2026-11-05-cpc/qualify.py \
  --target trs80gp --system /path/to/model4-system.dmk --simulator /path/to/trs80gp \
  --images ./cpc-originals --output ./cpc-model4-results
```

For Model 4, the startup batch on a private boot disk runs CONFIG from the work drive, binds the CPC disk, and performs the same copy and write checks. The prepared DMKs retained the source image’s CHRN order on every formatted track and decoded byte-for-byte to the original raw payloads. macOS LaunchServices returned 1100 before starting trs80gp in the qualification session. Use a desktop session for the guest run. The `prepare-model4` target checks the host conversions independently and labels the result `prepared`.
