# UNLZH — Restore a CP/M CrLZH file

[Utilities Manual](utilities_manual.md#compression-utilities) · [LZH](LZH.md)

UNLZH restores the supported old `10h` and new `20h` CP/M CrLZH variants with
additive checksums. It detects the variant from the header; no switch is needed.
The compressed input remains in place, and output is published only after its
checksum and file closes succeed.

## Syntax

```text
UNLZH [drive:]file [destination-drive:]
UNLZH /HELP
UNLZH /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` must each stand alone. See the
[shared command rules](utilities_manual.md#shared-compression-command-rules)
for program lookup, filename syntax and drive defaults.

## Help

`UNLZH /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
Combining an exact `/HELP` token with other input reports `Invalid /HELP usage.`;
if an exact `/VER` token is also present, `Invalid /VER usage.` takes precedence.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use UNLZH /HELP for help.`

The help screen is:

```text
UNLZH 1.0 (Build 003)
  - - -
 | CrLZH expansion
 |
 |   Usage: UNLZH [drive:]file [destination-drive:]

   Options:
     /HELP       Display this help.
     /VER        Display utility identification.
```

## Version identification

`UNLZH /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
UNLZH 1.0 (Build 003)
  - - -
 | BetterCP/M Utilities
 | CrLZH File Expansion
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. Combining `/VER` with a filename, destination drive or another option
prints `Invalid /VER usage.` and performs no file operation. Normal file
processing does not print this identification banner.

## Output name and supported files

The restored name comes from the header. `REPORT.TYT` may restore as
`REPORT.TXT`; changing the input's extension does not change that stored name.
Input need not have Y in its extension, but must contain the supported CrLZH
format. Ordinary LHA/`.LZH` archives are a different format and are not supported.

UNLZH accepts trailing blanks in historical three-slot extensions and ignores
later header metadata. It validates the resulting plain 8.3 name, refusing paths,
drive/user prefixes, wildcards and high-bit filename characters. It does not
restore metadata as attributes or timestamps, or offer an output-name override.
Some historical files have high-bit header names and are therefore refused even
when their compressed data is valid.

## Example

```text
UNLZH B:REPORT.TYT C:
```

This keeps `B:REPORT.TYT` and restores its original name on C: in your current
user area. While logged onto A:, `UNLZH B:REPORT.TYT` instead restores on A:.
An existing original name is never replaced.

## Completion and messages

Success prints `UNLZH: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](utilities_manual.md#compression-file-handling-and-recovery)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `UNLZH: unsupported CrLZH variant.` | Revision or checking mode is unsupported. Only `10h`/`20h` with additive checking are accepted. |
| `UNLZH: header exceeds 127 bytes.` | The stored name/metadata exceeds the supported bound. |
| `UNLZH: invalid or truncated CrLZH file.` | Wrong format, malformed encoded data or premature end. Check the format or obtain another copy. |
| `UNLZH: checksum mismatch.` | Restored content failed verification; no final output is published. |

UNLZH does not browse an archive or decode squeezed/CRUNCH files. Use USQ or
UNCR for those formats. `1Ah`, binary bytes and overlapping compressed matches
are restored without text conversion.

## Related documentation

- [LZH command](LZH.md)
- [Common operating rules](utilities_manual.md#compression-utilities)
- [UNLZH/LZH engineering specification](../engineering/LZH-UNLZH%20Specification.md)
