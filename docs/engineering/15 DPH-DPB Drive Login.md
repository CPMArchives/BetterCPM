# Engineering Specification 15: DPH/DPB Drive Login

Status: Implemented and verified
Date: 2026-09-01

## Result

System Services now establishes explicit drive-login state from the DPH and
DPB returned by BIOS `SELDSK`. Directory searches no longer compile in the MM
790K directory bound or reserved-track offset.

Login records the selected drive and obtains:

- sectors per logical track (`SPT`);
- highest allocation block (`DSM`);
- highest directory entry (`DRM`);
- reserved directory allocation masks (`AL0` and `AL1`);
- reserved logical tracks (`OFF`); and
- the BIOS allocation-vector address from the DPH.

It derives the number of 128-byte directory records from `DRM`, derives the
allocation-vector byte count from `DSM`, and uses `OFF` and `SPT` to translate
each directory-record index into a BIOS logical track and sector.

## Allocation-vector initialization

Login clears the DPB-sized allocation vector and installs `AL0` and `AL1`,
thereby marking the directory's reserved allocation blocks. For the MM 790K
DPB this produces a 50-byte vector beginning `C0h,00h`.

This is the initialization stage, not yet a complete logged-in allocation
map. File-owned blocks from live directory extents are not marked until the
next increment. Consequently filesystem mutation must remain disabled: using
the partially initialized vector to allocate blocks could overwrite files.

## Validity and invalidation

Login state begins invalid. A directory read automatically logs in drive A if
needed. The new invalidation service clears the validity byte; the next access
must read the DPH/DPB again. A failed or unsupported login leaves the state
invalid.

The present compact implementation accepts an `SPT` from 1 through 255, a
directory-record count fitting in eight bits, and an allocation-vector length
fitting in one byte. Unsupported larger DPBs fail rather than being truncated.
These limits cover the current MM 790K carrier and are explicit candidates for
later widening.

## Verification

The binary fixture obtains the production DPH and DPB through BIOS, dirties the
allocation vector, and verifies that login clears all 50 bytes and reinstalls
the `C0h,00h` directory mask.

It then changes the test DPB from `DRM=127, OFF=2` to `DRM=7, OFF=3`, explicitly
invalidates login state, and logs in again. An unsuccessful directory search
then performs exactly two reads instead of 32 and begins at logical track 3.
This proves the bounds and location are reloaded state rather than MM constants.

All prior exact-match, attribute-bit, error-propagation, BIOS, boot, and disk
tests continue to pass. Native CP/M ZSM4/Digital Research LINK and the host
cross assembler produce the same 426-byte component.

## Preserved implementation history

The component's private DMA buffer was provisionally at `E900h` through
Engineering Specification 14. Login enlarged the code beyond that boundary,
so the buffer moved intact to `EA00h`. A dated source comment retains the old
placement and reason for the change.

## Next increment

During login, scan every ordinary directory extent and mark each valid
file-owned allocation block in the allocation vector. Add duplicate,
out-of-range, deleted-entry, and reserved-metadata tests before permitting any
file-creation or block-allocation operation.

Engineering Specification 16 completed allocation reconstruction for both
8-bit and 16-bit CP/M allocation entries. File mutation remains deferred until
FCB and extent semantics are implemented and tested.
