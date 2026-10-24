# CR — Crunch one file

[Utilities Manual](utilities_manual.md#compression-utilities) · [UNCR](UNCR.md)

CR writes a CRUNCH 2.x-format file in one input pass while keeping the source.
Use UNCR to restore it. It writes the supported significant revision `20h`
with an additive checksum; there is no format-version or checksum-mode switch.

## Syntax

```text
CR [drive:]file [destination-drive:]
CR /HELP
CR /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` ignore other arguments. See the
[shared command rules](utilities_manual.md#shared-compression-command-rules)
for program lookup, filename syntax and drive defaults.

## Help

`CR /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
An exact `/HELP` token anywhere in the command ignores other arguments and
shows help. If `/VER` is also present, help takes precedence in either order.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use CR /HELP for help.`

The help screen is:

```text
CR 1.0 (Build 004)
  - - -
 | CRUNCH compression
 |
 |   Usage: CR [drive:]file [destination-drive:]

   Options:
     /HELP       Display this help.
     /VER        Display utility identification.
```

## Version identification

`CR /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
CR 1.0 (Build 004)
  - - -
 | BetterCP/M Utilities
 | CRUNCH File Compression
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. An exact `/VER` token anywhere in the command shows identification and ignores
other arguments, unless `/HELP` is also present, in which case help is shown.
Normal file
processing does not print this identification banner.

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
