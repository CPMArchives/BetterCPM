# UNCR — Restore a crunched file

[Utilities Manual](utilities_manual.md#compression-utilities) · [CR](CR.md)

UNCR restores supported CRUNCH significant revision `20h` files and verifies
their additive checksum. It keeps the compressed input. Both files written by
BetterCP/M CR and supported historical 2.x streams can be read, including streams
using dictionary resets and reassignment. CRUNCH 1.x is not supported.

## Syntax

```text
UNCR [drive:]file [destination-drive:]
UNCR /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/VER` must stand alone. See the
[shared command rules](utilities_manual.md#shared-compression-command-rules)
for program lookup, filename syntax and drive defaults.

## Version identification

`UNCR /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
UNCR 1.0 (Build 001)
  - - -
 | BetterCP/M Utilities
 | CRUNCH File Expansion
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. Combining `/VER` with a filename, destination drive or another option
prints `Invalid /VER usage.` and performs no file operation. Normal file
processing does not print this identification banner.

## Output name and supported files

The output uses the header's original name. For example, `REPORT.TZT` normally
restores as `REPORT.TXT`; renaming the input does not change the stored name.
The input need not have Z in its extension, but its contents must be CRUNCH.

UNCR accepts historical padding in the three extension slots and ignores later
header metadata. It validates the resulting plain 8.3 name before creating
output. Unsafe or high-bit filename characters are refused. It does not restore
metadata as timestamps, attributes, user areas or drives. There is no command
option to select a replacement output filename.

## Example

```text
UNCR B:REPORT.TZT C:
```

This keeps `B:REPORT.TZT` and restores the embedded original name on C:.
With A: logged on, omitting `C:` sends the restored file to A:, independently
of the input's B: prefix. An existing restored name is never replaced.

## Completion and messages

Success prints `UNCR: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](utilities_manual.md#compression-file-handling-and-recovery)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `UNCR: unsupported crunch variant.` | The significant revision or checking mode is unsupported. Older CRUNCH 1.x and non-additive checking modes are refused. |
| `UNCR: header exceeds 127 bytes.` | The stored name/metadata field exceeds the supported bound. |
| `UNCR: invalid or truncated crunched file.` | Wrong signature, malformed codes/repeats or premature end. Check the format or obtain another copy. |
| `UNCR: checksum mismatch.` | Restored data failed verification; no final output is published. |

UNCR is not a squeezed-file, CrLZH or general archive reader. The `.TZT` or other
Z-style extension is only a convention; it does not prove that a file is supported.

## Related documentation

- [CR command](CR.md)
- [Common operating rules](utilities_manual.md#compression-utilities)
- [UNCR/CR engineering specification](../engineering/CR-UNCR%20Specification.md)
