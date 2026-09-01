# Engineering Specification 18: Grouped and Wildcard Open

Status: Implemented and verified internal service
Date: 2026-09-01

## Result

The read-only FCB Open service now implements DPB `EXM` grouping and `?`
wildcards. It can activate the first matching directory extent across the
standard CP/M filename/type identity while retaining the caller's requested
logical extent.

## Extent-group matching

Login retains the DPB extent mask and rejects values above 15. Open compares
directory and requested `EX` after clearing the low bits selected by `EXM`.
The low six bits of `S2` must also match. Thus one physical directory entry can
represent the group of logical extents defined by the selected disk format.

After copying directory state, Open restores the caller's requested `EX` and
derives its working `RC` from the directory entry:

- requested `EX` less than directory `EX`: `RC=128`;
- requested `EX` equal to directory `EX`: use the stored directory `RC`; and
- requested `EX` greater than directory `EX`: `RC=0`.

The last case is reachable only within the same `EXM` group. It represents a
logical subextent beyond the directory entry's recorded end.

## Wildcard identity

In any of the eleven filename/type positions, a caller byte `?` matches the
corresponding directory character. Attribute bits remain excluded from the
comparison. On success the actual directory name, type, and attributes replace
the wildcard pattern in FCB bytes 1..11.

Scanning remains in directory order. The first matching entry is activated and
its zero-based slot within the 128-byte directory record is returned.

## Verification

The binary fixture changes the test DPB to `EXM=3` and creates three live
directory entries. It verifies:

- a wildcard matching two names activates the first directory entry;
- a grouped request for `EX=1` against directory `EX=3` returns `RC=128`;
- a request for `EX=3` returns the stored `RC=37`;
- the caller's requested `EX` and `CR` are preserved;
- `EX=4` does not cross into the preceding `EXM=3` group; and
- ordinary exact Open behavior remains unchanged.

Native CP/M ZSM4/Digital Research LINK and the host cross assembler produce
the same 866-byte component. All allocation, directory, BIOS, boot, and
physical disk regressions continue to pass.

## Function-15 boundary status

Engineering Specification 19 now places this engine behind an independently
buildable BDOS function-15 dispatcher for the initialized current-user,
drive-A case. The wider public boundary still needs:

- BDOS call dispatch through address `0005h` conventions;
- mutable current user and current/default drive state;
- temporary explicit-drive selection and restoration;
- and final CP/M-compatible disk-error presentation distinct from directory
  slot codes.

## Next increment

Install the public page-zero call gateway and define the minimum resident-image
composition and initialization path. Explicit-drive restoration can then be
widened without restructuring the Open engine.
