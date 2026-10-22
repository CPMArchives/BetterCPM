# CP/M 2.2 DDT.COM Reproduction Engineering Specification

22 October 2026. Reproduction baseline.

Implementation evidence: [DDT Reproduction Qualification](DDT%20Reproduction%20Qualification.md). The reproduction gate now passes complete byte identity. All reserved bytes are regenerated from independently archived PIP source and a reconstructed memory state; see the qualification report for provenance and historical limits.

The sole objective is to recreate, from the supplied Digital Research sources, the DDT.COM supplied in `sources/cpm2-plm(1).zip`. Acceptance requires the same complete file bytes and the same observed behavior under the same CP/M 2.2 environment. Preserve existing commands, messages, limitations, quirks, and errors. No enhancements, corrections, refactoring, Z80 extensions, BetterCPM integration, or interface changes belong in this effort.

A reference binary is present. The source identifies version 2.2, and the binary contains `DDT VERS 2.2`. This establishes a concrete reproduction target; it does not independently establish the archive's historical provenance or prove that the sources already reproduce it. The qualification report establishes full-file byte identity and bounded runtime smoke parity; it does not claim exhaustive behavioral test coverage or recovery of the original operator command sequence.

## Authoritative inputs

Authority here means the selected inputs for this reproduction, subject to proving their correspondence to the reference binary.

| Archive member in cpm2-plm(1).zip | Role and evidence |
| --- | --- |
| `cpm2-plm/DDT0MOV.ASM` | Startup relocator, `VERSION EQU 22`, `ORG 100H`. Copies the module from 0200H, applies its bitmap, and transfers control. Its initial LXI B operand is explicitly reserved for the module builder to fill. |
| `cpm2-plm/DDT1ASM.ASM` | 8080 assembler/disassembler. Default `DEBUG=FALSE`, `RELOC=TRUE`, origin 0000H. Monitor interface is fixed at module base plus 0680H. |
| `cpm2-plm/DDT2MON.ASM` | Monitor, headed CP/M DEBUGGER VERSION 2.2 and dated 1/80. Default `DEBUG=FALSE`, `RELOC=TRUE`. Reserves 0680H for the assembler/disassembler before emitting monitor code. |
| `cpm2-plm/DDT.COM` | Immutable comparison target for the entire distributed file. |
| `cpm2-plm/ASM.COM`, `MAC.COM`, `LOAD.COM` | Available historical tool candidates. Their presence does not prove which commands originally built DDT. |

There are no INCLUDE or MACLIB dependencies in the three DDT modules. Each module ends separately with END. They must be assembled with their intended address spaces and combined; simple textual concatenation is not a supported recipe. Preserve raw source bytes, including CRLF and trailing NUL padding, in evidence. Any assembler input sanitation must be confined to derived copies and recorded.

`README.TXT` describes a BDOS variant in the archive, not a DDT build procedure. `LOAD.PLM` and the PL/M utility sources are not DDT source dependencies. Rebuilding CP/M or BIOS is outside scope. Compiling the independently archived older PIP source is required solely to recreate the memory underlying DDT reserved storage; it adds no DDT runtime dependency.

The other uploaded archives were inventoried. `mmcpm232.zip` contains Montezuma system and transfer sources, with no DDT module or DDT binary. `Digital Research CP_M Operating System Manual.zip` contains appendix assembly files and HTML files; sampled chapter HTML contains a web challenge rather than the manual text. Neither archive supersedes the three DDT modules.

The scanned `sources/DDT.pdf` supplies behavioral context. Its printed pages 1–2 describe startup, relocation below BDOS, the prompt, command entry, and exit. Its table of contents identifies command descriptions and implementation notes. It is an older guide: its sign-on example differs from this source and binary. Use the supplied 2.2 binary and sources to resolve version-specific differences. The guide's handwritten examples are supporting material, not byte-level authority.

## Reference binary measurements

All offsets below are zero-based file offsets, distinguished from CP/M memory addresses.

| Property | Observed value |
| --- | --- |
| File length | 4864 bytes, 1300H, 38 CP/M records of 128 bytes |
| SHA-256 | `d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf` |
| Initial bytes | `01 BC 0F C3 3D 01` — LXI B,0FBCH; JMP 013DH |
| Startup area | File 0000H–00FFH; loaded at 0100H–01FFH |
| Payload length from initial operand | 0FBCH, 4028 bytes |
| Payload | File 0100H–10BBH; initially loaded at 0200H |
| Relocation bitmap | File 10BCH–12B3H; ceil(4028/8) = 504 bytes |
| Remaining file bytes | File 12B4H–12FFH; 76 bytes, all zero |

The payload starts `C3 83 06 00 00 00 C3 4F 03 C3 24 05`. At payload offset 0680H the monitor starts `C3 A2 06 C3 AA 06`, consistent with the source's entry arrangement. These checks support the proposed layout but do not replace a full assembled comparison. The retained storage is now reproduced from compiler-initialized PIP code using the memory model below. The final alignment matches the original. The precise original operator sequence remains unproven.

## Load and runtime assumptions

The COM file loads and starts at 0100H in an 8080-compatible CP/M 2.2 environment. The startup stack is set to 0200H; the first payload byte is also initially at 0200H. Keep these arrangements unchanged.

The relocatable payload is assembled relative to 0000H. The assembler/disassembler occupies the region before monitor offset 0680H; the monitor's leading DS reserves that region rather than supplying a second copy of it. Merge by addresses and preserve the assembler/disassembler bytes. Establish from listings whether any gap before 0680H requires filling.

DDT0MOV reads the high byte of the existing BDOS jump destination at 0007H. Its relocation base high byte is `(memory[0007H] - 1 - HIGH(payload_length)) mod 256`; its low byte is zero. With payload length 0FBCH, this subtracts 10H pages from the BDOS entry high byte. Do not substitute a modern TPA allocation rule or hard-code a 64K destination.

The relocator copies exactly 0FBCH bytes. The following bitmap supplies one bit per payload byte, most significant bit first. A set bit causes the relocation base high byte to be added to that byte. Generate this map from source relocation information or independently validated assembly comparisons; do not infer relocation merely by scanning for values resembling addresses.

The monitor preserves the original BDOS destination and changes the JMP operand at 0006H–0007H to enter DDT. It installs a JMP at RST 7, 0038H, and uses FFH restart instructions for breakpoints with DEBUG false. Its default debuggee PC and SP are 0100H; the default FCB is at 005CH and disk buffer at 0080H. Runtime verification must include these low-memory effects, BDOS forwarding, and warm boot. The monitor can cease exposing the assembler/disassembler after that region is overwritten; preserve its existing detection and reduced-memory behavior.

## Build dependencies and proposed reconstruction

The required build capabilities are an Intel 8080 assembler accepting the source's Digital Research directives and expressions, an address-aware image merger, and a relocation bitmap and COM packaging step. Source syntax includes TITLE, conditional assembly, DS, NOT, MOD, shifts, and binary constants with embedded `$` separators. Validate the selected assembler against these constructs before trusting its output.

The archive supplies ASM.COM and MAC.COM; test them as historical candidates under an isolated CP/M emulator. LOAD.COM can convert an appropriate absolute HEX image, but its presence does not establish that it creates the DDT bitmap or complete package. LINK.COM is also present, but no DDT link control file or relocatable-object recipe was found. PL/M is unnecessary for DDT assembly itself; ISIS-II PL/M-80 V3.1, LINK V3.0 and LOCATE V3.0 are retained as build dependencies for the older PIP seed image. Emulator choice affects test reproducibility and must be recorded, not built into DDT.

The following sequence is an engineering reconstruction to prove, not a recovered original command script:

1. Freeze archive and member hashes, assembler binaries, emulator version, CP/M image, memory layout, and input-file transformations. Work outside `sources/`.
2. Assemble DDT0MOV at 0100H, retaining a listing and error log. Keep the reserved module-length operand separate from assembler-generated code.
3. Assemble DDT1ASM and DDT2MON with their supplied production settings. Merge their emitted ranges into one zero-origin payload, retaining a symbol map and checking overlap and reserved ranges. Confirm the monitor starts at 0680H and determine the exact end and initialization of every DS region.
4. Reconstruct the relocation map. One candidate is a second assembly with both payload module bases shifted by 0100H while fixed CP/M addresses remain fixed. Compare against the zero-origin build: each relocatable high byte should change by one modulo 256. Validate every resulting mark against listings, expressions, and the reference map. The shipped RELOC=FALSE branch selects D000H and is not, by itself, the proposed +0100H build. Make any origin substitutions only in generated build copies.
5. Independently compile `third_party/dri-ddt/reproduction/PIP20.PLM` with the retained historical compiler. Link its BDOS interface and runtime; locate code at 0100H with a 64-byte stack. Load this generated PIP image at 0100H in the reconstruction memory. Overlay only the source-emitted DDT bytes into a work area at 0800H. A DDT reserved file offset f then retains PIP file offset f+0700H. Assert every retained byte is covered by a compiler CODE record.
6. Package the relocator into the first 100H file bytes, put the payload at file offset 100H, patch the startup length to 0FBCH only if the assembled extent proves that length, append the bitmap, and reproduce all gaps and the final padding. Derive executable bytes from source; never copy unexplained mismatches from the reference to make a comparison pass.
7. Repeat the build from frozen inputs in a clean directory. Require identical results before behavioral qualification.

The uploaded archives do not supply a DDT recipe. Additional archived build media provide a MAC/GENMOD/GENHEX/PRLCOM script, and the current drivers prove a source-derived reconstruction of the complete target. The memory model explains all storage bytes but is not proof of the original DRI chronological command sequence. A modern host packaging tool is acceptable only when its complete output is proven identical; changes to the DDT program are not an acceptable workaround.

## Byte verification plan

Compare the rebuilt file to the frozen reference by length, SHA-256, and full byte comparison. Acceptance is zero differing bytes across all 4864 bytes. Keep an offset-by-offset report even when hashes match, and record both tool and input hashes.

For a mismatch, report its file offset, corresponding initial load address where applicable, expected and actual bytes, payload-relative location, source symbol or listing line, and classification: relocator, initialized payload, reserved storage, bitmap, or padding. Diagnose assembler semantics, merge rules, origins, DS initialization, and packaging before suspecting source revision. A matching executable core with differing padding is still not full reproduction.

Independently simulate relocation at several valid CP/M BDOS placements and compare the resulting relocated memory images. Include bitmap bit order, last partial bitmap byte, entry transfer, original BDOS forwarding target, and the altered page-zero vectors. This checks the reconstruction of the file format separately from interactive tests.

## Behavior verification plan

Run original and rebuilt DDT in separate restores of the same CP/M 2.2 machine snapshot, using identical disks, RAM contents, console input, and CPU configuration. Capture raw console bytes, relevant memory snapshots, registers at agreed stops, and disk changes. Avoid timestamp or terminal transformations that could conceal differences. Repeat relocation tests with more than one valid memory size. Tests involving arbitrary memory use controlled fixtures, so results do not depend on residual RAM.

| Area | Differential coverage |
| --- | --- |
| Startup and exit | Bare DDT, automatic COM and HEX loading, exact 2.2 sign-on and prompt, initial registers, BDOS vector, RST 7 vector, Ctrl-C and G0 warm boot |
| Memory and arithmetic | D default and explicit ranges, ASCII rendering and continuation; F inclusive bounds; M ordinary and overlapping ranges in both directions; S substitution and termination; H sum and difference, present in the 2.2 dispatch table |
| Assembly and listing | A and L with representative 8080 instruction classes, immediate and address operands, invalid mnemonics, default listing continuation, and behavior after assembler/disassembler overwrite |
| Execution control | G with zero, one and two breakpoints; original instruction restoration; T and U counts and interruption; branches, calls, returns, restart, PCHL, and BDOS calls; X register and flag examination/modification |
| File input | I and R, COM versus HEX, load bias, EOF and HEX checksums, missing files and malformed input, reported load boundaries, FCB and DMA effects |
| Input and errors | Empty input, legal separators, invalid commands and operands, 32-character buffer boundary, line editing and interruption under the same BDOS |

Use the manual's command sections and examples to select baseline cases, then take exact expected results from the supplied binary. Do not add missing commands or repair behavior because an older guide suggests a different result. Test fixtures and emulator instrumentation remain outside DDT.COM.

## Completion criteria and first implementation gate

The deliverables for reproduction are unchanged source evidence, a deterministic build recipe, tool and environment hashes, assembly listings and merged image map, the generated bitmap, rebuilt DDT.COM, full byte comparison, relocation checks, and differential behavior transcripts.

Reproduction is complete only when a clean rebuild matches the entire reference file and the defined behavior checks pass without unexplained differences. A behavior-compatible rewrite or a source build that merely starts successfully does not meet the objective.

Assembler compatibility, payload extent, bitmap identity, and full-file byte reproduction now pass. The original zero-filled candidate remains a negative control, with 231 differences. Keep complete byte parity as a build assertion and retain the source-derived PIP memory provenance. Further behavioral tests must remain within reproduction scope.

## Repository integration and input editing

Historical sources and tool binaries are retained unchanged under `third_party/dri-ddt/`, with member and archive hashes in `provenance.json`. The reproducible build driver is `tools/build_ddt_reproduction.py`; the residue and no-reference controls are `tools/test_ddt_residue.py`; the differential CP/M smoke test is `tools/test_ddt_reproduction.py`. The older PIP compiler helper is `tools/build_ddt_seed.py`. Qualification outputs stay under `build/ddt-reproduction/`; no candidate is installed into the Utilities Disk or production utility build.

The exact-reproduction image preserves DDT2MON's GETBUFF, which calls BDOS Function 10 through TRAPAD with a 32-character command buffer. Rubout and Ctrl-U editing are exercised in the differential smoke test. A linked replacement editor would change source-emitted bytes and cannot satisfy this gate.

After exact historical reproduction is completed and verified, the subsequent BetterCP/M adaptation shall reuse the shared library at `src/utilities/common/ui/` where its behavior fits. Consult [Shared Input Library](../programmers/Shared%20Input%20Library.md) and [Shared Input and UI Specification](Shared%20Input%20and%20UI%20Specification.md). Preserve DDT's debugger command language, operand parsing, and execution semantics. Select only the required library modules through `tools/shared_ui.py`, using the same expansion for native and cross builds. Keep state caller-owned and bind input/render hooks explicitly. The standard editor's ESC/Ctrl-C, DEL, and Enter policies differ from historical BDOS editing; qualify those adaptations explicitly rather than replacing GETBUFF mechanically. DUMP and CONFIG provide existing text-editor bindings; choice components apply only to prompts that actually need a choice. No shared-library code is linked into this historical binary.

The earlier project-local engineering draft and Gate1 evidence remain historical context. Repository copies of the extracted DDT modules and reference binary are exact archive members. The uploaded project `sources/` directory remains read-only.
