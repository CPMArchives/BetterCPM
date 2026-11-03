# TED shared choice qualification

3 November 2026. The maintainer approved the immediate-choice correction in the
UI integration thread. TED 1.0 revision 004 now uses the established shared choice
controller. This record closes the TED behavior decision and bounded host/cpmsim
checks. The current-payload Model 4 `choices` campaign also passes; native
`choice-scope` and whole-release acceptance remain open.

## Behavior and interface

All confirmation questions display `(Y/N) [N]`. Y/N, case-insensitively, act
immediately without Enter. Enter chooses No. Invalid keys retain/repaint the
whole question. ESC/Ctrl-C cancels locally; Q is invalid in this modal context.
There is no typeahead purge: an independent following key stays available.

| Context | No/default | Cancel | Yes |
| --- | --- | --- | --- |
| Overwrite/protection | Refuse that publication; destination unchanged | Refuse that publication; destination unchanged | Authorize only the named operation; protection is a separate approval |
| Modified-document abandonment | Retain the edited document | Retain the edited document | Permit the requested abandonment |
| Recovery | Retain current document and recovery source | Retain current document and recovery source | Recover the validated checkpoint; source retained |
| Confirmed substitution | Skip one match and continue | Stop remaining matches; completed replacements retained | Replace this match |

Internal checkpoint flushing retains its established boundaries. Refusing a
publication does not promise that the editor performed no checkpoint I/O.
Existing file publication, backup, rollback and attribute policy is unchanged.

`frontend.mac:TE_CHOOSE` returns A=Y/N, carry clear; cancellation or malformed
controller configuration returns carry set. `TE_CONFIRM` preserves the existing
authorization interface, returning carry clear only for Y. `OP_SUB_LOOP` uses
`TE_CHOOSE` so No remains distinct from Cancel. Ordinary text fields keep their
shared editor and command aliases. The choice reader binds to `TE_READ` directly
and bypasses those aliases, including command-mode Ctrl-C submission.

The builder selects text and choice controllers together, emitting checks once;
it verifies the input-hook binding matches exactly once. No shared-library API,
core, BIOS, historical source or application feature is changed.

## Measured costs

TED.COM grows from 30,300 to 30,492 bytes (+192), retaining its 30,720-byte
filesystem allocation. Seven bytes hold choice configuration/value state; no
field or original-value buffer is added. The 2,048-byte private stack, 32-byte
low stack guard and 4,095-byte dirty-line bound are unchanged. The entry guard
still checks the full static image against the active exclusive TPA boundary.
The primary Utilities allocation remains 335,872 of 337,920 bytes, with 2,048
bytes free, including the updated TED.TXT.

Current COM SHA-256:
`5bf8ea6bd52987225c15ff880b6b80ccadfe811472c4bb9a2362516583d87e17`.

## Validation and evidence

- PASS: 318 complete frontend/choice cases, including every raw byte, default,
  invalid retries with the question visible, ESC/Ctrl-C, typeahead, unchanged
  provisional fields/history, caller IX/IY and malformed configuration refusal.
- PASS: actual save refusals/approvals, independent RO/SYS authorization,
  abandonment preserving edits, recovery preserving its source and per-match
  substitution No/Cancel scope. Response chunks arrive at actual controller reads
  in the model, so cancellation is not accidentally delivered during startup.
- PASS: existing text, publisher fault-injection and workspace tests; 105 command
  cases; 37 help screens/324 alias-parser checks/222 version queries; 24 specialized
  help/version queries.
- PASS: current TED exact ZSM4/LINK parity and help execution under stock CP/M,
  through `test_native_remaining_help.py`.
- PASS: real BetterCP/M cpmsim `choices` campaign: invalid retry, Enter=No on
  abandonment, No on overwrite, immediate Yes, final target and original backup
  readback; independent directory check rules out an earlier unauthorized backup.
- PASS: real cpmsim `choice-scope` campaign: No skips the first match, Yes replaces
  the second, Ctrl-C stops before further matches, and the saved bytes match that
  exact result. Source system/utility media remain unchanged and filesystem checks
  pass. These are disposable cross-build executions, not final packaged media.
- Observed private stack high-water: 54 bytes in the modeled frontend and save
  campaign, 52 bytes in the real substitution campaign; guards remain intact.
- PASS: maintainer-run Model 4 `choices` campaign on the exact current payload:
  invalid retry, Enter=No on abandonment, overwrite No and immediate Yes, exact
  target/original backup readback, no earlier unauthorized backup, filesystem and
  stack checks. Observed high-water 54 bytes; exclusive TPA ceiling 50,689.
- OUTSTANDING: Model 4 `choice-scope`. The initial attempt's RAM capture shows
  startup completed and TED returned to command input after `SU M /ONE/X/` found
  no match in lowercase `one one one one`. The physical-key helper uppercases
  letters; cpmsim had received lowercase text directly. This is a harness fixture
  mismatch, not a demonstrated editor hang. The fixture/search/expected output
  now use uppercase on both targets. Corrected cpmsim execution passes, saving
  exactly `ONE X ONE ONE` plus CRLF and padding; native rerun remains required.

[Results and source hashes](evidence/2026-11-03-ted-choice/results.json),
[receipts/logs](evidence/2026-11-03-ted-choice/receipts-and-logs.tar.gz) and
[checksums](evidence/2026-11-03-ted-choice/SHA256SUMS.txt) bind these claims.
Initial failed test-harness attempts remain in the archive: response timing was
corrected, and a missing-file check was changed to an independent directory
listing because cpmcp can return zero when no file matches. They are not program
regressions relabeled as passes.

The [Model 4 choices receipt and RAM diagnosis](evidence/2026-11-03-ted-model4-choices/results.json)
and its [capture/readback archive](evidence/2026-11-03-ted-model4-choices/receipts-and-logs.tar.gz)
retain the native pass, failed case-mismatch attempt and corrected cpmsim run.
No production TED source, binary or keyboard case policy changed for this correction.

## Reproduction

From the integration branch with existing reference toolchain/build prerequisites:

```sh
python3 tools/build_ted.py --output build/utilities
python3 tools/test_ted_frontend.py
python3 tools/test_ted_commands.py
python3 tools/test_ted_text.py
python3 tools/test_ted_publisher.py
python3 tools/test_ted_workspace.py
python3 tools/test_native_remaining_help.py
python3 tools/test_utility_finalization.py
python3 tools/test_remaining_utility_help.py
python3 tools/test_utility_ui_inventory.py
```

SYSTEMS and UTILITIES must be absolute paths to the existing paired reference
systems and Utilities images. OUTPUT must be a fresh absolute directory. This
run used the sibling `BetterCPM-release-push/build/rc564-systems` and
`BetterCPM-release-push/build/rc564-utilities`.

```sh
python3 tools/qualify_ted_editor.py --system "$SYSTEMS" --utilities "$UTILITIES" --output "$OUTPUT" --platforms z80pack --cross-smoke --scenario choices --identity-state auto
python3 tools/qualify_ted_editor.py --system "$SYSTEMS" --utilities "$UTILITIES" --output "$OTHER_OUTPUT" --platforms z80pack --cross-smoke --scenario choice-scope --identity-state auto
```

For Model 4, run those commands from a normal Terminal with `--platforms trs80gp`
and fresh absolute output directories. Each command performs file/backup,
filesystem and stack-canary checks after emulation; prepared media alone does
not satisfy that gate. Keep current host and Model 4 acceptance distinct.
