# Amstrad PCW 180K qualification

PCW passed read/write interchange on the patched cpmsim with the release System image identified in the receipt. BetterCP/M recovered all 24 original files, wrote and read back an 8 KiB probe through allocation block 174, and preserved the reserved track and the 512-byte tail beyond the last allocation block. Independent cpmtools/libdsk extraction from the repacked Extended DSK recovered every original file and the complete probe.

Model 4 media passed host preparation. Guest I/O on trs80gp and physical-media interchange remain open.

## Independent source

The fixture is RetroNerd's published PCW8256 CP/M boot disk modified for a second 180K drive. The downloaded RAR contains `CPM3 1-07H-Working.dsk`. The extracted image is stored locally as `retronerd-cpm107h.dsk`. Its original directory and all sector contents are retained. It contains 24 files, including BASIC.COM, DISCKIT.COM, J15CPM3.EMS, and B180.FIB. The source author describes the disk's modifications. [Source description](https://retronerd.co.uk/amstrad-pcw-8256-gotek-memory-and-other-upgrades/) · [Download page](https://retronerd.co.uk/download/cpm-1-07h-gotek-with-b-drive-modified/) · [Pinned hashes and member name](samples.json)

This first trial uses one populated independent image. Its 167 allocated blocks leave eight blocks for the write probe. All original files are copied as data, and the guest executes the BetterCP/M utilities from the test System disk.

## Format agreement

| Property | PCW definition |
|---|---|
| Physical geometry | 40 cylinders, one side, nine 512-byte MFM sectors per track |
| Sector IDs | 1 through 9 |
| Reserved tracks | 1, covering 4,608 bytes |
| Allocation | 1,024-byte blocks, DSM 174 |
| Directory | 64 entries, AL0 C0h, CKS 16 |
| Mapping | cpmtools `pcw`, libdsk `pcw180`, image driver `edsk` |
| Unallocated tail | 512 bytes after block 174 |

The first ten boot-sector bytes are `00 00 28 09 02 01 03 02 2A 52`. They agree with the geometry and allocation parameters reported by libdsk. The format uses 175 complete allocation blocks after its reserved track. [Amstrad boot specification](https://www.seasip.info/Cpm/amsform.html) · [cpmsim receipt](cpmsim-results.json)

The downloaded image has nine distinct rotational orders across its 40 tracks. Each track contains all sector IDs exactly once, with matching cylinder/head/size metadata and clear controller status. The host indexes sectors by ID for cpmsim and preserves each track's original sector order for the Model 4 DMK. Every DMK payload and all 40 sector orders were checked against the original EDSK. The guest-written sectors are reinserted into a copy of the original EDSK, preserving its container headers. [Conversion checks](conversion-checks.json) · [Model 4 preparation receipt](model4-preparation.json)

## Reproduce

Use Python 3.9+, cpmtools linked with libdsk, and a tar implementation that can extract the source RAR member. The runner verifies the archive hash before extracting a missing fixture. Existing fixture bytes are checked against the pinned image hash.

```sh
python3 -B docs/engineering/evidence/2026-11-05-cpc/qualify.py \
  --manifest docs/engineering/evidence/2026-11-06-pcw/samples.json \
  --target cpmsim --system /path/to/cpmsim-system.dsk \
  --simulator /path/to/patched/cpmsim \
  --images /path/to/originals --output /path/to/new-results --jobs 2
```

For Model 4, select `--target trs80gp`, supply the Model 4 System DMK and trs80gp executable, and run from a desktop Terminal. `--target prepare-model4` verifies the media conversion without starting the guest.

The supplied [Mac launcher](Run-Model4-PCW.command) uses the qualification workspace's sibling release media and the installed trs80gp. Set PCW_SYSTEM_IMAGE and PCW_SIMULATOR to override those paths. It creates a fresh results directory, captures the log, and prevents idle sleep while the runner is active.

Independent image trials run concurrently with `--jobs N`. The current PCW manifest has one image. The four original CPC fixtures were rerun with two workers to verify parallel isolation, and their sample results matched the previous cpmsim receipts. The defaults preserve the original CPC manifest and sequential operation.

The original download, extracted image, hashes, and receipts are indexed in the [reference collection](../../../../metadata/disk-image-reference/pcw.json).
