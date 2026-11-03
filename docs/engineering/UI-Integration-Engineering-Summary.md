# Shared UI integration engineering summary

3 November 2026. PR #571 is merged at
`bd4df2cd9f0a7a2edfa12112a8c02151eea5b90d`. Its bounded current-payload
Model 4 gates pass. The [argument-validation follow-up](UI-Argument-Validation-Followup.md)
fixes four discovered no-operand gaps and closes 28 malformed-tail evidence cells;
its host/build/cpmsim and current-payload 22-phase Model 4 gates pass.
Six development-only operational-tail entries remain explicitly outstanding.
No core, BIOS, resident RCP or historical third-party reference source was changed.
No new utility feature/library was introduced. Overall completion is not yet claimed.

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
The follow-up corrects the old monolithic query fixture: page zero now has a
real JP BDOS gateway so guarded programs see a valid TPA ceiling, and the existing
console collector handles both string and character output. All 314 checks now
pass. ED/SYSGEN expectations use the canonical full identification block. Earlier
fixture failures are retained separately in the follow-up archive.

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

### Completed Model 4 checksum and DASM campaign

The maintainer ran the full corrected command from a normal Terminal, with output
`ui-model4-submit-20261103-121633`. It passes all twenty executed/captured phases
on the reference system SHA-256
`4105ff45e411e25c0f3cd6024b970ddc231e6287086a553933e1fb577aaf2467`.
The command-script hash matches the independently exercised cpmsim protocol.
All six help/version outputs and the expected prompts/markers were reviewed;
checksum refusal/local Ctrl-C and DASM restart refusal complete normally.
Original payload/input/list readback, new checksum lists, system area and
filesystem checks pass. Binary hashes match the measured artifacts above.

[Receipt](evidence/2026-11-03-model4-pass/results.json),
[captures/readback/logs](evidence/2026-11-03-model4-pass/receipts-and-logs.tar.gz)
and [checksums](evidence/2026-11-03-model4-pass/SHA256SUMS.txt) retain the result.
This closes this bounded native gate for CRCKSUM/MD5SUM/DASM. The runner's generic
scope text mentions cpmsim BYE cancellation; BYE is not part of this Model 4 run.
TED native execution and whole-release acceptance remain separate gates.

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

This agent's Model 4 launch remains blocked by preflight code 1100; the maintainer's
normal-Terminal execution above passes. To reproduce, run the command below with
a fresh output directory; it performs independent
readback and filesystem validation after the emulator exits. Running only a
prepared invocation does not complete those assertions.

```sh
python3 tools/test_ui_integration_media.py --system "$SYSTEMS" --platform model4 --output build/ui-model4-executed
```

## Remaining decisions and verification

1. TED approval is resolved: immediate Y/N/default-No/invalid-retry conversion is
   implemented and covered by current host/cpmsim and native assembly evidence.
2. The changed-payload Model 4 gates now pass: checksum/DASM and both TED
   campaigns, with captured-screen and independent file/backup checks. Whole
   release packaging/conformance remains a separate acceptance boundary.
3. The follow-up closes the released-command malformed-tail review with bounded
   tests or documented existing language/host exceptions. Six development-only
   entries remain O. The four changed follow-up executables now pass their
   22-phase Model 4 execution gate. Broader release packaging acceptance remains separate.

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
receipts for this scope; original evidence remains historical. TED Model 4 execution
has passed both `choices` and corrected `choice-scope`; the PR remains a draft
pending the matrix's other outstanding verification. No further TED behavior approval
is requested.

### TED Model 4 choices pass and substitution-fixture correction

The maintainer's `ted-ui-model4-20261103-123016/choices` run passes on TED SHA-256
`5bf8ea6bd52987225c15ff880b6b80ccadfe811472c4bb9a2362516583d87e17`,
with exact target/backup verification, no premature backup generation, filesystem
checks and 54-byte private-stack high-water at TPA ceiling 50,689.

The following `choice-scope` run appeared stuck after launch. A 128-KiB RAM capture
establishes that startup and the substitution command had completed: TE_COMMAND_READ
is 1, EDITLEN is 0, the queue is empty and the private stack is in TE_PROMPT/TE_READ.
TE_FIELD at 53CDh contains `SU M /ONE/X/`, while the input file is lowercase
`one one one one`. `key_args` uppercases physical letters; the script waited for
a replacement question after a case-sensitive search which had no matches.
The previous inference that TED was stuck in startup was incorrect.

Only the harness fixture, search and expected bytes change to matching uppercase
on both platforms. The corrected cpmsim run passes, saving exactly
`ONE X ONE ONE\r\n` plus padding, retaining the original backup, with intact
guards and filesystems. TED production bytes, BIOS case behavior and core are
unchanged. Native execution of that corrected fixture now passes as recorded below.

```sh
python3 tools/qualify_ted_editor.py --system "$SYSTEMS" --utilities "$UTILITIES" --output "$OUTPUT" --platforms z80pack --cross-smoke --scenario choice-scope --identity-state auto
```

[Receipts and RAM diagnosis](evidence/2026-11-03-ted-model4-choices/results.json)
and [retained captures/readback](evidence/2026-11-03-ted-model4-choices/receipts-and-logs.tar.gz)
separate the successful campaign, failed harness attempt and corrected host run.

### Completed native TED substitution scope

The maintainer's `ted-scope-model4-20261103-125254` run passes on the same TED
payload, after correcting the fixture case only. Eleven captures show the
expected replacement/overwrite questions and return path. No skips the first
match, Yes replaces the second, Ctrl-C stops before the third/fourth; readback
is exactly `ONE X ONE ONE\r\n` plus padding. The original
`ONE ONE ONE ONE\r\n` backup is retained. Filesystem and canary checks pass;
stack high-water is 52 bytes at exclusive TPA ceiling 50,689.

[Receipt](evidence/2026-11-03-ted-model4-scope/results.json) and
[captures/readback](evidence/2026-11-03-ted-model4-scope/receipts-and-logs.tar.gz)
close the second bounded native TED gate. This does not close outstanding
malformed/combination cells or assert whole-release qualification.

## Four-utility follow-up: Model 4 gate closed

The maintainer's 3 November 2026 run at
`/Users/nathanael/Downloads/ui-noargs-model4-20261103-143246` passes all 22
phases with the current ADMTST/ANSITST/VT52TST/XSUB hashes. Eight queries,
twelve invalid invocations, normal XSUB installation and RSX LIST are captured
with unique completion markers. Payload and BATCHIO readback, both filesystems
and the reserved system area pass. All 22 captures, output checks and exact
payload/source hashes were reviewed before archiving the
[native receipt and file hashes](evidence/2026-11-03-ui-noargs-model4-pass/results.json).

The [follow-up record](UI-Argument-Validation-Followup.md) gives the exact
reproduction command and memory comparison. Its native gate is complete;
#573 is reviewable without another native run for these unchanged payloads.
Six development-only operational-tail O entries and missing historical UNLZH
fixtures remain recorded. No release images were refreshed or main merged here.
