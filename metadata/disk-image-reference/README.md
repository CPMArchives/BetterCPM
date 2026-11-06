# Disk-image reference collection

Preserve independently sourced disk images for format investigation, regression tests, and interchange checks. Keep pristine downloaded bytes in immutable archives. Keep manifests, expected results, and reproduction scripts in this repository.

## Available collection

| Collection | Images | Definitions | Qualification |
|---|---:|---|---|
| [Amstrad CPC](cpc.json) | 4 | CPCSYS, CPCDATA | All four images passed on cpmsim and trs80gp. Physical-media interchange is untested. |
| [Amstrad PCW](pcw.json) | 1 | PCW | cpmsim and trs80gp passed, with identical written image hashes. Physical-media interchange is untested. |
| [Ampro investigation](ampro-investigation.json) | 7 surveyed; 1 synthetic | AMP3 candidate only (`amp3`/`amp5`) | Vendor-source agreement and synthetic cpmsim pass. Original 80T SS image missing; Model 4 guest I/O untested. |
| [Model II investigation](model2-investigation.json) | 6 originals; 5 usable | ATONSS / ATONDS | Five cpmsim RAM write/read-back passes through the canonical adapter; one malformed image rejected. Model 4 and ROM remain unsupported. |
| [Pickles & Trout](pickles-trout.json) | 3 originals | PT2SS | Three cpmsim RAM passes, including master-disk random tail records. Model 4 and ROM remain unsupported. |
| [Bondwell 14](bondwell14.json) | 9 originals | BW14 | cpmsim RAM and trs80gp passed all files and final-block writes with FDF.RSX first; identical written images. |

The CPC archive is `BetterCPM-CPC-Reference-Images-2026-11-05.zip`, 177,908 bytes, SHA-256 `f807bd15481b2a6ea9111ed55b841bbecf011f3352c17e23c12a945d3ac7fe1f`. The maintainer holds a durable copy identified in the manifest. Other contributors can obtain the same originals from the pinned source URLs or request the archive from the maintainer if a source disappears.

The archive contains four original Extended CPC DSK files, a collection manifest, both emulator receipts, and SHA256SUMS for the contents. Its manifest describes the original collection. The repository manifest additionally identifies the completed archive. Expected file hashes come from the independent cpmtools/libdsk extraction verified during qualification.

## Use a collection

1. Extract the archive into a reference directory and verify SHA256SUMS. Preserve the originals in that directory.
2. Use the collection's pinned repository revision and documented converter to generate disposable emulator images in a fresh run directory. Retain the original sector IDs, order, and payloads and verify conversion before guest testing.
3. Run the required guest operations and compare recovered files with the independent expected hashes. Verify new writes through the final allocation block and preserve reserved tracks.
4. Retain the receipt with emulator and system-image hashes. Record the source image hash and converter revision so generated media can be reproduced.
5. Record qualification separately for each backend and physical media. Preserve partial, failed, and completed outcomes accurately.

The [CPC qualification runner and instructions](../../docs/engineering/evidence/2026-11-05-cpc/README.md) implement this process. Pass the archive's extracted `originals` directory to `--images` and a new disposable directory to `--output`. Its conversions use `tools/convert_fdf_image.py` and the boot-image builders from the pinned repository revision.

Independent disk-image trials may run concurrently with a separate emulator process and private writable media for each trial. Each disk's read-back follows its own write. The shared Amstrad runner accepts `--jobs N` to run image trials in separate worker processes with private media. It defaults to one worker and accepts `--manifest` for a pinned image set. Every completed trial saves its own receipt even if a different trial fails.

## Add reference images

Prefer images that add coverage, including populated user areas, differing sector orders, allocation boundaries, unusual sector IDs, and independently produced files.

For each image record the source URL, download date and its basis, SHA-256, size, container, machine, description, FDF identifier, cpmtools format, and libdsk driver or format when applicable. Preserve unknown or conflicting mappings explicitly. For CPC, libdsk reads physical geometry from the Extended DSK sector headers, while cpmtools selects `cpcsys` or `cpcdata` for the filesystem layout.

Obtain an independent file inventory and hashes where the source is readable. Keep the original even when investigation reveals a format conflict or damaged sector. Admit an image to the reference collection with its actual status and keep format qualification tied to completed evidence.

Create a new archive for each admitted batch, verify its contents and checksum, preserve a durable copy, and record its identifier in the manifest. Add the manifest and reproduction instructions to the repository and link the relevant format or qualification record. Keep generated images in disposable run directories and preserve expensive or otherwise irreproducible results with their receipts.
