# BetterCP/M

BetterCP/M is a compact, maintainable CP/M-compatible operating system for Z80-class computers. **BetterCP/M 1.0 is released.** Download the System package for your platform from the [published v1.0 release](https://github.com/CPMArchives/BetterCPM/releases/tag/v1.0), then follow the [quick start](#quick-start) below. Matching Utilities, complete Source and the four-manual Documentation collection are available separately. See the [documentation index](docs/README.md).

The project begins with CP/M 2.2 as its compatibility baseline while redesigning the operating system around explicit interfaces, documented state, reproducible builds, portable hardware boundaries, and independently testable subsystems. The objective is not simply to reproduce Digital Research CP/M source code, but to provide a clean and well-specified CP/M environment that remains practical on small 8-bit systems.

The released 1.0 baseline has qualified installation and reconstruction receipts for the exact published software packages. Qualification covers patched z80pack `cpmsim` and the TRS-80 Model 4 under `trs80gp`; it does not establish physical-hardware validation.

The finalized visual design is defined in the [BetterCP/M Visual Identity standard](specifications/VISUAL-IDENTITY.md).

The [Command and Utilities Reference](docs/user/command_reference.md) covers System Disk commands, resident commands, and primary/companion Utilities programs.

## Goals

BetterCP/M is designed around several principles:

- strong CP/M 2.2 application and programming compatibility;
- a compact resident system and a default transient-program area of at least 53 KiB;
- clear interfaces between the CCP, BDOS, BIOS, extensions, and hardware-dependent code;
- portable system code separated from machine-specific support;
- reproducible system and disk-image builds;
- explicit, inspectable configuration instead of undocumented system state;
- support for ROM-resident immutable code with mutable system state held in RAM;
- loadable command and resident extensions through CPX and RSX facilities;
- compatibility requirements backed by an executable conformance suite;
- native CP/M development and system-generation paths alongside modern cross-development tools.

BetterCP/M retains the familiar CP/M model of drives, user areas, FCB-based file access, transient `.COM` programs, BDOS calls, and BIOS services while providing a more structured foundation for extending and maintaining the system.

## The AI Elephant in the Room

### Does BetterCP/M Use AI?

Yes. Artificial intelligence has been used extensively in the implementation of BetterCP/M, including the production of its Z80 assembly-language source code. That may mean BetterCP/M is not for you. If you're still interested, read on.

### So Is BetterCP/M Vibe-Coded?

No. BetterCP/M is not [vibe-coded](https://x.com/karpathy/status/1886192184808149383). It is much closer to an [agentic coding](https://martinfowler.com/bliki/AgenticProgramming.html) project.

AI has been used extensively during the implementation phase of BetterCP/M, but the project's goals, scope, compatibility baseline, system design, architecture, interfaces, behavioral requirements, compatibility policy, acceptance criteria, and release requirements are human-directed. AI is used primarily to translate those requirements into code and to assist with analysis, testing, and documentation.

Generated code is not accepted merely because it assembles, boots, or appears to work. BetterCP/M is developed against explicit specifications, compatibility requirements, regression tests, reproducible-build requirements, and qualification criteria.

For a detailed explanation of how artificial intelligence is used in BetterCP/M, its limitations, and the safeguards used around AI-generated code, see [`AI.md`](AI.md).

## Current system

The released 1.0 system boots reproducibly on both the **TRS-80 Model 4 under `trs80gp`** and **z80pack `cpmsim`**. It provides a working BetterCP/M BIOS, BDOS, directory services, command processor, transient-program loader, resident commands, CPX command extensions, and relocatable RSX services.

The system supports four physical drives, runtime disk-format assignment, ordinary CP/M drive/user operation, persistent command history, SUBMIT/XSUB operation, configurable disk services, and the standard CP/M file operations exercised by the project's compatibility suite.

CONFIG, DUP, SYSBUILD, and SYSGEN provide the implemented configuration, disk-management, system-generation, and installation path. Disk configuration uses BetterCP/M's FDF/FDB format-description architecture.

The default unloaded memory configuration accepts a maximum record-aligned 53 KiB `.COM` image (54,272 bytes). The supplied cpmsim startup reports 53K TPA; Model 4 startup loads M4SCRN followed by ADM3A and reports 50K. Interactive FDB requires the unloaded 53K environment; see the platform installation guide for unloading and restoring the startup environment.

Subsystems are versioned independently. See [`specifications/SUBSYSTEM-VERSIONING.md`](specifications/SUBSYSTEM-VERSIONING.md) and the authoritative assignments in [`metadata/subsystem-versions.tsv`](metadata/subsystem-versions.tsv).
Utility `/VER` output and independent build counters are defined in [`specifications/UTILITY-VERSIONING.md`](specifications/UTILITY-VERSIONING.md), with assignments in [`metadata/utility-versions.tsv`](metadata/utility-versions.tsv).

## Future platforms

The [Platform Roadmap](docs/PLATFORM_ROADMAP.md) records existing baselines,
provisional P0–P3 priorities, and planned or exploratory ports. It distinguishes
bounded emulator validation, preliminary boot reports, and physical-hardware
status; all current testing is emulator-based.

## BetterCP/M 1.0

[BetterCP/M 1.0](https://github.com/CPMArchives/BetterCPM/releases/tag/v1.0) is published as seven ZIP downloads: two System packages, two Utilities packages, packaged Source, Documentation and optional Qualification Evidence. Packaging corrections preserve source and disk-image bytes while updating layouts, instructions and archive hashes; the accepted Documentation ZIP was built separately. Tag `v1.0` identifies qualified software merge `2842d0eb0732683d9280a38d576c3dba423cb893`, while the Documentation archive records commit `549378120a8220cf546deb9c7602cfb3f73b6b0e`.

The two released 1.0 platforms are:

- TRS-80 Model 4 / `trs80gp`;
- z80pack / `cpmsim`.

Both platforms have exact-artifact qualification, installation and file-preservation receipts under the lock. Model 4 qualification used trs80gp; physical Model 4 media transfer, Model 4D/4P and additional platforms remain outside those receipts.

The 1.0 system includes the normalized disk-state and FDF/FDB architecture, CONFIG/DUP/SYSGEN installation path, bounded persistent command history, CPX and RSX extension facilities, ordinary CP/M read-only/system/archive file attributes, and the native BetterCP/M clock-service architecture.

The production BetterCP/M private BDOS namespace occupies Functions 176–196, with current 1.0 services assigned at 176–183. Function 197 is reserved and undefined; 198–199 are non-public test selectors. Historical P2DOS Functions 200/201 remain outside the private namespace and are supplied through the P2DOS compatibility frontend.

Several larger extensions are deliberately outside the 1.0 boundary. These include named directories and PATH, a generalized dynamic PDS, filesystem timestamps, terminal-capability redesign, general bank-aware operation, and additional qualified platforms. They remain possible post-1.0 work rather than hidden prerequisites for the first release.

A bounded [terminal-monitor RSX](docs/architecture/31%20Terminal%20Monitor%20RSX.md)
was accepted for 1.0 on 2026-10-12 and implemented. It supplies a
loadable console personality through BIOS hooks and the existing startup-script
mechanism. The broader terminal-capability redesign remains post-1.0 work.

The authoritative scope and implementation sequence are defined by the [`BetterCP/M 1.0 Roadmap`](docs/releases/1.0-ROADMAP.md) and [`1.0 Implementation Contracts`](docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md).

## Release downloads

Get the seven ZIP packages from the [published v1.0 release](https://github.com/CPMArchives/BetterCPM/releases/tag/v1.0):

**For the released build, download [BetterCPM-1.0-Source.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-Source.zip).** This is the prepared Source package with matching source, native build material and the pinned dependency tar needed for offline reconstruction.

GitHub also adds **“Source code (zip)”** and **“Source code (tar.gz)”** automatically at the bottom of the release assets. Those are repository snapshots at tag `v1.0`, not the packaged Source download. They omit the packaged dependency tar and subsequent packaging/layout corrections. Use the named `BetterCPM-1.0-Source.zip` for released-source reconstruction; the automatic snapshots serve repository browsing.

| Package | Download and purpose |
| --- | --- |
| System — cpmsim | [BetterCPM-1.0-System-cpmsim.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-System-cpmsim.zip) — System/work disks, platform instructions and the pinned offline runtime reconstruction kit. |
| System — Model 4 | [BetterCPM-1.0-System-Model4.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-System-Model4.zip) — Bootable System and work DMKs with platform instructions. |
| Utilities — cpmsim | [BetterCPM-Utilities-1.0-cpmsim.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-Utilities-1.0-cpmsim.zip) — Primary Utilities and NOAH companion disks, manuals and instructions for obtaining matching source separately. |
| Utilities — Model 4 | [BetterCPM-Utilities-1.0-Model4.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-Utilities-1.0-Model4.zip) — Matching Utilities and NOAH companion DMKs, manuals and instructions for obtaining matching source separately. |
| Packaged Source | [BetterCPM-1.0-Source.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-Source.zip) — Complete matching source in one consolidated tree, native build material, tools, pinned dependency tar and patches for offline reconstruction. |
| Documentation | [BetterCPM-1.0-Documentation.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-Documentation.zip) — Four manuals, API chapters, examples and supporting guidance in Markdown/text form. |
| Qualification Evidence (optional) | [BetterCPM-1.0-Qualification-Evidence.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-Qualification-Evidence.zip) — Historical qualification archives, engineering receipts and review records; restoration instructions are in the packaged Source ZIP. |

Verify all seven ZIPs against [BetterCPM-1.0-SHA256SUMS.txt](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-SHA256SUMS.txt). The [release notes](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-RELEASE-NOTES.md) and [exact-file index](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-RELEASE.json) record current packaging identities and retained provenance.

Packaging corrections preserve the software source and disk-image bytes while changing ZIP layouts and hashes. All ZIP root folders now match their filenames without `.zip`; System and Utilities images use `images/cpmsim/` or `images/Model4/`. Utilities corresponding source is offered through the separate packaged Source ZIP. Its shared source tree is consolidated, its ZSM4 source archive is retained once, and optional historical evidence is a separate ZIP. Software and utility versions remain unchanged.

Some embedded source/build records retain historical “candidate” or “hold” wording. The published release establishes publication status; historical records do not override current download identities, usage instructions, licenses, known limitations or qualification boundaries. The original software lock records pre-correction archive identities, not current ZIP hashes.

## Quick start

Download the System ZIP for your platform; Utilities are optional and separate. Extract into a new directory, verify checksums, preserve the supplied images and run writable copies. With Utilities, use A: System, B: primary Utilities, C: NOAH companion and D: work. Without Utilities, use separate writable copies of the supplied blank work image for B:, C: and D:.

### TRS-80 Model 4 / trs80gp

Follow the [Model 4 installation guide](docs/platform/MODEL4-INSTALLATION.md). Select Model 4 in trs80gp, enable 80-track double-sided drives, and attach the matching DMK copies to physical drives 0–3. For example, with Utilities installed:

```sh
/path/to/trs80gp -m4 \
  -d0 /path/to/system-copy.dmk \
  -d1 /path/to/primary-utilities-copy.dmk \
  -d2 /path/to/companion-utilities-copy.dmk \
  -d3 /path/to/work-copy.dmk
```

The System DMK is `BetterCPM-Distribution-trs80gp-80T-DS-System.dmk`; primary Utilities and companion images are `BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk` and `BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk`. Wait for the A0 prompt after startup loads M4SCRN and ADM3A. Physical-media transfer requires a separate hardware-specific procedure; a DMK is an emulator container.

### Patched z80pack / cpmsim

Follow the [cpmsim installation guide](docs/platform/CPMSIM-INSTALLATION.md), including host prerequisites. Stock upstream cpmsim is insufficient. The System ZIP includes everything needed to reconstruct the pinned runtime offline; no Utilities or full Source download is needed to boot it.

From the extracted System package's `host/BetterCPM/` directory, build into a new output directory:

```sh
python3 tools/build_qualified_cpmsim.py \
  --source dependencies/z80pack-cpmsim-91fd28eb04e675c2127df88ed3f40675e15282e2.tar \
  --output build/cpmsim-runtime --profile runtime
```

Create `session/disks/` under that directory. Copy the System image `BetterCPM-Distribution-z80pack-332K.dsk` there as `drivea.dsk`, and separate writable work-image copies as `driveb.dsk`, `drivec.dsk` and `drived.dsk`. If using Utilities, replace B: and C: with copies of `BetterCPM-Utilities-z80pack-332K.dsk` and `BetterCPM-NOAH-z80pack-332K.dsk`. Then launch with the matching helpers:

```sh
export PATH="$PWD/build/cpmsim-runtime/z80pack/cpmsim/srctools:$PATH"
"$PWD/build/cpmsim-runtime/z80pack/cpmsim/cpmsim" -z -d "$PWD/session/disks"
```

Keep the generated `environment.json` build receipt. Use a host terminal of at least 80 columns by 24 rows when loading ANSISCRN/ANSI. Default cpmsim startup loads no terminal personality or clock provider. Use `BYE /Y` to exit to the host.

### First commands

At the guest prompt on either platform:

```text
:VER /BANNER
DIR A:
DIR D:
```

With Utilities installed, also inspect `DIR B:` and `DIR C:`. Continue with the [User's Guide](docs/user/users_guide.md) and [Command and Utilities Reference](docs/user/command_reference.md). Read the [1.0 errata](docs/releases/1.0-ERRATA.md), including the A0 companion requirement for XSUB and the ANSI terminal-size requirement. Use the platform guide for FDB's memory requirements and system installation; copying directory files alone does not install a bootable system.

## Building BetterCP/M

To use the released system, start with the downloads above. For exact 1.0 reconstruction, use the matching Source ZIP and [Source Build and Reconstruction Guide](docs/SOURCE-BUILD.md). The commands below build the current checkout, which may differ from the released bytes.

The complete current development image can be generated with:

```sh
python3 tools/build_complete_system.py
```

For an interactive native OS build under trs80gp, prepare fresh media and launch:

```sh
bash tools/start_native_build.sh
```

This rebuilds a coherent source/tool snapshot and creates a boot disk in A:,
the native build kit in B:, a SYSTEM-format work/installation disk in C:,
and a spare data disk in D:. Existing output directories are never overwritten.
Use `--prepare-only` to create media without launching, or supply a new output
directory after that option. Set `TRS80GP` to override the emulator executable.

In user zero, enter `B:` and `SUBMIT BUILD`. SUBMIT may be invoked from B:,
but its temporary command stream uses writable A0:, as required by the CCP.
The invoking user area is preserved; scripts may change drive/user without
changing the queue location.
The build selects C: and produces
verified `SYSTEM.SYS`. Then enter `B:SYSGEN C:SYSTEM.SYS C:` to install it on
that same disk without changing its ordinary files. Do not format C: between
building and installation. The script prints the media directory for later reuse.

Individual subsystem builders and tests remain available under `tools/` for development and qualification work.

BetterCP/M also preserves a native CP/M build path. ZSM4 produces relocatable objects which are linked with Digital Research LINK where applicable, and native results are compared with cross-built binaries where practical.

The source/build disk can be generated with:

```sh
python3 tools/build_source_disk.py
```

Start complete reconstruction with the [Source Build and Reconstruction Guide](docs/SOURCE-BUILD.md). Current development information is available in [`docs/programmers/BUILD-DISK.md`](docs/programmers/BUILD-DISK.md) and the engineering record with their staged-history reading notes.

## Documentation

BetterCP/M distinguishes between the **project/engineering record** and the **published documentation** intended for users, programmers, system developers, and technical readers.

The project record documents architectural decisions, implementation milestones, qualification evidence, current work, and deferred designs. The principal entry points are:

- [`docs/releases/1.0-ROADMAP.md`](docs/releases/1.0-ROADMAP.md) — authoritative 1.0 scope and work sequence;
- [`docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md`](docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md) — retained 1.0 implementation contracts;
- [`docs/architecture/`](docs/architecture/) — architectural specifications and design record;
- [`docs/architecture/32 BetterCPM Vision and Post-1.0 Direction.md`](docs/architecture/32%20BetterCPM%20Vision%20and%20Post-1.0%20Direction.md) — project-level direction for evaluating post-1.0 evolution;
- [`docs/engineering/`](docs/engineering/) — implementation and qualification record;
- [`docs/programmers/`](docs/programmers/) — current programming and development interfaces;
- [Shared input library](docs/programmers/Shared%20Input%20Library.md) — reusable utility editors, prompts, choices and integration contracts;
- [`docs/compatibility/`](docs/compatibility/) — compatibility requirements and evidence;
- [`docs/platform/`](docs/platform/) — platform specifications and implementation material;
- [`TODO.md`](TODO.md) — project backlog governed by the 1.0 roadmap.

Historical documents are retained when they provide useful design or implementation history. Their historical presence does not override later architecture specifications or the frozen 1.0 contracts.

The published Documentation collection has four principal manuals:

1. **[User's Guide](docs/user/users_guide.md)** — task-oriented operation followed by seven conceptual chapters.
2. **[Command and Utilities Reference](docs/user/command_reference.md)** — functional sections with alphabetized, independently usable resident/transient entries.
3. **[Programmer's Guide](docs/programmers/programmers_guide.md)** — application and extension development with linked CP/M 2.2 and BetterCP/M API references, worked examples and explicit stability boundaries.
4. **[Practical Porting Guide](docs/porting/practical_porting_guide.md)** — staged assessment, build, boot, BIOS/disk/memory integration, installation and qualification. Further hardware examples remain separate expansion.

Installation guides, source reconstruction guidance, release information, licensing and engineering records support these manuals. The former [Utilities Manual](docs/user/utilities_manual.md) and standalone command paths are locators into the consolidated reference.

The [non-documentation lock](docs/releases/non-documentation-lock-1.0/README.md) records the original five Source/System/Utilities archives and qualified software. Current packaging identities are recorded in the release index linked above. The accepted Documentation package has its own revision and provenance. Further programmer/porting expansion remains separate from the released 1.0 software baseline.

## Compatibility and testing

BetterCP/M compatibility is defined by documented behavioral requirements rather than by program names or superficial similarity to CP/M.

The system is tested with the separately maintained [**CP/M 2.2 Compatibility Suite**](https://github.com/CPMArchives/cpm-2.2-compatibility-suite), together with subsystem regression tests, platform tests, native/cross-build comparisons, and physical-system qualification procedures.

Historical milestone results retain their exact builds and scope. The November 2 card accounting and Model 4 batch are not universal two-platform passes. Later exact-package installation, native query, offline reproduction and protected-XIP receipts are summarized in the [retained release notes](docs/releases/RELEASE-NOTES-1.0.md) and [five-package lock](docs/releases/non-documentation-lock-1.0/README.md). New documentation checks do not rerun those trials. These receipts establish their stated emulator scope; no physical hardware qualification is implied. Publication status is recorded by the [v1.0 release](https://github.com/CPMArchives/BetterCPM/releases/tag/v1.0).

## Related projects

The CP/M compatibility foundation used by BetterCP/M is maintained in the [**CP/M 2.2 Compatibility Suite**](https://github.com/CPMArchives/cpm-2.2-compatibility-suite).

General CP/M diagnostic and system utilities such as SYSINFO are maintained separately in [**CP/M Tools**](https://github.com/CPMArchives/cpm-tools).

The BetterCP/M cpmsim target requires the [pinned emulator reconstruction](third_party/z80pack/README.md), including geometry interface v2. Runtime and ROM-qualification profiles are distinct.

## License and separate works

Original BetterCP/M software, tools, tests and reusable code examples are
[GPL-2.0-or-later](LICENSE); [COPYING](COPYING) contains the GPL text. Original
documentation prose and illustrations use CC BY 4.0; the complete text is in
[LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt).
[Documentation licensing](docs/LICENSING.md) explains embedded examples and reuse.
[NOTICE](NOTICE) identifies the scope and separately licensed/historical works.
Third-party material retains its own terms. The release ships BetterCP/M’s native
catalogue and excludes the original Montezuma DISK.FDF from all packages.
