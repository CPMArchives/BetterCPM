# DDT Model 4 display and input qualification

22 October 2026. DDT 1.0 Build 001; qualification against merged main `c7d8ed3`.

The remaining DDT Model 4/trs80gp display qualification passes without changing DDT. Seventeen screen stages verify the debugger's shared input binding through the emulated physical keyboard matrix and actual 80-column VRAM. A repeat run uses the retained source disk as an explicitly supplied input; only disposable copies are mounted.

## Fixture and harness corrections

The earlier retained release disk still produces a blank boot-only capture. It cannot establish a valid DDT control. A newly constructed test disk reaches the CCP prompt. The first fresh fixture nevertheless used cached system binaries: its BIOS listing dated 6 October translated CLEAR to `1Fh`, whereas current source translates it to ESC. Rebuilding every layout-dependent component with `tools/build_complete_system.py` fixes that fixture mismatch. DDT's cancellation binding needs no change.

The original harness also depended on a startup SUBMIT script and on screen-pattern waits which stalled despite matching text appearing in later VRAM captures. The repaired harness boots to a captured CCP prompt, enters `/VER` and DDT interactively, allows warm boot to settle, and uses bounded frame delays. Every captured stage is asserted afterwards; missing or late text fails the campaign. There is no automatic startup-script dependency or inferred pass from emulator exit alone.

The test retains `source.dmk`, mounts only `private.dmk`, and checks that an optional supplied source image is unchanged even when emulator execution fails. The successful campaign also leaves the private disk byte-for-byte unchanged. Reports hash the emulator, system fixture components, program, disks and captures. Freshness requires the complete-system build below; the test intentionally fails physical CLEAR assertions on the obsolete BIOS rather than hiding that difference.

## Observed behavior

| Stage | Verified result |
| --- | --- |
| Boot and version | CCP prompt, compact DDT identity, return after `/VER` |
| Entry and deletion | Visible `-H100,2X_`; physical DEL replacement submits `H100,20` |
| Interior editing | Physical Ctrl-S/G movement/deletion produces the same command and arithmetic result `0120 00E0` |
| Horizontal scroll | A 32-byte line displays the trailing 23 characters and underscore in the 24-cell viewport, preserving `-` |
| Clear | Ctrl-Y removes provisional text; `H1,2` produces `0003 FFFF` |
| Substitution | Original `0300 41` prefix stays visible beside provisional `99_` |
| Cancellation | Physical CLEAR discards `99`, returns to `-_`, and a subsequent dump still shows `0300 41 A` |
| Assembly/disassembly | Original `A400`, `MVI A,5`, `RET`, dot termination and `L400,402` produce `0402  RET` |
| Return and restart | `G0` returns to CCP; a marker command runs; DDT starts again; physical BREAK returns to CCP |

The edit, scroll and cancellation stages also have clean emulator screenshots. Inspection confirms the prefix, underscore and scrolling field are visible. The broader existing cpmsim campaign covers debugger execution, breakpoints, T/U, registers and COM/HEX loading; this native display campaign complements that coverage.

## Reproduction and binary isolation

The adaptation remains 6528 bytes, SHA-256 `4b72c62b846dc3aaff673bf6b2fa3569c8fdc9887ca7927b3bf6ce3c357b6e46`. Its source, debugger command language and shared input integration are unchanged. No shared-library or system-source change was required.

The independent historical build again matches all 4864 reference bytes, SHA-256 `d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf`, with zero differences. Historical files, builders and prior evidence archives remain untouched. After rebuilding current system artifacts, all 178 repository utility version/purity checks pass as well, resolving the earlier stale-artifact regression-suite limitation.

## Repeatable checks and evidence

From the repository root:

```sh
python3 tools/build_complete_system.py
python3 tools/test_ddt_model4.py --output /private/tmp/ddt-model4-current-qualification
python3 tools/test_ddt_model4.py \
  --image /private/tmp/ddt-model4-current-qualification/source.dmk \
  --output /private/tmp/ddt-model4-repeat-qualification
python3 tools/test_utility_versions.py
python3 tools/build_ddt_reproduction.py --output /private/tmp/ddt-model4-historical-check
```

Output directories must not already exist. Retained evidence is in `DDT-Model4-evidence.tar.gz`, with hashes and result summaries in `DDT-Model4-evidence.json`. It includes screen captures, screenshots, invocations, reports, disposable fixture disks, current-system build log and historical/build verification reports. Earlier inconclusive evidence remains a historical record, superseded by this campaign.

This closes Model 4/trs80gp display and physical-keyboard qualification on the direct BIOS console. No SCRN backend or monitor personality is needed or loaded. It does not claim real-hardware testing, additional monitor-provider combinations or whole Utilities Disk release acceptance; the Utilities images remain provisional.
