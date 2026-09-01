# Engineering Specification 14: Exact Directory Search

Status: Implemented and verified
Date: 2026-09-01

## Result

The initial System Services directory component now searches all 128 entries
of the temporary MM 790K drive-A directory.  It reads 32 logical directory
records through the standard BIOS interface and examines four 32-byte entries
per record.

The component exposes four provisional internal services:

1. load directory record zero;
2. return the first ordinary entry in record zero;
3. load a specified directory record from 0 through 31; and
4. search the whole directory for an exact user-number and 8.3 name match.

The first two vectors remain in their original positions so that this
increment does not silently invalidate the milestone-13 interface.

## Exact-match rules

The search accepts a user number from 0 through 15 and a pointer to an
11-byte, blank-padded CP/M filename and extension.  A match requires:

- the directory entry's user byte to equal the requested user number; and
- all eleven name/extension bytes to match after masking bit 7 on both sides.

Masking bit 7 prevents CP/M file attributes from changing filename identity.
No wildcard matching, extent selection, or FCB mutation is performed yet.
Deleted entries and reserved metadata entries cannot match an ordinary user
number and are skipped naturally.

The return is `A=0` with `HL` pointing at the matching 32-byte entry, `A=FFh`
when no entry exists, or the unchanged BIOS error status when a read fails.

## Current format dependency

The 32-record bound follows the current drive's `DRM=127`.  Track 2 and the
record count remain explicit MM 790K bring-up parameters in System Services;
they are not embedded in the geometry-neutral BIOS.  A later drive-login
increment will obtain these values from the selected drive's DPH/DPB rather
than compile them into the directory component.

## Verification

Binary execution verifies:

- exact user and 8.3 matching;
- rejection of a different name;
- rejection of the same name in a different user area;
- matching despite directory attribute bits;
- exactly 32 BIOS reads for a complete unsuccessful search;
- final-record mapping to cylinder 2, side 0, physical sector ID 6; and
- continued BIOS and directory error propagation behavior.

Native CP/M ZSM4/Digital Research LINK and the host cross assembler produce
the same 183-byte component.

## Next increment

Introduce drive-login state derived from the DPH and DPB, including directory
record bounds, allocation-vector initialization, and an explicit invalidation
rule.  The exact search can then stop depending on compiled MM 790K values.

Engineering Specification 15 completed the table-driven login and reserved
allocation initialization. Reconstructing file-owned allocation bits remains
the next step before the vector is safe for filesystem mutation.
