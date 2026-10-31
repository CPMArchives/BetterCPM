# CONFIG help correction — 2026-10-31

CONFIG 017 returned Invalid CONFIG usage for /HELP and /H. CONFIG 018 adds
case-insensitive exact unquoted help queries before disk/profile validation or
configuration access. Help takes precedence over /VER and malformed operands;
query-looking text inside quoted startup commands/format names remains data.
The quick reference follows the Utilities presentation, lists supported forms
and field groups, and fits 80 columns by 23 rows plus the returned prompt.

The ordinary program was 15,522 bytes, leaving only 94 bytes before its private
stack reservation. The new help code/text is disposable startup-only material
at 4000h, above the unchanged 3E00h–3FFFh private stack. Normal entry still uses
its existing AC00h minimum-memory guard. Normal code/data must remain below
3E00h; the builder now checks both regions instead of rejecting the entire
file merely because the help appendix extends above the stack.

## Verification

- test_config_help.py: exact aliases, HELP/VER precedence, malformed lookalikes,
  quoted data, command-tail preservation, no disk/settings I/O, screen bounds
  and rejection of main-code/private-stack overlap: PASS.
- test_config_command_line.py: existing CLI and identity behavior: PASS.
- test_config_physical_cli.py, test_config_logical_cli.py,
  test_config_edit_cli.py: parsing, validation and operation regressions: PASS.
- test_config_iobyte.py: saved IOBYTE capability/CRC gates, exact-byte saves,
  live-state preservation, verification and rollback: PASS. The fixture now
  expects the established full identification text and makes its simulated
  tail-jumped operation exit explicitly rather than returning through unowned
  stack contents.
- Native ZSM4/LINK under the retained rc551 qualified cpmsim runtime produces
  byte-identical CONFIG. /HELP /VER and /H both execute there and return to CP/M.
  The native runner checks for both screens and fails on missing output/timeout.
- Registry/projection tests and git diff --check: PASS.

The general disk-utility builder could not run initially because this checkout
had no build/system/resident.bin. Focused CONFIG assembly used its retained
config-validation/config-iobyte inputs; the missing Model 4 stage-one test
fixture was rebuilt from source for the IOBYTE regression. No new system or
candidate package was produced, and no Model 4 runtime PASS is claimed.
Final platform packages must regenerate their matching validation records through
the normal fresh System build before acceptance.

## Local binary identity

- CONFIG.COM: 17236 bytes.
- SHA-256: `343e464c868021a6a72c7eedc1621719ea2522af2507869b2f95811065d90254`.
- Normal code/data end: `3DA7h` (exclusive).
- Help query entry: `4000h`.
