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
