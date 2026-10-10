# BetterCP/M

BetterCP/M is a compact, maintainable CP/M-compatible operating system for Z80-class computers.

The project begins with CP/M 2.2 as its compatibility baseline while redesigning the operating system around explicit interfaces, documented state, reproducible builds, portable hardware boundaries, and independently testable subsystems. The objective is not simply to reproduce Digital Research CP/M source code, but to provide a clean and well-specified CP/M environment that remains practical on small 8-bit systems.

BetterCP/M has reached the **1.0 OS implementation milestone**: architecture Stages 1 through 8 and retained OS implementation Items 1 through 6 are complete. Utility selection and completion, release assembly, reproducible qualification tooling, and final release-candidate verification remain. This is a development milestone, not the declaration of a qualified 1.0 release.

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

No. BetterCP/M is not [vibe-coded](https://x.com/karpathy/status/1886192184808149383). It is much close to an [agentic coding](https://martinfowler.com/bliki/AgenticProgramming.html) project.

AI has been used extensively during the implementation phase of BetterCP/M, but the project's goals, scope, compatibility baseline, system design, architecture, interfaces, behavioral requirements, compatibility policy, acceptance criteria, and release requirements are human-directed. AI is used primarily to translate those requirements into code and to assist with analysis, testing, and documentation.

Generated code is not accepted merely because it assembles, boots, or appears to work. BetterCP/M is developed against explicit specifications, compatibility requirements, regression tests, reproducible-build requirements, and qualification criteria.

For a detailed explanation of how artificial intelligence is used in BetterCP/M, its limitations, and the safeguards used around AI-generated code, see [`AI.md`](AI.md).

## Current system

The current development system boots reproducibly on both the **TRS-80 Model 4 under `trs80gp`** and **z80pack `cpmsim`**. It provides a working BetterCP/M BIOS, BDOS, directory services, command processor, transient-program loader, resident commands, CPX command extensions, and relocatable RSX services.

The system supports four physical drives, runtime disk-format assignment, ordinary CP/M drive/user operation, persistent command history, SUBMIT/XSUB operation, configurable disk services, and the standard CP/M file operations exercised by the project's compatibility suite.

CONFIG, DUP, SYSBUILD, and SYSGEN provide the implemented configuration, disk-management, system-generation, and installation path. Disk configuration uses BetterCP/M's FDF/FDB format-description architecture.

The default memory configuration accepts a maximum record-aligned 53 KiB `.COM` image (54,272 bytes).

Subsystems are versioned independently. See [`specifications/SUBSYSTEM-VERSIONING.md`](specifications/SUBSYSTEM-VERSIONING.md) and the authoritative assignments in [`metadata/subsystem-versions.tsv`](metadata/subsystem-versions.tsv).
Utility `/VER` output and independent build counters are defined in [`specifications/UTILITY-VERSIONING.md`](specifications/UTILITY-VERSIONING.md), with assignments in [`metadata/utility-versions.tsv`](metadata/utility-versions.tsv).

## BetterCP/M 1.0

The architecture for BetterCP/M 1.0 is frozen, and the retained OS feature implementation is complete. The remaining roadmap covers utilities, release assembly, and final qualification against the accepted contracts. Testing may identify corrections; it does not imply another planned OS feature implementation stage.

The two required 1.0 platforms are:

- TRS-80 Model 4 / `trs80gp`;
- z80pack / `cpmsim`.

Both platforms already boot BetterCP/M. Remaining platform work includes reproducible qualification tooling and testing of the frozen release artifacts.

The 1.0 system includes the normalized disk-state and FDF/FDB architecture, CONFIG/DUP/SYSGEN installation path, bounded persistent command history, CPX and RSX extension facilities, ordinary CP/M read-only/system/archive file attributes, and the native BetterCP/M clock-service architecture.

The production BetterCP/M private BDOS namespace occupies Functions 176–196, with current 1.0 services assigned at 176–183. Function 197 is reserved and undefined; 198–199 are non-public test selectors. Historical P2DOS Functions 200/201 remain outside the private namespace and are supplied through the P2DOS compatibility frontend.

Several larger extensions are deliberately outside the 1.0 boundary. These include named directories and PATH, a generalized dynamic PDS, filesystem timestamps, terminal-capability redesign, general bank-aware operation, and additional qualified platforms. They remain possible post-1.0 work rather than hidden prerequisites for the first release.

The authoritative scope and implementation sequence are defined by the [`BetterCP/M 1.0 Roadmap`](docs/releases/1.0-ROADMAP.md) and [`1.0 Implementation Contracts`](docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md).

## Building BetterCP/M

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

Detailed build, native-development, system-generation, and testing procedures belong to the BetterCP/M build/development documentation rather than this project overview. Current development information is available in [`docs/programmers/BUILD-DISK.md`](docs/programmers/BUILD-DISK.md) and the engineering record while that documentation is being consolidated.

## Documentation

BetterCP/M distinguishes between the **project/engineering record** and the **published documentation** intended for users, programmers, system developers, and technical readers.

The project record documents architectural decisions, implementation milestones, qualification evidence, current work, and deferred designs. The principal entry points are:

- [`docs/releases/1.0-ROADMAP.md`](docs/releases/1.0-ROADMAP.md) — authoritative 1.0 scope and work sequence;
- [`docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md`](docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md) — retained 1.0 implementation contracts;
- [`docs/architecture/`](docs/architecture/) — architectural specifications and design record;
- [`docs/engineering/`](docs/engineering/) — implementation and qualification record;
- [`docs/programmers/`](docs/programmers/) — current programming and development interfaces;
- [`docs/compatibility/`](docs/compatibility/) — compatibility requirements and evidence;
- [`docs/platform/`](docs/platform/) — platform specifications and implementation material;
- [`TODO.md`](TODO.md) — project backlog governed by the 1.0 roadmap.

Historical documents are retained when they provide useful design or implementation history. Their historical presence does not override later architecture specifications or the frozen 1.0 contracts.

The published BetterCP/M documentation is organized into four families:

1. **User Documentation** — operating, configuring, installing, and maintaining BetterCP/M.
2. **Programmer Documentation** — writing software, CPXs, RSXs, and other programs against supported BetterCP/M interfaces.
3. **Technical Manuals** — authoritative descriptions of the operating system architecture and technical subsystems.
4. **Build & Development Guide** — building, modifying, testing, generating, and porting BetterCP/M.

These manuals are being developed from the reconciled project and engineering record.

## Compatibility and testing

BetterCP/M compatibility is defined by documented behavioral requirements rather than by program names or superficial similarity to CP/M.

The system is tested with the separately maintained [**CP/M 2.2 Compatibility Suite**](https://github.com/CPMArchives/cpm-2.2-compatibility-suite), together with subsystem regression tests, platform tests, native/cross-build comparisons, and physical-system qualification procedures.

Historical milestone results in the engineering record document what a particular build demonstrated at that point in development. Final BetterCP/M 1.0 qualification will be performed against frozen release-candidate images on both required platforms.

## Related projects

The CP/M compatibility foundation used by BetterCP/M is maintained in the [**CP/M 2.2 Compatibility Suite**](https://github.com/CPMArchives/cpm-2.2-compatibility-suite).

General CP/M diagnostic and system utilities such as SYSINFO are maintained separately in [**CP/M Tools**](https://github.com/CPMArchives/cpm-tools).
