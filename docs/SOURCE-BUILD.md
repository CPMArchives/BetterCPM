# BetterCP/M Source Build and Reconstruction Guide

This is the build entry point supporting all four manuals. It describes reconstructing the locked 1.0 software from its matching Source download, native development and the separate documentation build. Original prose is CC BY 4.0; original reusable code examples are GPL-2.0-or-later. See [licensing](LICENSING.md).

## Choose the right source

Use `BetterCPM-1.0-Source.zip`, whose exact identity is recorded in the [five-package lock](releases/non-documentation-lock-1.0/LOCK.json). Preserve it unchanged and extract a private working copy. Its software source revision is `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`; the qualification merge contains later receipts, not replacement binaries. Automatic GitHub source downloads omit the packaged dependency tar. Current main includes FDB 1.01 development and cannot be substituted while claiming exact release reconstruction.

From the extracted root, `source/BetterCPM/` is the software source tree. `source/dependencies/` contains the pinned offline cpmsim tar and instructions; `source/native-companions/` contains required host tool/source companions. Preserve `SOURCE-IDENTITY.json`, `SOURCE-FILES.json`, notices and internal checksums. Legacy `-candidate` roots/status fields are frozen build records; do not rename members or rewrite those records to make them appear current.

The independent cpmsim System download also has `host/BetterCPM/`, sufficient for the patched runtime, with its dependency tar under `dependencies/`. That kit does not replace the full Source tree for building all BetterCP/M components. Utilities downloads keep their own corresponding-source companions even when Source is available separately.

## Host prerequisites and runtime

Install Python 3, the expected Z80 cross assembler, cpmtools (`cpmcp`, `cpmls`, `fsck.cpm`), Git/tar/make and a C99 compiler. macOS runtime reconstruction uses Command Line Tools including codesign. Emulator execution needs the patched cpmsim runtime or trs80gp as appropriate; automated campaigns can also need Expect. Builders have specific local path defaults: use supported flags and record overrides rather than treating a maintainer path as an installed program.

From `source/BetterCPM/`, reconstruct ordinary cpmsim with a new output directory:

```sh
python3 tools/build_qualified_cpmsim.py \
  --source ../dependencies/z80pack-cpmsim-91fd28eb04e675c2127df88ed3f40675e15282e2.tar \
  --output build/cpmsim-runtime --profile runtime
```

From the independent System host kit, use `dependencies/` instead of `../dependencies/`. Keep `environment.json`, helper binaries and the build logs. The runtime executable is `build/cpmsim-runtime/z80pack/cpmsim/cpmsim`; its `srctools/` must be on PATH when using the guest host-transfer helpers. Stock upstream cpmsim is insufficient. Use the exact ordered patch/input lock; runtime and qualification profiles differ. Do not set ROM instrumentation for ordinary RAM operation. [Full installation/runtime procedure](platform/CPMSIM-INSTALLATION.md).

Host/compiler differences can change emulator executable bytes. Record what was built and tested; a successful compilation is not a new execution qualification result. The frozen offline reconstruction receipts apply to their recorded inputs, not arbitrary moving dependencies.

## Rebuild system and utility artifacts coherently

| Purpose | Entry point from the matching source root | Scope |
| --- | --- | --- |
| Rebuild layout-dependent components | `python3 tools/build_complete_system.py` | Builds the coherent resident/CCP/extensions/utilities/System package path in its implemented order. Not a general target selector. |
| Construct selected cpmsim System media | `python3 tools/build_distribution.py --target z80pack` | Selected System files and platform validation, not the entire six-download release. |
| Construct selected Model 4 System media | `python3 tools/build_distribution.py --target trs80gp` | Matching boot/BIOS, selected filesystem and validation. |
| Build selected utilities | `python3 tools/build_utilities.py` | Component build products; primary/companion image and source-kit recipes have their own recorded packaging inputs. |
| Create native kit/archive volumes | `python3 tools/build_source_disk.py` | Coherent symbols, tools and source mapping, with complete source on separate volumes. |
| Compose SYSTEM.SYS | `python3 tools/build_system_package.py` | Versioned metadata plus 20 KiB payload; installation is separate. |

Do not infer distribution membership by scanning a development disk or `build/`. Selected contents are in the locked image inventories. [System construction details](releases/DISTRIBUTION-BUILD.md) explain isolated snapshots, generated CONFIG fingerprints, outputs and receipt checks. Use `--work`/`--output` only as implemented by that builder; require a fresh work area after changed inputs or failed/incomplete preparation.

To construct Utilities primary and companion media with their source companions, the matching source tree provides:

```sh
python3 tools/build_utilities_disk.py --artifacts . --output build/utilities-disks --build
```

Use a fresh output directory. This produces provisional image reports and a host package, not replacement release downloads. Acceptance options such as `--ddt-acceptance` and `--toolchain-acceptance` bind matching receipts to exact output hashes; use the recorded commands and evidence in the Source/native companion material to reproduce a qualified selection. Do not reuse receipts against changed images. `build_utilities.py` alone is not a promise that every downloadable ZIP was rebuilt. Preserve ZSM4, TED and DASM complete companions, LINK permission/provenance, and any included CP/M Tools source mapping. Never invoke the old six-candidate assembler to replace locked packages during documentation reconciliation.

Keep the original artifacts separate from reconstruction outputs. Compare all eight images, guest utilities, runtime inputs and any ROM/overlay artifacts against their intended receipts before claiming exact reconstruction. A native/cross byte comparison and a boot test prove different properties. No reconstructed output replaces a locked download automatically.

## Native application and system builds

For ordinary applications, follow the [Programmer's Guide](manuals/Programmers-Guide.md) and native [ZSM4/LINK reference](manuals/Command-and-Utilities-Reference.md#zsm4). For the coherent native OS workflow, from the source root use:

```sh
bash tools/start_native_build.sh --prepare-only /path/to/new-native-session
```

The output must be new. Preparation creates A System, B native kit, C System-format work/installation target and D spare DATA. Launch with the matching platform procedure or omit `--prepare-only` using a configured `TRS80GP` executable. The preparation output states the actual directory and workflow. In guest user zero:

```text
B:
SUBMIT BUILD
B:SYSGEN C:SYSTEM.SYS C:
```

Wait for successful SYSTEM.SYS composition/readback before SYSGEN; the build selects C. Keep writable A0 for the authoritative batch queue. Do not format C between building and installation. Cold boot the installed target and verify files/configuration. Coherent generated link definitions prevent mixing addresses from different builds. Older `SUBMIT B:BUILD` descriptions in historical references do not replace this supplied complete preparation path.

## Documentation has a separate build

The frozen Source ZIP cannot contain newly written manuals/tools. Obtain the reviewed documentation revision separately; record it alongside the locked software revision. The documentation-only builder and split-provenance checker are part of this documentation workstream, not new requirements for rebuilding the frozen software. [Publication procedure](releases/DOCUMENTATION-PUBLICATION.md).

Use current Markdown/text originals. Older rendered User/Architecture PDF/DOCX files are withheld, and a developer's printed/exported copy is not an automatically qualified publication. No step here authorizes rebuilding the five archives, changing their embedded instructions, altering software versions, tagging or publishing a release.

## Reconstruction record

Keep source/package/checksum identities, actual tool versions and hashes, patch/input locks, commands, work-directory choices, generated maps, file/image comparisons and execution scope. Preserve failed outputs for diagnosis without falling back to old binaries. Further new-target development belongs to the [Porting Guide](manuals/Practical-Porting-Guide.md) and has its own qualification; it does not expand the locked 1.0 platform list.
