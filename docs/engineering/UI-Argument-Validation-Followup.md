# UI argument-validation follow-up to #571

3 November 2026. **Host/build/cpmsim/Model 4 PASS for the bounded follow-up gates.**
PR #571 merged at `bd4df2cd9f0a7a2edfa12112a8c02151eea5b90d`.
This follow-up preserves that implementation and the accepted UI/library APIs.
No frozen core, resident RCP, BIOS, new library or release image is changed.

## Trigger and correction

`ADMTST /BOGUS`, `ANSITST /BOGUS` and `VT52TST /BOGUS` previously reached
Function 182 provider lookup and began their diagnostic flow. `XSUB /BOGUS`
reached Function 177 installation requests (operations 3 and 1). These commands
document no operational operands, so accepting garbage could start an unintended
operation. This was demonstrated with execution of the compiled entry paths.

`src/utilities/{admtst,ansitst,vt52tst,xsub}.mac` now scans the counted command
tail at entry, immediately after the existing `UV_CHECK`. Empty, space-only and
TAB-only tails retain the original operation. Any other non-query tail prints
`Invalid usage.` followed by `Use NAME /HELP.` and returns without provider
lookup or installation. Exact query recognition and help-over-version precedence
remain with the existing common query handler; `/HELPER` and `/VER=1` are errors.
The bounded scan also refuses counted lengths >=128.

The inline guard is 36 bytes and adds no pushes, private stack, workspace or
resident allocation. Its A/B/HL scratch registers are not live at the original
operation entry. XSUB's message precedes `XS_END`, preserving its scratch bound.
Revisions advance to ADMTST 007, ANSITST 006, VT52TST 007 and XSUB 006.

## Build and memory

| COM | Before | After | Delta | 2-KiB disk allocation before/after |
| --- | ---: | ---: | ---: | ---: |
| ADMTST | 1,973 | 2,045 | +72 | 2,048 / 2,048 |
| ANSITST | 1,042 | 1,115 | +73 | 2,048 / 2,048 |
| VT52TST | 1,337 | 1,410 | +73 | 2,048 / 2,048 |
| XSUB | 698 | 768 | +70 | 2,048 / 2,048 |

The message length accounts for the different deltas. Each rounded static
TPA end page is unchanged; no new stack frame is introduced by valid entry.
ADMTST has only three bytes of file allocation headroom. Do not infer that a
future enlargement is free. ADM3A.RSX, ANSI.RSX, VT52.RSX and BATCHIO.RSX rebuilt
byte-identically. No media allocation, protected resident charge or established
TPA budget is increased. These are build/layout checks, not new platform-wide
minimum-memory qualification.

Reproduce with:

```sh
python3 tools/build_adm3a.py
python3 tools/build_ansi.py
python3 tools/build_vt52.py
python3 tools/build_batch.py
python3 tools/component_registry.py --check
python3 tools/test_utility_finalization.py
python3 tools/test_utility_versions.py
python3 tools/test_ui_integration_schedule.py
python3 tools/test_utility_ui_inventory.py
python3 tools/test_ui_integration_media.py --system ../BetterCPM-release-push/build/rc564-systems --platform cpmsim --noargs-only --output build/ui-noargs-cpmsim
```

The media output directory must not already exist. Run from this worktree with
the project's existing assembler, cpmtools and emulator dependencies installed.

## Evidence and limits

[Evidence index](evidence/2026-11-03-ui-argument-validation/results.json),
[archived logs and receipts](evidence/2026-11-03-ui-argument-validation/receipts-and-logs.tar.gz),
and [checksums](evidence/2026-11-03-ui-argument-validation/SHA256SUMS.txt)
bind exact source hashes and before/after binary hashes.

- Builds: four affected build groups pass. Unchanged companion hashes and the
  allocation comparison are in `noargs/baseline.json` and `noargs/after.json`.
- Compiled entry tests: 56 no-operand rejection/default-path cases, including
  127-byte bad/whitespace tails; invalid input cannot invoke manager services.
  The original 37 help screens, 324 alias/precedence/manager checks and 222
  version queries still pass. Fifteen ERA/USER/VER malformed-tail cases exercise
  the full entry path with file calls trapped and DU restoration constrained.
- Query fixture repair: `test_utility_versions.py` now uses an actual JP BDOS
  gateway and the existing console collector, rather than a false low TPA
  ceiling and last-call-only recorder. All 314 checks pass. ED/SYSGEN expectations
  use current full identification blocks. Earlier failed fixtures are archived.
- cpmsim: 22 phases pass, including eight help/version queries, twelve invalid
  invocations, ordinary XSUB installation and `RSX LIST`. Independent payload
  and BATCHIO readback, system/data filesystem checks and unchanged reserved
  system area pass on private copies of the reference system.
- Model 4: all 22 executed phases pass on these exact four binaries. Eight
  queries, twelve invalid invocations, normal XSUB installation and RSX LIST
  have matching completion captures. Independent payload/companion readback,
  both filesystems and unchanged system area pass. The maintainer's receipt is
  `/Users/nathanael/Downloads/ui-noargs-model4-20261103-143246/result.json`.
  Captures, query/error output, payload/source hashes and readback were reviewed
  again before archiving [native evidence](evidence/2026-11-03-ui-noargs-model4-pass/results.json).
  This closes this follow-up's native gate; it does not qualify the whole release.

The parser campaigns also close 24 other matrix entries without production
changes. Their exact commands/statuses are in the archive's `parser-closure*`
and `host-closure-final/results.json`. They cover existing DUP, SYSGEN, CONFIG,
DIR, PIP, DSYM, DLINK, DUMP, COPY, REN, ED, TED, NOAH, TIME, TYPE and six codec
parsers, plus ERA/USER/VER above. Counts are bounded case coverage, not exhaustive
language proofs. TED's operation parser is tested directly; existing frontend
integration evidence supplies its binding.

UNLZH's default historical run failed because authenticated `crlzh11.lbr` and
`crlzh20.lbr` fixtures are absent. The new explicit `--synthetic-only` switch
runs 75 self-contained full-Z80 cases and reports historical cases NOT RUN.
It does not relax the default historical requirement. The failed default log is
retained separately. Reproduce the bounded run with
`python3 tools/test_unlzh_com.py --synthetic-only`.

Six development-only operational-tail matrix entries remain O. They are absent
from current release disk membership, but have not been relabeled conforming.
The candidate report records the four identical guards as a low-priority,
maintenance-only consolidation possibility; no new library is implemented.

## Native gate reproduction

Run from an ordinary macOS Terminal, with the correct Model 4 emulator session
available. The existing runner drives the private images automatically:

```sh
ui="$HOME/.codex/.chatgpt-projects/g-p-6a682f002be881918281554d644daf48/BetterCPM-ui-integration"
python3 "$ui/tools/test_ui_integration_media.py" \
  --system "$ui/../BetterCPM-release-push/build/rc564-systems" \
  --platform model4 --noargs-only \
  --output "$HOME/Downloads/ui-noargs-model4-$(date +%Y%m%d-%H%M%S)"
```

The receipt, all 22 captures and payload/companion readback have been reviewed.
PR #573 is ready for engineering review of this bounded follow-up. Six development-only
matrix O entries and the absent historical UNLZH fixtures remain explicitly
recorded; no overall workstream-completion claim or automatic merge is authorized.
