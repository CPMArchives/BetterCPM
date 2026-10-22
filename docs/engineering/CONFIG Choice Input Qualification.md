# CONFIG choice input qualification

2026-10-22 — CONFIG 1.0 Build 015, dual-platform profiles

## Scope and compatibility

All existing CHOICE menu reads, direct physical-drive attachment selection and
three save approvals now use `common/configchoice.inc` and the shared choice-only
controller. The three approval paths are pending cold-start changes, all current
settings, and disk-boot IOBYTE. The existing caller continues to compare against
Y after KEY's ASCII case folding; every other key declines. Menus retain their
original invalid-key retry, Enter behavior, Ctrl-C dispatch and display. No
new default, echo, flush, cancellation alias or confirmation retry is added.

The binding transports one KEY event through a single printable `?` member,
then returns the original byte to the caller. The controller validates its
configuration; it does not replace application-specific accepted-key checks.
Menus and approvals share one immutable transport context, eliminating context
switches that could otherwise contaminate a later approval. Malformed controller
state returns Ctrl-C without reading input or dispatching a stale answer.
The editor's separate CI_READ binding and all previous editing behavior remain.
Acknowledgment pauses retain their original KEY path.

## Bounded footprint recovery

The Build 014 dual-profile baseline is 15,552 bytes. Forty-nine local JP→JR
changes save 49 bytes; identical `/PHYSICAL=` and two error-message strings
share storage, saving 157 bytes. Messages retain their exact contents. The
result before the choice binding is 15,346 bytes. The binding and controller
add 218 bytes, yielding **15,564 bytes**, 12 more than the baseline.

SHA-256: `fef0da4eee6ece728f9b58b7ae85a9d1f2c3263446813a1fa91daca56beb9879`.
There are **52 bytes** before the existing 3E00h private stack. Both 20-byte
validation profiles and both disk-boot IOBYTE descriptors remain linked. The
AC00h scratch guard, disk/rollback workspaces and unloaded TPA are unchanged.
Nothing moves into resident memory. Both native and cross builders now consume
`tools/build_config.py`'s same expansion; native ZSM4/LINK matches byte-for-byte.

## Compiled evidence

`tools/test_config_shared_choices.py` compares 512 menu cases (256 first bytes,
plain/inverse) against the legacy KEY route in the same expanded source. It
compares returned bytes, output-service bytes, consumed and remaining input, and
balanced stacks under hostile BDOS registers. Another 256 first-byte cases
compare save-approval input against KEY, including zero polling. Six alternating
menu/approval/attachment events retain their separate caller policies. Four
malformed configurations fail closed without input. The test checks the size
gate and inclusion of both validation/IOBYTE profiles.
Report: `build/config-choice-input/result.json`.

Regression checks pass for shared editor fields, full-tail/version parsing,
physical CLI, workbench CLI, logical CLI, pending defaults, startup-save rollback,
IOBYTE capability/CRC/write/verify/rollback, saved-drive CRC inspection, and
validation-record generation. The compiled workbench check was updated to accept
either JP or JR for the same required validation branch; runtime validation
checks are retained. Report: `build/config-choice-input/compiled-regressions.json`.

## Emulator and actual-media evidence

- `tools/test_config_choice_media.py`: ten menu stages on both cpmsim and native
  Model 4 cover invalid main selection, lower-case physical-drive entry, invalid
  drive letter, field entry, Ctrl-C return through menus, save-scope entry and
  rejection, and exit. All mounted images remain unchanged. Reports:
  `/private/tmp/bcpm-config-choice-menus-cpmsim/result.json` and
  `/private/tmp/bcpm-config-choice-menus-model4-final/result.json`.
- Existing shared-input live checks pass on cpmsim and native Model 4: startup
  editing, retained pending state, Escape/CLEAR cancellation, numeric errors and
  cancellation, normal return and unchanged disk. Reports:
  `/private/tmp/bcpm-config-choices-cpmsim-final/results.json` and
  `/private/tmp/bcpm-config-choices-model4/results.json`.
- `tools/test_config_startup_read.py`: native startup read/edit/clear/test,
  126-byte limit and pending-only save/readback pass; saved changes are restricted
  to the two startup records. Evidence: `build/test-results/config-startup-read`.
- `tools/test_config_save_all.py`: native merged active/pending save, cold-boot
  readback and injected-failure rollback pass. Evidence:
  `build/test-results/config-save-all`.
- `tools/test_config_iobyte_model4.py`: exact saved boot operand, unchanged live
  IOBYTE, next cold restore and warm preservation pass. Evidence:
  `build/test-results/config-iobyte-model4/run-guhg1sbq`.
- `tools/test_config_physical_fields.py`: native drive-type/sides toggles and
  constrained tracks/step-rate lists pass, without changing boot media. Captures:
  `build/config-choice-input/physical-fields`.

Harness corrections are explicit: the first cpmsim editor run sent Ctrl-C before
the choice field had finished printing; its corrected run waits for both final
backspaces. The first native menu run waited on inverse heading bytes and was
stopped; the completed run synchronizes on plain body text instead. The old
physical-field script still chose the former F main-menu entry and used short
boot/key delays; it now chooses C, uses the isolated native launcher and allows
fields to complete. Native checks first attempted without emulator access were
rerun with that access. Only completed corrected runs are counted as passes.

These checks qualify the bounded refactor and input integration; they are not a
new system-wide release acceptance run. Historical editor/command protocols
outside the prompted-field migration retain their documented boundaries.
