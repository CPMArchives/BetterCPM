# Part 9 reproduction

Use `assessment/part9-command-loader` for the experiment scripts. Its inputs
are preserved Part 8 full-RAM and checked-legacy stages, not a new release
build. The host prerequisites remain Python 3, z80asm 2.1 at `~/bin/z80asm`,+cpmtools, and the pinned Part 2 cpmsim. Adjust original host-specific assembler
defaults when reproducing on another host.

To reconstruct missing baselines, use a separate checkout of Part 8 commit
`6539c66877f3d09605aa86b1add57fe92748b250` and its
`tools/assessment_checked_profiles.py`, with `--carrier-bindings`, for
`cpmsim-fullram` and `cpmsim-legacy-checked`. Do not silently build the baseline
from the Part 9 tree: its additional source files change the private input
closure. The Part 8 report has the original evidence and full instructions.

From the Part 9 repository, substitute your absolute baseline/output paths:

```sh
python3 tools/assessment_part9_compact.py /tmp/p8-full --output /tmp/p9-compact
python3 tools/assessment_part9_stage.py /tmp/p8-full --output /tmp/p9-staged
python3 tools/qualify_part9_stage.py /tmp/p8-full /tmp/p9-staged
python3 tools/qualify_part9_bootstrap.py /tmp/p8-full /tmp/p9-staged
```

The stage builder emits source, listings, the 54-byte bootstrap and 1,172-byte
second stage, their bound carriers, and candidate CCP/RCP/HELLO files.
The carrier trailer is schema 2 with a CRC word. These candidates supersede
the incomplete Part 8 format experiment only within this isolated test.

Run emulator sessions sequentially because the pinned cpmsim uses shared
auxiliary FIFO names:

```sh
export BETTERCPM_ASSESSMENT_SIM=/path/to/pinned/cpmsim
python3 tools/qualify_part9_live.py /tmp/p8-full /tmp/p9-staged --compact /tmp/p9-compact
python3 tools/assessment_part9_stage.py /tmp/p8-legacy --output /tmp/p9-legacy
python3 tools/qualify_part9_live.py /tmp/p8-legacy /tmp/p9-legacy --smoke-only
```

The live harness copies the baseline disks into its own `qualification/`
directory. It patches raw records 60–67, 84–99 and 108–159, changes the resident
expected bootstrap-CRC operand, and replaces RCP/HELLO files in the private
image. It does not modify the baseline source, build outputs or system image.
The successful smoke image is preserved as `system.raw` with `diskdefs` in the
experiment directory. Do not install it as a supported release package.

Read `results.json`, `fixture-results.json`, `bootstrap-results.json` and
`qualification/results.json`, plus per-case transcripts. The compact
experiment has its own `results.json`. A new output directory is preferable;
the workbench tools may overwrite their own previous artifacts.

For deterministic assembly, rerun both builders into fresh directories and
compare `compact.bin`, `stage1.bin`, `stage1.carrier`, `stage2.bin`,
`stage2.carrier`, `ccp.rlm`, `RCP.CPX` and `HELLO.CPX`. The report's
`repeat-results.json` records the eight exact matches. It does not compare
post-session filesystem contents or claim a production-profile rebuild.

The full-staging loader protects the prospective destination until validation
completes. Header retention with streaming is only a proposed follow-up; no
test result in this part should be attributed to that unimplemented design.
