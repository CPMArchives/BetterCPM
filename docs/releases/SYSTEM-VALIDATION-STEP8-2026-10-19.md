# Step 8 — monitors and representative applications

Started 19 October 2026 after V044 closed Step 7. This is original Step 8,
equivalent to stage 6 in the condensed campaign table. Overall acceptance
remains open. Utilities Disk and CP/M Tools Disk are outside this campaign.

## Current decision — V047

**Step 8 CLOSED, 19 October 2026.** All five finite items are satisfied for the
selected emulator/subset/application scope. The initial and intermediate statuses
below remain historical progress records; the final disposition is at the end.
No unresolved release-blocking monitor/application finding was identified.
Overall system validation and final merged-source acceptance remain open.

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

| Item | Required evidence | Current status |
| --- | --- | --- |
| S8-01 | Shipped ADM3A, VT52 and ANSI with M4SCRN: dedicated test completion, native screen-memory attributes/position/erase/reset assertions, loaded-pair identity, unload and 53K restoration, shipped-file/filesystem audits | PASS — V045/V046: all three native pairs |
| S8-02 | Same three personalities with ANSISCRN: captured host bytes, software-terminal rendering, protocol-specific queries, parser reset and unload/53K, file/filesystem audits | PASS — V045: all three cpmsim pairs |
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

## V046 — native VT52 and ANSI display checks complete

Both remaining native personalities PASS using unchanged shipped providers:
`bettercpm-v045-r5-native-monitors/vt52-2gk8vx00` and
`bettercpm-v045-r5-native-monitors/ansi-6luy6xgj`. Their complete result records
and archive hashes are in the [evidence index](SYSTEM-VALIDATION-STEP8-EVIDENCE-2026-10-19.json).

- VT52: five captures verify loaded VT52/M4SCRN identity, row-5/column-10
  positioning, tab/right-margin behavior, parser reset, EOL/EOS erasure,
  test completion, both providers unloaded, 53K restored and a subsequent
  independent completion witness.
- ANSI: four captures verify ANSI/M4SCRN identity, positioning, reverse bits
  only on the selected word, erased suffix, parser reset, test completion,
  full unload/53K and the independent witness.
- Read-only reaudits of both retained captures/media PASS. All 28 shipped files
  other than the declared STARTUP.SUB fixture match baseline hashes and bytes;
  system tracks remain exactly unchanged, filesystems pass independent checks,
  and immutable original images retain their qualified hashes. Loaded TPA is
  50K for VT52/M4SCRN and 49K for ANSI/M4SCRN; both restore 53K on unload.
- The private guest queue, supplemental one-key pause and completion witness
  are recorded fixtures. MREG READY gates input only after the pause helper has
  loaded. Their presence is not a change to the shipped OS or provider payload.

S8-01 and S8-02 are satisfied for the selected six-pair display regression.
The native archive is saved outside temporary storage, reopened and verified
against every file hash, including the excluded incomplete retry artifacts.
Screen-memory assertions are actual native-emulator results, not substituted
CPU-model or physical-terminal claims. Step 8 remains OPEN for final subset/
application/profile disposition and S8-05 input/operator review. The guest
startup fixture avoids initial host command-entry timing; it does not establish
that the separate V040 input anomaly has been fixed.

## V047 — final requirement and profile disposition

| Item | Disposition | Evidence and limits |
| --- | --- | --- |
| S8-01 | PASS | All three native personality/M4SCRN pairs complete their dedicated exercises, screen-memory assertions, parser reset and unload/53K; independent filesystem/file audits pass. |
| S8-02 | PASS | All three actual cpmsim/ANSISCRN pairs complete their exercises, protocol queries, captured-wire/software-terminal assertions and unload/53K. |
| S8-03 | PASS, documented subsets | Both-backend relocated production protocol matrices and six actual-manager lifecycle cases cover wrap/scroll/margins, rendition/cursor, bounded parser cancellation/reset and movement. Additional manager-selection cases pass on both BIOS builds. Host BEL output is exactly 07h for all three personalities; three separate native recordings each contain exactly 512 threshold transitions, with emulator sound effects muted. |
| S8-04 | PASS, selected external applications | Unchanged VT52 WordStar opens/edits/saves/returns on cpmsim, saved bytes are inspected, and unload restores 53K. Unchanged MM CONFIG opens its native ADM3A menu correctly; writes and MM-specific configuration are outside this witness. |
| S8-05 | Bounded regression PASS; historical observation retained | Basic console and ADM3A/M4SCRN each receive exact A0:MEDIA + CR bytes at 12, 25 and 60-unit timings. All six samples contain colon 3Ah. Qualified A0:VER /VER executes afterward; Backspace repairs RSX LISX to RSX LIST; complete unload restores 53K. The old intermittent anomaly is not reproduced, not assigned a cause, and not claimed fixed. |

### Contract coverage and explicit limits

- Position, basic movement and erasure combine actual native pages with host
  wire/rendering assertions. ADM3A wrap and reverse blank fills, VT52's clamped
  right margin and bottom/reverse scroll, and ANSI margins/save/rendition and
  malformed-sequence handling have independent production CPU-model checks.
- Model 4 remains a physical 80-column, 24-row monochrome rendering target.
  Native reverse cells are checked; canonical ANSI styles/colors are not a
  promise of physical colors or a 25th row. The host backend's larger-geometry
  assertions use a software terminal. The old 25-row TE configuration is not
  promoted to Model 4 compatibility evidence.
- Personality selection/rejection, movement and preserved parser state are
  checked through the actual production manager in instruction fixtures;
  synthetic selection providers are labeled as such. Dedicated native and live
  cpmsim exercises establish real provider binding, return and unload behavior.
  These are selected combinations, not an exhaustive protocol/application matrix.
- Native audio recordings verify generated waveforms rather than merely nonzero
  audio. No physical-speaker loudness, human hearing, real Model 4 hardware or
  arbitrary physical terminal certification is claimed. Actual cpmsim PTY wire
  and software-terminal results remain distinguished from those profiles.
- Matrix-key injection exercises guest input and CCP editing, not the user's
  macOS modifier remapping or every host keyboard layout. The historical V040
  observation stays in the campaign as not reproduced. The final acceptance
  pass must include the same focused input regression; no production fix is
  inferred merely from success at a slower timing.

### Final evidence and exclusions

The [evidence index](SYSTEM-VALIDATION-STEP8-EVIDENCE-2026-10-19.json) now records
18 hash-verified accepted PASS results and three durable raw archives. The V047
archive contains native input captures/probe sources, three complete WAVs,
executed runners, before/after media, filesystem/file audits, selection fixtures,
and the extended production protocol/BEL-wire check. It was reopened and every
archived file checked against its hash manifest.

The combined audio attempt did not reach its final marker; its partial recording
is excluded. Separate input-ready, per-personality captures all complete and
pass. The first two-target selection wrapper reused a mutable fixture request
pointer from the first target; resetting it to 0300h between targets makes both
pass. A fresh diagnostic run shows no duplicate-load changes to the retained
bytes. This is an excluded wrapper-state failure, not a production defect or an
ignored failed result. Earlier capture-ordering/input-ready retries remain
explicitly excluded as recorded in V045/V046.

No OS, monitor payload, key mapping or permanent memory allocation changed.
The frozen V044 images remain the baseline; this is not final merged-release
acceptance. Step 9, complete release workflows, is next. Broader conformance and
final acceptance accounting remain open in their proper campaign stages.

A final live cpmsim switching session also PASSes ADM3A, VT52 and ANSI dedicated
exercises in that order while retaining ANSISCRN between personalities. All
three identities are observed, no missing-provider diagnostic occurs, full
unload restores 53K, and every shipped file/filesystem audit passes. This is
actual same-session switching evidence; synthetic manager fixtures are not used
as a substitute for it. The incomplete native combined-audio queue remains
excluded, not reclassified as a passing switching workflow. Complete native
release sessions, including switching, remain part of Step 9.
