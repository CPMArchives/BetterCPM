# Engineering Specification 93: Drive-Qualified Default FCBs

## Decision

The CCP recognizes an optional `A:` through `P:` prefix on each of the two
default-FCB operands. The FCB drive byte uses the CP/M convention 1 for A
through 16 for P; a bare drive operand leaves the eleven name/type bytes
space-padded.

This is portable CCP behavior, independent of how many drives a particular
BIOS currently implements. The Model 4 BIOS still exposes physical drives A
through D, while applications may receive and validate the complete CP/M
default-FCB drive encoding.

## Patch history

The first default-FCB implementation deliberately postponed drive prefixes.
Consequently, `MDIR B:` received a drive-zero FCB whose filename began `B:` and
reported misleading results for the second disk. The corrected parser consumes
the prefix before parsing the 8.3 fields.

The resident CCP previously ended at `ECEAh`, leaving 21 bytes before the fixed
`ED00h` physical-sector buffer. The prefix recognizer uses exactly those 21
bytes, so the CCP now ends at `ECFFh` and requires no memory-map change.

## Verification

The focused CCP test covers bare `B:`, `D:FILE.DAT`, and the boundary
`P:LAST.BIN`. Native ZSM4/LINK and cross builds must remain byte-identical.
Physical verification runs the original Montezuma Micro `MDIR.COM` against a
separately mounted B: image containing `HELLO.COM`.

Under `trs80gp`, `MDIR B:` now reports `HELLO.COM`, one file occupying 2K,
784K free on B:, and then returns to the A: prompt. This is the same image that
the old parser incorrectly reported as empty.
