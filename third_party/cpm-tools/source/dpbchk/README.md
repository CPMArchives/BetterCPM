# DPBCHK

Future development is tracked in the suite-wide `../ROADMAP.md`.

DPBCHK is a read-only validator for CP/M 2.2 disk parameters. It checks the
selected drive's block mask, extent mask, allocation range, directory
reservation, checksum-vector size, and required DPH pointers.

## Use

The complete suite user manual is `../docs/TOOLS.DOC`.

```text
DPBCHK
DPBCHK B:
DPBCHK /HELP
DPBCHK /INFO
DPBCHK /VERSION
```

With no drive, DPBCHK examines the current drive. The original drive is
restored before the program returns to the CCP. A result can be `PASS`,
`WARN`, or `FAIL`; warnings identify plausible but nonstandard values.

## Native CP/M build

Keep `DPBCHK.MAC`, `BUILD.SUB`, `ZSM4.COM`, and `LINK.COM` on one drive,
then run `SUBMIT BUILD DPBCHK`.

The source uses ZSM4 notation but only 8080 instructions. It reads the DPB
through documented CP/M 2.2 BDOS calls and obtains the DPH through the
standard BIOS `SELDSK` entry. It performs no sector reads or writes.

## License

GPL-2.0-or-later. See the repository `LICENSE`.
