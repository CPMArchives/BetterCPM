# Engineering Specification 25: Allocation and DPB Pointers

## Milestone

BetterCP/M now implements BDOS function 27 (Get Allocation Vector Address) and
function 31 (Get Disk Parameter Block Address). Applications can inspect the
current drive's live allocation and format state through `CALL 0005h`.

## System Services boundary

Two entries extend the provisional System Services vector table:

- `E815h`: return the current drive's allocation-vector address; and
- `E818h`: return the current drive's DPB address.

These vectors keep BDOS independent of private directory-component labels and
layout. Before returning either pointer, System Services checks its login-valid
state. An invalidated context is relogged and its allocation state rebuilt;
failure is returned without publishing a stale pointer.

The vector addresses are provisional internal interfaces. The pointers they
return are compatibility-visible only for the current valid drive and must be
queried again after reset, selection, relogin, or another invalidation event.

## Function 27

Function 27 returns in `HL` the base of the current drive's live allocation
vector. Its length is derived from the DPB as `(DSM/8)+1`, with high-bit-first
allocation-block mapping.

For the empty MM 790K development disk, the first allocation byte is `C0h`:
the first two 2K blocks are reserved for the 128-entry directory. The remaining
allocation bits are reconstructed during login from live directory extents.

Applications may inspect this BDOS-maintained object. Arbitrary application
writes through the pointer have no portable meaning, and the vector's accuracy
while its drive is software write-protected is not guaranteed by CP/M 2.2.

## Function 31

Function 31 returns a pointer to the current drive's live, BIOS-supplied DPB.
The test decodes all 15 bytes of the MM 790K definition:

- `SPT=80`;
- `BSH=4`, `BLM=15`, `EXM=0`;
- `DSM=394`, `DRM=127`;
- `AL0=C0h`, `AL1=00h`;
- `CKS=32`; and
- `OFF=2`.

The DPB is format data, not a universal BetterCP/M constant. Different drives
may use distinct definitions or share one. Its documented mutability will be
important to the future CONFIG utility, but callers must follow the eventual
apply/invalidate/relogin contract rather than changing format fields blindly.

## Return convention

Both functions use the established 16-bit path, returning the pointer in `HL`
with `A=L` and `B=H`. A storage failure is mapped to the current provisional
`FFh` failure result rather than exposing a stale address.

## Verification

Direct tests compare both returned pointers with the selected BIOS DPH,
validate the reserved ALV bits, and decode the complete DPB. The resident test
queries both through an application `CALL 0005h` and validates their contents.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical components: 903 bytes for directory/System Services and 336
bytes for BDOS.

## Next increment

Implement BDOS functions 17 and 18 (Search First and Search Next), copying
matching 32-byte directory entries into the selected DMA buffer in directory
order. This will make function-26 DMA state observable through a standard
read-only file operation before any directory mutation is introduced.
