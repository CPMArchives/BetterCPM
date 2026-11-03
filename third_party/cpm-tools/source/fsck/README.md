# FSCK

Future development is tracked in the suite-wide `../ROADMAP.md`.

FSCK is a read-only CP/M 2.2 filesystem consistency checker. It reads every
raw directory entry and checks user numbers, record counts, allocation-block
ranges, directory-block references, and duplicate block ownership.

The complete operator reference is [TOOLS.DOC](../docs/TOOLS.DOC). The shared
CP/M tools disk includes the same file for use with `TYPE TOOLS.DOC`.

## Use

```text
FSCK
FSCK B:
FSCK B: /V
FSCK B: /VERBOSE
FSCK /HELP
FSCK /INFO
FSCK /VERSION
```

With no drive, FSCK examines the current drive. The original drive is
restored before the program returns to the CCP. `/V` and `/VERBOSE` are exact
aliases that display each active directory entry and detailed findings.

## Native CP/M build

Keep `FSCK.MAC`, `BUILD.SUB`, `ZSM4.COM`, and `LINK.COM` on one drive,
then run `SUBMIT BUILD FSCK`.

The source uses ZSM4 notation but only 8080 instructions. It obtains disk
geometry through CP/M 2.2 and reads directory records through the documented
BIOS entry points. It never writes a sector.

## License

GPL-2.0-or-later. See the repository `LICENSE`.
