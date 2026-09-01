# Engineering Specification 74: File Read-Only Terminal Path

## Status

Implemented and physically qualified on the TRS-80 Model 4 target.

## Compatibility behavior

CP/M 2.2 does not normally return to a transient program after that program
attempts to write through an FCB carrying the file read-only attribute. The
resident BDOS reports `File R/O` and abandons the transient through WBOOT.

BetterCP/M previously refused the mutation safely but returned `FFh`. The BDOS
now detects the FCB attribute before sequential, random, or zero-fill random
write dispatch, prints the resident error, and transfers through the BIOS WBOOT
vector. The lower directory layer retains its non-mutating refusal as defense
in depth.

## Fixture correction

Host files do not carry CP/M directory attributes. The generated compatibility
disk now explicitly sets T1 bit 7 on `BTRO.DAT`, making it the canonical file
read-only fixture expected by the suite.

## Physical result

Both terminal procedures display the required message and return to a usable
CCP prompt:

```text
A>RANDTEST /0368
...
File R/O
A>

A>RANDTEST /0369
...
File R/O
A>
```

Case 0368 covers Sequential Write and case 0369 covers Random Write. Automated
runs used private disk copies, and the reproducible source image remained
unchanged. Native ZSM4 and cross assembly produce 1,950 byte-identical BDOS
bytes. The BDOS and composed-system regressions pass.

These two procedures complete physical qualification of all 41 required
RANDTEST catalog items. The remaining RANDTEST entries are diagnostic,
not-guaranteed observations or the explicitly out-of-scope private DRI seek
implementation.

