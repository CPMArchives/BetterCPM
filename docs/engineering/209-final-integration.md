# Spec 209 final integration acceptance

The integration acceptance gates pass on cpmsim and Model 4 under trs80gp.
The six rebuilt archives are review candidates. **The 1.0 package freeze
remains HOLD.** This report does not authorize release, publication or tagging.

Candidate build input is `54c503652fa957798bf2d0d636f4172851195926`.
The following evidence-only commit adds this report and receipts; it is not
the source revision embedded in those archives. Candidate checksums are in
the generated candidate directory's `SHA256SUMS.txt`.

## Findings fixed

The normal System build now includes FDB.COM and its matching FDBVIEW.OVL;
package checks require both and enough space for recoverable replacement.
The canonical Utilities build also builds FDB. Package manuals include the
workbench and qualified installation instructions.

Native command conversion exposed an exit hang: command mode inspected an
uninitialized high-memory viewer cleanup pointer. Cleanup now checks session
mode first; the 40-case converter regression poisons that pointer. Shared
catalogue runtime conversion is opt-in for FDB and CONFIG, preserving the
frozen DUP binary. Three fixed-size text changes keep full-description and
long-filename interactions within 80 columns without moving executable code.

## Acceptance gates and evidence

Receipts and captured native output are in
[the review evidence directory](../reviews/2026-11-04-fdb-final/).
`native-evidence.tar.gz` preserves the qualified campaign subsets, runner
snapshots and logs; its paths below are relative to `qualified-evidence/`.

| Gate | Result and evidence |
| --- | --- |
| Stock round trip | PASS on both emulators: native export/recompile of all 108 entries, byte identity and independent host cross-checks; `fresh-acceptance/{cpmsim,model4}-roundtrip/evidence.json`. Stock catalogue is 8,448 bytes, SHA-256 `06e2d88e30c38bebe4eaf0975a3e302086874e719109dc3898bb72a0f7ded6a5`. |
| New entry | PASS: preceding 108 entries preserved, named 109th selected in CONFIG, actual known-file read through the new binding on both platforms; `fresh-acceptance/{cpmsim,model4}-config/`. |
| Catalogue and exchange | PASS: KAYPRO.FDB import/inspect/save, unchanged source and unrelated entries, N–I–S, both encodings, single and whole exports; `catalogue-z80pack`, `catalogue-stable-trs80gp`, `cpmsim-session`, `model4-stable-session` under `fresh-acceptance/`. |
| Drive editor | PASS: capture, edit, validate, confirmed B–D apply and named save; A and cold defaults preserved. Native public-state snapshots plus final assertion logs are in `fresh-acceptance/{cpmsim,model4}-editor/` and `final-fdb-fresh-*-editor.log`. |
| Failure/recovery | PASS: malformed/checksum/extension/map/duplicate/BREAK/replacement interruption coverage in host session/editor regressions; actual native disk-full failure audits on both emulators retain the original catalogue and pending work. See `fresh-acceptance/*-diskfull/` and host logs. |
| Resources/UI | PASS: 59 session/editor cases, maximum 80 columns; peak program stack 40 of 512 bytes. Interactive address span 53,255 bytes leaves 1,017 bytes within 53 KiB; converter span 50,944 leaves 3,328. FDB.COM is 19,710 bytes; overlay 4,608. See `resources.json`, `ui-cpmsim/` and bounded Model 4 UI captures. System free space is 92 KiB/550 KiB, exceeding 10 KiB plus two directory entries needed for replacement. |
| Installation/cold boot | PASS on both platforms: actual SYSGEN export/install, named BCPM780 binding and file read, installed cold boot, saved configuration and file/reserved-area audits; `cpmsim/`, `install-model4/`. Model 4 bootstrap normalization is explicitly recorded rather than treated as unexplained byte drift. |
| Model 4 console restoration | PASS with current pair: normal 50 KiB safely refuses FDB; unload ADM3A then M4SCRN to obtain 53 KiB; run viewer/menu and quit; unmodified `SUBMIT STARTUP` restores M4SCRN then ADM3A and 50 KiB. Actual keyboard file read, cold boot/default refusal, all 32 original files and reserved tracks pass; `restore-focused/`. |
| Six archives and source | PASS: all member hashes after clean extraction, locked components and reserved areas, manuals/licenses/link closure, offline Source ZIP reconstruction of runtime, guest tools, all System components and all eight images. Separate JSON receipts accompany this report. |

## Evidence applicability and trial disposition

The full native operational and installation campaigns used source
`47d5bd86c4ba717fe04ffe7a9c3c350897984b12`. Source `03cc88a9` changes only three
fixed-size UI text blocks and the matching-pair tag/checksum. Mechanical
comparison verifies every executable byte, other data byte and symbol address
is unchanged (`ui-code-applicability.json`). Targeted native checks exercise
the final pair on both platforms, including Model 4 viewer page 4, full-width
description, long input, exit, restoration and cold boot. Final FDB.COM hash
is `471b29358597f0dafdfd43ae9fa3945ee36f410afdebc689ea06d5c0637b7da2`.

The final guide-only build has all eight media images byte-identical to
`03cc88a9` (`final-media-identity.json`). Earlier locked conformance/ROM/core
results are carried forward only for identical components and reserved areas;
438 intermediate component comparisons and the package lock checks establish
that scope. This is not a claim that every earlier test was newly executed.

Timed-out exploratory runs are not passes. The bounded `ui-native-final/`
captures prove UI behavior only; their intermediate manual console restoration
stalled and its cause was not established. The complete qualified restoration
uses `restore-focused/` and the shipped queued startup script instead.
The successful Model 4 catalogue runner omitted its emulator-exit flag: it
reached a captured fresh CP/M prompt, was stopped privately, and all actual
file postconditions were independently audited after closure. Its receipt and
executed/corrected runner snapshots record that disposition; emulator exit
status is not presented as a successful runner result.

The package constructor's Model 4 receipt deliberately says manual execution
pending: it does not launch that emulator. The separate native receipts above
close that gate. Utilities' existing provisional inventory labels are retained;
this integration does not reopen pending selections or lift the package freeze.
