# RomWBW terminal and compatibility qualification

28 November 2026; Linux x86-64, pinned romwbw_emu 1.51 / RomWBW 3.5.1.
The terminal, native toolchain and focused system checks pass. Full independent
suite qualification remains **BLOCKED** by the two-logical-drive scope.

## Integrated terminal modules

ADM3A, VT52 and ANSI use capability 32 and the exact private resident binding.
Their combined personality/renderers call the register-preserving HBIOS leaf
WB_TXA. The leaf replaces unused halt code: BIOS remains 597 bytes in the same
allocation, with no permanent display reservation and no loss of default TPA.
No separate SCRN module or cpmsim port output is used.

| Module | Complete budgeted path | Existing limit |
| --- | ---: | ---: |
| ADM3A | 1,247 bytes | 1,280 bytes |
| VT52 | 1,247 bytes | 1,280 bytes |
| ANSI | 1,759 bytes | 1,792 bytes |

The shared 81-command lifecycle verifies absence/admission, same-owner TCAP
discovery and refusal, invalid console route refusal, typed and legacy output,
rendered row/column and reverse attributes, warm returns, relocation across a
temporary HELLO allocation, reload and exact unload restoration. HELP PIP runs
through each personality. STAT again reports 57,344 maximum loadable COM bytes
after unloading. A cpmsim ANSI carrier with the **same private build identity**
is refused by the platform capability check before it can execute port output.
A second negative fixture retains the correct HBIOS capability but changes its
binding to public class 0; it is also refused. Before the explicit class check,
the same fixture was admitted. All guest runs use strict unexpected-port rejection.

## Independent compatibility suite

The eleven automatic groups execute the original COM binaries from
`CPMArchives/cpm-2.2-compatibility-suite` revision
`a9a878fcd2e36698c7e856654a85847a004fdd20`. Each binary is verified against that
revision's SHA256SUMS. Test instructions and oracles are unchanged. Primary
fixtures reside on B:, including the required user-1 BTUSR and read-only BTRO.

There are **262 qualified automatic assertions**, with zero unexpected errors.
The raw suite reports 263 P and four F; those raw results remain in the JSON and
transcripts. The following seven cards do not have their required provider:

| Utility | Card | Raw result | Missing prerequisite |
| --- | --- | --- | --- |
| DIRTEST | 0200 | F | Explicit C: directory fixture |
| FILETEST | 0158 | F | C: explicit Open fixture |
| FILETEST | 0278 | F | Writable C: explicit Make/write target |
| FILETEST | 0169 | Not-run | C: BTBFILE.DAT |
| FILETEST | 0242 | Not-run | C: BTBFILE.DAT |
| RANDTEST | 0556 | F | Full-directory D: with BTFULL.DAT |
| RANDTEST | 0557 | P, excluded | Same D: fixture; absent-drive Open can short-circuit the test's precondition helper |

The 0557 apparent pass is deliberately excluded from the qualified count.
Missing prerequisites are **not** promoted to passes. The harness returns exit
2 with status BLOCKED for this known unavailable-provider set and exit 1 for an
unexpected failure. Manual/external cards also remain outside this run.
These results do not qualify C:/D:, additional HBIOS logical drives, full-media
procedures, physical firmware drivers or hardware.

## Retained evidence

| File | Scope |
| --- | --- |
| `display-result.json`, `display.txt` | Terminal lifecycle, exact budgets/binding, HELP, 56 KiB restoration, raw transcript hash. |
| `compatibility-result.json`, `compat-*.txt` | All eleven original groups, per-card raw verdicts, binary hashes and explicit prerequisite exclusions. |
| `toolchain-result.json`, `toolchain.txt` | Pinned native ZSM4 indexed Z80 assembly, macro/include expansion, multi-module LINK and execution of CHECK.COM. |
| `system-result.json`, `utilities-result.json` | Original 15 system checks and 30 portable utility queries plus file/archive/batch functional checks repeated on the expanded image. |
| `install-result.json`, `config-result.json` | Expanded-image installation and independent host extraction; installed cold boot; confirmed startup/PDS/IOBYTE settings across installation. |
| `build.json`, `emulator.json` | Exact image, modules, source-runner hashes, resident bounds, pinned emulator sources, compiler and executable identity. |

Shared-profile (11), component-input (14) and registry (9) tests pass.
Console text normalizes terminal escapes, line endings, trailing whitespace and
workspace paths. Original raw captures remain in the build output directories;
their hashes are retained in the result records. No platform release is assigned.
