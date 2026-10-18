# Step 7 utility-validation reconciliation — 18 October 2026

## Decision

**Step 7 is not closed. Exactly four named utility items remain below.** Seven
other utility groups have sufficient selected operational/recovery evidence for
this step. There is no unresolved production utility defect identified by this
reconciliation. The blockers are missing audit bundles and a supported-device
coverage gap; neither justifies another open-ended utility campaign.

This is the original eleven-step plan's **Step 7, utility operations and failure
recovery**, equivalent to stage 5 in the campaign's condensed table. The condensed
stage 7 is a different, end-to-end workflow stage. Previous progress reports mixed
these boundaries and repeatedly carried broader validation work under Step 7.
This decision supersedes those broad statements, without changing historical
results or declaring system acceptance.

The evidence audit inspected 34 result records: 29 retained files report PASS;
five historical records are unavailable. It records paths, verdicts and SHA-256
identities in
[SYSTEM-VALIDATION-STEP7-EVIDENCE-2026-10-18.json](SYSTEM-VALIDATION-STEP7-EVIDENCE-2026-10-18.json).
This is a result-record/coverage reconciliation, not re-execution of those tests
or an independent reanalysis of every raw capture.

## Requirement-to-evidence matrix

| Utility group | Required operations and boundaries | Evidence and Step 7 disposition |
| --- | --- | --- |
| DIR/STAT | Logical files vs physical extents; attributes; multi-extent accounting; /WHEREIS scopes and incomplete searches | V026 shipped-image and controlled error/capacity checks. **Satisfied for this step.** |
| COPY/MOVE | Exact/wildcard copies; collisions; verification; attributes; source deletion; partial-output and failure handling | V024/V025 shipped operations and controlled read/write/close/verification/cleanup failures. **Satisfied for this step.** |
| PIP | Copy/concatenation/transforms; device routing; guarded replacement, verification and interruption | V030 retained shipped/DRI-reference and controlled-device/error checks pass. Actual supported host endpoints were not exercised in this campaign. **Open S7-04.** |
| ERA | Protected-file selection and confirmations; accounting; destructive block zeroing and directory scrub; shared-block preservation | V021 records passing protection/destructive campaigns, but their raw audit bundles disappeared before V023. **Open S7-01, evidence restoration.** |
| REN | Templates, collisions, multi-DU selections, attributes and partial-failure/recovery policies | V023 retained shipped operations and four controlled suites. **Satisfied for this step.** |
| TYPE | Paging, file boundaries, both navigation directions, EOF and read failures; actual emitted bytes | V027 shipped and controlled navigation/read recovery; V041 resident behavior; V042 native byte capture. **Satisfied for this step.** |
| ED | Edit/insertion/transfer workflows, work/backup lifetime, save/exit, full disks/directories and corrected DRI failures | V028 controlled matrices, plus seven V036 native protection/full-media/rename recovery cases. **Satisfied for this step.** |
| CONFIG | Inspect/pending/default/startup/IOBYTE workflows; activation, save, validation and rollback | V028 controlled failure/CRC/IOBYTE checks and V035 native combined-save/third-write rollback/cold activation. **Satisfied for this step.** |
| DUP | Interactive/CLI operation, geometry, refusal/confirmation, format/copy/check and CRC recovery | V017–V019 record passing shipped and controlled cases; their raw bundles are unavailable. **Open S7-02, evidence restoration.** |
| SYSGEN | Disk and named-package installation/export, validation, confirmations, recovery files and installed boot | V017/V018/V020 record passing workflows and controlled error/parser matrices; their raw bundles are unavailable. **Open S7-03, evidence restoration.** |
| SUBMIT/TIME/VER/CPX/RSX | Operational/version/provider behavior, batch continuation/cleanup, manager refusal/recovery and memory restoration | V029–V034 retained operational and failure checks. XSUB console fallback and malformed optional CPX findings are corrected and qualified, not still-open defects. **Satisfied for this step.** |

The evidence supports selected representative workflows and controlled fault
matrices, not every possible media fault or a Cartesian product of all cases
on both emulators. V034 manifest comparison confirms DIR, REN, COPY, ERA, TYPE,
ED, PIP, DUP, SYSGEN and RCP are byte-identical across platforms. Combined with
native BIOS/filesystem/return checks and selected native utility repetitions,
this permits reuse of their platform-independent instruction-level and cpmsim
behavioral evidence. It does not turn a cpmsim execution into a native execution
or validate a platform's device routing. The audited V023 and V034 cpmsim manifests also retain identical utility/RCP
binaries, including CONFIG, preserving the earlier instruction-level utility
evidence across the loader fix. CONFIG differs between platforms and has its
separate native save/rollback/cold-boot evidence.

## Finite remaining checklist

| ID | Work required | Completion evidence |
| --- | --- | --- |
| S7-01 | Restore the V021 ERA protection and destructive/shared-block campaigns on private, hash-identified current disks. Retain the executed sources and results. | Protected files/confirmation/accounting match the contract; allocated blocks and scrubbed entries are independently inspected; shared blocks and survivors remain intact; shipped-file and filesystem audits pass. Reuse `run_validation_cpmsim_era.py` and `run_validation_cpmsim_era_destructive.py`. This restores lost evidence, rather than asserting V021 failed. |
| S7-02 | Restore DUP's V017–V019 selected operation and CLI/refusal/recovery evidence. | Retained cpmsim format/copy/check and native geometry/CRC/decline checks, with required 53K precondition, exact target/source comparisons, protected-drive refusal and clean filesystem/shipped-file audits. Reuse existing media/CLI tools and `run_validation_model4_dup.py`; no requirement to repeat every option on every target. |
| S7-03 | Restore SYSGEN's V017/V018/V020 package/disk-source and controlled recovery evidence. | Named export/install and disk-source install, confirmations/alias protection, package/recovery-file refusals and controlled failure/parser checks; exact package/system bytes, unchanged containing filesystem/sentinel and installed cold boot. Reuse the existing cpmsim/native SYSGEN runners and export/command-line suites. |
| S7-04 | Exercise actual supported cpmsim PIP printer/punch/reader routing, and the selected native disk/CRT/unsupported-device path against campaign-identified binaries. | Exact host output/input bytes, EOF and IOBYTE restoration; unavailable native aliases rejected before destination mutation; verified disk copy/CRT output; final caller/media/file audits. Adapt `test_pip_endpoints_media.py` and `test_pip_model4_media.py`. Their pre-campaign qualification is a reference, not a fresh campaign pass. |

The V023 loss is explicitly documented in the campaign ledger. A historical
recorded PASS is not a currently retained raw bundle. Restoring those three
bundles is a bounded evidence repair; it must not be described as three newly
discovered implementation projects. Conversely, controlled PIP device fixtures
cannot be used to claim actual host endpoints worked.

Do not add blanket native repetition, exhaustive hardware permutations or new
optional features to this checklist. A new failing result may require a specific
fix and regression, but must be identified as a new finding rather than folded
silently into an expanding “last bit.” Once S7-01 through S7-04 have accepted
results and no unresolved utility-contract findings, **close Step 7**.

Run those restorations against a clean merged build where practical, so they
can also supply final acceptance evidence if no relevant code changes afterward.
Do not require two identical utility reruns solely because two phase labels apply.

## Remaining work outside Step 7

- Reconcile BIOSTEST/ERRTEST documentary cards, unavailable-drive/physical-error
  profiles and other conformance requirements under the conformance stage.
- Review monitor rendering, terminal/keyboard observations and the V040 input
  anomaly under console/monitor/platform validation. The anomaly's cause remains
  unassigned; successful later entry is not proof of a fix.
- Review actual clock providers/platform capabilities under device/profile
  validation. TIME's controlled parser/provider/unsupported-SET behavior is
  already covered; do not change the real host clock to claim a utility pass.
- Complete end-to-end release workflow closure where required.
- Rebuild and rerun acceptance against the final clean merged revision. This is
  the final acceptance stage, not a permanent reason to leave Step 7 partial.
- Documentation alignment follows system validation. Utilities Disk and CP/M
  Tools Disk qualification remain separate, as agreed.

Separating these items is not a waiver or a pass. In particular the live PIP
endpoint requirement stays in S7-04; it is not moved out merely to close a gate.
