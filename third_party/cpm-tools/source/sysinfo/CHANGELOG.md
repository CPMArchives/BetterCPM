# Changelog

## 1.0.0-dev8

- Add the exact `/HELP` alias and clarify long aliases on the help screen.

## 1.0.0-dev7

- Added `/MAP` for the documented public memory layout.
- Added synonymous `/VER` and `/VERSION` utility/system version reports.
- Added `/ALL:SHORT` for a compact system, state, and drive overview.

## 1.0.0-dev6

- Added `/DRIVES` compact inventory for logged or explicitly named drives.
- Added `/ALLOC` for block, capacity, allocation-vector, and directory-reserve
  details on current, specified, or logged drives.
- Included current-drive allocation details in `/ALL`.

## 1.0.0-dev5

- Added `/CHECK` with `PASS`, `WARN`, and `FAIL` structural diagnostics.
- Audit public vectors, address ordering, BIOS jumps, current DPB geometry,
  allocation-vector availability, and space accounting.
- Included the health check in `/ALL`.

## 1.0.0-dev4

- Added `/BIOS` with all 17 standard CP/M 2.2 BIOS jump-table entries.
- Validate every jump opcode and target before displaying it.
- Included the BIOS report in `/ALL`.

## 1.0.0-dev3

- Added `/SPACE` for allocation-vector-based total, used, and free capacity.
- Added current-drive, explicit-drive, and `/LOGGED` space selection.
- Included the current drive's space report in `/ALL`.

## 1.0.0-dev2

- Added `/STATE` for the current drive, user, login vector, and read-only vector.

## 1.0.0-dev1

- Initial standalone system-information reports.
