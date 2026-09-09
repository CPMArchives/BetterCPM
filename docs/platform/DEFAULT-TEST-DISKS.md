# Default high-capacity test disks

The installed BIOS defaults are:

| Logical | Physical | Format | SPT | DSM | OFF |
|---|---:|---|---:|---:|---:|
| A | 0 | BetterCP/M SYSTEM 780K, MM Extended geometry | 80 | 389 | 2 |
| B | 1 | MM 80T DS DATA 800K | 40 | 399 | 0 |
| C | 2 | MM 80T DS DATA 800K | 40 | 399 | 0 |
| D | 3 | MM 80T DS DATA 800K | 40 | 399 | 0 |

The boot carrier reserves two cylinders (20 KiB), so A has 780 KiB of
allocation space, not MM's 790 KiB. The earlier DSM=394 over-advertised the
last five blocks; DSM=389 now matches the image builder's 390-block limit.
The historical boot-builder filename still contains 790K.

All four have 80 cylinders, two sides and ten 512-byte sectors per side.
A uses the existing cylinder-based SPT and reserved-system-area convention;
B-D use one CP/M track per surface and no reserved system area. Capacity
names describe allocation space before directory/file use. No RSX is needed.
Cold boot restores these records from the system image; CONFIG changes survive
warm boot. CONFIG H saves current settings into A:'s resident carrier.
Standalone SYSGEN copies and verifies the complete reserved area onto a target
configured with the same SYSTEM format, without altering its file area.

Run `python3 tools/build_complete_system.py`, then
`python3 tools/build_test_disks.py --output /path/to/new/test-directory`.
The second command refuses an existing directory, to preserve test data.
It creates drivea.dmk through drived.dmk, a configuration manifest, and
launch-trs80.command. Data disks have empty CP/M directories; only A is bootable.
The launcher mounts all four images in the correct physical drives.

## Two emulator targets

trs80gp is the implemented boot target. `test_default_disks.py` boots it with
private copies and exercises the final record of each data disk, then returns
to the command prompt. It verifies that the system image is unchanged.

z80pack/cpmsim now has a separate statically linked console/disk adapter.
Its raw 77 x 26 x 128-byte test disks use a different system-area layout from
these DMKs. See [z80pack target](../../src/platform/z80pack/README.md) for the
builder, launcher, tests and current disk-configuration/formatting limits.
Portable BDOS, CCP and module services share the common memory map. A future
loadable BIOS-driver architecture is deferred; neither target uses it now.

## Independent filesystem check

The builder also emits logical-order `.img` files and local `diskdefs` for
cpmtools. From the output directory, use `cpmls -T raw -f bettercpm-system -l
drivea.img` and `cpmls -T raw -f bettercpm-data -l driveb.img` (likewise C/D).
Explicit `-T raw` avoids libdsk guessing a container type from an erased disk.
The system listing and empty B/C/D listings have passed these checks. These
flat images are not yet bootable with cpmsim.

The end-of-disk test exposed a stale BDOS selection when a transient used BIOS
calls directly. The command reloader now invalidates the cached context before
opening its system files; the test then returned successfully to A's prompt.
This adds transient reloader code and does not reduce TPA.
