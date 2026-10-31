# Installing BetterCP/M on z80pack / cpmsim

BetterCP/M requires a patched cpmsim with geometry interface version 2.
Stock upstream cpmsim is insufficient for the supported disk interface.
Use the runtime build below for ordinary operation and retain its build receipt
with the checksums of the BetterCP/M images you run.

## Sources and prerequisites

Use the matching BetterCP/M source package, including
`tools/build_qualified_cpmsim.py`, `third_party/z80pack/upstream.json`,
`third_party/z80pack/README.md`, `third_party/z80pack/LICENSE` and the complete
`third_party/z80pack/patches/` directory.

The upstream repository is <https://github.com/udo-munk/z80pack.git>, pinned at
`91fd28eb04e675c2127df88ed3f40675e15282e2`. The runtime profile applies
`0001-disk-geometry.patch` followed by `0002-raw-fdf-backend.patch`.
Their SHA-256 checksums are in `upstream.json`. Do not substitute a moving
branch, a stock executable or an unidentified local patch.

Install Python 3, Git, tar, make and a C99 compiler. On macOS, install the
Xcode Command Line Tools, including codesign. cpmtools is needed for host-side
image inspection/copying; Expect is needed for automated qualification.
The reconstruction builder compiles cpmsim and its helpers, including cpmrecv
and cpmsend, from the same pinned source.

## Build the patched runtime

From the root of the matching BetterCP/M source package:

```sh
git clone https://github.com/udo-munk/z80pack.git z80pack-upstream
git -C z80pack-upstream cat-file -e 91fd28eb04e675c2127df88ed3f40675e15282e2^{commit}
python3 tools/build_qualified_cpmsim.py --source z80pack-upstream \
  --output build/cpmsim-runtime --profile runtime
```

An extracted source package carries SOURCE-IDENTITY.json so the builder can
record its source commit without a .git directory. For offline reconstruction,
restore the supplied pinned upstream Git bundle as described in the package
README, then pass that repository to --source.

The output directory must be new. The builder extracts committed files at the
pin, checks patch hashes, applies patches in order and builds a private tree.
It ignores working edits and existing installed binaries. It does not fetch
missing commits; fetch the pin first if a shallow clone lacks it. Do not apply
the patches again to its generated tree.

The executable is `build/cpmsim-runtime/z80pack/cpmsim/cpmsim`. Keep
`build/cpmsim-runtime/environment.json`: it records source, patches, commands,
compiler, build logs and executable/helper hashes. Build success alone is not
a runtime qualification pass. Different hosts may produce different executable
bytes, so record and validate the actual binary used.

The separate `qualification` profile adds `0003-rom-qualification.patch` and
ROM instrumentation. Ordinary users need the `runtime` profile. Do not set
`CPMSIM_ROM_START` for normal operation. See the
[pinned reconstruction instructions](../../third_party/z80pack/README.md)
for engineering qualification.

## Mount release media and boot

Extract the platform package into a new directory. Verify its published
checksums, preserve the originals and run writable copies in a new session.
The accepted package must supply these images and matching format definitions:

| Drive | Image / role |
| --- | --- |
| A: | `BetterCPM-Distribution-z80pack-332K.dsk`, System Disk |
| B: | `BetterCPM-Utilities-z80pack-332K.dsk`, primary Utilities |
| C: | `BetterCPM-NOAH-z80pack-332K.dsk`, companion Utilities |
| D: | Formatted expendable 332K work disk |

C: retains its historical NOAH image name. It contains NOAH.COM, NOAH.OVL,
NOAH.TXT, PATCH.COM, PATCH.TXT, COMPARE.COM and COMPARE.TXT. Use the matching
NOAH executable and overlay. CRCKSUM and MD5SUM are on B:.

Create `session/disks/`. Copy A:, B:, C: and the formatted work disk to
`drivea.dsk`, `driveb.dsk`, `drivec.dsk` and `drived.dsk` in that directory.
The default raw images are 368,640 bytes each; they are not DMK files.
Close an emulator before changing its mounted media. From the source root:

```sh
export PATH="$PWD/build/cpmsim-runtime/z80pack/cpmsim/srctools:$PATH"
"$PWD/build/cpmsim-runtime/z80pack/cpmsim/cpmsim" -z -d "$PWD/session/disks"
```

Use the freshly built executable and its helpers. A cpmrecv execution error
means the helper/PATH setup is incomplete. `tools/bcpm` contains maintainer-specific
paths and is not a portable installer for a fresh package.

If you already have a configured `bcpm` installation, you can select the
extracted writable copies explicitly:

```sh
bcpm mount a /path/to/system-copy.dsk
bcpm mount b /path/to/primary-utilities-copy.dsk
bcpm mount c /path/to/companion-utilities-copy.dsk
bcpm mount d /path/to/work-copy.dsk
bcpm z /usecurrent
```

`mount` accepts A–D in either case, with an optional colon (`A:` also works).
`z /usecurrent` leaves all current drive assignments unchanged and does not
require locally built distribution images. A: must be present and configured
images must resolve to regular files. Plain `bcpm z` retains automatic selection
of the built System/Utilities images on A–C, leaving D: as configured. Close the
emulator before changing its mounts.

At the guest prompt:

```text
VER /BANNER
DIR A:
DIR B:
DIR C:
B0:CRCKSUM /VER
B0:MD5SUM /VER
C0:NOAH /VER
C0:PATCH /VER
C0:COMPARE /VER
BYE /Y
```

Check banners against the candidate manifest. Save the transcript, initial
image hashes and emulator environment.json. The cpmsim startup script runs
`:VER /BANNER`; no terminal personality or clock provider is loaded automatically.
BYE exits to the host shell. Complete the release checklist's fresh-install and
file-operation checks before accepting a candidate.

## Required release-package contents

Include the pinned lock, complete patch series, reconstruction builder, these
instructions and the z80pack license in the cpmsim host release. If distributing
an emulator executable, include its required helpers and environment.json and
provide the matching upstream source with the applied patches. Preserve the
separate BetterCP/M and utility licensing, attribution and corresponding-source
material. The release checklist must bind the tested emulator and disk images
to the files actually published.

## Live disk changes with MOUNT

`MOUNT.COM` is supplied on the cpmsim System disk in user 0. It requires
an emulator built with the guest MOUNT interface; it is not a Model 4 tool.

```text
MOUNT B: IMAGE.DSK
MOUNT B: "/path/with spaces/Disk Image.dsk"
MOUNT /U B:
MOUNT /UNMOUNT [B,C,D]:
MOUNT /L
MOUNT /LIST [A,C,D]:
MOUNT /VER
MOUNT /HELP
MOUNT /H
```

Bare `MOUNT` lists all supported drives, as does `/L` without a selector.
Unmounting always requires an explicit drive or list. Options can precede
or follow the selector. Mounting accepts one drive and one image only.
Host path case is preserved; relative paths resolve from the emulator's
working directory. The image must be a readable, nonempty regular raw file.
MOUNT does not convert formats or infer filesystem compatibility: the BIOS
selects the raw layout when accessing the disk. The legacy host geometry table
is not used as a size limit for FDF media. Listings show the full path, raw
format, and host read/write availability.

A replacement is checked before the current attachment changes. An image
already attached to another drive is rejected, including hard-link and
symlink aliases. Attachments last for this emulator session and do not change
the launcher's disk links. Restarting the emulator restores its launch media.
The command resets the affected BDOS drive state through existing function 37.

Changing or ejecting A: prompts:

```text
** WARNING: Changing A: while the system is running may cause
disk errors or loss of unsaved data. Continue? [y/N]
```

Only Y/y proceeds. Any other response cancels the entire command, including
all drives in a multi-drive unmount, with:

```text
Operation cancelled. No changes made.
```

There is no open-file tracking or additional safety interlock. You are
responsible for completing writes and choosing suitable media. Replacing A:
does not boot a new OS; Ctrl-C is a warm boot, not a machine reset. Normal
command return may also invoke a warm boot. System disk dependencies can
therefore cause errors immediately after changing A:. Use an emulator reset
and its boot sequence when you intend to boot the replacement disk.

## Host file transfers

The cpmsim System disk also includes R.COM and W.COM in user 0.
`R` reads a host file into CP/M; `W` writes a CP/M file to the host.
Both report version `1.0 (005-dev)` and support `/VER`, `/H`, and `/HELP`.

```text
R "My assembly source.asm" B3:SOURCE.ASM
W B3:SOURCE.ASM "My updated assembly source.asm"
```

Host filenames preserve case and refer to files in the emulator working
directory; R/W do not accept host paths or wildcards. Quote names containing
spaces. A long host source name requires an explicit CP/M 8.3 destination.
MOUNT, R and W are omitted from Model 4 media and general utility manuals.
