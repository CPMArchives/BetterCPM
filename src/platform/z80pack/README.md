# z80pack / cpmsim adapter

This is a second hardware binding for BetterCP/M, not a Model 4 BIOS running
under another machine. Shared BIOS vectors/state, BDOS, gateway, file loader,
CCP, CPXs and RSX manager retain the common memory layout. This target uses
cpmsim console ports 0/1 and record-DMA disk ports 10-17. No TRS-80 port or
memory-map emulation is required, and the installed z80pack is unchanged.
The target READER entry reads cpmsim auxiliary-input port 5.  The host-side
`cpmsend` helper supplies a normal reader stream; when no sender is attached,
cpmsim returns CP/M end-of-file (`Ctrl-Z`).

`python3 tools/build_z80pack_boot.py --output build/z80pack` builds a private
set of target artifacts and disks. It refuses to overwrite an existing disks
directory. Start `build/z80pack/launch-z80pack.command` in a terminal. BYE exits
the emulator. The launcher supplies the path to z80pack's cpmrecv helper.

A-D are raw 77-track, 26-sector, 128-byte-sector images (256,256 bytes each),
using linear record order. A reserves five tracks and has 234 KiB of allocation
space; B-D reserve none and have 250 KiB each. Directory storage consumes two
1-KiB blocks on each disk. These are explicitly described by the accompanying
`diskdefs`; they are IBM-3740-sized media with our system-area allocation,
not an assertion that an arbitrary CP/M IBM-3740 boot disk is interchangeable.

System absolute record allocation on A:

| Records | Contents |
|---|---|
| 0 | 128-byte bootstrap loaded by cpmsim |
| 8-59 | Packed resident image |
| 60-67 | Transient command reloader |
| 68-75 | CPX controls |
| 76-83 | Optional RSX manager |
| 84-111 | Relocatable CCP carrier |
| 130 onward | CP/M directory and allocation blocks |

The bootstrap reads the resident image and enters the standard BIOS BOOT
vector. The ordinary module-reconstruction algorithm is reused with a target
raw-record reader. Direct 128-byte DMA avoids aliasing the module buffer with
a physical-sector staging buffer. Warm boot invalidates BDOS's drive context
before reading system modules. Unloaded TPA remains 54,273 bytes.

## Current interface limits

The standard BIOS disk/console entries work. BDOS 207 discovery and getters
report fixed target geometry. Runtime hardware/format setters and WD-style
write-track requests return unsupported (2); CONFIG editing and DUP formatting
are not yet ported to this virtual controller. Their COM files are present
for compatibility testing, not as a claim of complete target support.
The inverse-character service reports unavailable and menus use plain output.
RSX load/unload and the shared CPX controls remain available.

`python3 tools/test_z80pack_reader.py` builds private media and runs the
independent BIOSTEST 0471 two-stage procedure.  It first proves a supplied
uppercase `R`, then restarts without a sender and proves immediate `Ctrl-Z`.

`python3 tools/test_z80pack_boot.py` uses private copies of all disks. It boots,
lists files, runs HELLO, creates/writes/closes/reopens/reads files on B-D, verifies
their bytes with cpmtools, then loads and unloads ECHO.RSX and checks 53K TPA.
The transcript is saved as verification.txt. `cpmls -T raw -f
bettercpm-z80pack-system disks/drivea.dsk` reads the filesystem from the output
directory. Use bettercpm-z80pack-data for the other disks.
