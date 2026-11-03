# CP/M Tools

Small system-information and diagnostic utilities for CP/M 2.2-compatible
systems.

Each utility is maintained in its own directory with its source, build script,
documentation, tests, and current CP/M executable. The tools are deliberately
kept independent so that users can build or copy only the programs they need.

The complete operator reference is [TOOLS.DOC](docs/TOOLS.DOC). The shared
CP/M image contains the same manual for use with `TYPE TOOLS.DOC`.
Future development is tracked separately in the [project roadmap](ROADMAP.md);
the tools image carries the same text as `ROADMAP.DOC`.

## Available tools

### [SYSINFO](sysinfo/)

A read-only system-information utility. SYSINFO reports documented,
application-visible CP/M state, including memory vectors, disk parameters,
drive allocation, free space, the standard BIOS jump table, and structural
health checks.

The current development release is `SYSINFO 1.0.0-dev8`.

### [DISKINFO](diskinfo/)

A read-only disk-structure utility. DISKINFO reports the selected drive's
Disk Parameter Header pointers, complete CP/M 2.2 Disk Parameter Block,
derived filesystem geometry, and current allocation totals.

The current development release is `DISKINFO 0.1.0-dev4`.

### [DPBCHK](dpbchk/)

A read-only disk-parameter validator. DPBCHK checks block and extent
geometry, allocation limits, directory reservation, checksum-vector size,
and required DPH pointers for internal consistency.

The current development release is `DPBCHK 0.1.0-dev2`.

### [FSCK](fsck/)

A read-only filesystem consistency checker. FSCK examines raw directory
entries and allocation lists for malformed user numbers and record counts,
invalid block references, directory-block references, and duplicate block
ownership. A verbose mode displays the entries and individual findings.

The current development release is `FSCK 0.1.0-dev1`.

### [DISKEDIT](diskedit/)

A read-only, CP/M-resident, filesystem-aware sector browser. DISKEDIT dev2
displays each 128-byte sector in hexadecimal and ASCII, identifies its track,
translated sector and structural region, and shows allocation-block ownership
for DATA sectors.

The current development release is `DISKEDIT 0.1.0-dev2`.

### [COMINFO](cominfo/)

A read-only static inspector for CP/M transient programs. COMINFO dev2 reports a
`.COM` file's logical length and load range, direct BDOS, warm-boot, and other
page-zero references, symbolic immediate BDOS function calls and common DE
arguments, and heuristic Z80 prefix-byte findings. Verbose mode shows offsets.

The current development release is `COMINFO 0.1.0-dev2`.

### [BDOSPROBE](bdosprobe/)

A CP/M-resident behavior probe for documented BDOS calls. The CP/M command is
`BDOSPRB` to fit the eight-character filename limit. Dev4 provides read-only
version, console-status, disk-state, allocation-vector, DPB, and current-user
probes. Its first guarded state probe selects only the drive reported as
current and verifies that public disk state remains unchanged.

The current development release is `BDOSPROBE 0.1.0-dev4`.

## Planned tools

### BDOSTRACE

A runtime tracer for BDOS calls made by another transient program. BDOSTRACE
will record function numbers and significant arguments while passing calls to
the real BDOS without changing the observed program behavior.

### BIOSINFO

A possible deep BIOS inspector covering the complete jump table, shared or
stub entry points, disk-selection structures, sector translation, and device
routines. It will remain part of SYSINFO instead if the useful scope is not
substantial enough for a separate utility.

### MEMINFO

A possible detailed memory-layout inspector covering page zero, the TPA,
CCP, BDOS, BIOS, default FCBs and DMA, and unusual low-memory modifications.
It is lower priority because much of this information may properly remain in
SYSINFO.

## Building

Enter a tool's directory and run its build script. For SYSINFO:

```text
cd sysinfo
./build.sh
```

See the README in each tool directory for its requirements and command-line
interface.

DISKINFO, DPBCHK, FSCK, DISKEDIT, COMINFO, and BDOSPROBE are assembled natively under CP/M with ZSM4 and
Digital Research LINK. Running the project-level `./build.sh` builds them
and produces one verified Montezuma Micro 80T SUPER DS DATA 880K image. The
shared image contains every current utility and source file, the universal
`BUILD.SUB`, and one copy each of ZSM4 and LINK. For example,
`SUBMIT BUILD FSCK` rebuilds FSCK from `FSCK.MAC`.
`SUBMIT BUILD BDOSPRB` rebuilds BDOSPROBE from `BDOSPRB.MAC`.

## License

Unless otherwise noted, original source code and documentation in this
repository are licensed under the GNU General Public License, version 2 or,
at your option, any later version (`GPL-2.0-or-later`). See `LICENSE`.
