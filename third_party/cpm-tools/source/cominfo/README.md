# COMINFO

Future development is tracked in the suite-wide `../ROADMAP.md`.

COMINFO dev2 is a read-only static inspector for CP/M transient programs. It
reports a COM file's logical CP/M length and load range, direct references to
the public warm-boot and BDOS entries, other direct page-zero references, and
heuristic Z80 prefix-byte findings. Dev2 recognizes immediate BDOS function
selection, prints symbolic CP/M 2.2 function names and counts, and reports an
adjacent LXI D argument when it occurs in either common instruction order.

The complete suite user manual is `../docs/TOOLS.DOC`.

## Use

```text
COMINFO file.COM
COMINFO file.COM /V
COMINFO /HELP
COMINFO /INFO
COMINFO /VERSION
```

`/V` and `/VERBOSE` print the file offset of each finding. Static byte-pattern
analysis cannot prove that bytes are executable instructions, so COMINFO keeps
its definite address-pattern results separate from heuristic Z80 prefix bytes.
Calls whose function is selected dynamically remain explicitly unknown.

## Native CP/M build

Keep `COMINFO.MAC`, `BUILD.SUB`, `ZSM4.COM`, and `LINK.COM` on one drive, then
run `SUBMIT BUILD COMINFO`.

## License

GPL-2.0-or-later. See the repository `LICENSE`.
