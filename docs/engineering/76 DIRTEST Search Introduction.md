# Engineering Specification 76: DIRTEST Search Introduction

## Status

DIRTEST is installed, and its Search group is physically qualified on the
TRS-80 Model 4 target.

## System changes

The reproducible conformance disk now carries `DIRTEST.COM`. BDOS Search First
recognizes FCB drive byte `3Fh` (`'?'`) as CP/M's special current-drive,
all-user directory enumeration request instead of rejecting it as an ordinary
invalid drive.

The generated media also installs independent `BTUSR.DAT` copies in users zero
and one. The copies receive separate allocation blocks so user-scoped Delete
or Rename testing cannot corrupt the surviving user's fixture.

## Required results

All nine required Search cases pass physically:

```text
0196  P  R  Search slot=01; next=01
0198  P  R  Attribute search=03; next=00
0200  P  R  Explicit result=01; next=00
0202  P  R  Users found mask=03
0204  P  R  First=00; next=01
0206  P  R  First=00; next=FF
0208  P  R  Search=00; next=42
0210  P  R  First DMA=00; next=01
0212  P  R  Repeat first=00; next=01
```

This covers returned directory-entry layout, attribute comparison,
explicit-drive search, all-user search, continuation and exhaustion, DMA
selection changes, and repeat-search ordering stability.

## Diagnostic observations

```text
0214  O  N  Before drive change=00; next=FF
0216  O  N  Failed search=FF; next=A5
```

These observations have no CP/M 2.2 conformance effect. Native ZSM4 and cross
assembly produce 1,955 byte-identical BDOS bytes; BDOS and composed-system
regressions pass.

