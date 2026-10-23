# USQ — Restore a squeezed file

[Utilities Manual](utilities_manual.md#compression-utilities) · [SQ](SQ.md)

USQ restores one squeezed file and checks its stored additive checksum before
publishing the result. It leaves the compressed file in place. The restored
filename comes from the header, not from replacing Q in the input extension.

## Syntax

```text
USQ [drive:]file [destination-drive:]
USQ /HELP
USQ /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` must each stand alone. See the
[shared command rules](utilities_manual.md#shared-compression-command-rules)
for program lookup, filename syntax and drive defaults.

## Help

`USQ /HELP` displays a one-screen quick reference with syntax, options, an
example, drive defaults and important restrictions, then returns without
accessing files. Letter case and surrounding spaces or TABs do not matter.
Combining an exact `/HELP` token with other input reports `Invalid /HELP usage.`;
if an exact `/VER` token is also present, `Invalid /VER usage.` takes precedence.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use USQ /HELP for help.`

## Version identification

`USQ /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
USQ 1.0 (Build 002)
  - - -
 | BetterCP/M Utilities
 | Squeezed File Expansion
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. Combining `/VER` with a filename, destination drive or another option
prints `Invalid /VER usage.` and performs no file operation. Normal file
processing does not print this identification banner.

## Output name and supported files

For a squeezed file containing the original name `REPORT.TXT`, output is
`REPORT.TXT` on the destination drive. The input may have any valid 8.3 name;
USQ checks the squeezed signature and decoding tree rather than its extension.

The complete embedded name must be a safe plain 8.3 filename. Drive/user
prefixes, paths, wildcards, high-bit characters, padded spaces and appended
metadata are not accepted by this command. USQ does not restore file attributes
or timestamps, and you cannot override the stored name on the command line.

## Example

```text
USQ B:REPORT.TQT C:
```

This keeps `B:REPORT.TQT` and restores `C:REPORT.TXT` if that is the stored
name. If C: already contains `REPORT.TXT`, USQ refuses to replace it. While
logged onto A:, `USQ B:REPORT.TQT` instead selects A: as the destination.

## Completion and messages

Success prints `USQ: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](utilities_manual.md#compression-file-handling-and-recovery)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `USQ: invalid or truncated squeezed file.` | Wrong format, invalid header/tree/repeat data, an overlong stored name, or premature end. Obtain a sound copy or confirm the format. |
| `USQ: checksum mismatch.` | Decoded content failed verification; no restored filename is published. |
| `USQ: unsafe embedded filename.` | The stored name is outside this command's filename rules. Renaming the input does not change it. |

USQ reads squeezed SQ files. It does not decode CRUNCH, CP/M CrLZH or archive
containers. Embedded `1Ah` is ordinary data. Historical files with otherwise
valid compressed data can still be refused because of their stored filename.

## Related documentation

- [SQ command](SQ.md)
- [Common operating rules](utilities_manual.md#compression-utilities)
- [USQ/SQ engineering specification](../engineering/SQ-USQ%20Specification.md)
