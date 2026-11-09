# NDR implementation checks

Checked against the v1.1.1 CCP source. The JSON records assembly/allocation
measurements for the default Model 4, cpmsim-fullram and Model II-fullram
profiles. NDR provider payloads are byte identical across these layouts.

Executed checks:

- `tools/test_ndr.py`: assembled management and shell/PATH code, name limits,
  duplicate/reserved names, saved sets, returning write errors, invalid loads,
  relocation, prompt output, file operands, quoted text, command-line bounds,
  caller-user restoration and numeric PATH capture. Ordinary blank-prefixed CP/M
  command tails, raw tails, repeated blanks, mixed-case management keywords and
  provider-independent help/version queries are exercised explicitly. Run for all
  three layouts.
- `tools/test_path_edits.py`: existing numeric PATH edits and rejection atomicity;
  run for all three layouts, with absent NDR.
- `tools/test_ccp.py`: existing CCP behavior, default layout.
- `tools/test_ccpreload.py`: actual Model 4 reloader restoration and error paths,
  including the compact bootstrap carrier.
- `tools/test_ndr_manager.py`: production manager with the z80pack CPU core;
  first-load/shared overhead, exact 512-byte marginal charge, offline stateful
  reconstruction, unload recovery and empty reload.
- `tools/test_ndr_budget.py`: separate protected-provider and reclaimable-CCP
  allocation measurements; provider ceiling enforced at 768 bytes.

The profile execution checks use a controlled BDOS filesystem/console fixture;
this is not booted media or hardware sign-off. Published 1.1/1.1.1 artifacts
were not changed or rebuilt. Full release-media qualification belongs to the
1.2 release workstream.

Two broader checks have pre-existing failures, reproduced unchanged in the clean
v1.1.1 checkout: `test_utility_help_layout.py` expects NOAH's old `/HELP` label
instead of the existing `/H /HELP` label; `test_distribution.py` expects the
old development heading for release versions other than exactly 1.1. Neither
failure is caused by NDR, and neither test was weakened for this change.
