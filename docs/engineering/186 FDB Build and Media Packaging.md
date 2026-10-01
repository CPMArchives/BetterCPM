# Engineering Specification 186: FDB Build and Media Packaging

## Result

The normal host build now compiles `metadata/DISK.FDF` into
`build/catalog/DISK.FDB`, independently reads the completed binary, and requires
107 supported descriptors before publishing it. Temporary-file read-back and
atomic replacement prevent a failed compilation from replacing a previously
valid output.

Both release-target media builders install that exact 8,320-byte `DISK.FDB` as
an ordinary user-zero CP/M file. During the transition, they also retain the
historical `DISK.FDF` required by the current CONFIG implementation. The native
build disk carries `DISK.FDB` so a system built from it has the runtime catalogue
available for the forthcoming CONFIG reader. It does not carry the 51 KiB host
FDF source: BetterCP/M 1.0 has no native FDF compiler, and that unnecessary copy
would reduce the 800K build disk to two free allocation blocks.

## Focused evidence

`tools/test_fdb_packaging.py` performs two independent builds, requires byte
identity, validates all 107 descriptors, installs the result through the native
build-disk filesystem writer, extracts it through the independent directory
reader, and validates the recovered bytes again.

Real TRS-80 and z80pack media builds complete with the added file. Extraction
of `DISK.FDB` from the generated z80pack system image matches the host artifact
byte for byte with SHA-256
`4dea7bd989580fc13f61e79d47e92466a440799c41b002f4caba65ec8f893c03`.
The native build disk retains ordinary capacity after omitting the unused text
source copy.

## Boundary

This increment supplies and packages the catalogue only. CONFIG still reads the
historical text file and cannot select FDB descriptors yet. Replacing that path
with the validated FDB reader and normalized-binding transaction is the next
Step 4 implementation increment.
