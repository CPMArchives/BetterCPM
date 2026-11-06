# Amstrad CPC System and Data interchange

Both supplemental definitions passed file interchange under the patched cpmsim using BetterCP/M System media. The guest read 47 files from four independently published, nonempty disk images. Each disk accepted a write through its highest allocation block and the guest copied the entire file back to another drive. On trs80gp, CPCSYS passed on both System images. The guest recovered all 29 original files and wrote and read back 50 KiB on CPC464 disk 1 and 128 KiB on CPC664 disk 2. Each write reached block 170 and preserved both reserved tracks. Each repacked EDSK matched its cpmsim counterpart byte-for-byte. CPCDATA also passed on CPC6128 disk 3. All 17 original files matched, the 8 KiB probe reached block 179 and read back intact, and the repacked EDSK matched the cpmsim result. The Booster disk also passed, preserving its original CLIENT file and writing and reading back the full 176 KiB probe through block 179. All four Model 4 results are complete, and all four repacked EDSKs match the cpmsim results byte-for-byte. Physical interchange remains open. [Completed Model 4 results](model4-results.json)

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

For Model 4, the startup batch on a private boot disk runs CONFIG from the work drive, binds the CPC disk, and performs the same copy and write checks. The prepared DMKs retained the source image’s CHRN order on every formatted track and decoded byte-for-byte to the original raw payloads. The first desktop run of the CPC464 System disk reached the wildcard COPY. The work disk contained a closed 256-byte `AMSDOS.COM` with the expected SHA-256. The next 8,192-byte `ASM.COM` payload matched in the destination blocks, though its open directory entry still showed zero bytes. In the decoded MMI008 logical sector stream the matching payload starts at byte 59,392. The interrupted work DMK has SHA-256 `b738874705a514e75971ed9c4ccb6070a857c83fdb16d1749b624762049a6350`. The three remaining SUBMIT commands were the probe write, return copy and completion marker. The original 240-second wall clock deadline killed the run before the CPC disk was written. This supplies partial read evidence only.

Run trs80gp from a desktop session. The runner reports writes to the private A/B/C images every 30 seconds. It stops after ten minutes without an observed disk write, with a 24-hour outer limit per image. The in-emulator screen wait has no elapsed-frame cutoff. A result requires the original host byte and final-block checks to pass. Each completed image gets its own `sample-result.json`. The `prepare-model4` target checks the host conversions independently and labels the result `prepared`.

The four pristine source images and both final emulator receipts are preserved in the [disk-image reference collection](../../../../metadata/disk-image-reference/README.md). Its manifest identifies the archive, pinned sources, expected file hashes, and reproduction revision.
