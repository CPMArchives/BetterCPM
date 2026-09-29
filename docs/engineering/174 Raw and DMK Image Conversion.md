# Raw and DMK Image Conversion

Status: Implemented host interoperability tool  
Date: 2026-09-29

`tools/convert_fdf_image.py` converts a disk represented by canonical z80pack
raw sector bytes into a DMK physical-track container and extracts the same disk
back into raw form. This changes the host serialization, not the CP/M disk
format.

Canonical raw images contain decoded sector payloads. Tracks are ordered by
cylinder and then side. Within each surface track, sectors occupy ascending
sector-ID slots. The FDF sector table supplies rotational order. A DMK adds the
ID fields, data marks, gaps, density markers and CRCs that a controller-level
emulator requires.

The default definition is the BetterCP/M CCS 40-cylinder, double-sided,
double-density 332K format. Therefore a daily-use z80pack image can be
converted with:

```sh
python3 tools/convert_fdf_image.py raw-to-dmk driveb.dsk driveb.dmk
python3 tools/convert_fdf_image.py dmk-to-raw driveb.dmk driveb-returned.dsk
```

Use `--format 'exact DISK.FDF description'` for another definition and `--fdf`
for another catalog. Existing output is protected unless `--force` is given.

The first implementation deliberately accepts only uniform MFM surface-track
definitions with ordinary cylinder, side and sector-ID conventions. It
supports decoded/inverted payload translation. FM, mixed-size sectors,
cylinder-wide logical tracks, side-major/reversed mappings and continuous IDs
are rejected because a lossy or guessed conversion would be worse than an
explicit unsupported result.

DMK extraction checks the header geometry, every ID address mark, cylinder,
side, sector ID, size code, ID CRC, normal data mark and data CRC. Duplicate,
missing, extra, truncated and deleted-data sectors are rejected. A raw-to-DMK-
to-raw round trip must reproduce every input byte. A DMK-to-raw-to-DMK round
trip preserves geometry, rotational IDs and sector payloads; gap bytes and
exact address-mark placement are normalized.
