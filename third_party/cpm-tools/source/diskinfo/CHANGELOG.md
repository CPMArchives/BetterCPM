# Changelog

## 0.1.0-dev4 — 2026-08-31

- Clarify the exact `/HELP` and `/VERSION` aliases on the help screen.

## 0.1.0-dev3 — 2026-08-31

- Add `/DPH`, `/DPB`, `/GEO`, and `/ALLOC` section selectors.
- Add the common `/H`, `/HELP`, `/INFO`, `/VER`, and `/VERSION` interface.
- Accept a drive before or after a report selector and reject ambiguous or
  extra operands.

## 0.1.0-dev2 — 2026-08-31

- Correct the usable data-block count on disks with allocation blocks larger
  than 1 KiB. Dev1 subtracted directory KiB from a block count.
- Add the missing space before the allocation-vector address.

## 0.1.0-dev1 — 2026-08-30

- Add current-drive and explicit-drive selection.
- Report standard DPH pointers and the complete CP/M 2.2 DPB.
- Derive block, directory, extent, and capacity information.
- Count used and free allocation blocks from the current ALV.
- Restore the original drive before returning to CP/M.
- Correct the warm-boot vector operand address found during first execution.
- Preserve report values across BDOS console calls.
