# Engineering Specification 37: Set File Attributes

## Milestone

BetterCP/M now implements BDOS function 30 (Set File Attributes), completing
the contiguous CP/M 2.2 BDOS function range 12 through 32 in the current
filesystem and drive-control layer.

## Call and result contract

Function 30 receives an FCB in `DE`. The low seven bits of bytes 1 through 11
form the filename/type match pattern; `?` matches any character. The high bit
of each corresponding FCB byte is the desired attribute value.

`A=00h` reports that at least one extent was updated. `FFh` reports no match,
invalid drive, software write protection, or a pending-allocation conflict.
Internal storage failure is carried separately and currently also maps to
`FFh` at the BDOS boundary.

## Attribute update

Every matching extent in the current user area is updated. For each of the
eleven filename/type bytes, System Services preserves the directory byte's low
seven bits and replaces only bit 7 from the caller FCB. This supports the
traditional T1 read-only, T2 system, and T3 archive positions while remaining
faithful to CP/M's full eleven-byte attribute representation.

Set Attributes intentionally does not reject a file whose read-only bit is
already set: clearing or changing that bit is the purpose of the function.
Current-drive software protection is still enforced before media access.

## Coherence and failures

The operation refuses to run while pending allocation ownership exists. Only
directory records containing a match are written, and completion invalidates
cached login state. As with Delete and Rename, multi-record updates cannot be
globally atomic on CP/M media; a later physical failure is reported and forces
the next operation to rescan the actual directory.

## Verification

Executable tests create two wildcard-matched extents, set high bits in both a
filename byte and type bytes, and verify that every low seven-bit character is
unchanged. A second call clears all eleven attribute bits. Software protection
is verified through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services and BDOS binaries.

## Next increment

Engineering Specification 38 begins the random-record cluster with function 35
(Compute File Size). The next increment is function 36 (Set Random Record),
which converts the current sequential position into the same 24-bit form.
