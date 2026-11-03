# Shared UI integration engineering summary

3 November 2026. **Draft; workstream completion and merge acceptance remain
open.** Clear, compatible work is implemented and tested. TED's confirmation
correction is approved and implemented; the matrix's outstanding verification
cells and changed-binary Model 4 execution remain open. No core, BIOS, resident RCP or historical third-party
reference source was changed. No new utility feature/library was introduced.

## Reviewable implementation

Published implementation commit:
`8bc26cd1e85d4d138b4d62b13f712b86ad961e98`, on
`stabilization/shared-ui-conformance`, based on main
`1fda9b6194c5b2055814ab9ae74711ad7c37191f`.
The equivalent local implementation commit is `1b4204d` based on the accepted
`fb06225` worktree; intervening main changes are documentation-only. Publication
uses the current-main tree, preserving those unrelated documentation updates.

- BYE selects the existing choice-only controller. Its displayed question now
  uses `(Y/N) [N]`; Y/N are immediate, Enter/LF remains No, ESC/Ctrl-C cancels,
  invalid keys repaint, and no queued independent input is flushed.
- DASM's CHIN selects the existing strict one-key compatibility binding. Its
  historical bit folding, echo, no-default and any-non-Y decline policies stay
  intact. Its command language and file publisher are untouched.
- CRCKSUM/MD5SUM retain their already common decision loop as a measured media
  exception. Direct modal input/output corrects the real-BDOS Ctrl-C warm-boot
  defect; local cleanup now runs. Typed ASCII/CR/LF/BS echo is preserved locally;
  unassigned controls do not enable cooked printer/pause behavior in this modal
  context. Enter still means Yes, A retains its run-wide meaning, `?` repeats
  help/question, and ESC remains invalid.
- Current input dependency closures and executable revisions are recorded:
  BYE 004, DASM 004, CRCKSUM 010, MD5SUM 004; TED advances to 004 in the
  approved follow-up below. No counter advances for unchanged
  utilities or test/documentation-only edits.
- Focused old consumer tests now use current full identification blocks and
  CONFIG's accepted code/stack/help layout validator. No production legacy
  consumer behavior is changed by those harness corrections.

The [inventory](UI-Integration-Inventory.md) records authority and active-work
checks. The [52-row matrix](UI-Conformance-Matrix.md) distinguishes applicability,
compatibility exceptions and verification gaps. The [candidate report](Shared-Library-Candidate-Report.md)
is read-only; none of its proposed consolidation is implemented.

## Size, stack and TPA

| Artifact | Baseline bytes | Current bytes | Delta | 2-KiB allocation before → after |
| --- | ---: | ---: | ---: | ---: |
| CRCKSUM.COM | 22,415 | 22,473 | +58 | 22,528 → 22,528 |
| MD5SUM.COM | 18,320 | 18,378 | +58 | 18,432 → 18,432 |
| DASM.COM | 21,248 | 21,504 | +256 | 22,528 → 22,528 |
| BYE.COM | 1,097 | 1,325 | +228 | 2,048 → 2,048 |
| TED.COM | 30,300 | 30,492 | +192 | 30,720 → 30,720 |

The initial checksum controller trial used 22,695/18,600 bytes. Both crossed
allocation boundaries: primary Utilities would require 339,968 content bytes
against 337,920 available. The retained compact implementation requires 335,872
bytes, leaving the original 2,048 bytes free. This is filesystem allocation,
not merely a sum of COM sizes. Disk membership and capacity are unchanged.

DASM's additional code advances its page-aligned static layout one page; its
existing minimum-TPA guard advances accordingly (D_MEM_END is now B400h, and
the entry checks D_MEM_END+100h). This does not increase the supported platform
TPA budget, but an environment at the previous exact minimum needs requalification;
no unchanged-minimum claim is made. Its existing fixed workspace sizes and stack
are retained. Current full-command tests exercise the accepted boundary and one
byte below it. Low-memory deployments remain an explicit review consideration.

No resident allocation changes. Checksum private stack remains 512 bytes, with
its existing untouched low guard in full-command tests. Measured prompt stack
use is 24 bytes; DASM's complete tested binding peaks at 40 bytes. BYE retains
256 stack bytes with an independently painted 64-byte low guard. Choice-only
consumers omit field editors/renderers. CONFIG's current dual-profile build has
59 bytes between ordinary code and its unchanged private stack; help is in the
accepted disposable region above that stack, not ordinary executable code.

`sizes.json` in the evidence archive binds current COM hashes and allocation.
No release image or stable image collection was refreshed by this work.

Evidence: [index and current artifact hashes](evidence/2026-11-03-ui-integration/results.json),
[receipts and logs](evidence/2026-11-03-ui-integration/receipts-and-logs.tar.gz),
[checksums](evidence/2026-11-03-ui-integration/SHA256SUMS.txt).

## Executed validation

All counts below describe bounded tests, not universal qualification.

- Shared UI: 68 compiled engine/controller cases, formatter/screen/layout
  campaigns, hostile callbacks, buffer limits, empty policies, words, defaults,
  immediate choices, cancellation, stack balance and module omission. Native
  ZSM4/LINK parity passes for six selected fixtures. No new library code changed.
- Changed consumers: 524 checksum prompt comparisons, every delivered byte,
  invalid repeats/help/cancel/default/All and exact typeahead decisions; 330 BYE
  full-core cases including every raw byte, private guard, caller state and
  shutdown/fallback; 256 DASM comparisons including hostile scratch registers,
  IX/IY and one-key approval. Current full-command campaigns: CRC 135, MD5 88,
  DASM operational/failure/boundary cases.
- Expanded query suite: 37 complete help screens, 324 alias/precedence/manager
  parser checks and 222 exact version queries. Four specialized help paths pass
  24 compiled queries. CONFIG help/CLI tests, six NOAH no-overlay query checks
  and the existing full-Z80 codec query campaign pass.
- Existing shared consumers: CONFIG 512 menu/256 approval cases plus transitions
  and malformed state; DUP 1,024 menu/drive comparisons and strict approval;
  SYSGEN approvals/destination; ERA choices/recovery; REN choices/names;
  COPY 774 prompt/field comparisons; PIP 258 complete protected replacements;
  DDT 17 compiled consumer cases and 100 repeated entries; TED's original 21 complete
  frontend cases, superseded for current TED by the follow-up below.
- Additional applicable regressions pass: DUMP 174 enhanced cases, COMPARE 94,
  PATCH 88, SEARCH parser, PIP parser, STAT unknown options, TIME errors,
  TYPE paging and DIR options. Native parity/help passes for DUMP/DASM/DSYM/TED.
- Actual BetterCP/M cpmsim: the focused 24-step campaign exercises changed
  query/choice paths, normal list creation, repeated help, invalid responses,
  refusal and local Ctrl-C, DASM restart refusal and BYE cancellation. Independent
  readback proves original input/list/executable contents unchanged, new lists
  correct, system area unchanged and filesystem valid. Source system image is
  preserved. Private boot disks may acquire ordinary SUBMIT startup bookkeeping;
  whole-disk byte identity is not asserted for writable boot copies.
- Registry projection, 52-row membership coverage, changed Python syntax and
  whitespace checks pass.

Original failed trials are retained separately from final passes. In particular,
the first real-media Ctrl-C failure is not relabeled as a pass. Source-level
models which return a cooked Ctrl-C cannot establish real-BDOS cancellation.
The old monolithic `test_utility_versions.py` main still has a known incompatible
query/output assumption and fails; it is not a claimed passing suite. The
expanded focused query suite and component suites above supply current coverage.

## Reproduction

### Model 4 runner correction after the first Terminal attempt

The 3 November Terminal run at `ui-model4-20261103-114907/shared`
failed before utility behavior could be qualified. Captures show the first
command overlapping `RSX LOAD M4SCRN` from STARTUP.SUB (only `GUS` reached
the command prompt), followed by rejected B: commands. The runner had also
constructed B: with the reserved-track system layout; configured B: requires
the standard 800K data layout, including its sector order and OFF=0.

`tools/test_ui_integration_media.py` uses the existing FDF data-disk
conversion and cpmtools path for B:, independently reads every payload back
after conversion, and checks the filesystem before launch. The first correction
used a blocking `UIREADY.COM` startup sentinel, but continued to wait on generic
`A0>` text between utility launches. The second Terminal attempt at
`ui-model4-fixed-20261103-115606` timed out after 600 seconds and seven captures.
Its captures show alternate commands being lost while the runner matched an
older prompt on screen. Version commands executed; this was not a completed
query or choice campaign.

The current runner uses the established SUBMIT/marker protocol from
`dasm_native.campaign`: private STARTUP.SUB loads the existing screen/terminal
modules and runs `SUBMIT UIQUAL`. All shell commands are queued in UIQUAL.SUB.
Each completed operation runs a unique blocking `UIxx.COM` marker; only modal
responses and marker acknowledgements use physical key input. After a marker is
acknowledged it scrolls old screen text away before warm boot, preventing a later
wait from matching a previous question. A: scripts/markers and B: payloads are
independently read back, and both prepared filesystems are checked before launch.
Captured help/version output and all twenty completion/prompt captures are
required. Failures receive a concise FAIL receipt with the last capture count
and next expected marker. Utility binaries, core and reference media are unchanged.

Corrected Model 4 preparation and the 24-step cpmsim regression pass:

```sh
python3 tools/test_ui_integration_media.py --system ../BetterCPM-release-push/build/rc564-systems --platform model4 --prepare-only --output build/ui-integration/model4-corrected-final
python3 tools/test_ui_integration_media.py --system ../BetterCPM-release-push/build/rc564-systems --platform cpmsim --output build/ui-integration/cpmsim-runner-regression
```

Preparation is not Model 4 execution; the corrected native campaign still
requires a normal Terminal run. Failed captures and corrected preparation/
cpmsim receipts are retained in
`evidence/2026-11-03-model4-runner/receipts-and-logs.tar.gz`.

The replacement protocol additionally passes six executable Z80 marker tests
(including hostile BDOS scratch registers), the exact twenty Model 4 command
phases on real cpmsim, all six query-output checks, preserved-input/new-list
readback, boot-area comparison and filesystem checks. The command script hashes
match between the cpmsim exercise and prepared Model 4 media:
`b8f8d2df27ebfbe14ce84b1d8e124d86e599926cbd8f1806e984690b805c4b28`.

```sh
python3 tools/test_ui_integration_schedule.py
python3 tools/test_ui_integration_schedule.py --system ../BetterCPM-release-push/build/rc564-systems --output build/ui-integration/cpmsim-submit-final
python3 tools/test_ui_integration_media.py --system ../BetterCPM-release-push/build/rc564-systems --platform model4 --prepare-only --output build/ui-integration/model4-submit-final
```

The BYE queued-input case remains in the original cpmsim campaign. It is excluded
from the Model 4 SUBMIT protocol test because BYE is cpmsim-only and its Escape
accepts cancellation before a subsequent queued `n`; the CCP intentionally treats
that pending byte as SUBMIT cancellation. An initial overbroad test captured this
expected boundary and is retained as a failed harness trial. Another trial passed
the command/file checks but used invalid fsck option ordering; the final campaign
uses `fsck.cpm ... -n image` and passes. Current evidence and the second failed
Terminal capture set are in
`evidence/2026-11-03-model4-submit/receipts-and-logs.tar.gz`.

### Build and regression commands

Use the branch's existing reference toolchain and frozen system prerequisites.
The broad utility builder expects the already built Model 4 resident/boot/CCP
artifacts; a fresh empty build directory is not a complete system build.
Run `tools/build_utilities.py` after preparing those prerequisites, and explicitly
build SEARCH, TED and monitor/codec programs through their existing builders.
TED's default development output is not the Utilities staging directory; use
`python3 tools/build_ted.py --output build/utilities` when testing that inventory.

```sh
python3 tools/build_z80pack_bye.py
python3 tools/build_dasm.py
python3 tools/build_crc.py
python3 tools/build_md5sum.py
python3 tools/test_shared_ui.py
python3 tools/test_shared_ui_format.py
python3 tools/test_shared_ui_screen.py
python3 tools/test_shared_ui_layouts.py
python3 tools/build_native_shared_ui.py
python3 tools/test_z80pack_bye.py
python3 tools/test_dasm_shared_choice.py
python3 tools/test_checksum_prompt_transport.py
python3 tools/test_crc.py
python3 tools/test_md5sum.py
python3 tools/test_dasm.py
python3 tools/build_native_crc.py
python3 tools/build_native_md5sum.py
python3 tools/test_native_remaining_help.py
python3 tools/test_utility_finalization.py
python3 tools/test_remaining_utility_help.py
python3 tools/test_utility_prompt_help.py
python3 tools/test_utility_ui_inventory.py
python3 tools/component_registry.py --check
```

The evidence archive retains exact additional commands/logs. CONFIG's legacy
choice qualification explicitly expects dual-platform validation/IOBYTE records;
build with `tools/build_disk_utilities.py --config-extra-resident
build/z80pack/resident.bin --config-extra-spt 128`, alongside that resident's
matching `bios.lst`. Default single-platform output is a different fixture.

For the focused media campaign, SYSTEMS is a directory containing the existing
paired `z80pack/report.json` and `trs80gp/report.json` plus their identified images.
The run here used `../BetterCPM-release-push/build/rc564-systems`.

```sh
python3 tools/test_ui_integration_media.py --system "$SYSTEMS" --platform cpmsim --output build/ui-cpmsim
python3 tools/test_ui_integration_media.py --system "$SYSTEMS" --platform model4 --prepare-only --output build/ui-model4-prepared
```

Model 4 **execution remains blocked**, preflight code 1100. From a normal Terminal,
run the full command below with a fresh output directory; it performs independent
readback and filesystem validation after the emulator exits. Running only a
prepared invocation does not complete those assertions.

```sh
python3 tools/test_ui_integration_media.py --system "$SYSTEMS" --platform model4 --output build/ui-model4-executed
```

## Remaining decisions and verification

1. TED approval is resolved: immediate Y/N/default-No/invalid-retry conversion is
   implemented and covered by current host/cpmsim and native assembly evidence.
2. Execute changed artifacts under Model 4 and inspect captured screens. Prepared
   inputs and historical receipt applicability are not native qualification.
3. Close remaining per-utility malformed/combination verification cells before
   claiming complete suite-wide conformance. Broader release conformance and
   packaged release acceptance remain separate.

This branch is suitable for engineering review as a draft. It is not presented
as satisfying the assignment's complete-and-ready-to-merge criterion.


## Approved TED follow-up

The maintainer approved the proposed TED behavior change. Revision 004 now uses
the existing choice controller for overwrite/protection, recovery, abandonment
and substitution. Enter selects No; invalid input retains the question; Y/N are
immediate; ESC/Ctrl-C cancels locally. No skips one substitution and Cancel stops
further matches. Text editing and command aliases remain unchanged.

The [TED qualification](TED%20Shared%20Choice%20Qualification.md) records 318 current
frontend cases, 105 command cases, publisher/workspace/text regressions, exact
ZSM4/LINK parity and two real cpmsim campaigns with independent target/backup
readback. TED grows by 192 bytes within its existing allocation, and Utilities
retains 2 KiB free. Updated user/native scripts no longer send Enter after Y/N.
Current [evidence](evidence/2026-11-03-ted-choice/results.json) supersedes TED 003
receipts for this scope; original evidence remains historical. Model 4 execution
still fails host preflight 1100, so the PR remains a draft pending that execution
and the matrix's other outstanding verification. No further TED behavior approval
is requested.
