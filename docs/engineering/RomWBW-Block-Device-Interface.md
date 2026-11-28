# RomWBW block-device interface and installation

Engineering scope: the RomWBW target only. Existing floppy targets retain
Function 181 ABI 5 and their existing configuration/installation behavior.

## Why a distinct interface

ABI 5's physical profiles and 64-byte floppy binding have an eight-bit cylinder
count and controller timing fields. RomWBW hd512 exposes 1040 tracks. Inventing
floppy cylinders, sides or timing values would misrepresent that device.
The RomWBW backend therefore advertises **BDCF ABI 6** and block-device bindings.
Clients must check the descriptor signature, ABI and counts before using it.
ABI-5-only clients cannot treat these as floppy profiles.

## Discovery and requests

Function 181 uses C=181, B=operation, DE=80-byte request. As for ABI 5, the
request must be entirely in owned TPA at or above 0100h and below the live
0006h boundary, without wrapping. IX and caller SP are preserved; other
registers and flags are scratch. Status is HL=0 success, 1 invalid/I/O failure,
2 unsupported, with A=L. Discovery returns a pointer instead of a status.

The 16-byte discovery descriptor is `BDCF`, ABI 6, logical count 4, floppy
physical count 0, binding length 64; words +8/+10/+12/+14 are respectively
NULL, logical DPH table, NULL, NULL. The logical table retains the 80-byte
stride of DPH followed by binding, but is inspection-only.

| B | Operation | Contract |
| --- | --- | --- |
| 0 | Discover | No request; return the descriptor pointer. |
| 3 | Get block binding | Request +0 is logical index 0..3; copy 64 bytes to +1. Unbound drives remain queryable. |
| 4 | Set B/C/D binding | Request +0 must be 1..3. Validate all 64 bytes before publication. A cannot be rebound. |
| Other | Unsupported | Valid requests return 2 without changing a binding. |

## Binding layout

Offsets below are relative to the 64-byte binding (request +1).

| Offset | Bytes | Meaning |
| --- | --- | --- |
| 0 | 1 | HBIOS disk unit, or FFh for an unbound drive. A is always the firmware boot unit. |
| 1 | 15 | CP/M DPB. Fixed SPT=64, BSH=5, BLM=31, EXM=1, DSM=2047, DRM=511, AL0=F0h, AL1=0, CKS=0, OFF=16. |
| 16 | 2 | `HB` block-mapping signature. |
| 18 | 1 | Mapping version 1. |
| 19 | 1 | Flags, zero in this target. |
| 20 | 2 | Physical sector bytes, 512. |
| 22 | 4 | Base LBA, zero in this target. |
| 26 | 4 | Physical sector count, 16,640. |
| 30 | 34 | Reserved zero. |

Set accepts the exact fixed DPB/mapping with a different unit, or FFh to
unbind the selected drive. It rejects aliases of any other bound unit, invalid devices, non-512-byte
sectors and other capacities, preserving the previous binding. Successful
publication invalidates BDOS login/cache contexts with Function 37.
No runtime filesystem resizing, formatting, MBR or nonzero slice support is
implied. Additional formats and nonzero slices need explicit validated mapping
and boot-address work rather than changing this record silently.

## Persistence

Physical LBA 4 contains a 512-byte `BWCF` record: magic +0..3, version=3 at
+4, logical count=4 at +5, saved B unit at +6, saved IOBYTE at +7, two's
complement word checksum at +8, saved C and D units at +10 and +11, and
remaining reserved bytes zero. All 256
little-endian words sum to zero. A is never persisted as a device number: the
firmware boot unit determines it on every cold boot. CON must remain TTY (low
two IOBYTE bits = 1). Versions 1 and 2 from earlier unpublished engineering images are rejected;
there is no silent interpretation or automatic migration of those records.

The shared CONFIG interface retains startup-command and PDS editing, including
pending settings that take effect only at cold boot. BLOCKCFG.OVL handles the
block options; PDSCONF.OVL retains the common PDS validator and menus.
CONFIG /SHOW reports live/saved IOBYTE, mappings, saved startup text and PDS choices.
CONFIG /IOBYTE=n validates available routes, confirms, writes and verifies the
record while leaving live IOBYTE unchanged. A failed save attempts restoration.
Block saves preserve the saved IOBYTE.

CONFIG /SHOW inspects live mappings. CONFIG /LOGICAL=B|C|D /UNIT=n or /UNBIND
validates and changes the live mapping; /SAVE writes a complete physical
configuration sector to A and verifies it by reading it back. A subsequent
cold boot verifies the header and checksum. A corrupt record stops boot;
saved B/C/D mappings are checked independently. Missing or unsuitable devices
and aliases of A or a previously restored drive remain unbound, while A boots.
`/SAVE` saves all three live mappings and preserves saved IOBYTE. Warm boot does not discard a live mapping.

## Installation

The RomWBW engineering SYSGEN accepts B: only, after CONFIG binds a separate
fixed hd512 device. It requires all 512 destination directory entries to be E5,
including user areas other than zero. It refuses a nonempty disk before writes.

Preflight verifies the source's reserved area against a build-time CRC with
the mutable LBA-4 configuration sector and both 256-byte saved BCST/PDS records
(at bytes 128 and 32896) normalized. Shared CONFIG mirrors and verifies BCST/PDS
writes in both locations. It opens and verifies
all manifest source files before destination writes. The installer's own source
file gets a runtime preflight CRC; other files have build-time expected CRCs.
The installer invalidates destination boot metadata, copies files through BDOS,
reopens every destination file to verify its complete CRC and record count,
then copies and verifies reserved sectors. It creates a default unbound B/C/D
configuration for the installed disk, preserves saved IOBYTE and both startup/PDS
records, and writes/verifies the RomWBW boot-info
sector last. Reported I/O failures trigger attempted deletion of its explicit manifest
files; interruption can still leave an incomplete target requiring a fresh or
cleaned disk. This is installation onto an empty disk, not an in-place upgrade.

The 56 KiB unloaded COM floor is preserved by recovering unused BIOS padding
and moving cold HBIOS initialization to the bootstrap. Four 80-byte DPH/binding
records and one 256-byte active ALV occupy 576 bytes
in protected common RAM. The existing shared BDOS rebuilds that active ALV on
every drive-context change, publishing allocated block ownership before it can
forget an unclosed FCB. This replaces the former two redundant ALVs, so adding
C:/D: requires no larger resident reservation or banked allocation maps.
Only sector staging uses
HBIOS-allocated banked memory; the shared BDOS/CCP/RSX residency model is unchanged.
