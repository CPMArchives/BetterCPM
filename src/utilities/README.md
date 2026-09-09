# BetterCP/M command utilities

This directory is the canonical home of commands maintained as part of the
BetterCP/M operating system.  Their executables are collected in
`build/utilities/` by running:

```sh
python3 tools/build_utilities.py
```

The collection currently contains:

| Family | Commands | Source |
|---|---|---|
| System configuration | `CONFIG`, `DUP` | `config.mac`, `dup.mac`, `disk/` |
| Extension management | `CPX`, `RSX` | `cpx.mac`, `rsx.mac` |
| Stock command replacements | `DIR`, `ERA`, `REN`, `TYPE`, `USER`, `CLS`, `SUBMIT`, `XSUB`; `SAVE` is resident in the CCP | this directory and `../cpx/rcp.mac` |
| System reporting | `STAT`, `VER` | `stat.mac` and `../cpx/rcp.mac` |
| Maintenance | `WARM` | `warm.mac` |

`PIP` is a planned BetterCP/M standard-utility replacement and will join this
collection when implemented.  `RSXTEST` and `RSX2TST` are development probes;
they are built with `RSX.COM` but are not release utilities.

Loadable extension modules are kept separately in `src/rsx/` and `src/cpx/`,
because they are not transient commands even when a `.COM` manager installs
them.

General CP/M utilities are intentionally maintained in the separate
[`CPMArchives/cpm-tools`](https://github.com/CPMArchives/cpm-tools) repository.
That project currently includes SYSINFO, DISKINFO, DPBCHK, FSCK, DISKEDIT,
COMINFO, and BDOSPROBE.  They target CP/M 2.2-compatible systems generally,
rather than BetterCP/M interfaces. BetterCP/M system disks include a pinned,
checksum-verified binary snapshot and its `TOOLS.DOC` manual. Their source,
tests, and release history remain in `cpm-tools`; they must not be forked into
this directory.
