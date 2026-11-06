# ATON and Lifeboat Model II format investigation

**Investigation baseline:** five original images passed **host-only** file extraction and full-free-space
write/read-back through their actual last allocation block. One malformed ATON
image was rejected before filesystem access. No BetterCP/M guest or physical
media pass is claimed, and no entry was added to the supplemental catalogue.

**Follow-up completed:** both layouts now pass cpmsim RAM interchange through
the explicit reserved-surface adapter and are admitted as ATONSS/ATONDS.
See [INTERCHANGE.md](INTERCHANGE.md) for current scope and receipts. The host
investigation below remains the evidence that led to that implementation.

## Original media and results

Images came from [pski/model2archive](https://github.com/pski/model2archive/tree/fa76dabb8c41d915cb27c54985555bc9e29baabd/Software/CPM),
pinned at `fa76dabb8c41d915cb27c54985555bc9e29baabd`.
The archive labels ATN223IS as ATON 2.23I single-sided, ATN225BS/BD as
ATON 2.25B single/double-sided, and the LB images as Lifeboat Model II CP/M.
[Source paths, hashes and tool revision](sources.json) · [Complete receipt](host-results.json)

| Original IMD | Sides | Original files | Probe bytes | Highest block | Result |
|---|---:|---:|---:|---:|---|
| ATN223IS.IMD | 1 | 19 | 473,088 | 299 | Host pass |
| ATN225BD.IMD | 2 | 31 | 954,368 | 607 | Host pass |
| ATN225BS.IMD | 1 | — | — | — | Rejected: track 34 IDs are 1,2,3,4,5,5,5,5 |
| LB224A.IMD | 1 | 52 | 24,576 | 299 | Host pass |
| LB225D.IMD | 1 | 39 | 274,432 | 299 | Host pass |
| LB225DF80.IMD | 1 | 7 | 503,808 | 299 | Host pass |

All six original images are retained unchanged, including the malformed image.
The five accepted images have no unavailable, deleted-data or error-marked
sectors, and their recorded cylinder/head values match their track headers.
The double-sided image uses alternating heads. Per-track sector order is
recorded in the receipt and preserved when rebuilding the written IMD copy.

## The 11,520-byte prefix and corrected allocation bounds

The first physical surface, cylinder 0/head 0, is **FM, 500 kbit/s,
26 × 128 bytes**, IDs 1–26: 3,328 bytes. Every remaining surface is
**MFM, 500 kbit/s, 8 × 1,024 bytes**, IDs 1–8: 8,192 bytes.
These rates and encodings are recorded by IMD mode 0 and mode 3 respectively.
The first two surfaces are reserved, giving `3,328 + 8,192 = 11,520` bytes.
For single-sided disks these are cylinders 0 and 1; for double-sided ATON
they are cylinder 0 heads 0 and 1. The data areas therefore begin at
cylinder 2/head 0 and cylinder 1/head 0 respectively.

| Parameter | Single-sided ATON / Lifeboat | Double-sided ATON |
|---|---:|---:|
| Cylinders / physical surfaces | 77 / 77 | 77 / 154 |
| Raw sector-payload bytes | 625,920 | 1,256,704 |
| Data surfaces after reserved area | 75 | 152 |
| SPT / BSH / BLM / EXM | 64 / 4 / 15 / 0 | 64 / 4 / 15 / 0 |
| DSM / DRM | 299 / 127 | 607 / 191 |
| AL0 / AL1 | C0h / 00h | E0h / 00h |
| CKS / OFF | 32 / 2 | 48 / 2 |
| Logical sector order | 1,4,7,2,5,8,3,6 | 1,4,7,2,5,8,3,6 |

Exact 15-byte OEM DPB patterns are present in each accepted image's reserved
area. Their byte offsets and values are recorded in the receipt. The
single-sided pattern starts at raw offset 0xC30 in ATN223IS, 0x149 in LB224A,
and 0x1F0 in both LB225D images. The double-sided pattern starts at 0xC06 in
ATN225BD. These parameters agree with the physical bounds, complete file
extraction, fsck, and final-block write/read-back.

The [stock cpmtools rows](upstream-diskdefs.txt) combine offset 11,520 with
77 data tracks for `trse` and 154 for `trsf`. cpmtools calculates capacity
from `seclen * sectrk * (tracks - boottrk) / blocksize`; the byte offset is
additional. Consequently both ATON rows overstate capacity by **eight 2 KiB
blocks (16 KiB)**: stock DSM 307/615 versus actual DSM 299/607.
The `trs5` row correctly specifies 75 data tracks and DSM 299.
The local [diskdefs](diskdefs) use 75 and 152 data surfaces with offset 11,520.
They describe raw filesystem views, not a uniform physical disk geometry.

## Verification scope

The IMD decoder checks each track and sector, then sorts payloads by physical
cylinder/head/sector ID. A separate Python filesystem reader applies the
logical sector order and reads 16-bit allocation pointers. Its extraction of
all original files matches cpmtools byte for byte. cpmtools writes a
position-varying deterministic probe filling every free block; Python and
cpmtools independently recover it. Both readers preserve every original file.
The allocated block set ends at 299 or 607 and fills the actual data area.
The raw length and all 11,520 reserved bytes remain unchanged. Repacking
preserves IMD comment, track headers and sector order, and decoding that copy
reproduces every written raw byte. fsck passes before and after each write.

These runs used three workers with independent writable images. They execute
no historical COM program and do not alter the original downloads.

The Homebrew cpmtools/libdsk build aborts on the raw offset because 11,520 is
not divisible by the configured 1,024-byte sector size. The pinned cpmtools
source was therefore built with its POSIX device backend (`./configure`,
without a `--with-libdsk` argument). This host result is not a libdsk pass.

## Backend and architecture boundaries

The generic FDF/converter path describes uniform track layouts. Merely
declaring 77/154 MFM surfaces would imply a 16,384-byte reserved area and a raw
image 4,864 bytes longer than these originals. A platform can own a special
boot-track mapping, but that contract must be explicit. Current FDF support
for different sector sizes *within a track* does not describe this exception
between tracks. Mixed-track formats remain deferred in
[Stage 8 reconciliation](../../155%20Stage%208%20Architecture%20Reconciliation.md).

The existing Model 4 converter also rejects 8 × 1,024-byte sectors at its
6,378-byte DMK track length. [Recorded rejection and capacity checks](backend-limits.json).
Double-sided ATON additionally needs CKS 48; current binding validation accepts
at most 32. Reducing CKS, discarding the boot track, or changing sector sizes
would change the tested contract and is not silently substituted here.

The [pinned Model II fork catalogue](fork-M2DISK.FDF) uses **16 × 512** for
`PT2SS` and `BCM2SS`, whereas these originals use **8 × 1,024**. SPT 64 does
not make them physically interchangeable; ATON/Lifeboat also need the skew-3
logical sector order. The fork's comment explicitly assigns its exceptional
FM boot surface to Model II platform code. Source:
[a-griff/BetterCPM at e24f4b58](https://github.com/a-griff/BetterCPM/blob/e24f4b5859e9d9c5abcb044e1eaafe12d3e72c64/src/platform/trs80m2/M2DISK.FDF).

Before catalogue promotion, choose and implement an explicit mixed-track
adapter/platform contract, then run BetterCP/M guest interchange on it.
A normalized data-area test can be useful separately but cannot qualify the
original physical layout. No architecture or BIOS limits are changed here.

## Reproduce

Obtain the six pinned originals and build the pinned cpmtools POSIX backend.
Run from the repository root with a new results directory:

```sh
python3 -B docs/engineering/evidence/2026-11-06-model2/inspect_images.py \
  --images /path/to/originals --cpmtools /path/to/cpmtools-posix \
  --output /path/to/new-results --jobs 3
```

The originals and receipts are indexed in the
[reference collection](../../../../metadata/disk-image-reference/model2-investigation.json).
