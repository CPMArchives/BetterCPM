# BetterCP/M Utility Compatibility Ledger

Status: Initial inventory  
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
| `DIR` | Default/current DU listing, drive qualification, wildcard selection, DIR/SYS filtering, one display per file, CP/M four-column presentation | `BASIC.CPX`, with transient fallback planned | Numeric DU implemented; named DU and optional richer listings planned | Resident implementation complete | Transient fallback remains a separate distribution task; named DU awaits the common resolver |
| `ERA` | Exact/wildcard deletion, `*.*` safety behavior, CP/M-compatible errors | `BASIC.CPX`; `ERA.COM` exists | Numeric and named DU | Implemented, partial compatibility | Reference deletion/error matrix and protected-media tests |
| `REN` | CP/M old/new syntax, exact rename semantics and errors | `BASIC.CPX` | Numeric and named DU | Implemented, partial compatibility | Reference syntax matrix, duplicate/missing/protected cases |
| `TYPE` | Sequential text display through CP/M EOF with compatible missing-file behavior | `BASIC.CPX` | Numeric and named DU; optional paging | Implemented, partial compatibility | Text, EOF, empty, missing, control-byte, and DU cases |
| `SAVE` | Save the requested TPA pages to an 8.3 file with compatible validation | `BASIC.CPX` or transient fallback | DU target and explicit ranges may be added | Planned | Reference page-count, overwrite, range, and disk-error tests |
| `USER` | Select and report CP/M user areas according to compatible syntax | Transitional core CCP; future command policy pending | Direct `5:` navigation and named DU make it optional interactively | Implemented, transitional | Existing DIRTEST user-area suite plus command syntax tests |

The minimal CCP itself remains command-processing machinery. Commands migrate
to CPXs only after their CPX implementations and transient fallbacks are
verified.

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
