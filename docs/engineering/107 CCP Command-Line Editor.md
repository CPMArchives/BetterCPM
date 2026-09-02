# Engineering Specification 107: CCP Command-Line Editor

## Milestone

The BetterCP/M CCP now owns an enhanced command-line editor without changing
BDOS Function 10.  Transient CP/M programs therefore retain the documented
CP/M 2.2 buffered-console contract, while the replaceable command environment
can provide richer interactive behavior.

## Editing contract

The editor supports:

- Left and Right cursor movement within the current line;
- insert mode and overwrite mode, toggled by Insert;
- Backspace/Delete of the character immediately left of the cursor;
- Up to recall the preceding command;
- Down to dismiss recalled text and restore an empty line;
- a 127-character command limit.

Each new command starts in insert mode.  Typing at the end appends in either
mode.  Typing inside the line shifts the tail in insert mode and replaces the
character under the cursor in overwrite mode.

The editor redraws using only carriage return and ordinary console output.  It
does not require ANSI or terminal-specific cursor escapes: it inserts a visible
underscore at the logical cursor position, prints the rest of the line, erases
one stale trailing cell, returns to the margin, and reprints through the logical
cursor position.  The marker is removed before command execution.

## Model 4 binding

The shared Model 4 BIOS now publishes its special-key matrix row using the
traditional control-byte values for Enter, Clear, Break, Up, Down, Left, and
Right.  Clear is the physical Insert/overwrite toggle.  The unmodified Left
key moves the cursor; Shift-Left produces DEL (`7Fh`) for Backspace/Delete.
This remains a platform binding; the CCP editor consumes logical bytes and does
not inspect Model 4 hardware.

The compact keyboard table remains within one linked page in every current
consumer.  Its row-pointer increment is correspondingly kept eight-bit so the
physical read diagnostic, whose 512-byte carrier was already nearly full, can
include the new Shift-Left translation without exceeding one sector.

## Memory result

The editor, one-command history buffer, and editing state enlarge the CCP to
1836 bytes, with a 2048-byte page-rounded allocation.  The command loader
automatically calculates the new CCP base at `B7FDh`; no fixed address or
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
