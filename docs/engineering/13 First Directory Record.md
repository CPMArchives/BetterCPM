# Engineering Specification 13: First Directory Record

Status: Implemented and verified
Date: 2026-09-01

## Result

BetterCP/M now contains its first filesystem-facing System Services code.  The
new component reads the first 128-byte directory record of drive A exclusively
through the public CP/M BIOS vectors.

It performs this sequence:

1. select drive A and reject an unavailable drive;
2. select logical track 2, taken from the current MM 790K `OFF` value;
3. select logical sector 0;
4. set a private 128-byte DMA buffer;
5. call BIOS `READ`; and
6. return the BIOS error unchanged or expose the loaded record.

The operation maps through the production BIOS to cylinder 2, side 0, physical
sector ID 1, quarter 0.  No Model 4 hardware knowledge or MM sector interleave
has entered the filesystem layer.

## Initial entry classification

A second service scans the four 32-byte directory entries in the loaded record
and returns the first ordinary CP/M entry whose user byte is 0 through 15.
Deleted entries (`E5h`) and other reserved metadata entry types are skipped.

The scanner does not yet compare filenames, interpret extents, or build an
allocation vector.  It preserves every directory byte unchanged, including
the attribute bits carried in the high bits of filename and extension bytes.
This narrow classification therefore does not foreclose CP/M-compatible
timestamps or other reserved directory metadata.

## Architectural boundary

The directory component is above the BIOS and uses only its standard entry
points.  It is not incorporated into the Model 4 BIOS.  Its provisional
`E800h` code placement, `E900h` buffer, and `F000h` BIOS base are bring-up
addresses pending the resident-memory specification.

Two provisional internal vectors expose record loading and first-entry
classification without making callers depend on routine sizes.  These are not
yet CP/M BDOS entry points.

## Verification

The binary execution fixture combines the independently assembled directory
component with the production BIOS.  Only the lowest physical-reader routine
is instrumented.  It verifies:

- the exact cylinder, side, and physical sector selected by the BIOS;
- transfer through the BIOS physical scratch buffer and DMA copy;
- an empty record containing four deleted entries;
- skipping reserved metadata before an ordinary user-7 entry;
- preservation of the 11-byte CP/M filename/extension field; and
- unchanged propagation of a physical-read error.

Native CP/M ZSM4/Digital Research LINK and the host cross assembler produce
the same 69-byte component.

## Next increment

Generalize the reader across all directory records described by `DRM`, then
implement an exact 8.3 name and user-number match without yet interpreting or
opening extents.

