# SQ — Squeeze one file

[Utilities Manual](utilities_manual.md#compression-utilities) · [USQ](USQ.md)

SQ writes a squeezed file while keeping the original. It reads the source
twice, first to analyze it and then to produce the compressed stream. Keep the
source unchanged until SQ finishes. Use USQ to restore it.

## Syntax

```text
SQ [drive:]file [destination-drive:]
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and switches are not accepted. See the
[shared command rules](utilities_manual.md#shared-compression-command-rules)
for program lookup, filename syntax and drive defaults.

## Output name and supported files

| Source | Output |
| --- | --- |
| `REPORT.TXT` | `REPORT.TQT` |
| `CODE.ABC` | `CODE.AQC` |
| `SHORT.A` or `SHORT.AB` | `SHORT.AQ` |
| `NOEXT` | `NOEXT.QQQ` |

SQ replaces the middle extension character with Q. A name already containing Q
in that slot, such as `REPORT.TQT`, is refused even if you choose another drive.
The stored original name has no drive or padding spaces.

## Example

```text
SQ A:REPORT.TXT B:
USQ B:REPORT.TQT C:
```

These commands leave `A:REPORT.TXT` and `B:REPORT.TQT` in place and restore
`C:REPORT.TXT`. C: must not already contain that name in your current user area.

## Completion and messages

Success prints `SQ: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](utilities_manual.md#compression-file-handling-and-recovery)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `SQ: input name already squeezed.` | The middle extension character is Q. Check that you selected the original source. |
| `SQ: cannot reopen input for second pass.` | The close/reopen needed for pass two failed. Check source media and accessibility. |
| `SQ: input changed between passes.` | SQ detected different input. Keep a stable source and run again. No final compressed file is published. |
| `SQ: encoding failed.` | An encoding/configuration/capacity failure occurred; retain the source. |

SQ's pass comparison is not a guarantee against every possible source change.
It stores every CP/M record byte; it does not stop at text `1Ah`. Squeezed output
is compatible with the supported SQ format but is not promised to match an old
encoder byte for byte.

## Related documentation

- [USQ command](USQ.md)
- [Common operating rules](utilities_manual.md#compression-utilities)
- [SQ/USQ engineering specification](../engineering/SQ-USQ%20Specification.md)
