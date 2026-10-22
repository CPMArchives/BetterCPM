# BetterCP/M DDT adaptation qualification

22 October 2026. DDT 1.0 (Build 001).

The initial adaptation passes source transcription, native assembly, relocation, compiled input and BetterCP/M debugger tests. The remaining Model 4 display/input campaign now passes; see [Model 4 qualification](DDT%20Model%204%20Qualification.md). Whole Utilities release acceptance remains separate.

## Artifact and compatibility boundary

`build/utilities/DDT.COM` is 6528 bytes, SHA-256 `4b72c62b846dc3aaff673bf6b2fa3569c8fdc9887ca7927b3bf6ce3c357b6e46`. Its 5028-byte payload reserves 20 pages (5120 bytes), compared with the historical 16 pages. Startup begins at 0100H; the packaged payload and startup stack begin at 0400H. The bootstrap is 386 bytes. The 629-byte relocation bitmap contains 862 marks and reproduces independent payload builds at 0100H and 3100H from the zero-origin build.

The original assembler/disassembler and monitor comprise 4028 bytes. The only changed bytes within that core are the 15-byte GETBUFF hook, replaced by a jump and explicit zero padding. The additional 1000 payload bytes comprise 68 bytes of alignment, 291 bytes of adapter code, 264 bytes of caller state/private stack, and 377 bytes of shared input engine. The original parser, 8080 assembler/disassembler, command dispatch and execution machinery remain intact. No Z80 debugger language extensions were added.

The immutable 4864-byte historical reference and exact reproduction retain SHA-256 `d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf`. Historical builders, inputs and evidence are separate from the adaptation. See [historical specification](DDT%20Historical%20Reproduction%20Specification.md) and [reproduction qualification](DDT%20Reproduction%20Qualification.md).

## Verification

- `python3 tools/build_ddt.py`: original Intel source versus translated Z80 source parity for all three modules, deterministic storage, independent origins, relocation bitmap and packaging. The reference is comparison-only.
- `python3 tools/build_native_ddt.py`: native ZSM4/LINK matches all three cross-built payload origins and bootstrap. Native assembly uses CSEG with `.PHASE` and LINK `[A]`; an absolute segment alone does not produce the required linked image.
- `python3 tools/test_ddt.py`: seven version/invalid-version cases preserve page zero; combined unmodified core equals separately assembled originals; changes within the core stay within GETBUFF; reference hash remains exact.
- `python3 tools/test_ddt_input.py`: 17 compiled input cases and 100 repeated entries, hostile BDOS register clobbers, private stack canaries, buffer bounds, insertion/deletion, word movement, clear aliases, empty submission, ignored TAB, prefix/cursor rendering, ESC, Ctrl-C and retained queued input.
- `python3 tools/test_ddt_live.py --baseline IMAGE`: 56 BetterCP/M interactions on disposable cpmsim media cover identity, edited arithmetic, F/D/M, A/L, S/X, empty and queued assembly input, cancelled substitution, COM/HEX loading, G breakpoint/restoration, T/U, G0 and Ctrl-C. Disk readback and consistency checks pass. A stock CP/M conversational smoke suite also passes.

The input binding uses the existing shared event engine and WordStar profile without modifying either. DDT owns its 24-cell viewport, 32-byte command buffer, private 256-byte editor stack, submission and cancellation policy. ESC abandons only provisional input and returns to the command prompt; previously accepted changes remain. Ctrl-U/X/Y clear the provisional line. Unassigned controls, including TAB, are ignored. Debugger output retains its original cooked console path.

BetterCP/M's coherent pending-input handling is required for the queued multi-line assembly test. Stock CP/M's cooked output and direct-input pending caches can lose the first queued character; stock validation therefore covers conversational input, not that queued case. This adaptation does not change historical debugger output to work around stock BDOS behavior.

## Initial Model 4 limitation (resolved)

The Model 4 test and an independent boot-only control both produced blank screen captures. The control could not establish a working display, so this is inconclusive rather than a DDT pass or a diagnosed DDT failure. The test harness uses disposable copies; the retained baseline was restored and its original SHA-256 verified after a control wrote startup queue state. The corrected campaign rebuilds current system components, uses a working disposable boot fixture and asserts settled VRAM captures. It passes physical keyboard editing, scrolling, cancellation, assembly/disassembly and warm boot. No DDT binary change was required; the new Model 4 qualification record supersedes this initial inconclusive result.

Build and test reports, native logs and debugger transcripts are retained in the adaptation evidence archive. The scripts provide repeatable checks; platform paths are command-line parameters where applicable. Utilities disk packaging may be used for development, with whole Utilities release status retained in release documentation.

## Integration checks

Both development Utilities images pass file readback and filesystem consistency checks; the Model 4 DMK also passes raw/DMK round-trip verification. They remain provisional. A fresh installed build retains the same artifact hash. Exact historical reproduction was rebuilt independently with zero differing bytes.

The repository-wide `test_utility_versions.py` did not complete against the existing build directory: unrelated STAT/CONFIG/DUP/TYPE artifacts reached the execution limit, DIR encountered an unsupported opcode, and the PIP development artifact was absent. These are not a passing global regression result. DDT's seven isolated identity/purity cases pass against its freshly built artifact.

A complete current-system rebuild also resolves the stale/missing-artifact version-suite limitation above: all 178 utility identity, resident dispatch, invalid usage and fall-through checks now pass. Earlier evidence archives remain unchanged as records of their original runs.
