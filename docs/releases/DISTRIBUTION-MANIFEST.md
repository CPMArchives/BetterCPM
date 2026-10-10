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

- DIR.COM
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
- DISK.FDB
- WHEREIS.COM: planned; include once implemented.
- RCP.CPX: required resident command package.
- CPX.COM and RSX.COM: extension managers.
- BYE.COM: cpmsim-only simulator exit command.
- ZPRTC.RSX: cpmsim clock provider only.
- FREHDCLK.RSX: Model 4/FreHD clock provider only; requires FreHD hardware/emulation.
- General-purpose full-screen editor: exact program TBD.

## Utilities Disk

- XSUB.COM
- DUMP.COM
- DRI ED.COM for BetterCP/M 1.0. A BetterCP/M-compatible replacement is later work.
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
- No on-disk documentation filenames or placement have yet been selected.
- Files are installed in user 0, the boot/search location, unless a later
  manifest revision specifies otherwise.

Unresolved items must appear in the distribution report. They must not be
quietly resolved by copying additional files from development media.

## Required runtime dependencies

The approved RSX manager and clock providers require the existing file-backed
manager helpers below. These are runtime overlays, not optional test extensions;
`src/system` and `tools/build_rsx_runtime_overlays.py` define their dependencies.

R3PLAN.RSX, R3SLOTS.RSX, R3SNAP.RSX, R3CARR.RSX, R3META.RSX, R3COORD.RSX,
R3PROF.RSX, R3KCTX.RSX, R3KEEP.RSX, R3KPRE.RSX, R3FINAL.RSX, R3DROP.RSX,
R3MOVE.RSX, R3COMIT.RSX, R3RESOL.RSX.

Clock providers are shipped for explicit loading; no provider is loaded by
default. P2DOS and 104/105 compatibility adapters are not selected by this
manifest. No HELLO, STATEFUL, diagnostic, or conformance-test packages are shipped.

`metadata/distribution.json` is the machine-readable System Disk projection of
this document. It records build/status/target information separately from disk
membership. Both representations must be updated together for approved changes.
