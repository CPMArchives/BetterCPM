# Engineering Specification 186: FDB Build and Media Packaging

## Result

The normal host build now compiles `metadata/DISK.FDF` into
`build/catalog/DISK.FDB`, independently reads the completed binary, and requires
107 supported descriptors before publishing it. Temporary-file read-back and
atomic replacement prevent a failed compilation from replacing a previously
valid output.

Both release-target media builders install that exact 8,320-byte `DISK.FDB` as
an ordinary user-zero CP/M file. This specification originally retained the
historical `DISK.FDF` during CONFIG's transition. Engineering Specification 192
completed the native reader and removed that runtime text copy. The native
build disk also carries `DISK.FDB`; it does not carry the 51 KiB host FDF source.
BetterCP/M 1.0 has no native FDF compiler, and that unnecessary copy would
reduce the 800K build disk to two free allocation blocks.

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

This increment supplied and packaged the catalogue. Engineering Specifications
187 through 192 subsequently completed native validation, selection, binding,
runtime transition, and release-media cleanup.
