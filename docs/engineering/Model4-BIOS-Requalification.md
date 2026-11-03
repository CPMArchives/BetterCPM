# Model 4 BIOS requalification after merge

Status: selected cpmsim and new Model 4 native checks pass; release acceptance
remains pending, 2026-11-03. No further run of this completed batch is requested.

PR #574 merged the keyboard correction into main at
`232f059a032b58a4079d394c35a81a164f393da3`, after the audit and UI fixes.
This isolated follow-up branch, `codex/model4-requalification`, carries the
keyboard capture-parser correction and reconciles derived ROM metadata/tests.
It changes no production assembly source relative to that merged main.

## Fresh candidate identity

Both System disks were freshly prepared from source commit
`0bd7f127ebca849fe613c7a36b3cd9c1c38314a8`, using the existing pinned runtime
whose executable hashes were independently verified. Build snapshots are
separate for each platform. The authoritative preparation reports and raw
regression evidence are retained with
`evidence/2026-11-03-model4-requalification/summary.json` and its archive.

| Artifact | SHA-256 |
|---|---|
| Model 4 System DMK | `83e9ac2daa566312d5825a39d0f0ac4e3ef04cf83446aac7b493db30640edc5d` |
| cpmsim RAM System DSK | `e44e39f9dd938da9039853296867ea8b099fc93e8389dd19d138794d7569169b` |
| Model 4 BIOS, 757 bytes | `c7b8150ce55ae151880de64ab38ed4f873d3080ea5589be090253a1461a8ab4c` |
| cpmsim BIOS, 623 bytes | `989ee082cfaa644cd89a4b031198dd6a01fc35fb923978fb06d9b39c569ff8c2` |

The Model 4 BIOS is identical to the manually tested draft. The new distribution
also includes the separately merged audit/UI changes, so the old application
screens and old release conformance are not full-image acceptance for this disk.
The later audit follow-up assigned BIOS 1.14 revision 002 to both recorded
BIOS binaries. [Assignment and replay procedure](AUDIT-BLOCKER-CORRECTIONS.md#audit-follow-up-on-3-november-2026)

## ROM metadata and exact expectations

The first clean preparation stopped at an ownership consistency check. The
ROM RAM-map copy sources still named E3BBh for BDOS live state and EB54h for
cpmsim BIOS disk state. The assembled/ownership addresses are E3BCh and EB64h.
Only those source fields changed; destination placements and sizes did not.

The next preparation exposed stale exact reference-count assertions. Comparison
with the previous inventory identifies precisely two removed BIOS ROM operands:
one duplicate `JP MC_CALL` and the cursor dispatch now using JR. No RAM operand
is lost. Expected BIOS references therefore change from 124 to 122, and total
packed-code references from 790 to 788. All 105 CONFIG references remain.
The merged BDOS change shifts the packed BIOS entry by one byte to F1AFh.
The exact relocation expectations were refreshed to the measured layout while
retaining independent checks of every operand, both shifted assemblies, inverse
relocation, and the absence of changes outside inventoried operands.

The successful third preparation passes the ROM ownership, RAM-map, template,
cold-initializer, packing, reference-inventory and relocation checks. All targets
resolve; unexplained changed bytes are zero. This does not claim protected XIP
execution qualification. The RAM map remains 2256 object bytes plus 156 reserved
bytes, with a DF00h ROM boundary; no memory expansion was introduced.

## Fresh observations

The cpmsim image passes filesystem/file-integrity/config-fingerprint checks and
boots through the pinned runtime. Seven returning groups pass: BIOSTEST 5,
ERRTEST 5, ENTRYTST 25, CCPTEST 12, DISKTEST 7, FILETEST 28 and RANDTEST 39.
That is **121 passing assertions, zero failure/error rows**, with 23 observation
rows and 100 excluded/not-run rows kept separate. This is not a rerun of all
627 cards or the previous full reconciliation.

ADM3A, VT52 and ANSI provider/backend regressions pass, including rendered
controls, completion, unload/53K, filesystem checks and shipped-file preservation.
Ordinary full-TPA batch and XSUB full-TPA input/reconstruction checks also pass.
The instruction-level keyboard/rollover/loader/IOBYTE, 17 BIOS-vector contracts
with all 80 reads/writes and errors, and both platform monitor-hook checks pass
against the fresh build artifacts.

Two initial monitor invocations used unsuitable relative paths and are unscored;
the final absolute-path invocation passed all three personalities. Earlier
failed preparation attempts are retained as build diagnostics, not accepted media.

The new Model 4 image passes host media integrity checks. The agent-side
launcher preflight returned LaunchServices 1100 before starting an emulator.
The maintainer then started the combined desktop Terminal batch, which completed
without subsequent operator input. Its eleven group summaries total **269 pass,
zero fail and zero error**. ADM3A, VT52 and ANSI provider checks all pass,
including their shipped-file audits, unchanged system tracks and clean
filesystems. All results bind to the new Model 4 image hash above.

The reviewed receipts and captures are retained in
`evidence/2026-11-03-model4-requalification/native-qualification-evidence.tar.gz`,
with a separate member hash manifest and `native-model4-conformance.json`.
Both new images and the earlier candidate were rehashed after qualification;
their original hashes are unchanged. The earlier 269 passes remain historical
evidence; this is a distinct 269-pass run on the new image.

The consolidated source/contract assessment is
`Model4-Lowercase-Final-Code-Review.md`. It records the build-matched M4SCRN
publication requirement, component-revision decision, and a retained pending
input/status discrepancy reproduced in both BIOS generations for separate
post-1.0 investigation. No additional production fix is proposed here.

## Completed desktop Terminal batch: reproduction reference

The completed run used a normal macOS Terminal. Each harness uses private media. This command
block runs the previously reviewed Model 4 batch and the three provider checks;
it does not replace the frozen candidate or publish a release.

```sh
kb="$HOME/.codex/.chatgpt-projects/g-p-6a682f002be881918281554d644daf48/BetterCPM-model4-requalification"
out="$HOME/Downloads/model4-bios-requal-$(date +%Y%m%d-%H%M%S)"

python3 -B "$kb/tools/run_release_model4_conformance.py" \
  --baseline "$kb/build/model4-requalification-systems-v3/trs80gp" \
  --suite "$kb/../BetterCPM-release-push/build/rc564-conformance-suite" \
  --output "$out/conformance"

for monitor in ADM3A VT52 ANSI; do
  python3 -B "$kb/tools/run_validation_model4_monitors.py" \
    --baseline "$kb/build/model4-requalification-systems-v3/trs80gp" \
    --monitor "$monitor" --scripted-start \
    --output "$out/monitors"
done
```

The individual receipts and screens were inspected before counting these native
passes. Ordinary physical host CAPS quick taps remain unconfirmed; scripted
matrix input does not settle the earlier host-key behavior. This limitation
does not imply a newly demonstrated production defect or require rerunning the
completed batch. Physical-host follow-up and release acceptance remain separate
maintainer decisions.

The earlier candidate `6d6c103507ce8558700b3b8e412ac500de361226` and its evidence
remain intact. Its Model 4 distribution hash was rechecked as
`4105ff45e411e25c0f3cd6024b970ddc231e6287086a553933e1fb577aaf2467`.
