# Part 10 reproduction

Use `assessment/part10-streaming-loader`. Inputs are the preserved Part 8
checked stages described in Part9-Reproduction.md, built from commit
`6539c66877f3d09605aa86b1add57fe92748b250` with `--carrier-bindings`, for
`cpmsim-fullram` and `cpmsim-legacy-checked`. Do not regenerate that baseline
from this source tree: the additional files change its private input closure.
Host prerequisites are Python 3, z80asm 2.1 at `~/bin/z80asm`, cpmtools and the
pinned Part 2 cpmsim (SHA-256
`b2d4384af06dbea8d32bc43eab539bf9e4857e74780577a249d0e8c5e22c955d`).

Substitute absolute baseline and output paths:

```sh
python3 tools/assessment_part10_stream.py /tmp/p8-full --output /tmp/p10-stream
python3 tools/qualify_part10_stream.py /tmp/p8-full /tmp/p10-stream
python3 tools/qualify_part9_bootstrap.py /tmp/p8-full /tmp/p10-stream
export BETTERCPM_ASSESSMENT_SIM=/path/to/pinned/cpmsim
python3 tools/qualify_part10_live.py /tmp/p8-full /tmp/p10-stream
python3 tools/assessment_part10_stream.py /tmp/p8-legacy --output /tmp/p10-legacy
python3 tools/qualify_part10_live.py /tmp/p8-legacy /tmp/p10-legacy --smoke-only
```

Run cpmsim sessions sequentially because the emulator uses shared auxiliary
FIFO names. The live harness patches only private disk copies in its output
folder. `system.raw` and `diskdefs` preserve the successful smoke image; do not
install this proof image as a supported release. The full campaign runs on
full-RAM; the legacy control runs only the smoke test.

For repeat assembly, raw-carrier audit and processing comparison:

```sh
python3 tools/assessment_part10_stream.py /tmp/p8-full --output /tmp/p10-repeat
python3 tools/assessment_part9_stage.py /tmp/p8-full --output /tmp/p9-reference
python3 tools/audit_part10_stream.py /tmp/p8-full /tmp/p10-stream /tmp/p10-repeat --reference /tmp/p9-reference
python3 tools/measure_part10_stream.py /tmp/p8-full /tmp/p9-reference /tmp/p10-stream
```

The measurement script assembles its controlled adapters in the supplied
experiment directories. Use separate copies if preserving a prior directory's
exact provenance. It counts functional-runner dispatches, with block operations
handled in one dispatch; results are not physical Z80 timings. Its stack minima
cover only the loader and controlled adapter.

Read `results.json`, `fixture-results.json`, `bootstrap-results.json`,
`memory-and-image-audit.json`, `instruction-measurements.json` and
`qualification/results.json`, plus per-case transcripts. The report preserves
the dispatch results under `measure-stream/`. Seven generated binaries/carriers
must match on repeat assembly. CCP/RCP/HELLO must also match Part 9 byte-for-byte.

The header cache occupies 1000h–15FFh and the record buffer 1600h–167Fh. All
CRC/cursor/binding state fits in the stage carrier below 0D00h. Rejected loads
may leave payload bytes at their prospective address. The fixture checks those
bytes against the precise prefix from successful reads, guards unrelated
memory, and confirms the allocation boundary was not published.

This procedure does not generate a fresh compatibility contract or exercise
production builders/installers. Those are proposed Part 11 work.
