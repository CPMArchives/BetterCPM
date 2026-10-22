# DDT Reproduction Qualification

22 October 2026. **Exact reproduction passes.** The source build reproduces every byte of the supplied 4864-byte CP/M 2.2 DDT.COM, including the 231 bytes which differed in the earlier zero-filled build. The result is generated from the DDT assembly sources and an independently compiled CP/M 2.0 PIP memory image. No bytes are taken from the comparison DDT.COM to fill storage.

| Measurement | Result |
| --- | --- |
| Complete file size | 4864 bytes, 1300H |
| Reference and rebuilt SHA-256 | `d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf` |
| Differing bytes | 0 |
| DDT payload | 4028 bytes; 3900 emitted by source, 128 reserved |
| Relocation bitmap | 504 identical bytes; 765 marks |
| Source-uninitialized file bytes explained | All 245, including 117 startup-page bytes |
| Build with comparison file absent | Produces the same complete candidate before comparison raises FileNotFoundError |
| Independent clean rebuild | Same PIP seed, payloads, bitmap and final file |

## Explanation of the retained memory

The unexplained bytes are initialized instructions from an older PIP build. The CP/M 2.0 PIP source, independently extracted from Udo Munk's archived CP/M 2.0 source disk, differs from the uploaded CP/M 2.2 PIP source in later EOF, destination-close, copy-selection, and multiple-copy code. Compiling it with ISIS-II PL/M-80 V3.1 and locating it with a **64-byte stack** reproduces the instructions and variable addresses found in every DDT reserved range.

The compiler/tool environment is retained in `third_party/dri-ddt/reproduction/cpm22src.tgz`; the older source is `PIP20.PLM`. `reproduction/provenance.json` records download URLs, archive hashes, source-disk hash, filesystem extraction path, and the generated PIP digest. These inputs are independent of DDT.COM. The source archive used to establish PIP provenance is included in the exact-reproduction evidence bundle.

The native build executes these ISIS commands after copying the source and BDOS interface to its scratch drive:

```text
:f0:asm80 :f2:trint.src
:f1:plm80 :f2:pip.plm
:f1:link :f2:pip.obj,:f2:trint.obj,:f1:x0100,:f1:plm80.lib to :f2:pip.mod
:f1:locate :f2:pip.mod code(0100H) stacksize(64)
```

After returning to CP/M, OBJCPM converts the located module. The resulting PIP image is 7296 bytes with SHA-256 `2ccaa962a2df3f30cb0925fc641c8616d3f26192d3cd102666cd2f66b5fb45b5`. The original compiler object records are checksum-validated, and all 245 seed offsets used by DDT are covered by initialized CODE-segment records. They are not unexplained storage inside the PIP build.

## Reconstructed memory state

Load the regenerated PIP image at 0100H. Construct DDT in a separate work area at 0800H by overlaying only bytes emitted by its three assembly sources. Place the relocator at work offset 0000H and the zero-origin payload at work offset 0100H; reserve the monitor's leading 0680H for the assembler/disassembler. Supply the relocator length operand from the payload extent, append the independently generated bitmap, and zero the final 76 bytes for record alignment. Export 0800H through 1AFFH inclusive.

Source-uninitialized positions retain the underlying PIP image. Therefore every such DDT file offset `f` maps to PIP file offset `f + 0700H`, or memory address `f + 0800H`.

| DDT file range, inclusive | Bytes | PIP file range, inclusive |
| --- | --- | --- |
| 008BH–00FFH | 117 | 078BH–07FFH |
| 010CH–0114H | 9 | 080CH–0814H |
| 077AH–077FH | 6 | 0E7AH–0E7FH |
| 1049H–1064H | 28 | 1749H–1764H |
| 1066H–10BAH | 85 | 1766H–17BAH |

The byte at DDT offset 1065H is source-defined COMLEN=20H. It overwrites a PIP operand byte, which explains an apparent address discrepancy when that surrounding instruction was initially compared as one sequence. The final monitor NOP is also source-defined and takes precedence over underlying memory.

`residue-provenance.json` records every retained byte's DDT offset, PIP offset, memory address and value. Before/after memory images preserve the complete reconstructed state. This is a sufficient, independently generated memory state explaining the complete target. It does **not** establish that the original DRI operator used these precise work addresses and commands: equivalent copying or buffer layouts can produce the same state.

## Assemblers and bitmap

The retained DRI MAC.COM (CP/M MACRO ASSEM 2.0) and z80asm 2.1 in Intel mode emit identical DDT bytes. Native Intel HEX records are checksum-validated and establish coverage independently of the cross assembler's DS fill. MAC accepts the original production source syntax. The archived ASM.COM reports TITLE and monitor-symbol errors, so it is not the compatible unmodified-source tool.

Both payload modules are assembled at 0000H, 0100H and 3100H. Comparing the first two builds yields exactly 765 page-relocation bytes. Packing the marks most-significant-bit first reproduces the 504-byte reference bitmap. Applying it with biases 01H and 31H reproduces the independently assembled payloads. All marks lie in source-emitted bytes.

An archived CP/M source-build `CMD4.SUB` supplies a separate historical pipeline using MAC, PIP HEX concatenation, GENMOD, GENHEX and PRLCOM. It reproduces all source-defined bytes but not this reference's residue. Its current GENMOD work-buffer arrangement retains different PIP offsets. Thus that script supports the tool family and construction mechanism, but is not claimed as the exact original DRI recipe. The script's doubled dollar signs are SUBMIT escapes; explicit interactive execution uses a single dollar sign.

## Verification and controls

The complete source build passes byte comparison, length and SHA-256 checks. Clean repeated builds regenerate the same seed and final image. A test supplies a nonexistent comparison path: the complete matching image is written before verification attempts to open that path. The build does not execute a reference DDT.

Two negative controls reject nearby hypotheses. The same older PIP source located with a 100-byte stack reintroduces 37 byte differences. Retaining PIP at the offsets implied by a 0600H work area reintroduces 241 differences. The old zero-filled control still differs by the original 231 bytes. None of those controls modifies the DDT instruction stream.

Original and rebuilt images produce identical CP/M smoke transcripts for startup, H, F, D, M, X, L, an invalid command, G0, rubout and Ctrl-U editing. This is a bounded runtime check, not exhaustive execution of every case in the engineering behavior matrix. Complete binary identity is now established independently of that smoke coverage.

## Rebuild and retained evidence

From the repository root:

```text
python3 tools/build_ddt_reproduction.py
python3 tools/test_ddt_residue.py
python3 tools/test_ddt_reproduction.py
```

All three commands now return success. The seed compiler helper is `tools/build_ddt_seed.py`. Requirements are Python 3.9+, z80asm 2.1, cpmsim, cpmtools and Expect. Paths are configurable. The compiler and linker run from the retained archive in disposable disk copies; network access is unnecessary for a rebuild.

The output is `build/ddt-reproduction/DDT-reproduced.COM`. The exact-reproduction evidence bundle and its SHA-256 manifest are beside this report as `DDT-Reproduction-Exact-evidence.tar.gz` and `.json`. It contains source/tool provenance, compiler object and listings, generated inputs, assembler outputs, memory images, per-byte provenance, bitmap, final binary, positive and negative controls, and smoke transcripts. The earlier Gate1 bundle remains as historical evidence of the zero-filled mismatch.

The repository was updated to merged main ecb3379 before integrating this work. No BetterCP/M adaptation, shared-library linkage, command enhancement, production disk installation, or behavior change is included. The documented shared input library remains reserved for the subsequently authorized adaptation.
