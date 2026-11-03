# Release disk format verification

Tested the eight media in the four System and Utilities review ZIPs built at
`9cc9c7cfb305aa431ec44ee869c2bff76c1a3b95` on 2026-11-03. That commit
is based on main `91c91f7b06569ef9aca6e534f431f22cf0c9aaf8`.
The earlier list incorrectly identified historical MMI012 as the release
System layout. The installed Model 4 boot disk has a separate 780 KiB layout.

| Review ID | Filesystem | CP/M records per logical track | Reserved logical tracks | Directory offset in decoded sector stream | Allocation |
|---|---|---:|---:|---:|---:|
| MMF017 | cpmsim System, Work, Utilities, NOAH | 36 | 6 surfaces | 27,648 bytes | 166 × 2 KiB |
| MMI008 | Model 4 Work, Utilities, NOAH | 40 | 0 | 0 bytes | 400 × 2 KiB |
| MMI012 | Optional historical Extended System | 40 | 2 surfaces | 10,240 bytes | 395 × 2 KiB |
| BCPM780 | Actual BetterCP/M Model 4 System | 80 | 2 cylinders | 20,480 bytes | 390 × 2 KiB |

BCPM780 is a review ID. Allocation includes the directory. The CCS medium
has another 1,024 bytes after its last whole allocation block.

## Where the definitions come from

* **MMF017.** The CCS System 300 manual gives the double-sided, 40-cylinder
  5¼-inch mini drive's DP5D1 parameters in Appendix C. Appendix B explains
  cylinder addressing. In the vendor table, 72 records per cylinder and
  three reserved cylinders translate to 36 records per side and six reserved
  surfaces in the cpmsim address space. Each surface holds 18 sectors of 256
  bytes. Appendix D's T518 uses step four, with nine sectors before starting
  the second cycle. That gives two cycles beginning at IDs 1 and 2.
  The DSK records bytes in sector slots and carries no on-disk MFM address
  marks. Readback verifies the mapping in this emulator container.
  [CCS System 300 CP/M Supplementary Manual, revision B](https://bitsavers.org/pdf/ccs/CCS_System_300_CPM_Supplimentary_Manual_Sep81.pdf)
* **MMI008 and MMI012.** Larry Kraemer's published TRSN and TRSR descriptions
  specify 80 cylinders, two alternating sides, ten 512-byte sectors per side,
  MFM, and odd IDs followed by even IDs in the logical sector map. The
  published offsets are zero and two surface tracks respectively. We used
  these format facts to write new definitions. The cpmtools distribution
  corroborates capacity and directory geometry, but its TRSN stanza uses
  skew zero, so we did not adopt it as the physical sector ordering. The
  packaged nonempty DMKs allowed full-file validation of the TRSN mapping.
  These sources establish an alternative to extracting the CONFIG binary;
  the historical ancestry of the third-party tables is unverified.
  [Kraemer's TRSN and TRSR tables](https://www.trs-80.com/sub-reference-dos-cpm.htm)
  · [cpmtools diskdefs](https://github.com/lipro-cpm4l/cpmtools/blob/cpm4l/cpmtools-2.21/diskdefs)
* **BCPM780.** The installed BetterCP/M BIOS uses one logical track per
  cylinder. We tested that convention against all 29 files on the actual
  boot disk and also tried the historical definition as a negative control.
  The 790K mapping fails to recover the boot disk's expected directory.
  Older builder filenames containing “790K” are unsuitable for format
  identification. [Installed BIOS defaults](../../../platform/DEFAULT-TEST-DISKS.md)
* Allocation block size is 2,048 bytes throughout. The last block number
  follows from the whole blocks remaining after the reserved area. The
  directory has 64 entries for CCS and 128 for the Model 4 formats. The
  directory allocation bitmap, extent mask and removable-media checksum
  vector follow the CP/M disk parameter rules.
  [Digital Research CP/M 2.2 Operating System Manual, section 6](https://www.cpm.z80.de/manuals/archive/cpm22htm/ch6.htm)

## Reproduce the host check

With Python 3.9+ and cpmtools with libdsk installed, run
`python3 verify.py /path/to/candidates/9cc9c7cfb305aa431ec44ee869c2bff76c1a3b95`
from this folder in a checkout. [review.fdf](review.fdf) is the only format
input. The test compiles and reads back its four descriptors, verifies ZIP
and disk digests, decodes every sector ID and data CRC in the four Model 4
DMKs, and compares each file's length and SHA-256 with the package receipt.
It checks both blank Work disks and uses temporary raw media for writes.
The explicit libdsk 800K raw geometry avoids a host-side autodetection error
that can return a plausible directory but corrupt file reads.

All 128 file instances matched. As a separate post-check, all numeric and
topology fields of the three historical IDs matched the descriptors read
back from both packaged FDBs. Only the review display strings differ. The four fresh full-volume tests filled
every available allocation block, recovered a record-specific pattern byte
for byte and preserved the reserved area. The MMI012 positive host control
used constructed media. [Eight image hashes and full-volume results](media-results.json)

## Guest checks on disposable disks

The cpmsim run started with a copy of the reviewed 332K System disk. Its
catalogue was replaced with the 512-byte review FDB. CONFIG bound logical B
by its new display name, TYPE read the marker on a fresh 332K disk, and COPY
wrote a second file. The separately exported 128-byte CP/M record matched
the original. The review-only change to the startup disk means its digest
differs from the packaged System image in the host check.

The Model 4 batch run booted a copy of the verified 780K System disk with a
temporary STARTUP.SUB. Physical drive 1 held a new MMI008 data disk with the
review FDB; physical drive 2 held a new MMI012 compatibility disk. From B,
CONFIG selected each review entry by name. TYPE displayed the distinct
markers. The guest copied records between the volumes and the host decoded
the resulting disks and compared the records with the fixtures. Each marker
is ASCII `MEDIA-OK-` followed by its format ID, CR/LF, and CP/M EOF bytes
through the 128th byte. The receipt records the commands, emulator hashes,
screen captures and exported hashes. Earlier timed keyboard attempts dropped
characters or timed out; the recorded Model 4 result comes from the guest
batch script. Testing covers simulated media. Physical controllers and
interchange with a surviving original 790K disk were outside this trial.
[Guest results](guest-results.json)

## Release decision

Adopt independently authored inputs for the cpmsim 332K, Model 4 800K data
and BetterCP/M 780K System layouts when integrating release media. Keep the
historical 790K ID distinct if retained for compatibility. These review
descriptions differ from the current guest display strings. CONFIG accepts
those strings on its command line, so integration must preserve or explicitly
migrate the public names. The temporary four-entry catalogue is intentionally
outside the build path. The production catalogue, scripts and package source
snapshots still contain historical inputs. Decide the 104 other admitted
entries, remove or clear the underlying source material, rebuild, and repeat
exact-media qualification before freeze.
