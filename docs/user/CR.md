# CR — Crunch one file

[Utilities Manual](utilities_manual.md#compression-utilities) · [UNCR](UNCR.md)

CR writes a CRUNCH 2.x-format file in one input pass while keeping the source.
Use UNCR to restore it. It writes the supported significant revision `20h`
with an additive checksum; there is no format-version or checksum-mode switch.

## Syntax

```text
CR [drive:]file [destination-drive:]
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
| `REPORT.TXT` | `REPORT.TZT` |
| `CODE.ABC` | `CODE.AZC` |
| `SHORT.A` or `SHORT.AB` | `SHORT.AZ` |
| `CODE.AZC` | `CODE.ZZZ` |
| `NOEXT` | `NOEXT.ZZZ` |

CR replaces the middle extension character with Z. A missing extension or an
existing middle Z selects `.ZZZ`; `.ZZZ` input is refused even with another
destination drive. This fallback differs from LZH's successive Y naming rule.
CR stores the original filename, including three padded extension slots, for UNCR.

## Example

```text
CR A:REPORT.TXT B:
UNCR B:REPORT.TZT C:
```

This leaves the original on A:, the crunched file on B: and the restored
`REPORT.TXT` on C:, all in your current user area. An existing C: output is refused.

## Completion and messages

Success prints `CR: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](utilities_manual.md#compression-file-handling-and-recovery)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `CR: cannot crunch .ZZZ names.` | This input extension has no supported next name. Check that you chose the intended original file. |
| `CR: encoding failed.` | An encoding/configuration/capacity failure occurred; retain the source. |

CR uses one pass and resets its compression dictionary at capacity. It does not
promise the same compressed bytes, size or heuristics as a historical encoder.
Its output is an individual CRUNCH file, not an archive. All input-record bytes,
including `1Ah`, are preserved for restoration.

## Related documentation

- [UNCR command](UNCR.md)
- [Common operating rules](utilities_manual.md#compression-utilities)
- [CR/UNCR engineering specification](../engineering/CR-UNCR%20Specification.md)
