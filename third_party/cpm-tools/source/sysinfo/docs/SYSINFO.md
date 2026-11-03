# SYSINFO — CP/M System Information Utility

SYSINFO is a read-only CP/M 2.2-compatible transient utility. It reports the
documented page-zero vectors, TPA boundary, IOBYTE assignments, current public
system state, and the CP/M version. Console output uses only BDOS functions 2
and 9.

## Commands

```text
SYSINFO
SYSINFO /MEM
SYSINFO /IO
SYSINFO /VECTORS
SYSINFO /BIOS
SYSINFO /CHECK
SYSINFO /STATE
SYSINFO /DISK
SYSINFO /DISK B:
SYSINFO /DISK A: B: C:
SYSINFO /DISK /LOGGED
SYSINFO /DPB
SYSINFO /DPB B:
SYSINFO /DPB A: B:
SYSINFO /SPACE
SYSINFO /SPACE B:
SYSINFO /SPACE /LOGGED
SYSINFO /DRIVES
SYSINFO /DRIVES A: B:
SYSINFO /ALLOC
SYSINFO /ALLOC B:
SYSINFO /ALLOC /LOGGED
SYSINFO /MAP
SYSINFO /VER
SYSINFO /VERSION
SYSINFO /ALL:SHORT
SYSINFO /ALL
SYSINFO /H
```

Options are case-insensitive. `/H` gives a brief description of every option.

`/STATE` reports the current drive and user number plus the BDOS login and
read-only vectors. Each vector is printed in hexadecimal and decoded as drive
letters. All four values are obtained through query operations and are left
unchanged.

`/BIOS` derives the standard CP/M 2.2 BIOS jump-table base from the documented
page-zero warm-boot vector. It validates and displays the target of each of the
17 standard entries from `BOOT` through `SECTRAN`. SYSINFO does not call any
entry, so the report does not change device or disk state. A missing page-zero
`JMP`, a zero target, or a malformed table entry is reported rather than used.

`/CHECK` performs a read-only structural health audit. It checks the page-zero
warm-boot and BDOS vectors, plausible BDOS/BIOS address ordering, all 17 BIOS
jumps, the current drive's DPB, DPB block geometry, and allocation accounting.
Each line is marked `PASS`, `WARN`, or `FAIL`. These are integrity diagnostics,
not CP/M conformance results; unusual but potentially legal placement produces
a warning rather than a failure.

`/DISK` prints a decoded summary for the current drive by default. `/DPB`
prints the raw and decimal values of its standard disk parameter block. Both
accept one or more explicit drive names; `/DISK /LOGGED` uses the BDOS login
vector. CP/M has no portable call that enumerates configured but unlogged
drives. Inspecting an explicitly named, previously unused drive can add that
drive to the BDOS login vector because CP/M 2.2 requires selecting it before
BDOS function 31 can return its DPB. SYSINFO restores the original current
drive and never requests directory or data-sector I/O.

`/SPACE` reports total, used, and free capacity in KiB, followed by total and
free allocation-block counts. It accepts the same current-drive, explicit
drive-list, and `/LOGGED` selections as `/DISK`. The figures come from BDOS
function 27's allocation vector and the standard DPB; SYSINFO does not scan
the directory or modify the disk.

`/DRIVES` gives a compact inventory. With no operands it reports logged-in
drives; an explicit drive list reports those drives instead. `St` is `C` for
the current drive, `L` for another logged drive, or `-`; `RO` is `R` for a
read-only drive. The remaining columns show allocation-block KiB and total,
used, and free KiB.

`/ALLOC` reports the current drive's allocation-block size, total/allocated/
free block counts, allocated/free KiB, allocation-vector byte count, and the
number of directory-reserved blocks. It accepts explicit drive lists and
`/LOGGED`. Figures come only from the DPB and allocation vector.

`/MAP` prints a concise public memory map: page zero, the TPA range ending
immediately before the BDOS entry, the BDOS entry, warm-boot target, BIOS jump
table, and default DMA address. It does not guess a CCP address or physical
RAM top.

`/VER` and `/VERSION` are synonyms. They report the SYSINFO development
version, the BDOS-reported CP/M version, and the Intel 8080 processor floor.

`/ALL:SHORT` combines the ordinary system summary, public system state, and
compact logged-drive inventory. It intentionally omits the long BIOS, DPB,
allocation, and structural-check tables printed by `/ALL`.

## Portability decisions

- The word at `0006h` is reported as the BDOS entry/TPA upper boundary only
  when location `0005h` contains the documented `JMP` opcode.
- The BIOS base is derived from the documented warm-boot jump-table entry
  (`0001h` target minus three) only when location `0000h` is a `JMP`.
- Standard CP/M does not expose a portable CCP base or physical system-top
  value. SYSINFO prints `Unknown` for those fields.
- IOBYTE is decoded according to the standard two-bit CON/RDR/PUN/LST fields.
- The default DMA field reports CP/M's initial transient-program DMA address,
  `0080h`; SYSINFO never changes it.

## Build

Run `./build.sh` from the repository root. The result is
`build/SYSINFO.COM`, assembled for the Intel 8080 instruction subset and
loaded by CP/M at `0100h`.
