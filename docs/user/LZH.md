# LZH — Compress one CP/M CrLZH file

[Utilities Manual](utilities_manual.md#compression-utilities) · [UNLZH](UNLZH.md)

LZH writes a CP/M CrLZH file in one input pass while keeping the original.
Use UNLZH to restore it. LZH emits the newer `20h` CrLZH variant with additive
checking. It creates an individual compressed file, not a general LHA archive.

## Syntax

```text
LZH [drive:]file [destination-drive:]
LZH /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/VER` must stand alone. See the
[shared command rules](utilities_manual.md#shared-compression-command-rules)
for program lookup, filename syntax and drive defaults.

## Version identification

`LZH /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
LZH 1.0 (Build 001)
  - - -
 | BetterCP/M Utilities
 | CrLZH File Compression
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. Combining `/VER` with a filename, destination drive or another option
prints `Invalid /VER usage.` and performs no file operation. Normal file
processing does not print this identification banner.

## Output name and supported files

| Source | Output |
| --- | --- |
| `REPORT.TXT` | `REPORT.TYT` |
| `CODE.ABC` | `CODE.AYC` |
| `CODE.AYC` | `CODE.AYY` |
| `CODE.AYY` | `CODE.YYY` |
| `SHORT.A` or `SHORT.AB` | `SHORT.AY` |
| `SHORT.YY` | `SHORT.YYY` |
| `NOEXT` | `NOEXT.YYY` |

These are the historical CrLZH naming rules. Replace the middle slot with Y;
if it is already Y, replace the last slot; if the last two are YY, select YYY.
A missing extension also becomes YYY. An existing `.YYY` input is refused even
with a different destination drive. The original name, including three padded
extension slots, is stored inside for UNLZH.

## Example

```text
LZH A:REPORT.TXT B:
UNLZH B:REPORT.TYT C:
```

This keeps `A:REPORT.TXT`, creates `B:REPORT.TYT` and restores
`C:REPORT.TXT`. All file operands use your current user area; C: must not already
contain the restored name.

## Completion and messages

Success prints `LZH: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](utilities_manual.md#compression-file-handling-and-recovery)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `LZH: cannot compress .YYY names.` | This extension is the end of the historical naming sequence. Check that you chose the intended original file. |
| `LZH: encoding failed.` | An encoding/configuration/capacity failure occurred; retain the source. |

There is no switch to write the old `10h` variant, select a CRC mode or choose a
compression level. Output need not be byte-identical to an old encoder. LZH preserves
all input-record bytes, including `1Ah`; no text conversion is performed.

## Related documentation

- [UNLZH command](UNLZH.md)
- [Common operating rules](utilities_manual.md#compression-utilities)
- [LZH/UNLZH engineering specification](../engineering/LZH-UNLZH%20Specification.md)
