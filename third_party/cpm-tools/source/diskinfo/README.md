# DISKINFO

Future development is tracked in the suite-wide `../ROADMAP.md`.

DISKINFO is a read-only CP/M 2.2 disk-structure report. The first development
release displays the selected drive's DPH pointers, complete DPB, derived
filesystem geometry, and current allocation totals.

## Use

The complete suite user manual is `../docs/TOOLS.DOC`.

```text
DISKINFO
DISKINFO B:
DISKINFO /DPH
DISKINFO B: /DPB
DISKINFO /GEO
DISKINFO /ALLOC
DISKINFO /HELP
```

With no argument, DISKINFO examines the current drive. The selected drive is
restored before returning to the CCP. `/DPH`, `/DPB`, `/GEO`, and `/ALLOC`
select one section of the report. `/H` and `/HELP` show the complete command
summary; `/INFO` shows build information, and `/VER` or `/VERSION` prints the
program version. Options and drive letters are case-insensitive, and the drive
may precede or follow a report selector.

## Native CP/M build

Keep `DISKINFO.MAC`, `BUILD.SUB`, `ZSM4.COM`, and `LINK.COM` on one drive,
then run:

```text
SUBMIT BUILD DISKINFO
```

The script assembles `DISKINFO.MAC` to a relocatable file and links it at the
standard CP/M transient load address to produce `DISKINFO.COM`.

## Compatibility

The source uses ZSM4 notation but only 8080 instructions. It obtains the DPB
through documented CP/M 2.2 BDOS calls and the DPH through the standard BIOS
`SELDSK` entry. It performs no sector reads or writes.

## License

GPL-2.0-or-later. See the repository `LICENSE`.
