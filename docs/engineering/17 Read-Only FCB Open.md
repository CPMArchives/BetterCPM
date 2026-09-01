# Engineering Specification 17: Read-Only FCB Open

Status: Implemented and verified internal service
Date: 2026-09-01

## Result

System Services now activates an existing exact directory extent into a
33-byte sequential CP/M File Control Block. This is the first read-only FCB
Open result, built above the BIOS and directory/login layers.

The service accepts a user number in `A` and an FCB pointer in `DE`. For the
current drive-A carrier it:

1. validates FCB drive byte 0 (current) or 1 (A);
2. searches the logged-in directory for the exact user and 8.3 identity;
3. selects an exact `EX` and `S2` extent;
4. rejects a directory `RC` outside the documented range 0 through 128;
5. copies directory bytes 1 through 31 into FCB bytes 1 through 31; and
6. returns the matching directory slot code 0 through 3.

No match returns `FFh`. The directory user byte is not copied over the FCB
drive byte. FCB byte 32 (`CR`) remains caller-owned and unchanged.

## Extent and FCB fields

The implementation treats:

- `EX` as the low five-bit requested extent;
- `S1` as opaque reserved state copied from the directory entry;
- the low six bits of `S2` as the requested extent module;
- `RC` as the extent's valid-record count, constrained to 0..128; and
- bytes 16..31 as the disk-format-dependent allocation state established by
  the matching directory extent.

Filename and extension attribute bits do not participate in identity matching,
but the actual directory bytes—including attributes—are copied into the
activated FCB.

## Compatibility basis

This behavior follows the project's CP/M 2.2 FCB/Open compatibility evidence:
successful Open supplies directory/allocation state, preserves the FCB drive
selection and caller-managed `CR`, returns a directory code 0..3, and returns
`FFh` when the identity is absent. DRI-private high-`S2` dirty state is not
copied as an implementation requirement.

## Deliberate limits

This is an internal exact-open service, not yet the public BDOS function-15
dispatcher. It currently supports:

- exact names only, without `?` wildcards;
- `EXM=0`, as used by the MM 790K carrier;
- current drive/A only; and
- an explicitly supplied user number.

Physical BIOS failures retain the internal storage error path; the eventual
BDOS boundary must apply the specified CP/M disk-error presentation rather
than confuse an internal status with a successful directory slot.

## Verification

The binary fixture constructs an extent in directory slot 2 with `EX=3`, an
opaque nonzero `S1`, `S2=2`, `RC=34`, attribute bits, and a distinctive
allocation map. Open returns 2 and copies bytes 1..31 exactly while preserving
the FCB drive byte and a caller `CR` of 9.

It separately verifies that a requested `EX=4` returns `FFh` without changing
the FCB and that `RC=129` is rejected. All prior allocation, login, directory,
BIOS, boot, and physical disk tests continue to pass.

Native CP/M ZSM4/Digital Research LINK and the host cross assembler produce
the same 785-byte component.

## Build diagnostics

The cross build now retains an assembler listing in the ignored build tree.
This records exact addresses and makes native-era relative-branch range errors
diagnosable without altering the source or binary.

## Next increment

Implement `EXM`-grouped extent selection and RC adjustment, then add `?`
wildcard matching and first-match activation. Those are the remaining search
semantics before connecting this service to a public BDOS function-15 entry.

Engineering Specification 18 completed grouped extents and wildcard-first
activation. The Open engine is now ready to be placed behind an initial BDOS
function dispatcher.
