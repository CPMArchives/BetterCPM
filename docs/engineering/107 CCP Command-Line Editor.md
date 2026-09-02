# Engineering Specification 107: CCP Command-Line Editor

## Milestone

The BetterCP/M CCP now owns an enhanced command-line editor without changing
BDOS Function 10.  Transient CP/M programs therefore retain the documented
CP/M 2.2 buffered-console contract, while the replaceable command environment
can provide richer interactive behavior.

## Editing contract

The editor supports:

- Left and Right cursor movement within the current line;
- WordStar `^S`/`^D` character movement and `^A`/`^F` word movement;
- insert mode and overwrite mode, toggled by Insert;
- `^V` as an insert/overwrite alias;
- `^H` or DEL to remove the character left of the cursor;
- `^G` to remove the character under the cursor;
- `^T` to remove the next word and adjacent spacing;
- physical Up and Down to traverse persistent command history;
- `^E` to continue the current instruction queue on a new physical line;
- `^U` or `^X` to discard the complete current instruction queue;
- `^C` to warm-boot and `^P` to toggle printer echo;
- a 127-character command limit.

Each new command starts in insert mode.  Typing at the end appends in either
mode.  Typing inside the line shifts the tail in insert mode and replaces the
character under the cursor in overwrite mode.

The editor redraws using only carriage return, ordinary console output, and an
optional BetterCP/M cursor-character service. On the Model 4, the character at
the logical cursor is displayed in reverse video; at the end of a line, a blank
cell is reversed. Platforms without attribute support receive the earlier
visible-underscore fallback. No ANSI or terminal-specific cursor escapes are
required, and the marker is removed before command execution.

Console output is treated as destructive of working registers.  In particular,
the redraw routine reconstructs its command-tail pointer after emitting the
cursor rather than assuming that a console service preserves `HL`. This
prevents an interior cursor from exposing unrelated page-zero bytes as glyphs.

## Model 4 binding

The shared Model 4 BIOS publishes distinct internal logical bytes for physical
Left and Right so they do not collide with `^H` and other ASCII controls.
Control-letter chords are translated from the modifier row. Clear remains the
physical Insert/overwrite toggle; Shift-Left produces DEL (`7Fh`). This remains
a platform binding: the CCP consumes logical bytes and does not inspect Model 4
hardware.

The compact keyboard table remains within one linked page in every current
consumer.  Its row-pointer increment is correspondingly kept eight-bit so the
physical read diagnostic, whose 512-byte carrier was already nearly full, can
include the new Shift-Left translation without exceeding one sector.

## Memory result

The editor, history client, editing state, and portable cursor fallback enlarge
the CCP to 2361 bytes, with a 2560-byte page-rounded allocation. With the
current 512-byte persistent history reservation, the command loader
automatically calculates the default CCP base at `B3FDh`; no fixed CCP address or
temporary ceiling is introduced.

## Verification

- CCP parsing, navigation, DIR, and CPX-dispatch regression tests pass.
- Disk-backed relocation passes at calculated `B7FDh` and arbitrary `B601h`.
- One- and two-CPX reconstruction remain intact around the enlarged CCP.
- Native CP/M and cross builds produce byte-identical CCP and BIOS binaries.
- The composed WBOOT/Function-0 path executes the enhanced CCP.
- Ordinary physical `DIR` and `HELLO` input under `trs80gp` remains verified.
- The physical read and write diagnostics remain within their carriers and
  pass on cylinder 2, side 1, sector 10.

Manual Model 4 verification is required for the host/emulator mapping of the
special keys because `trs80gp` raw matrix injection does not reproduce those
interactive transitions reliably in a compound automated edit.
