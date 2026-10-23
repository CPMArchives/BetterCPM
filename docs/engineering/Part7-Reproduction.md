# Part 7 reproduction

Use `assessment/part7-checked-profiles`. These are assessment commands, not a
release build. Host prerequisites are Python 3, z80asm 2.1 at `~/bin/z80asm`,
cpmtools on PATH, and the reconstructed Part 2 cpmsim executable. The source
builders retain some original `/Users/nathanael/bin/z80asm` defaults; set their
assembler defaults appropriately if reproducing on a different host. No ROM
or native-ZSM4 qualification is implied.

Choose fresh absolute output paths. The wrapper refuses existing output trees.
Run from the repository root:

```sh
python3 tools/assessment_checked_profiles.py cpmsim-fullram --output /tmp/p7-full
python3 tools/assessment_checked_profiles.py cpmsim-legacy-checked --output /tmp/p7-legacy
python3 tools/assessment_checked_profiles.py model4-legacy --prepare-only --output /tmp/p7-m4
```

The model4 command prepares source/layout only. A real Model 4 build is
intentionally refused by this prototype wrapper. Unknown profile names and
ROM/full-RAM Model 4 combinations are refused before output creation. The
`cpmsim-legacy` profile can produce the unchecked legacy regression control.

Run the executed-code fixtures in the full-RAM staging tree:

```sh
cd /tmp/p7-full
python3 tools/qualify_part7_container.py /tmp/p7-legacy/build/system/R3PACK.RSX
python3 tools/qualify_part7_raw.py
```

Run cpmsim campaigns sequentially because the private emulator uses shared
auxiliary FIFO names. Substitute the actual reconstructed emulator path:

```sh
export BETTERCPM_ASSESSMENT_SIM=/path/to/pinned/cpmsim
python3 tools/qualify_part7_live.py
P7_FOREIGN_PACK=/tmp/p7-legacy/build/system/R3PACK.RSX python3 tools/qualify_part7_faults.py
python3 tools/qualify_part7_edges.py
```

These campaigns make private disk copies under the staging tree's
`qualification/` directory. They do not alter the built `assessment-media/`
image. The support module can select an alternate staging root through
`P7_ROOT`; its default is the tree containing the script.

Read `qualification/results.json`, per-case transcripts, and
`assessment-build-logs/container-tests.json` / `raw-tests.json`. The checked
build's actual patched resident checksum operands and symbol coordinates are
in `build/z80pack/checked-load.json`; the assembly listing precedes that operand
patch and is not the final byte authority. Inspect `bios.bin` and the manifest
when comparing final bytes.

The wrapper first builds an unchecked control in the isolated tree, retains
its media and hash manifest under `unchecked-control-media/`, then rebuilds
the selected checked products and validates distribution read-back. Do not
use intermediate Model 4 products as qualified platform artifacts. The final
prototype media is `assessment-media/system.raw`.

For deterministic rebuilding, repeat the same profile in a second fresh
output tree and compare the compatibility ID, executable/carrier outputs and
final media. Listing timestamps and source-provenance commit fields are not
binary-equivalence tests. Part 7 compared 136 binary/media artifacts.

The companion report's evidence bundle contains the exact tested outputs,
source transformations, selected generated source, manifests and transcripts.
Its legacy-parity and profile-admission JSON files record additional host
checks. The complete report documents which adoption gates remain open.
