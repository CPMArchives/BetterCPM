# SYSINFO

Future development is tracked in the suite-wide `../ROADMAP.md`.

SYSINFO is a standalone CP/M 2.2 system-information utility. It reports only
documented, application-visible state and does not modify disk contents.

Current reports include the CP/M version, memory vectors, I/O byte, disk
parameter information, `/STATE` (current drive, user, login vector, and
read-only vector), `/SPACE` (total, used, and free disk capacity), `/BIOS`
(the validated standard BIOS jump table), and `/CHECK` (a read-only structural
health audit).
Drive inventory and allocation details are available through `/DRIVES` and
`/ALLOC`.
`/MAP`, `/VER` (also `/VERSION`), and `/ALL:SHORT` provide concise memory,
version, and overview reports.

## Build

Run `./build.sh`. The script uses `Z80ASM` when set, then searches `PATH`,
then checks `~/bin/z80asm`.

The resulting program is `build/SYSINFO.COM`.

## Use

Run `SYSINFO /H` under CP/M for the complete command summary. `SYSINFO /ALL`
prints every report, while `/STATE` prints the current session state.

## Project boundary

SYSINFO is independent of the CP/M 2.2 compatibility ledger and conformance
suite. The `cpm-2.2-compatibility-suite` project may bundle a pinned binary on
convenience disk images, but this repository is the source and release
authority.

## License

SYSINFO source code and documentation are licensed under the GNU General
Public License, version 2 or, at your option, any later version
(`GPL-2.0-or-later`). See `LICENSE`.
