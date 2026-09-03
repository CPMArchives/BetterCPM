# BetterCP/M Utility Compatibility Ledger

Status: Verified baseline inventory
Baseline: Standard CP/M 2.2 command environment and distribution utilities

## Purpose

This ledger prevents an incomplete or merely similar replacement from being
reported as a compatible BetterCP/M utility. For every standard command or
program it records the compatibility baseline, planned extensions, current
implementation state, and evidence required for completion.

The inventory is a living engineering document. `Implemented` means code
exists; it does not mean baseline compatibility is complete. `Conformant`
requires the applicable behavior to be specified and tested against reference
CP/M behavior.

## Canonical CP/M 2.2 distribution inventory

The stock executable baseline contains eleven transient programs:

```text
ASM.COM     DDT.COM     DUMP.COM    ED.COM      LOAD.COM
MOVCPM.COM  PIP.COM     STAT.COM    SUBMIT.COM  SYSGEN.COM
XSUB.COM
```

The Digital Research manual's transient-command summary directly describes
`STAT`, `ASM`, `LOAD`, `DDT`, `PIP`, `ED`, `SYSGEN`, `SUBMIT`, `DUMP`, and
`MOVCPM`. `XSUB.COM` is the distributed companion that lets a submitted job
supply console input to another transient program. The distinction matters:
XSUB is part of the distribution baseline even though it is installed by a
SUBMIT workflow rather than used like an ordinary interactive utility.

The stock disk can also contain source and integration material such as
`BIOS.ASM`, `CBIOS.ASM`, `DEBLOCK.ASM`, `DISKDEF.LIB`, and `DUMP.ASM`. These
are distribution artifacts, not additional standard transient commands.

`MOVCPM.COM` and `SYSGEN.COM` are stock executables but installation-dependent:
their exact binaries and low-level effects depend on the target system. They
therefore have BetterCP/M workflow-equivalence requirements rather than a
requirement to reproduce DRI's private relocatable system image.

## Common requirements

Every replacement shall:

- be freely redistributable with BetterCP/M;
- accept the ordinary CP/M syntax and defaults of its counterpart;
- preserve required file effects, interaction, termination, and error paths;
- run under native BetterCP/M and be buildable under native CP/M where
  practical;
- support ordinary drive-qualified names without changing their meaning;
- use the common BetterCP/M parser/resolver for numeric and named DU extensions
  when that service is defined; and
- have focused regression tests plus physical or reference-system comparison
  where behavior cannot be established by unit tests alone.

Planned common filename forms are:

```text
FILE.COM
B:FILE.COM
5:FILE.COM
B5:FILE.COM
WORK:FILE.COM
```

`WORK:` is illustrative named-DU syntax. Its namespace, ambiguity rules, and
central resolution service remain to be specified; individual utilities shall
not introduce private interpretations meanwhile.

## Resident and command-environment baseline

| CP/M command | Minimum compatible behavior | BetterCP/M placement | Extensions | Status | Required evidence |
|---|---|---|---|---|---|
| `DIR` | Default/current DU listing, drive qualification, wildcard selection, DIR/SYS filtering, one display per file, CP/M four-column presentation | `BASIC.CPX` plus matching `DIR.COM` fallback | Numeric DU implemented; named DU and optional richer listings planned | Resident and transient implementations complete | Physical resident/transient parity and selection tests; named DU awaits the common resolver |
| `ERA` | Exact/wildcard deletion, all-wildcard confirmation, CP/M-compatible cancellation and `NO FILE` behavior | `BASIC.CPX`, with `ERA.COM` transient fallback | Numeric DU implemented; named DU planned | Baseline implementation complete | Physical exact/multi-extent/drive/fallback tests and BDOS wildcard/read-only tests; named DU awaits the common resolver |
| `REN` | `NEW=OLD` and historical left-arrow syntax, exact-only names, same-drive enforcement, `FILE EXISTS`/`NO FILE` behavior | `BASIC.CPX`, with `REN.COM` transient fallback | Numeric DU implemented; named DU planned | Baseline implementation complete | Physical syntax/exact/drive/fallback tests and BDOS multi-extent/read-only tests; named DU awaits the common resolver |
| `TYPE` | Literal sequential text display through CP/M EOF, exact-name validation, compatible errors, Ctrl-S pause and Ctrl-C abort | `BASIC.CPX`, with `TYPE.COM` transient fallback | Numeric DU and `/P` paging implemented; named DU planned | Baseline implementation complete | Physical literal/EOF/error/DU/paging/fallback tests and cooked-console control tests; named DU awaits the common resolver |
| `SAVE` | Save 0..255 256-byte TPA pages from 0100H to an exact 8.3 file; replace an existing destination; reject wildcards; report storage exhaustion | `BASIC.CPX`; no transient fallback is possible because loading one would overwrite the TPA being saved | DU target is supported; explicit address ranges may be added | Implemented | Automated page-count, zero-page, replacement, drive, syntax, and full-directory error tests; allocation-full awaits DPB correction |
| `USER` | Select and report CP/M user areas according to compatible syntax | `BASIC.CPX` plus matching `USER.COM` fallback; transitional core-CCP copy remains temporarily | Direct `5:` navigation and named DU make it optional interactively but do not remove the compatibility requirement | CPX and transient implementations complete | Physical CPX/transient state-change tests and existing DIRTEST user-area suite |
| `CLR` | No stock CP/M counterpart | `BASIC.CPX` plus matching `CLR.COM` fallback | Clear the configured console and home its cursor | Resident and transient extension implementations complete | Physical CPX/transient clear-and-prompt tests; portable terminal-capability service remains future work |
| `VER` | No stock CP/M counterpart | `BASIC.CPX` plus matching `VER.COM` fallback | Report BetterCP/M version and eventually its platform and interface versions | CPX and transient implementations complete; core copy remains temporarily | Physical CPX/transient parity and recovery-path tests |
| `WARM` | No stock CP/M counterpart; `Ctrl-C` is the canonical interactive warm boot | Transient-only `WARM.COM` | Scriptable explicit warm boot | Transient implementation complete; core copy remains temporarily | Native/cross parity and physical Function 0/WBOOT reconstruction test |

The minimal CCP itself remains command-processing machinery. `BASIC.CPX`
contains the complete stock resident-command set—`DIR`, `ERA`, `REN`, `SAVE`,
`TYPE`, and `USER`—plus the BetterCP/M `CLR` and `VER` extensions. Matching
transient fallbacks are required for all eight commands except `SAVE`; loading
`SAVE.COM` at `0100h` would destroy the TPA
contents it is meant to preserve. A transient fallback must match its CPX
counterpart and shall not acquire a divergent, transient-only feature set.
Commands migrate out of the core CCP only after their CPX implementations and
applicable transient fallbacks are verified.

## Standard transient utility baseline

| CP/M utility | Minimum compatible behavior | BetterCP/M replacement | Planned extensions | Status | Required evidence |
|---|---|---|---|---|---|
| `PIP.COM` | Copy/concatenate files and devices; standard options, verification, text/binary and wildcard behavior | New implementation | Numeric/named DU, clearer diagnostics, additional devices | Not started | Reference option matrix; data/device/error comparison |
| `STAT.COM` | Disk/file/device status, attributes, assignments, and standard operands | New implementation | Named DU, capacity detail, BetterCP/M configuration reports | Not started | Reference output semantics and mutation tests |
| `ED.COM` | Compatible command-mode text editing, buffers, file lifecycle, and recovery files | New implementation | Optional modern interactive mode without changing baseline mode | Not started | Scripted reference sessions and failure/recovery tests |
| `ASM.COM` | CP/M assembler source syntax, symbols, pseudo-operations, outputs, and diagnostics | New implementation or qualified redistributable implementation | Z80 mode may be explicit; ZSM4 remains the system-source assembler | Not started | Corpus comparison of HEX/PRN/symbol/error output |
| `LOAD.COM` | Convert compatible Intel HEX input to `.COM` with standard validation and messages | New implementation | Extended-address diagnostics where harmless | Not started | Valid, sparse, malformed, checksum, and size cases |
| `DDT.COM` | Load, inspect, modify, trace, breakpoint, assemble/disassemble, and save workflows | New implementation | Z80 registers/opcodes and BetterCP/M symbols | Not started | Scripted debugger sessions on reference fixtures |
| `DUMP.COM` | Conventional hexadecimal file display and EOF behavior | New implementation | DU operands, ranges, ASCII column options | Not started | Byte-for-byte/reference presentation fixtures |
| `SUBMIT.COM` | Positional substitution, command-file generation/execution order, quoting, and errors | New implementation | Numeric/named DU | Not started | Reference substitution and nested/error workflow tests |
| `XSUB.COM` | Feed submitted input to programs using compatible console-buffer conventions | New implementation, possibly coordinated with an extension | Integrate with future extended-submit CPX | Not started | Interactive-input capture and chained SUBMIT tests |

## System-construction and platform utilities

| CP/M utility/workflow | Compatibility purpose | BetterCP/M treatment | Status | Required evidence |
|---|---|---|---|---|
| `MOVCPM.COM` | Configure a CP/M system for a memory size and relocate its resident image | BetterCP/M configuration/build replacement; literal DRI image relocation is not portable | Not started | Equivalent supported-memory configuration and boot tests |
| `SYSGEN.COM` | Transfer or install the bootable system image | Platform-aware BetterCP/M system installer | Not started | Reproducible install/readback/boot tests per platform |
| Vendor `FORMAT` tools | Prepare physical media for a selected geometry | BetterCP/M format utility using platform drive descriptors | Not started | Geometry, skew, verify, bad/error, and cross-tool image tests |
| Montezuma `CONFIG` workflow | Select and edit drive formats and system defaults | BetterCP/M `CONFIG`, including preset and field-level editing | Designed, not implemented | Saved/default profile, validation, cpmtools conversion, and reboot tests |

`MOVCPM` and `SYSGEN` replacements preserve user-visible goals and workflows;
they need not reproduce private patching of Digital Research binaries.

## BetterCP/M additions—not baseline substitutes

`CPX.COM`, `RSX.COM`, future extended-submit CPXs, named-DU management, and
platform configuration tools extend the distribution. Their presence does not
remove any baseline replacement obligation above unless the compatible command
is available through both the default command environment and a transient
fallback.

## Vendor/OEM utilities—not universal CP/M 2.2 requirements

OEM disks commonly bundle utilities whose behavior belongs to their hardware,
enhanced command environment, or the wider CP/M community. The Montezuma Micro
Model 4 disk, for example, includes `CONFIG.COM`, `DUP.COM`, `MDIR.COM`,
`EXBIOS.COM`, `KEYDEF.COM`, and modem/support programs in addition to the DRI
baseline; inclusion does not imply Montezuma Micro authorship. Archived MDIR
2.1 source identifies that line as the community-developed **CP/M-2 Master Disk
Directory**, originally by Jeff Hammersley and derived from earlier community
work. The version of `MDIR.COM` bundled by Montezuma Micro remains to be matched
against that source lineage.

BetterCP/M may recreate or redistribute useful examples—especially CONFIG,
DUP, and MDIR—but they are tracked as platform or distribution features, not
mislabeled as stock CP/M requirements or automatically attributed to the disk
vendor.

## Completion rule

A ledger row may advance to `Conformant` only when:

1. its behavioral baseline is cited or captured in an engineering
   specification;
2. ordinary CP/M syntax has executable coverage;
3. BetterCP/M extensions have separate coverage and do not alter baseline
   syntax;
4. native and cross builds meet the project's parity rule where applicable;
5. required physical/reference comparison has been recorded; and
6. known deviations are explicit rather than hidden by the utility name.
