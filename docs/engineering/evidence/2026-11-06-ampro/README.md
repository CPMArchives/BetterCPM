# Ampro 80-track single-sided investigation

Status: vendor-source agreement and synthetic cpmsim pass. No independently
imaged 80-track single-sided disk has been found in the surveyed downloads.
Model 4 media preparation passed; guest I/O and physical-media interchange
are untested. This candidate is not included in either the production or
supplemental catalogue.

## Definition and evidence

The current cpmtools `amp3` and `amp5` definitions describe the same filesystem
and sector geometry. One candidate, `AMP3`, covers that shared layout; the two
names do not require duplicate FDB entries.

| Property | Candidate | Evidence |
|---|---|---|
| Geometry | 80 cylinders, one side, MFM, 5 x 1,024 bytes | libdsk `ampro400s`; vendor BIOS sector-size detection; AMPRODSK `SS96`, `ASK3`, `SKW2` |
| Sector IDs | 1 through 5 | BIOS `XLTSS`; AMPRODSK `SKW2` |
| Physical order | 1,4,2,5,3 | AMPRODSK `SKW2`; reconstructed in synthetic fixture |
| Logical order | Ascending sector ID | BIOS `XLTSS`; cpmtools skew 0 |
| DPB | SPT 40; BSH 4; BLM 15; EXM 1; DSM 194; DRM 127 | BIOS 1.6 and 3.8 `DPARM` |
| Directory allocation | AL0 C0h; AL1 00h; CKS 32 | BIOS `DPARM` |
| Reserved area | OFF 2; 10,240 bytes | BIOS `DPARM` |
| Allocation area | 195 x 2,048 bytes = 399,360 bytes | DPB and geometry agree exactly; no partial tail |

The independently archived vendor files are in Bitsavers'
[Ampro_LBZ80-CPM.ZIP](https://bitsavers.trailing-edge.com/bits/Ampro/Ampro_LBZ80-CPM.ZIP):
`SOURCE3.zip/bios-1-6.asm`, `SOURCE3.zip/bios-3-8.asm`, and
`SOURCE1.zip/ad-3-3.asm`. BIOS 3.8 explicitly assigns `DPARM` to both double-sided
48-tpi and single-sided 96-tpi disks. `SSDD96` has 1,024-byte sectors; `XLTSS`
supplies ascending IDs. AMPRODSK selects track 79 as the last track and uses
`SKW2` for the five-sector format. The current libdsk 1.4.2 built-in formatter
independently produces 80 x 1 x 5 x 1,024-byte geometry with IDs 1–5.

The published cpmtools definitions were checked against these vendor files,
rather than treating inconsistent descriptions of disk diameter or historical
third-party `diskdefs` variants as evidence for another layout. The existing
production Ampro entries `MMF006` and `MMF007` use ten 512-byte sectors per track.

## Original-image search

[Pinned downloads](sources.json) and [image survey](image-survey.json) preserve
what was examined:

- Five IMD files in the Bitsavers archive are 40-cylinder, double-sided,
  ten-sector, 512-byte images with IDs 17–26. Their 409,600-byte raw size also
  happens to match this candidate. Geometry prevents treating them as AMP3.
- Tom Slaight's [LBSYS-F.IMD](https://retrotechnology.com/restore/ampro_lb.html)
  is 40-cylinder, single-sided, ten-sector, 512-byte media. Its published
  comment lacks the standard `IMD ` signature; the original bytes are retained.
- Bitsavers' DM718.IMD is 80-cylinder, double-sided, 18 x 512-byte HD media.

All tracks in these seven files were inspected. Decoding the five archive
images by cylinder/head/sector reproduced their separately supplied IMDU raw
conversions exactly. cpmtools extraction from those raw images reproduced all
three vendor source files byte for byte; see [source checks](source-checks.json).
Direct IMD reads with the locally installed libdsk returned a seek failure for
the source disks; the verified archived raw conversions were used for extraction.

No surveyed image qualifies the 80-track single-sided candidate. Obtaining a
nonempty original remains the promotion gate.

## Synthetic diagnostic result

The [fixture generator](prepare_synthetic.py) uses libdsk `ampro400s`, three
deterministic files of 128, 1,152 and 32,896 bytes, and the vendor formatter's
sector order. It is explicitly synthetic and contains no vendor software.
The fixture exercises physical-sector and extent boundaries.

On patched cpmsim, BetterCP/M recovered all three files, wrote and read back
356,352 bytes (348 KiB) through allocation block 194, and preserved all 10,240
reserved bytes. Independent cpmtools/libdsk extraction verified the repacked
EDSK. [Receipt](cpmsim-synthetic-results.json) · [Fixture manifest](synthetic-samples.json)

The runner now accepts a candidate catalogue and independent host diskdefs.
This case uses existing `MMI008` work/return disks because the default 332 KiB
work disk cannot hold the candidate's full allocation area. It configures the
physical drive capabilities before applying the 80-track logical bindings.
The boot disk remains the release 332 KiB System image. CPC/PCW defaults are
preserved, and all five cpmsim regressions match their previous sample receipts.

Model 4 preparation preserves every generated sector and all 80 track orders.
That checks conversion only, and does not establish guest I/O correctness.
[Preparation receipt](model4-synthetic-preparation.json)

## Reproduce

Use cpmtools with libdsk, `dskform`, Python 3.9+, and the pinned BetterCP/M
release media/emulator identified in the receipts. Run from the repository root:

```sh
python3 -B tools/fdfcomp.py \
  docs/engineering/evidence/2026-11-06-ampro/CANDIDATE.FDF \
  docs/engineering/evidence/2026-11-06-ampro/CANDIDATE.FDB
python3 -B docs/engineering/evidence/2026-11-06-ampro/prepare_synthetic.py /path/to/new-fixtures
python3 -B docs/engineering/evidence/2026-11-05-cpc/qualify.py \
  --catalogue docs/engineering/evidence/2026-11-06-ampro/CANDIDATE.FDF \
  --diskdefs docs/engineering/evidence/2026-11-06-ampro/diskdefs \
  --manifest /path/to/new-fixtures/samples.json --images /path/to/new-fixtures \
  --work-format MMI008 --target cpmsim --system /path/to/release-system.dsk \
  --simulator /path/to/patched/cpmsim --output /path/to/new-results
```

For host-only Model 4 preparation, use `--target prepare-model4` and the release
Model 4 System DMK. To repeat the original-image survey, run `inspect_sources.py`
with `--images` naming the three pinned downloads and `--output` a new directory.

Before promotion, obtain and archive a nonempty original 80T SS image, check its
CHRN metadata and filesystem against the vendor definition, and run preserved-file
and final-block write/read-back tests on cpmsim and Model 4. Use private images
and `--jobs N` for independent trials; each image's read-back follows its write.
