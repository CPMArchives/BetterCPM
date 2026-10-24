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
- STARTUP.SUB: editable user-0 startup script; runs `:VER /BANNER`, then loads ADM3A on Model 4.

- DIR.COM: includes the `/WHEREIS` file-location mode.
- ERA.COM
- TYPE.COM
- REN.COM
- VER.COM
- COPY.COM
- CONFIG.COM: [engineering specification](../engineering/CONFIG%20Specification.md).
- DUP.COM: [engineering specification](../engineering/DUP%20Specification.md).
- TIME.COM
- SYSGEN.COM: [engineering specification](../engineering/SYSGEN%20Specification.md).
- STAT.COM
- SUBMIT.COM
- PIP.COM: DRI-compatible transfers, DU operands, `/VER`, and qualified platform devices.
- ED.COM: DRI CP/M 2.2 behavioral reimplementation in Z80/ZSM4, with simple DU addressing, `/VER`, and documented DRI defect corrections; [engineering specification](../engineering/ED%20Specification.md).
- DISK.FDB
- RCP.CPX: required resident command package.
- CPX.COM and RSX.COM: extension managers.
- R3PACK.RSX: required RSX-manager runtime container.
- BYE.COM: cpmsim-only simulator exit command with confirmation, `/Y`, `/VER` and `/HELP`; [command reference](../user/BYE.md).
- ZPRTC.RSX: cpmsim clock provider only.
- ADM3A.RSX: MM-style ADM-3A monitor provider for Model 4 only.
- ADMTST.COM: ADM-3A visual, cursor, bell and keyboard test utility, Model 4 only.
- FREHDCLK.RSX: Model 4/FreHD clock provider only; requires FreHD hardware/emulation.

## Utilities Disk

- XSUB.COM
- DUMP.COM: enhanced read-only hex/ASCII viewer with `/P`, required `/40`, `/FROM=`, exact DU access, interactive Find/Go To, sealed DRI `/BARE`, and visually styled `/VER`; [engineering specification](../engineering/DUMP%20Specification.md).
- TED.COM: selected full-screen editor adaptation of Hector Peraza's TED, with
  WordStar-compatible non-document editing/file commands, recoverable saving,
  bounded memory ownership and source-text preservation. Implementation and
  both-platform qualification are pending; no TED binary is included yet. See
  [engineering specification](../engineering/TED%20Specification.md).
- DASM.COM: selected adaptation of Richard Conn's DASM 1.5 from SIG/M volume
  91, with ZSM4-compatible Zilog output, native symbol conversion, recoverable
  file publication and bounded transient-memory ownership. Implementation,
  [development implementation](../engineering/DASM%20Implementation%20Status.md) exists;
  release acceptance, converter packaging and both-platform disk qualification are pending; no DASM
  binary is included yet. See [engineering specification](../engineering/DASM%20Specification.md).
- ZSM4.COM: unmodified ZSM4 4.7, pinned to Hector Peraza revision
  `96a9ac1081172e1c08291521b77d2a715ec59c8b`; GPL-2.0-or-later.
- LINK.COM: unmodified Digital Research LINK 1.3, extracted from pinned
  z80pack `hd-tools.dsk`; CP/M redistribution permission retained.
- TOOLINFO.TXT, ZSM4COPY.TXT and LINKCOPY.TXT: tool identities, usage,
  copyright and complete applicable license/permission texts. These selected
  notices do not settle general on-disk manual placement.
- The host Utilities package must include `ZSM4-SOURCE.tar.gz` (complete
  corresponding source and original build material), `Toolchain-Provenance.json`,
  `LINK-Permission.html` and `TOOLCHAIN-README.txt` alongside both images.
  `BetterCPM-Utilities-package.zip` bundles both images, reports, companions
  and `Utilities-SHA256SUMS.txt`. Keep these companions when redistributing;
  the disk image alone is not the
  complete toolchain distribution. See [toolchain qualification](../engineering/Utilities%20Toolchain%20Qualification.md).
- DDT.COM: initial DRI-compatible debugger adaptation with shared line editing and `/VER`; [engineering specification](../engineering/DDT%20Specification.md). Exact historical reproduction is retained separately as the verification baseline. Model 4 real-screen/physical-keyboard, native/cross and BetterCP/M cpmsim qualification pass; [Model 4 evidence](../engineering/DDT%20Model%204%20Qualification.md).
- Standalone Z80 disassembler: exact program TBD.
- Noah’s ARK (`NOAH.COM` with `NOAH.OVL`): selected unified archive utility, targeting CP/M `.ARK` and `.LBR` containers. The [engineering specification](../engineering/NOAH%20Specification.md) behavioral baseline is complete; implementation has begun with development-only LBR LIST/TEST/extraction with shared selectors and overwrite prompts; the complete interface remains post-1.0 work. This foundation is not yet included on disk.
- SQ.COM and USQ.COM: standalone Z80 squeeze/unsqueeze commands using the
  common codec ABI, two-pass SQ input, optional destination drive and temporary
  output that is published only after successful processing and closes.
  Usage: `SQ [drive:]file [destination-drive:]` and
  `USQ [drive:]file [destination-drive:]`. The default destination is the logged
  drive, in the current user area. SQ uses historical squeezed-file naming;
  USQ restores the validated embedded name. Existing outputs are refused.
  Both preserve all bytes in CP/M records, including `1Ah` padding.
- UNCR.COM: standalone uncruncher for CRUNCH significant revision `20h`
  with additive checksums. Uses the shared file adapter and safe temporary
  output, with the same command syntax and destination defaults as USQ.
  Historical padded extensions and metadata are supported; the raw header
  field is bounded to 127 bytes. CRUNCH 1.x and other variants are refused.
- CR.COM: standalone one-pass CRUNCH `20h` encoder with capacity resets,
  using the shared adapter and safe temporary output. Syntax and destination
  defaults match SQ. Historical naming replaces the middle extension letter
  with Z; an absent extension or existing middle Z becomes `.ZZZ`. A source
  already named `.ZZZ` is refused. The original filename is embedded for UNCR.
- UNLZH.COM: standalone decoder for CrLZH `10h` and `20h` with additive
  checksums, using the shared file adapter, bounded embedded names and safe
  temporary output. Usage: `UNLZH [drive:]file [destination-drive:]`. Existing
  outputs are refused; the default destination is the logged drive. Embedded
  filenames with high-bit characters are refused rather than normalized.
- LZH.COM: standalone one-pass CrLZH `20h` encoder with additive checksums,
  shared file I/O and safe temporary output. Usage:
  `LZH [drive:]file [destination-drive:]`; the destination defaults to the
  logged drive. Historical names progress `ABC` -> `AYC`, `AYC` -> `AYY`,
  `AYY` -> `YYY`; missing extensions become `.YYY`, and `.YYY` input is
  refused. Original names, including padded extension slots, are embedded
  for UNLZH. Existing outputs are refused.
- Standalone compression commands are implemented.
  Individual commands are sufficient for release 1.0. A unified archive/codec
  interface through Noah’s ARK is post-1.0 work.
- Broader development/userland tools generally belong here; individual additions
  still require selection.

### Provisional daily Utilities media

`tools/build_utilities_disk.py --build` assembles the currently implemented
selected components: DUMP.COM, DDT.COM, XSUB.COM and its required BATCHIO.RSX,
SQ.COM, USQ.COM, CR.COM, UNCR.COM, LZH.COM and UNLZH.COM, plus the selected
ZSM4/LINK binaries and their three notice files (15 files total). DDT is the owned adaptation, not the historical reference; its Model 4 screen/input campaign passes on disposable current-system media. DDT also passes [Utilities release acceptance](../engineering/DDT%20Utilities%20Release%20Acceptance.md) from B: beside normal System A: on both platforms. `--ddt-acceptance REPORT` binds that component verdict to the exact artifact and image hashes; it does not promote the whole disk. The builder verifies
file readback and the filesystem, and produces a 332K raw cpmsim image and an
80T DS 800K data DMK for Model 4. Reports explicitly list pending selections;
these are provisional daily media, not a fully qualified Utilities release.
No third-party program is silently selected or substituted.

The tracked `tools/bcpm` launcher mirrors the maintainer's personal script.
After its ordinary System Disk build, `bcpm build` creates these Utilities media
and mounts the raw image as cpmsim B:. `bcpm z` also selects Utilities as B:;
`bcpm t` selects the native Utilities image as B: and the existing development
build disk as C:. Neither automatically mounts the conformance suite. Replacing
an existing cpmsim B: symlink preserves its old target; a regular disk file is
never overwritten. Existing emulator sessions must be closed before rebuilding
or switching mounted media.

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

## Default cold-start command

Both distribution images save `SUBMIT STARTUP` in their existing BCST startup
record. `A0:STARTUP.SUB` supplies the cold-boot sign-on through `:VER /BANNER`
without permanent BIOS code. The Model 4 script then runs `RSX LOAD ADM3A`;
the cpmsim script currently contains only the banner command. Warm boot does not rerun the cold-start command.
Users may edit the script or change/disable the saved command through CONFIG.
A missing script reports the ordinary SUBMIT error and returns to the prompt.
No ECHO command is supplied; ECHO.RSX is a diagnostic extension, not a shell
command or distribution component.


The Model 4 monitor build uses `tools/build_adm3a.py`, called by the complete
system build. Release artifacts are `build/rsx/ADM3A.RSX` and
`build/utilities/ADMTST.COM`; development listings/copies remain under
`build/monitor-development`. These portable personality/test entries are supplied on both disks. The Model 4
startup script loads M4SCRN before ADM3A; cpmsim users load ANSISCRN before
ADM3A when selecting that personality. Both disks supply the portable VT52.RSX and VT52TST.COM; the bounded ANSI/VT100 provider is also supplied on cpmsim.

VT52 release artifacts are `build/rsx/VT52.RSX` and
`build/utilities/VT52TST.COM`, generated by `tools/build_vt52.py` during the
complete build. Both disks supply the same portable personality. The Model 4
disk additionally supplies `M4SCRN.RSX`; cpmsim supplies `ANSISCRN.RSX` for an
ANSI host endpoint. `tools/build_screen_backends.py` builds these before VT52.
Load the matching backend before VT52, and unload it after VT52. Startup does
not automatically select VT52; the Model 4 startup loads M4SCRN and then ADM3A.
See [portable integration](../engineering/VT52%20Portable%20Backend%20Integration.md)
for qualification scope. These optional loaded modules add no permanent core
memory. The Model 4 backend must be built with the supplied BIOS.


Both system disks supply the same portable `ANSI.RSX` and `ANSITST.COM`, built
by `tools/build_ansi.py` into `build/rsx` and `build/utilities`. Load the matching
full-control backend first: M4SCRN on Model 4, ANSISCRN on cpmsim. ANSI is not
selected automatically at startup. The unchanged TE VT100 editor passes the
cpmsim application campaign with a 25-row host window; that configuration is not
qualified for the 24-row Model 4. See the provider qualification record for the
supported subset and test limits.

## Compression 1.0 feature freeze

The six selected compression commands are feature-frozen at version 1.0
Build 004 after the forgiving query amendment to baseline `00e6785`
(merged in `569825d`). The
[qualification index](../engineering/Compression-1.0-Qualification.json)
records final COM hashes and the completed stock CP/M 2.2 historical/query
campaigns. Package these qualified bytes; a changed artifact needs relevant
requalification. The [1.0 compression release checklist](1.0-ROADMAP.md#compression-utilities--10-feature-freeze-and-release-checklist)
records completed BetterCP/M platform and native assembly qualification;
[clean pinned emulator reconstruction](../engineering/CPMSIM%20Reconstruction%20Qualification.md)
also passes, while final Utilities image/component acceptance remains open. This freeze does not change disk
membership or promote provisional media to a release.

Build 004 compression platform execution is recorded in the
[platform qualification record](../engineering/Compression%20Utilities%20Platform%20Qualification.md).
cpmsim and Model 4 component checks pass after pinning host disk geometry.
Utilities media remain PROVISIONAL; this campaign does not close whole-disk acceptance.

[Native ZSM4/LINK qualification](../engineering/Compression%20Native%20Build%20Qualification.md)
passes for all six Build 004 commands with exact executable parity.

## Current ten-file inventory acceptance — 2026-10-24

The maintainer selected qualification of the current implemented inventory while
keeping unresolved selections open. [Acceptance and evidence](../engineering/Utility%20Release%20Reacceptance.md)
cover exact ten-file membership/user 0, independent FDF allocation and executable
readback, filesystem integrity, Model 4 conversion, and all included components
on the recorded System/Utilities pairs. The shared query change is reaccepted
for current shipped utilities. Both Utilities images remain byte-identical to
the compression-qualified images; their current hash manifest is retained.

This is current-inventory acceptance, not final approval of the complete release
inventory. Full-screen editor/disassembler selection, ZSM4/LINK packaging and
on-disk documentation/native-build materials remain open. NOAH's complete
interface is selected post-1.0 work; its development foundation stays excluded.
The builder reports it as deferred rather than an unselected 1.0 archive tool.

## Full-screen editor selection — 2026-10-25

The maintainer selected TED with WordStar-compatible editing/file commands and
corrections for file safety, memory ownership and source-text preservation.
[The engineering specification](../engineering/TED%20Specification.md) defines
the adaptation and both-platform acceptance gates. This resolves the editor
selection mentioned in earlier checkpoints; implementation, packaging and
qualification remain pending. Existing Utilities images and their evidence are
unchanged. Update the builder's pending-editor description when implementing
this selection; do not substitute the upstream binary as a qualified release.

## Disassembler selection — 2026-10-25

The maintainer selected Richard Conn's DASM 1.5, accepting SIG/M's historical
public-domain distribution practice as the basis for redistribution and
modification. Preserve upstream provenance and credits with the adaptation.
[The engineering specification](../engineering/DASM%20Specification.md) defines
ZSM4 compatibility, native symbol conversion, file safety, memory ownership
and round-trip acceptance on both platforms. This resolves disassembler
selection in earlier checkpoints. A [development implementation](../engineering/DASM%20Implementation%20Status.md)
and native symbol converter now exist; full specification acceptance,
packaging and disk qualification remain pending. Existing Utilities images and their acceptance evidence are
unchanged. ZSM4 and Digital Research LINK retain their third-party identities
and versions.
