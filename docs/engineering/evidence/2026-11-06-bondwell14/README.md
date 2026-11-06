# Bondwell 14 qualification

**BW14 passes cpmsim RAM file interchange with the existing FDF.RSX mapper.**
Nine independent workers recovered all 152 original files, filled each disk
through allocation block 174, and read the probe back through BetterCP/M.
The longest worker took 29.704 seconds. No BIOS, BDOS, CONFIG or mapper source
changes were needed. The supplemental catalogue now has seven entries; the
production 108-entry catalogue is unchanged.

Model 4 media and its parallel runner are prepared, including physical DMK
round trips. The first user-launched batch failed at DIR with Bad Sector and
was interrupted. The corrected load order has not yet passed on Model 4; no
Model 4 pass is claimed. This session's read-only
LaunchServices lookup returned 1100 (BOOTSTRAP_NOT_PRIVILEGED), so automated
launch here remains unavailable; the failed batch was launched by the user. ROM, physical media, historical booting and formatting remain
untested. This evidence concerns file interchange, not execution of Bondwell
CP/M 3 or its applications under BetterCP/M.

| Original | Files | Probe bytes | Highest block written/read |
|---|---:|---:|---:|
| CSTAR.IMG | 16 | 231,424 | 174 |
| DSTAR.IMG | 15 | 251,904 | 174 |
| DSTARFIX.IMG | 17 | 247,808 | 174 |
| RSTAR1.IMG | 16 | 288,768 | 174 |
| RSTAR2.IMG | 11 | 184,320 | 174 |
| SYSTEM1.IMG | 29 | 51,200 | 174 |
| SYSTEM2.IMG | 36 | 69,632 | 174 |
| WSTAR1.IMG | 3 | 245,760 | 174 |
| WSTAR2.IMG | 9 | 227,328 | 174 |

[Sources](sources.json) · [Host checks and inventories](checks.json) ·
[cpmsim results](cpmsim-results.json) · [Model 4 preparation](model4-preparation.json)

## Original evidence and geometry

The [RetroArchive distribution](http://www.retroarchive.org/hardware/bondwell/bw14dsks.zip)
contains nine CopyQM 3.24 containers despite their `.IMG` suffixes, plus the
original README, recording scripts and ROMs. The ZIP's SHA-256 is pinned in
sources.json. Every original image matches the size and SHA-1 in MAME's
[BW14 software list](https://github.com/mamedev/mame/blob/master/hash/bw14.xml);
the captured CC0 XML and its Git blob identity are retained here. Matching
hashes establish identical bytes, not nine independent dump sources.

The CopyQM headers and MAME's
[BW12/BW14 format](https://github.com/mamedev/mame/blob/master/src/lib/formats/bw12_dsk.cpp)
agree on 40 cylinders, two sides, 18 sectors of 256 bytes, MFM and IDs 0–17.
The original README describes 360K double-sided media. CopyQM does not retain
per-sector angular positions: the prepared DMKs use synthetic ascending-ID
tracks, not a claimed reproduction of original physical interleave.

SYSTEM1 contains the BW14 DPB at canonical raw offsets 3263 and 68995:
`2400040f01ae007f00c00020000200`. It specifies SPT 36, BSH 4, BLM 15,
EXM 1, DSM 174, DRM 127, AL0 C0h, AL1 00h, CKS 32 and OFF 2.
The supplied system's 128-entry directory takes precedence over the 64-entry
`bw14` definition in cpmtools. Only SYSTEM1 contains this exact DPB sequence;
the other images are qualified by their filesystem and guest results.

Logical surfaces visit all of side 0, then all of side 1, both forwards.
The canonical emulator raw image remains cylinder/head/ascending-sector-ID
order. Thus the directory is at canonical byte 18,432 (C2/H0), but byte 9,216
in a side-major logical stream. The two reserved logical surfaces total 9,216
bytes; 175 two-KiB allocation blocks follow, leaving an unused 1,024-byte tail.
Every original directory in this set uses only user 0 and deleted entries;
this does not qualify CP/M 3 timestamp, label or password entries generally.

`media.py` independently decodes bounded CopyQM RLE and validates its header
checksum and historical data CRC. The CRC's six-bit table index follows
[LibDsk drvqm.c](https://github.com/lipro-cpm4l/libdsk/blob/1a6803566a0e4a766f7f51acb9baf9e11551ba77/lib/drvqm.c).
LibDsk independently decodes both the original and reconstructed containers;
POSIX cpmtools extracts every original and written file and checks allocation.
All original directory entries, reserved surfaces, unused tail and image length
survive the guest writes. Repacked CopyQM headers/comments are preserved except
for the two checksums. The compressed representation may change.

LibDsk's CopyQM driver rewrites its input container on close in this installed
version, even during conversion. An early inspection consequently recompressed
the extracted working members. They were restored from the unchanged ZIP and
verified against MAME before the final run. The final runner gives LibDsk only
disposable copies and checks the original hashes after every trial.

An initial guest setup omitted FDF.RSX; CONFIG refused the optional side-major
binding. The final runner builds/loads the existing mapper before binding.
This refusal is not counted as a passed trial. Final receipts refer only to the
clean nine-worker run on pristine, hash-verified originals.

## Use

Load **FDF before other RSXs**. The first Model 4 batch loaded screen RSXs
before FDF; their ordinary chain jumps overwrite HL, which the private FDF
mapper call uses as its input record number. A controlled cpmsim test reproduces
Bad Sector with P2DOS before FDF and passes full SYSTEM1 interchange with FDF
before P2DOS. The corrected Model 4 startup puts FDF first. This is a load-order
workaround for an existing private-ABI limitation, not a general RSX fix.
See [load-order evidence](load-order-results.json) and `check_load_order.py`,
which takes the same runtime arguments as qualify.py except --catalogue/--jobs.
Its two cases are deliberately sequential and each uses private media.

Build the mapper with `python3 tools/build_fdf_rsx.py` and place FDF.RSX on
BetterCP/M's System disk. Convert an original container into a fresh raw image:

```sh
python3 docs/engineering/evidence/2026-11-06-bondwell14/media.py \
  to-raw /path/to/SYSTEM1.IMG /path/to/private.raw
```

Mount that canonical raw image as physical drive 1 in cpmsim. Put SUPPDISK.FDB
on the C work disk under the name DISK.FDB, then:

```text
RSX LOAD FDF
CONFIG /PHYSICAL=1 /TRACKS=40 /SIDES=2 /STEP=6
C:
A:CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="Bondwell 14 40T DS"
A:
DIR B:
```

Reconstruct a new container using the original template:

```sh
python3 docs/engineering/evidence/2026-11-06-bondwell14/media.py \
  to-cqm /path/to/SYSTEM1.IMG /path/to/private.raw /path/to/written.cqm
```

Both commands refuse to overwrite an output. Repacking refuses changes to the
reserved surfaces or unused tail. `diskdefs` is for the **side-major logical
stream**, not the canonical raw image mounted by cpmsim.

## Reproduce

Run from the repository root. The qualification System is the unchanged PR632
RAM System; its [preparation](../2026-11-06-model2/system-preparation.json) and
hash are pinned. The runner adds FDF.RSX only to each private System copy.

```sh
python3 -B tools/build_fdf_rsx.py
python3 -B docs/engineering/evidence/2026-11-06-bondwell14/check.py \
  --images /path/to/originals --output /path/to/checks.json
python3 -B docs/engineering/evidence/2026-11-06-bondwell14/qualify.py \
  --images /path/to/originals --system /path/to/qualified-RAM-System.dsk \
  --mapper build/rsx/FDF.RSX --simulator /path/to/patched/cpmsim \
  --cpmtools /path/to/POSIX-cpmtools --dsktrans /path/to/dsktrans \
  --catalogue docs/engineering/evidence/2026-11-06-bondwell14/qualification-catalogue.FDF \
  --output /path/to/new-results --jobs 9
```

The host checks cover original hashes, independent inventories, embedded DPB,
physical DMK round trips, malformed CopyQM rejection, preservation failures and
native FDB compile/export. Existing FDF compiler and FDB reader suites pass.
M2WORK is only a scratch definition. Each worker owns its writable media and
saves its receipt independently; its own read-back follows its own write.

For Model 4, run [Run-Model4-BW14.command](Run-Model4-BW14.command) in a normal
macOS Terminal. Its defaults point to this project's prepared dependencies;
`BW14_IMAGES`, `BW14_SYSTEM`, `BW14_SIMULATOR`, `BW14_CPMTOOLS`, `BW14_MAPPER`
and `BW14_JOBS` override them. It prepares fresh private disks and starts nine
workers. It prints the result directory; each successful disk writes its own
result.json and the aggregate is written only after all pass. No duration is
predicted from the much faster cpmsim result. The Model 4 runner remains
unqualified until that guest batch completes.
