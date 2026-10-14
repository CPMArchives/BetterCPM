# BetterCP/M Distribution Manifest

Status: authoritative manifest in progress.
Established by the maintainer, 2026-10-10.

This document determines distribution membership. Development-disk contents and
build output directories are not distribution inventories. Planned components
remain members even when no implementation is available. Do not silently omit
an implemented component whose current build fails, substitute an older binary,
or change membership to meet disk capacity.

The immediate packaging target is the System Disk for both z80pack/cpmsim and
trs80gp/Model 4. Utilities and CP/M Tools disk assembly can follow separately.
The two System Disks require their own platform boot and BIOS implementations.
All membership or layout changes require discussion with the maintainer.

## System Disk

- README.TXT: introductory ASCII text in user 0, from `src/distribution/README.TXT`.

- DIR.COM: includes the `/WHEREIS` file-location mode.
- ERA.COM
- TYPE.COM
- REN.COM
- VER.COM
- COPY.COM
- CONFIG.COM
- DUP.COM
- TIME.COM
- SYSGEN.COM
- STAT.COM
- SUBMIT.COM
- PIP.COM
- ED.COM: planned DRI CP/M 2.2 behavioral reimplementation in Z80/ZSM4, with simple DU addressing and /VER; [engineering specification](../engineering/ED%20Specification.md) and reference baseline recorded.
- DISK.FDB
- RCP.CPX: required resident command package.
- CPX.COM and RSX.COM: extension managers.
- R3PACK.RSX: required RSX-manager runtime container.
- BYE.COM: cpmsim-only simulator exit command.
- ZPRTC.RSX: cpmsim clock provider only.
- FREHDCLK.RSX: Model 4/FreHD clock provider only; requires FreHD hardware/emulation.

## Utilities Disk

- XSUB.COM
- DUMP.COM
- General-purpose full-screen editor: adopt an existing program; exact program TBD.
- ZSM4
- LINK
- Debugger: TBD.
- Standalone Z80 disassembler: exact program TBD.
- Archive utility: likely LU or NULU; selection TBD.
- Compression tools: SQ/USQ, CR/UNCR, CrLZH; exact artifacts TBD.
- Broader development/userland tools generally belong here; individual additions
  still require selection.

## CP/M Tools Disk

This is separate from the BetterCP/M Utilities Disk and derives from the
separate CP/M Tools project.

- SYSINFO
- BIOSINFO
- DISKINFO
- MEMINFO
- Similar portable diagnostic/information tools: final project inventory TBD.

## Outstanding packaging decisions

The lists above establish membership, not implementation status. The builder
must record implementation/build status and target applicability separately.

- Required operating-system boot/resident components are installed as the
  target's system, rather than inferred from development-directory files.
- README.TXT is the selected introductory on-disk document. Additional on-disk
  documentation filenames and placement remain undecided.
- Files are installed in user 0, the boot/search location, unless a later
  manifest revision specifies otherwise.

Unresolved items must appear in the distribution report. They must not be
quietly resolved by copying additional files from development media.

## Required runtime dependencies

The approved RSX manager and clock providers require `R3PACK.RSX`, a single
15 KB fixed-slot container of the existing runtime helpers. It replaces the
fifteen separately distributed R3 helper files; these remain diagnostic build
artifacts. The container is an internal manager dependency, not an extension
to load with RSX LOAD. `tools/rsx_container.py` fixes the slot order and
`tools/build_rsx_runtime_overlays.py` builds it. Keep it matched to the system
build. This packaging cleanup does not change the overlay architecture; the
post-1.0 architectural review remains planned.

Clock providers are shipped for explicit loading; no provider is loaded by
default. P2DOS and 104/105 compatibility adapters are not selected by this
manifest. No HELLO, STATEFUL, diagnostic, or conformance-test packages are shipped.

`metadata/distribution.json` is the machine-readable System Disk projection of
this document. It records build/status/target information separately from disk
membership. Both representations must be updated together for approved changes.
