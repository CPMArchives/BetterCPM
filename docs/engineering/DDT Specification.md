# BetterCP/M DDT Engineering Specification

22 October 2026. Initial adaptation, version 1.0 Build 001.

BetterCP/M DDT retains the CP/M 2.2 DDT debugger command language and execution model, with BetterCP/M utility identification and shared-library line editing. This adaptation is a separate artifact from the exact historical reproduction.

The [historical reproduction specification](DDT%20Historical%20Reproduction%20Specification.md), [reproduction qualification](DDT%20Reproduction%20Qualification.md), reference inputs under `third_party/dri-ddt/`, reproduction tools and evidence bundles remain unchanged. The 4864-byte baseline must retain SHA-256 `d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf`. Adaptation outputs live under `build/ddt-development/` and `build/utilities/DDT.COM`.

## Debugger compatibility

Preserve commands A, D, F, G, H, I, L, M, R, S, T, U and X, their operand grammar, hexadecimal numeric interpretation, case folding, prompts for debugger data, error handling and command continuation. Preserve empty-line behavior and the dot terminator in assembly and substitution. Do not add Z80 instruction mnemonics to A/L or change the 8080 stepping model. New debugger commands, enhanced file selection, DU syntax, persistent history and full-screen debugging are outside this initial adaptation.

Keep the 0100H default debuggee PC/SP, default FCB and DMA conventions, RST 7 breakpoints, restoration of replaced instructions, BDOS forwarding, and G0/Ctrl-C warm boot. The assembler/disassembler remains the first 0680H of the relocatable payload, with its existing overwrite-detection behavior. The larger resident payload reduces available debuggee memory; calculate and report its actual size.

## Utility identity and startup

Add DDT 1.0 Build 001 to the utility identity table. Startup and an exact, case-insensitive `/VER` request use the repository's compact utility identification convention. Invalid combinations involving the exact `/VER` token use the existing shared version error. Process version queries before relocation, page-zero vector installation, file loading or debugger input. Other command tails retain the original startup file semantics.

The startup code may grow to a larger page-aligned area, but its module address and stack must agree with the package. The program still starts at 0100H and relocates its payload below the original BDOS gateway. Relocation is page based with one bitmap bit per byte; derive the bitmap from independent origin builds, and verify a distant alternate origin. Keep any new code and state out of the reclaimable assembler/disassembler region. Do not assume a fixed 64K placement.

## Shared input binding

Reuse `tools/shared_ui.input_source(standard=True, words=True)` from `src/utilities/common/ui/`. The event engine owns insertion, cursor movement, backspace/delete and optional word editing; DDT owns reading, rendering, command acceptance and debugger state. Do not copy another editor or alter the library's existing consumers.

All historical GETBUFF callers use the same binding: command prompt, assembler entry, memory substitution, and register replacement. Bind the counted edit buffer to the existing 32-byte COMBUF and publish its length through CURLEN. Empty Enter submits an empty line. Accepted printable bytes reach the original parser unchanged; GNC retains original case folding. Unassigned control keys follow the shared event profile and do not become command bytes; TAB is not silently converted to a different operand delimiter.

Retain Ctrl-C as a warm boot. Ctrl-U and Ctrl-X clear only the provisional line; Ctrl-Y uses the shared clear action. Ctrl-S/D move left/right, Ctrl-A/F move by words, Ctrl-H/DEL erase left, and Ctrl-G erases under the cursor. Enter submits. ESC discards the current provisional line and abandons the active interactive command to the main prompt; already accepted S/A changes are retained. ESC must not commit a partial operand or leave a saved register/address frame on the stack.

Use direct BDOS Function 6 for input and redraw so cooked output cannot consume editing keys as flow control. Forward through the saved underlying BDOS path after DDT has installed its gateway. Balance callback stacks and preserve the debugger's saved machine state. Give the editor a private, measured stack and restore the monitor's stack on submission; cancellation returns through the monitor's normal reset path.

The renderer starts at the existing input field position, preserving the printed '-' or address/register prefix. Use a bounded 24-cell field, horizontal scrolling, and backspace positioning; show an underscore caret at end of input. This fits a 40-column console with existing debugger prefixes and adds no SCRN or terminal escape dependency. Erase stale field cells on shrink/cancellation and leave the cursor at the logical insertion point. Normal debugger output retains its existing console path. Qualify the actual rendered field, not only buffer contents.

## Source and build structure

Adaptation code is maintained separately from the immutable DRI files. Translate 8080 mnemonics to byte-equivalent Z80 syntax using a syntax-aware transformation which preserves quoted strings and comments. Retain attribution and validate the unmodified translated core against historical source-emitted bytes before applying adaptation hooks. Keep the assembler/disassembler's private symbols distinct from monitor symbols when assembling a combined payload.

The only initial core hook is GETBUFF, which jumps to the shared input binding. Keep the fixed entry vector layout. Initialize newly owned state deterministically; historical PIP residue is not an adaptation build dependency. Generate the payload at multiple origins, include the editor and its state in the relocation extent, and package it with the adaptation startup. Require native ZSM4/LINK and cross-assembler byte parity for the adaptation.

Build `DDT.COM` as an owned utility and register it in the canonical utility builder. Utilities media may include the adaptation after qualification; never substitute the historical reference for the owned utility. Keep the historical builders, input hashes and exact evidence untouched.

## Acceptance

Before implementation, this specification defines the permitted changes. Qualification must establish:

- The historical reference, reproduction inputs and tools are unchanged, and exact historical reproduction still passes.
- The translated unmodified source emits the same initialized bytes as the original 8080 sources.
- Native/cross adaptation parity, deterministic clean builds and bitmap correctness at multiple origins.
- Version purity and identification; no debugger vectors or files changed by `/VER`.
- The same debugger results for ordinary command and error fixtures, including assembly/substitution/register input, COM/HEX loading, G breakpoints, T/U and G0.
- Editing behavior, 32-byte bounds, empty input, ESC/Ctrl-C, typeahead retention, prefix preservation, visible caret, and repeated entry without stack growth.
- Execution on a disposable BetterCP/M image, memory bounds and BDOS forwarding; record platform and coverage limits explicitly.

The initial adaptation may change identity, editing presentation and resident footprint. Any further semantic difference requires an explicit specification change and separate qualification.

## Implemented qualification

See [adaptation qualification](DDT%20Adaptation%20Qualification.md) for the measured footprint, build/test commands and completed Model 4 display qualification. The initial implementation is 6528 bytes and reserves 20 resident pages.

## Model 4 qualification closure

Qualify the existing adaptation on a disposable, freshly constructed Model 4 system disk built with `tools/build_complete_system.py`, after a boot-only control reaches the CCP prompt. An older retained release disk that produces a blank control screen is not a valid DDT fixture. The harness must preserve the supplied source image, record its hash and the private test image, and check actual VRAM captures for editing, cancellation, debugger results and warm-boot return. No debugger or shared-input behavior changes are authorized by a fixture repair. Keep the historical reproduction and adaptation artifact hashes unchanged.

## Utilities Disk release acceptance

Accept DDT as a component of the existing provisional Utilities Disk; unrelated pending members do not become accepted or selected. Rebuild current system and Utilities artifacts, verify the packaged DDT hash on both raw cpmsim and native Model 4 data media, then mount only disposable System A: and Utilities B: copies. Launch `B:DDT` from A:, test the unchanged command language and shared editing, load a controlled debuggee from the caller's drive, and return through G0 and Ctrl-C/BREAK. Exercise Model 4's normal loaded monitor configuration as well as its real keyboard/display. Confirm command search/drive restoration, byte-identical source media, unchanged Utilities media and debuggee, and filesystem integrity after execution. Record the component verdict separately from whole-disk provisional status. Preserve both qualified DDT binary hashes and all historical reproduction inputs.

See [Utilities release acceptance](DDT%20Utilities%20Release%20Acceptance.md) for the component verdict, image-bound receipts and remaining whole-disk scope.
