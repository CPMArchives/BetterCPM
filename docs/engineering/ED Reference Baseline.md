# ED reference baseline

## Selected target

BetterCP/M ED targets DRI's CP/M 2.2 context editor, with only simple DU addressing
and standalone `/VER` added. This is a behavioral Z80/ZSM4 reimplementation.
The reference source is not compiled by BetterCP/M, and no PL/M toolchain is
added to its build. The invocation/build foundation has started; the text buffer, first inline/line commands and T display are now checked against the stock oracle, while the interactive/file engine remains incomplete.

The [accepted engineering specification](ED%20Specification.md) governs scope.
Exact artifact identities are in
[third_party/dri-ed/provenance.json](../../third_party/dri-ed/provenance.json).
This baseline is specific and reproducible; it is not a claim to have found the
last ED bug-fix revision ever shipped with CP/M 2.2.

## PL/M source

The source is `cpm2-plm/ED.PLM` from the project's supplied `cpm2-plm(1).zip`.
It is retained as `third_party/dri-ed/ED.PLM` without newline normalization.
It identifies DRI copyright 1976–1979 and records PRL modifications in May 1979
and CP/M 2.0 modifications in August 1979. Those comments describe its ancestry;
they do not turn this into a CP/M 3 or third-party editor target.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Supplied source ZIP | 273,825 | `706cc4c90d35d6c1f2b521309b539207b5bc54fea034b01c377a5f50e8bf348f` |
| `ED.PLM` | 50,062 | `8e3d68d21e5e92c11c789f17578133f2e45f675d103b335702632617c67b4a07` |

The source archive is catalogued as original CP/M 2.2 source at the
[DRI source archive](https://www.cpm.z80.de/source.html). Its included
`README.TXT`, retained as `archive-README.TXT`, identifies the Caldera `PLM.ZIP`
release and describes a BDOS-only difference between archives. The supplied ZIP
has a macOS directory wrapper and `__MACOSX` entries. Its hash identifies the
actual archive used here, not an independently retrieved original Caldera ZIP.
No ED source modification is claimed by that README. Full historical source
chain verification and behavioral source/binary correspondence remain separate
qualification evidence, not assumptions inferred from the archive label.

## Stock binary oracle

`ED-CPM22-reference.COM` is extracted without rebuilding or patching from:

```text
Repository: https://github.com/udo-munk/z80pack
Commit:     b7a6fa36a2ee185a73727dc5b56ac1af40679e81
Disk:       cpmsim/disks/library/cpm22-1.dsk
Filesystem: ibm-3740
Entry:      user 0, ED.COM
```

The disk SHA-256 is
`86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2`.
The stock ED binary is 6,656 bytes, SHA-256
`adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f`.
Its embedded identity is DRI copyright 1979. This is the CP/M 2.2 binary oracle;
a newly compiled source image must not be substituted for it.

The source ZIP also supplies an ED.COM. That member is retained as
`ED-source-archive-reference.COM`, 6,563 bytes, SHA-256
`713ac9fd3a13b2a65d4825c2034faeaa9c2ecff88cc17ce51404c1fa71c66ad3`.
It has 3,025 differing bytes in the common prefix compared with the stock disk
binary. The mismatch is not only sector padding. This archive binary is useful
comparison evidence but is not the normative oracle. The cause has not been
qualified; do not label it a later feature revision or assume it merely fixes bugs.

## Manual edition

The primary documentation reference is Digital Research's
[CP/M Operating System Manual, July 1982](https://bitsavers.trailing-edge.com/pdf/digitalResearch/cpm/CPM_Operating_System_Manual_Jul82.pdf),
Section 2, The CP/M Editor. The rendered copyright page identifies **First
Printing: July 1982**. The scan is 9,796,253 bytes, SHA-256
`1cb4aec4fe99ae1958c2ef4e46d2910b5b913072ce188003c464d8258f89d44e`.
It is not vendored or required by the production build. The manual explains the
editor; the selected stock binary resolves observable disagreements.

The supplied `ED.pdf` is an earlier manual whose cover says copyright 1976,
1978. It is retained as background evidence in the project references, not as
proof of the complete CP/M 2.2 command set. Its hash is recorded in provenance.

The supplied HTML Operating System Manual ZIP has a September 1983 third-edition
index, but its `ch2.htm` contains a web challenge page rather than ED documentation.
It must not be mistaken for a usable ED chapter. The verified 1982 scan supplies
the manual baseline instead. No scripts from that HTML artifact were executed.

## Qualification handoff

Implementation must establish fixtures against the stock oracle before freezing
source-derived assumptions, particularly:

- E/H/O/Q transitions, their required standalone syntax and final logged drive;
- alternate-output collision, backup deletion and work-file placement;
- new-file, RO/SYS and interrupted-session behavior;
- verification default, letter case, numeric special values and buffer limits;
- R library lookup, X transfer-library lifetime and command/input controls;
- disk/directory failures and exact diagnostics.

Extend the verified drive rules to explicit DU state. Do not restore the caller
DU unconditionally: the accepted specification preserves historical exit-drive
behavior. DU users 16–31 require BetterCP/M-specific coverage beyond the stock
CP/M 2.2 namespace. Library names remain single-file operands, not selectors.

The reference artifacts are not installed as BetterCP/M ED.COM. ED stays planned
in the System Disk manifest until the Z80 implementation and qualification are
complete. The full-screen editor remains a separate Utilities Disk item.

## Initial executable fixtures

`tools/qualify_ed_reference.py` now captures new/existing E and Q behavior,
backup/work states, split output and destination collision. Both
`tools/fixtures/ed-initial-oracle-cpm22.json` and
`tools/fixtures/ed-initial-oracle.json` reproduce against the pinned binary.
The former is the stock-CP/M behavioral target; the latter records current
BetterCP/M host differences rather than blessing them as ED semantics. See
[implementation qualification](ED%20Implementation%20Qualification.md).
