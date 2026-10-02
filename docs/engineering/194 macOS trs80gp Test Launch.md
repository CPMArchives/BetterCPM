# macOS trs80gp test launch

## Problem

On macOS 27.2, starting the executable inside trs80gp 2.5.8's application
bundle directly from the Codex test subprocess aborts before emulator
initialization. The crash stack ends in AppKit application registration through
`NSApplicationMain`, `_RegisterApplication` and `abort`. No Z80 instruction or
BetterCP/M code executes.

Manual application launch is unaffected. A targeted comparison also proved
that `/usr/bin/open` starts the same binary and boots BetterCP/M successfully,
establishing that the failure belongs to the direct GUI-process launch context
rather than the generated media.

## Bounded launcher

`tools/trs80gp_launch.py` supplies the missing macOS application context without
changing trs80gp or its batch arguments. It creates a temporary minimal app
wrapper, asks LaunchServices to start it, changes to the test's writable working
directory and replaces itself with the configured trs80gp executable.

LaunchServices does not reliably carry the hundreds of keyboard-matrix
arguments used by longer tests. The helper therefore stores the arguments in a
temporary newline-delimited file and passes only that file's name in the launch
environment. The wrapper reconstructs the complete array before `exec`.

LaunchServices also reparents the application process. The wrapper publishes
its PID before replacement; the helper polls that exact PID, enforces the
caller's timeout and terminates only that process on timeout. Expected captures
and media results remain the source of test success rather than an assumed GUI
exit status. Set `BETTERCPM_TRS80GP_DIRECT=1` to retain direct execution when
running outside the affected launch context.

## Qualification

The Step 5 cross-format SYSGEN matrix uses the helper. Both the installed-source
and `SYSTEM.SYS` paths completed, preserved the populated filesystem and
cold-booted the installed destination to `A0>`. Three captures were produced
for each installation case, and no test or emulator process remained afterward.

Other tests may adopt the helper when they encounter the same confirmed macOS
launch failure. This correction does not require a wholesale test-suite
migration and does not alter BetterCP/M runtime code.
