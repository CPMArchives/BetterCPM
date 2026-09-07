# Runtime disk configuration, ABI version 3

Updated September 7, 2026. BIOS implementation 1.6/API 1.3; BDOS
implementation 1.6/API 1.2. The standard 17 BIOS vectors remain unchanged.

## Scope and current limits

The resident BIOS owns four logical-drive records (A–D), each with
its own DPH, writable DPB and format. Allocation and check vectors are shared
workspace; BDOS rebuilds allocation ownership when changing logical disks. Four
physical records describe drives 0–3. Logical aliases can use the same hardware
with different formats. Successful reconfiguration resets BDOS disk context,
login state and directory cache; close every file before making changes.
Switching media or writing through an alias also requires a BDOS disk reset
before reusing other aliases. No background media-change detection is provided.

A remains the bootstrap filesystem in this first implementation: its format
and mapping cannot be changed. Formatting physical drive 0 is rejected even
through another logical drive. This protects command-environment reconstruction
until system-disk migration is implemented. These restrictions are explicit
status-2 results, not silently ignored requests.

Accepted runtime definitions have 1–80 cylinders, one or two sides, 1–32
sectors per side, 128/256/512/1024-byte physical sectors, at most 512 directory
entries and 1,024 allocation blocks. The Model 4 implementation accepts 5-inch
hardware; 8-inch drive support is not implemented. Standard alternating-side
track order, FM/MFM and inverted data are supported. Optional FDF.RSX handles other side ordering, ID-track numbering and mixed
sector sizes. Five catalogue records still fail consistency validation. Native ZSM4 parity for the new disk
module and real-hardware timing remain unverified.

DISK.FDF is the format source for CONFIG.COM. The BIOS
accepts decoded records and does not open or parse text files. Do not translate
through diskdefs or guess omitted physical parameters. The current MM-style
system image retains its existing 80-track, double-sided, 790K default profile.

## Calling convention

Call BDOS 207 (C=207), B=operation, DE=request pointer. Operation 0 has no
request. For other operations reserve an 80-byte buffer wholly within the TPA,
starting at 0100h or above. HL returns 0=success, 1=invalid/error,
2=unsupported, or a nonzero controller error status for I/O; A mirrors L.
IX and the caller's stack are preserved. Other registers are scratch.
Controller error codes may overlap validation statuses; interpret them in the
context of the operation. Requests are synchronous and controller waits bounded.

| B | Operation | Request |
|---|---|---|
| 0 | Discover | HL points to the descriptor below |
| 1 | Read physical record | byte 0=index; bytes 1–6 receive settings |
| 2 | Set physical record | byte 0=index; bytes 1–6=settings |
| 3 | Read logical record | byte 0=index; bytes 1–64 receive binding |
| 4 | Set logical record | byte 0=index; bytes 1–64=binding |
| 5 | Format one track | byte 0=logical, 1=cylinder, 2=side, word 3=stream length, word 5=stream pointer |

Discovery descriptor: `BDCF`, byte ABI version=3, logical count=4,
physical count=4, binding size=64, then two little-endian pointers to the
physical table and logical table. These pointers are for inspection; applications
should use operations 2/4 for validated updates. There is no SYS-GEN persistence
operation yet. Warm boot preserves records; cold boot reloads the saved image.

Physical settings: drive size in inches (5), cylinder count, side count,
WD step-rate code (0=6ms, 1=12ms, 2=20ms, 3=30ms), motor spin-up in quarter
seconds (0–16), head-settle milliseconds (0–255). The last two fields are the
recovered timing concepts; their exact missing BetterCP/M menu wording is unknown.
Reducing hardware capabilities beneath an attached format is rejected.

## Logical binding layout

Offsets here are relative to the binding itself, one byte after the request index.

| Offset | Size | Meaning |
|---|---|---|
| 0 | 1 | Physical drive 0–3; FF means undefined |
| 1 | 15 | Standard CP/M DPB: SPT, BSH, BLM, EXM, DSM, DRM, AL0, AL1, CKS, OFF |
| 16 | 1 | Cylinders |
| 17 | 1 | Physical sectors per side |
| 18 | 1 | Maximum sector size code: 0=128, 1=256, 2=512, 3=1024 |
| 19 | 1 | DISK.FDF flags: 80h=MFM, 40h=double-sided, 10h=inverted data |
| 20 | 32 | Sector IDs in logical skew order; unused bytes zero |
| 52 | 1 | Zero=uniform, one=explicit mixed-size map |
| 53 | 8 | Four two-bit size codes per byte, low bits first, in sector-table order |
| 61 | 3 | Reserved, write zeros |

DPB words are little-endian. SPT is the physical sector count times 2^size-code
for these FDF profiles; double-sided disks have two CP/M tracks per cylinder.
The internal default 790K profile additionally uses flag 20h to retain its
legacy cylinder-based SPT=80 convention. Applications must not submit that flag.
DPB validation checks sector count/size agreement, BSH/BLM/EXM consistency,
workspace bounds, directory reservations, allocation capacity and unique sector
IDs before committing. A failed set leaves the existing logical record intact.
Unbinding B–D uses physical FF; other binding fields are ignored.

Logical storage has an 80-byte stride: DPH at +0, binding at +16.
Four records occupy 320 bytes; the shared 128-byte allocation vector and
32-byte check vector follow them. Each DPH points to its own DPB and the
shared workspace. ABI version 3 identifies this changed table layout.

## Formatting

DUP supplies a complete WD write-track stream, including address marks, CRC
commands, sector IDs and data/gap bytes. Geometry and stream-buffer bounds are
checked; the BIOS does not validate the stream's internal contents. DUP must
construct it from the chosen DISK.FDF definition, including sector size and
inversion. Supply trailing gap bytes beyond one revolution: index completion
ends the command successfully, whereas exhausting the stream first fails.
Formatting a disk is repeated operation-5 calls for every cylinder/side;
DUP owns progress, abort handling, user confirmation and verification.

The transfer loops are timing-sensitive. Read data inversion and write-buffer
inversion happen outside the timed byte loop. Do not add per-byte work without
checking controller data-loss status and verifying the resulting sectors.

## Build and validation

The packed system has a D501h TPA ceiling: 54,273 bytes starting at 0100h.
The resident image uses 13 sectors. Three two-sector carriers hold the
warm-boot reloader, disk/CPX controls and optional RSX manager; the CCP uses
seven sectors. Controls reuse the idle physical-sector buffer. The manager
costs one additional KiB only while RSXs are active, plus their allocations.
The system disk must remain available for these overlay reads and warm boot.
Private BIOS entries +57 and +60 fetch controls and the RSX manager respectively;
the standard 17 vectors and existing +51/+54 entries retain their positions.
See the engineering memory-consolidation completion report for exact bounds.

The boot builder reassembles the BIOS, runtime disk module, extension and tables,
and rejects a resident image containing stale bytes. A failed oversized BIOS
build does not replace the last good BIOS, resident image or boot disk.

Checks for this change:

- `test_bios.py`: 17 vectors, console transport, all 80 default logical reads
  and writes, DMA preservation on errors and sector translation.
- `test_bios_build.py`: injected 12-byte overflow, stale BIOS, stale runtime
  disk code, preservation of previous artifacts and reproducible rebuild.
- `test_disk_config.py`: real trs80gp query/get/set, pointer-wrap rejection,
  MM FDF binding and aliasing, invalid-definition rejection, hardware mismatch,
  formatting a disposable track, read/write, adjacent-record preservation and
  return to the command prompt.
- `test_trs80_boot.py`: boot, directory listing and HELLO command/tail.
- `test_packed_tpa.py`: overwrite the advertised TPA, survive in resident BDOS,
  rebuild the command environment and retain a resident RSX.

## CONFIG/DUP

The transient menus, runtime FDF parser and DUP formatting operation are
implemented. See [CONFIG/DUP usage and limits](CONFIG-DUP.md). Copy, disk-error
checking and SYSGEN persistence remain future work; diskdefs conversion remains
deferred in both directions.

## Optional format mapper

FDF.RSX implements BDOS 208: B=0 queries the 4644h signature; B=1 is the
private BIOS mapping call, and B=2 validates/normalizes extended geometry.
The mapper uses a private stack. BIOS transfer loops use the returned actual
sector length and quarter offset. No persistent pointer into the RSX is kept.
Unloading FDF selects the system drive and detaches dependent B-D records
before the chain manager releases memory. The module currently allocates 768
bytes, plus the shared 1024-byte manager when loaded alone.

Cylinder-based SPT is recognized during extended normalization and marked
internally with bit 20h. MM SUPER is normalized into five 1024-byte sectors
and one 512-byte sector. Arbitrary explicit two-bit size maps use the same
mapping path; their sum must agree with SPT. The original DISK.FDF is unchanged.
