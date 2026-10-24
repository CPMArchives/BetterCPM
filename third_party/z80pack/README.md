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
python3 tools/test_qualified_cpmsim.py --runtime /private/tmp/cpmsim-runtime \
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
