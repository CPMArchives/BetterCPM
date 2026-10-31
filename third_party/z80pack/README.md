# Pinned BetterCP/M cpmsim reconstruction

`upstream.json` is the source/patch/profile lock. Upstream is
https://github.com/udo-munk/z80pack.git at
`91fd28eb04e675c2127df88ed3f40675e15282e2` (17 June 2025 merge #549;
not a release tag). Its presence in the upstream repository was confirmed via
the GitHub commit API on 24 October 2026.

The runtime series preserves the local geometry branch's committed changes:

1. `0001-disk-geometry.patch`: commit `a9248a9186405d11ba17250f37301b079bd57f93`.
2. `0002-raw-fdf-backend.patch`: commit `9bf3c8ac0ee3cf9bdc8748b0bec5bdc7670f79f9`.

Those are the only runtime code changes between upstream and local
`b7a6fa36a2ee185a73727dc5b56ac1af40679e81`; its final commit adds backend
notes only. Local untracked files, installed binaries and object files are not
inputs. Geometry interface version 2 on ports 18/19 is required by BetterCP/M.

The qualification profile additionally applies `0003-rom-qualification.patch`
and builds with `ROM_QUALIFY=YES`. This is the existing CPU/DMA write guard,
control-register protection and named ROM stack high-water/overflow observer.
Its previously stacked zero-context diff was regenerated as one contextual
patch, preserving the result of the established `patch -p1` application.
`tools/cpmsim-rom-qualification.patch` is a compatibility symlink to this file.
There is one authoritative patch series. Runtime builds contain no guard.
Qualification protection is activated explicitly with `CPMSIM_ROM_START=DF00`.
The separate general PC/SP observer in `tools/build_cpmsim_stack_trace.py` is
optional host instrumentation; if needed, feed it the reconstructed runtime
source tree and retain its own observer/binary manifest. It is not a runtime
requirement or part of these compression runs.

## Build and validate

Prerequisites: Python 3, Git, tar, make, a C99 compiler, and on macOS codesign.
Qualification tests also require Expect, cpmtools and the BetterCP/M assembler.
The supplied Git repository is only an object source; it may be on another
branch or contain working edits. A missing pinned commit or mismatched patch
fails. No network fetch, checkout mutation or installed binary copy occurs.

```sh
python3 tools/build_qualified_cpmsim.py --source /path/to/z80pack \
  --output /private/tmp/cpmsim-runtime --profile runtime
python3 tools/build_qualified_cpmsim.py --source /path/to/z80pack \
  --output /private/tmp/cpmsim-qualification --profile qualification
python3 tools/test_qualified_cpmsim.py --source /path/to/z80pack --runtime /private/tmp/cpmsim-runtime \
  --qualification /private/tmp/cpmsim-qualification --output /private/tmp/cpmsim-probes
```

Each output directory must be new. Manifests record committed upstream objects,
ordered patch hashes, patched input hashes, project revision, compiler/make/host,
build command lines, full compiler logs, cpmsim and all helper hashes. Helpers
include cpmrecv and cpmsend, built from the same archive. Defaults explicitly
select release optimization, no GUI panel, and the selected guard profile.
Cross-host executable byte identity is not promised: qualify the resulting hash.
Use the produced `z80pack/cpmsim/cpmsim` and its sibling `srctools` in tests.

After primitives, run ordinary BetterCP/M boot/compression and applicable disk
interchange checks, then protected XIP using `test_z80pack_rom_xip.py --simulator`
with the reconstructed qualification executable. Keep stage failures and logs;
do not claim an untested binary inherits the installed emulator's acceptance.

Upstream's MIT-style license is retained in `LICENSE`. This directory ships
provenance and patches, not an upstream source or executable distribution.

## Live media changes

`0004-live-media.patch` opens the currently assigned raw image for each
synchronous disk command and closes it after the transfer. This applies to
runtime and qualification builds. Geometry interface version 2 is unchanged.
Images may be absent at startup and inserted later. Missing, inaccessible or
non-regular files return disk errors; read commands use read-only access and
writes require read/write access. There is no full-size image requirement.

Replace a drive link (for example with `bcpm mount d /path/to/image`) while
at the guest command prompt, then press Ctrl-C to reset/re-log guest disk state.
Finish application writes before swapping media. Changing format also requires
selecting the matching guest format. A warm boot which reads A: requires a
compatible bootable system disk to remain in A:.

The emulator holds one descriptor for a whole command, so a link replacement
cannot redirect a partially completed command. There is no deferred write queue
in this controller; guest-side buffered writes still require normal CP/M care.
Each transfer now incurs an open/close pair; no performance equivalence claim
is made. The original unmodified upstream remains available separately.

Run the focused media regression against either built profile:

```sh
python3 tools/test_cpmsim_live_media.py --simulator /path/to/cpmsim
```

It tests initially empty drives, atomic link replacement, ejection, reinsertion,
read-only reads and write rejection, writable transfers and shortened media,
all within one emulator process using disposable images.

## Host file transfer

Both profiles include `0005-host-transfer.patch`. The builder also assembles
`z80pack/cpmtools/r.com` and `w.com` and records their hashes under
`guest_utilities` in environment.json. Install R together with the matching
emulator: host read status 1 now denotes EOF, while FF denotes an error.
Old R works with the new emulator; new R reports EOF as an error on old ones.

The commands accept source followed by optional destination:

```text
R FILE.TXT
W FILE.TXT
R TEST.TXT B3:
R TEST.TXT B3:TEST2.TXT
W B3:TEST.TXT TEST2.TXT
```

Host names are flat names with case preserved, relative to the emulator's
working directory. CP/M operands accept drive A-P and optional user 0-15;
unspecified locations use the current drive/user. User selection is restored
on ordinary success and error exits. Destinations default to the source name.
`/VER`, `/H`, and `/HELP` are exact, case-insensitive queries handled before
file operations. R/W currently identify as 1.0 (004-dev).

The patch corrects text EOF across records, read/close error reporting, stale
handles, and the optional SIMBDOS_NO_OVERWRITE implementation. Default
overwrites remain destructive; partial destinations may remain on failure.
Text export still follows the extension table; explicit text/binary modes and
safer replacement are future work. H: mapping, host listing, and MOUNT are not
implemented by this patch.

Focused checks in the reconstructed tree:

```sh
python3 tests/test_host_transfer.py
python3 tests/test_rw_queries.py
python3 tests/test_rw_transfers.py
```

The transfer test uses the actual Z80 core and host service with a BDOS fixture;
full guest-OS integration remains unqualified.

Host operand spelling is now significant. For example,
`W TEST.TXT tEsT.TxT` creates the host destination with that exact spelling.
`R Test.txt` and `R TEST.TXT` select different files on case-sensitive hosts.
An omitted W destination inherits the uppercase CP/M filename; an omitted R
destination uppercases the host name for CP/M. Existing overwrite policy still
applies when different host spellings normalize to the same CP/M name.

The updated CCP preserves the original command tail while retaining uppercase
command dispatch and default FCB construction. This applies to loaded commands
and GO/JUMP. The resident allocation grows by 256 bytes. Older CCPs still fold
typed host names; install the updated CCP to use mixed-case host operands.
This also means transient programs receive mixed-case arguments; programs
that parse the tail themselves must fold their own case-insensitive keywords.

### Long host filenames

```text
R "My assembly source.asm" B3:SOURCE.ASM
W B3:SOURCE.ASM "My updated assembly source.asm"
```

Double quotes group host operands containing spaces. Long host source names
require an explicit CP/M 8.3 destination filename, including when selecting
a destination DU. No truncation or generated aliases occur. Host names retain
typed case and are limited to printable ASCII and the existing 127-byte whole
command tail. Paths and wildcards remain unsupported. Quotes cannot be embedded
or escaped; empty quoted operands fail.

Port 161 host-service functions 128/129 open/create a host file from a bounded
NUL-terminated string at DE. Record reads/writes, DMA and close are unchanged,
and legacy FCB-based host functions remain available. Rebuild and install the
matching R/W and emulator; the older interface cannot open long names.
