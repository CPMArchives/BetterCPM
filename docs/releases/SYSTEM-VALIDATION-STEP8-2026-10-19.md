# Step 8 — monitors and representative applications

Started 19 October 2026 after V044 closed Step 7. This is original Step 8,
equivalent to stage 6 in the condensed campaign table. Overall acceptance
remains open. Utilities Disk and CP/M Tools Disk are outside this campaign.

## Remaining phase order

1. Step 8: monitors and representative applications.
2. Step 9: complete release workflows, including installation/configuration.
3. Step 10: fix findings and run appropriate regressions.
4. Step 11: final clean merged-source builds, acceptance and result accounting.

The utility-failure paragraph preceding the monitor section in the maintainer's
list belongs to closed Step 7. Retain its evidence and run affected regressions
if new findings justify them; do not reopen it as a duplicate campaign.
Documentation alignment follows system validation, followed by completing and
separately qualifying the Utilities Disk and CP/M Tools Disk.

## Evidence and baseline

V013/V014 record historical three-personality regressions, but their named raw
temporary directories are absent at this review. They remain recorded results,
not currently retained raw evidence. Refresh the six selected shipped-image
pairs and preserve the new bundles outside temporary storage before closure.
Use the V044 clean committed baseline (`5f3f3f38bb11`), whose runtime files are
unchanged by the subsequent validation/roadmap edits. Final merged-revision
acceptance remains Step 11; do not label this baseline as that final revision.

## Finite checklist

| Item | Required evidence | Initial status |
| --- | --- | --- |
| S8-01 | Shipped ADM3A, VT52 and ANSI with M4SCRN: dedicated test completion, native screen-memory attributes/position/erase/reset assertions, loaded-pair identity, unload and 53K restoration, shipped-file/filesystem audits | RUNNING: run_validation_model4_monitors.py, three personalities |
| S8-02 | Same three personalities with ANSISCRN: captured host bytes, software-terminal rendering, protocol-specific queries, parser reset and unload/53K, file/filesystem audits | RUNNING: run_validation_cpmsim_monitors.py |
| S8-03 | Map documented screen subsets to executable evidence for wrap, scrolling/margins, rendition, cursor, malformed/incomplete sequence handling, switching and backend limits. Reuse current matching binary tests where retained; add only concrete missing checks. Explicitly distinguish Model 4's 80x24 monochrome display and software-terminal oracles from physical-terminal observations | OPEN: contract/evidence matrix |
| S8-04 | Representative unmodified terminal applications with appropriate configurations: identify original binary/configuration and hashes, actual edit/save/return and independent saved-content checks. Retain native and host-backend evidence as appropriate; shipped TYPE/ED alone do not substitute for third-party application compatibility | OPEN: inspect available WordStar/TE fixtures and adapt qualification without replacing shipped providers |
| S8-05 | Revisit the unassigned V040 native command-entry anomaly with bounded fresh entry/return checks. Record any physical terminal, keyboard or audible behavior still requiring an operator, with exact profile and reason; no blanket manual PASS or exclusion | OPEN: profile/review |

These items do not promise every historical terminal command or every application
on every platform. A failure creates a named finding and focused regression;
unsupported behavior is classified against the documented subset, never silently
counted as a pass. Old audit prose is not assumed to be current implementation
status without checking its later integration/qualification records.

## Completion

Close Step 8 when the five items are accounted for with retained passing evidence
or explicit justified applicability/accepted-limit decisions, and no unresolved
release-blocking monitor/application finding remains. Native captures, CPU-model
results, host wire data and physical observations must remain distinguishable.

## V045 initial results — 19 October 2026

Step 8 remains OPEN. Accepted raw evidence is preserved outside temporary storage
with a per-file-verified archive; see
[SYSTEM-VALIDATION-STEP8-EVIDENCE-2026-10-19.json](SYSTEM-VALIDATION-STEP8-EVIDENCE-2026-10-19.json).

- S8-01: ADM3A/M4SCRN native captures pass all seven page/keyboard/unload
  assertions plus shipped-file/filesystem audits. Completed captures were
  reaudited without rerunning the emulator. VT52 and ANSI are still running;
  no result is assigned until screen and integrity audits finish.
- S8-02: all three actual cpmsim personality/ANSISCRN runs PASS. Loaded identity,
  rendered position, protocol-specific queries/controls, dedicated test
  completion, full unload/53K and all 30 shipped-file audits pass.
- S8-03: production carrier hashes match the distribution manifests; each tested
  payload is also compared to the payload embedded at offset 512 in its carrier.
  Both backends and two relocation placements pass ADM3A wrap/backspace/scroll,
  reverse blank fills, line insert/delete, parser reset and visibility;
  VT52 right/bottom margins, scroll/reverse-scroll, EOL/EOS erase and reset;
  and 340 ANSI streams covering position/default parameters, SGR/save/restore,
  visibility, incomplete/malformed/oversized sequences, cancellation and regions.
  ANSI-host 80x25/100x40 geometry checks are software-terminal results, not an
  extra physical Model 4 row. Six actual-manager instruction-level lifecycle
  cases (three personalities, two BIOS builds) PASS movement/state retention,
  public lookup, backend dependency and unload/TPA restoration. Native display
  results remain distinct from these CPU-model checks.
- S8-04: unchanged VT52 WordStar COM and overlays from the archived reference
  disk PASS actual cpmsim opening/edit/save/return, saved-document inspection,
  unload/53K and unchanged shipped-file/filesystem checks. Unchanged historical
  MM CONFIG 3.10 plus DISK.FDF PASS the native Model 4 opening-menu screen,
  screenshot and shipped-file/filesystem audits through default ADM3A/M4SCRN.
  The screenshot was visually inspected: heading reverse video and menu layout
  agree with the screen-memory capture.
  The emulator intentionally exits at that menu; MM configuration writes and
  application exit behavior are not claimed. These are two selected external
  application witnesses, not every application/protocol combination. TE's old
  25-row host result is not reused as Model 4 compatibility evidence.
- S8-05 remains OPEN. Native host-entered SUBMIT attempts at 12- and 25-unit
  timing produced no loaded-pair capture and are excluded as incomplete, with
  input cause unassigned. They establish no monitor verdict. The retry selects
  the exercise via a declared STARTUP.SUB fixture, preserving all other shipped
  files; this removes initial host command entry from display qualification but
  does not fix or close the input observation. The successful native MMCONF
  entry and ADM3A keyboard test are positive witnesses, not proof that the
  intermittent input issue is resolved.

Next bounded work: finish native VT52/ANSI screen audits, reconcile documented
subsets/platform limits against the evidence above, and complete the input and
operator-profile disposition. Physical terminal/keyboard and audible outcomes
must be explicitly accounted for where part of the applicable contract. No
production OS or monitor code changed in V045.

The first startup-script retry exposed a capture-ordering race: the dedicated
test could clear the RSX listing before its capture gate. A supplemental
one-character pause after RSX LIST now separates identity capture from the
screen exercise. Those incomplete attempts are excluded as harness evidence,
not monitor failures. This does not resolve the separate initial host-command
entry observation.

The pause fixture also announces `MREG READY` before the harness injects its
continuation key, preventing a second race while the helper loads. Initial
results remain partial; native VT52/ANSI are not counted from loaded-pair
captures alone.
