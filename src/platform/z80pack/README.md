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

`python3 tools/build_z80pack_image.py --output build/z80pack` builds a private
set of target artifacts and disks. It refuses to overwrite an existing disks
directory. Start `build/z80pack/launch-z80pack.command` in a terminal. BYE exits
the emulator. The launcher supplies the path to z80pack's cpmrecv helper.

A-D use the California Computer Systems 40T DS DD 332K default: 40 cylinders,
two sides, 18 256-byte sectors per side, and 368,640 bytes per raw image. A:
contains the installed system and distribution files. B:-D: are empty formatted
and boot-capable SYSGEN targets. The generated `diskdefs` describes the same
bytes to cpmtools. `build_z80pack_boot.py` remains a compatibility wrapper.

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
| 216 onward | CP/M directory and allocation blocks |

The bootstrap reads the resident image and enters the standard BIOS BOOT
vector. The ordinary module-reconstruction algorithm is reused with a target
raw-record reader. Direct 128-byte DMA avoids aliasing the module buffer with
a physical-sector staging buffer. Warm boot invalidates BDOS's drive context
before reading system modules. Unloaded TPA remains 54,273 bytes.

## Runtime disk formats

The standard BIOS disk/console entries work. BDOS 181 discovery, getters, and
physical/logical setters are implemented. A remains the protected bootstrap
format; B-D can be rebound by CONFIG to uniform, double-sided, and FDF-assisted
raw layouts. The adapter deblocks 256-, 512-, and 1024-byte sectors into CP/M
records. The raw host representation contains decoded sector bytes, including
for hardware formats whose controller representation is inverted. DUP formats
uniform raw media by initializing every mapped physical sector to E5 and then
performing its normal read-back verification. Optional FDF conventions and
explicit mixed-size maps remain unsupported by the raw formatter because their
mapping service cannot be called recursively from the disk-configuration API.
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
The transcript is saved as verification.txt. From the output directory,
`cpmls -f bettercpm-default disks/drivea.dsk` reads the same filesystem.

The generated `disks/drivea.dsk` through `disks/drived.dsk` names are relative
symbolic links.  Their image files live in `disks/library/`.  To change mounted
media, replace a drive link with a relative link to another library image.  This
keeps saved images in the library when a drive assignment changes and makes the
mounted set visible with `ls -l disks`.

`python3 tools/test_z80pack_interchange.py` creates independent 256-byte,
512-byte, and double-sided cpmtools images, writes a file with cpmtools, binds
each image through CONFIG, reads and copies it under BetterCP/M, and extracts
the result with cpmtools for a byte-for-byte comparison.
