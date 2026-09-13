# z80pack / cpmsim adapter

This is a second hardware binding for BetterCP/M, not a Model 4 BIOS running
under another machine. Shared BIOS vectors/state, BDOS, gateway, file loader,
CCP, CPXs and RSX manager retain the common memory layout. This target uses
cpmsim console ports 0/1 and record-DMA disk ports 10-17. No TRS-80 port or
memory-map emulation is required. Variable-format media require the BetterCP/M
cpmsim geometry interface version 2 from the `bettercpm-disk-geometry` branch
of the companion z80pack repository.
The target READER entry reads cpmsim auxiliary-input port 5.  The host-side
`cpmsend` helper supplies a normal reader stream; when no sender is attached,
cpmsim returns CP/M end-of-file (`Ctrl-Z`).

`python3 tools/build_z80pack_boot.py --output build/z80pack` builds a private
set of target artifacts and disks. It refuses to overwrite an existing disks
directory. Start `build/z80pack/launch-z80pack.command` in a terminal. BYE exits
the emulator. The launcher supplies the path to z80pack's cpmrecv helper.

A-D initially use raw 77-track, 26-sector, 128-byte-sector images (256,256
bytes each), using linear record order. A reserves seven tracks and has 227
KiB of allocation space; B-D reserve none and have 250 KiB each. Directory
storage consumes two 1-KiB blocks on each disk. B-D may be replaced with raw
images in another CONFIG-selected format. The same unmodified image is then
usable with a matching cpmtools `diskdefs` entry.

System absolute record allocation on A:

| Records | Contents |
|---|---|
| 0 | 128-byte bootstrap loaded by cpmsim |
| 8-59 | Packed resident image |
| 60-67 | Transient command reloader |
| 68-75 | CPX controls |
| 76-83 | RSX reconstruction manager |
| 84-91 | RSX validator |
| 92-99 | Service-descriptor publisher |
| 100-107 | Resident-service resolver |
| 108-120 | Relocatable CCP carrier |
| 182 onward | CP/M directory and allocation blocks |

The bootstrap reads the resident image and enters the standard BIOS BOOT
vector. The ordinary module-reconstruction algorithm is reused with a target
raw-record reader. Direct 128-byte DMA avoids aliasing the module buffer with
a physical-sector staging buffer. Warm boot invalidates BDOS's drive context
before reading system modules. Unloaded TPA remains 54,273 bytes.

## Runtime disk formats

The standard BIOS disk/console entries work. BDOS 207 discovery, getters, and
physical/logical setters are implemented. A remains the protected bootstrap
format; B-D can be rebound by CONFIG to uniform, double-sided, and FDF-assisted
raw layouts. The adapter deblocks 256-, 512-, and 1024-byte sectors into CP/M
records. The raw host representation contains decoded sector bytes, including
for hardware formats whose controller representation is inverted. WD-style
write-track formatting remains unsupported because a raw file needs no
controller-level format operation.
The inverse-character service reports unavailable and menus use plain output.
RSX load/unload and the shared CPX controls remain available.

`python3 tools/test_z80pack_reader.py` builds private media and runs the
independent BIOSTEST 0471 two-stage procedure.  It first proves a supplied
uppercase `R`, then restarts without a sender and proves immediate `Ctrl-Z`.

The system disk also contains the read-only `ZPRTC.RSX` clock provider. Load it
with `RSX LOAD ZPRTC`; the hardware-independent `TIME` and `TIME /PROVIDER`
commands then use cpmsim's ports 25/26 clock interface. The provider preserves
the emulator's BCD/binary mode and rejects samples crossing a clock tick.

`python3 tools/test_z80pack_boot.py` uses private copies of all disks. It boots,
lists files, runs HELLO, creates/writes/closes/reopens/reads files on B-D, verifies
their bytes with cpmtools, then loads and unloads ECHO.RSX and checks 53K TPA.
The transcript is saved as verification.txt. `cpmls -T raw -f
bettercpm-z80pack-system disks/drivea.dsk` reads the filesystem from the output
directory. Use bettercpm-z80pack-data for the original data disks.

`python3 tools/test_z80pack_interchange.py` creates independent 256-byte,
512-byte, and double-sided cpmtools images, writes a file with cpmtools, binds
each image through CONFIG, reads and copies it under BetterCP/M, and extracts
the result with cpmtools for a byte-for-byte comparison.
