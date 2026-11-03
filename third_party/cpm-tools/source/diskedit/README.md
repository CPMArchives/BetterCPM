# DISKEDIT

Future development is tracked in the suite-wide `../ROADMAP.md`.

DISKEDIT dev2 is a read-only, filesystem-aware CP/M 2.2 sector browser. It
starts at track zero, displays each 128-byte record in hexadecimal and ASCII,
and shows its logical and translated BIOS location. In the DATA region it also
shows the allocation block and its owning user/file, `FREE`, or `CONFLICT`.

The complete suite user manual is `../docs/TOOLS.DOC`.

## Use

```text
DISKEDIT
DISKEDIT B:
DISKEDIT /HELP
DISKEDIT /INFO
DISKEDIT /VERSION
```

Interactive commands are `N` for next, `P` for previous, `S` for the first
system record, `D` for the first directory record, `T` for the first data
record, and `Q` to quit. On a DATA-only format, `S` reports that no SYSTEM
area exists and leaves the position unchanged. Dev2 contains no write command
and never calls the BIOS `WRITE` entry.

## Native CP/M build

Keep `DISKEDIT.MAC`, `BUILD.SUB`, `ZSM4.COM`, and `LINK.COM` on one drive,
then run `SUBMIT BUILD DISKEDIT`.

## License

GPL-2.0-or-later. See the repository `LICENSE`.
