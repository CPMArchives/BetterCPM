# Engineering Specification 61: Function 40 Live FCB Reads

## Milestone

BetterCP/M now preserves an activated FCB when Random Read follows Function 40
in the same logical extent before Close. This fixes the first independent
compatibility-suite failures, cases 0602, 0603, and 0605.

## Defect

Function 40 correctly allocated and initialized a block, wrote the caller's
record, and updated the live FCB. Random Read then unconditionally reopened the
extent from its older on-disk directory entry. Because CP/M applications may
read through the same FCB before Close, that reopen discarded the new allocation
map and record count too early.

Random Read now compares the requested EX/S2 with the activated FCB. For the
same extent it retains the live allocation and RC state; an extent transition
continues to use the ordinary directory Open path.

## Verification

The regression reproduces `ENTRYTST`'s lifecycle exactly: Make an empty file,
write random record 2 with Function 40, then read records 0, 1, and 2 without
closing. Records 0 and 1 must contain zeros and record 2 must contain the
caller's `A5h` pattern.

On the regenerated physical compatibility disk, independent `trs80gp` runs of
`ENTRYTST /0602`, `/0603`, and `/0605` each report one pass, zero failures,
zero errors, and zero observations.

## Resident layout

The correction exceeded the former Directory Services region by 39 bytes.
Directory Services therefore moves from `D700h` to `D600h`, consuming 256 bytes
of the existing unused gap above BDOS. Its vector order is unchanged; the CCP
remains at `E940h` and the BIOS remains at `EF00h`.

Native CP/M and cross builds must remain byte-identical at the revised address.
