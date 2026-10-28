# macOS trs80gp test launch

## Original launch-context problem

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

## Restricted-tool diagnosis, 2026-10-28

A later failure occurs even when using the wrapper or opening the original
installed application through LaunchServices. Do not assume that the earlier
wrapper alone fixes every execution context.

Evidence from the current tool session:

- The trs80gp 2.5.8 executable exists, is executable and matches its bundle's
  CFBundleExecutable entry. The session belongs to user 501's Aqua bootstrap
  domain; this is not simply an SSH/non-GUI login.
- LaunchServices and CoreServicesUIAgent are running. Both open paths nevertheless
  return kLSNoExecutableErr (-10827).
- Direct execution aborts in HIServices `_RegisterApplication` during AppKit
  `NSApplication` initialization. The crash report identifies SIGABRT; no guest
  output or screen capture was produced.
- Read-only `bootstrap_look_up` calls for LaunchServices and WindowServer return
  1100. The installed macOS SDK defines this as BOOTSTRAP_NOT_PRIVILEGED, distinct
  from BOOTSTRAP_UNKNOWN_SERVICE (1102). Access is denied; the service is not
  merely missing. The system log reader also explicitly refuses execution while
  sandboxed, so no local sandbox-denial log is claimed.

This establishes that this caller cannot reach services required for application
registration. Combined with the crash location, working ordinary launches and
[the matching Codex report](https://github.com/openai/codex/issues/30043), it
strongly identifies the sandbox launch boundary as the cause. It does not
establish a trs80gp emulation defect. The specific local denial log cannot be
read from this session.

`tools/trs80gp_launch.py` now probes the LaunchServices send right before either
macOS app-bundle launch path. A denied/unavailable lookup raises a clear host
launch error before spawning the GUI. It releases a successful send right,
preserves the original argument/timeout contract and leaves non-macOS execution
unchanged. The direct-execution override does not bypass this check. This is a
permission diagnostic and crash-prevention correction, not a permission grant or
a Model 4 PASS. Seven focused cases cover denial, missing service, permitted direct execution,
non-macOS execution, normal completion, timeout cleanup and cancellation cleanup; a real probe in the affected session
reports denial without launching trs80gp.

The execution policy for this session disables sandbox-escalation requests.
The utility launcher cannot change that policy. The supported next step is an
approved emulator/test launch outside the restrictive sandbox. Use the desktop
app's permissions control to permit an approval request, then retry the existing
bounded test through that mechanism. The documented **Ask for approval** mode
keeps the normal sandbox and allows reviewed exceptions; **Full access** is a
broader setting and is not required as the default recommendation. See
[ChatGPT permissions](https://learn.chatgpt.com/docs/permission-modes).

No application was re-signed, security setting changed, LaunchServices database
reset, privileged launch service installed or user disk replaced. Do not route
an otherwise blocked launch through AppleScript, launchd or an unreviewed host
helper to evade the session's permission boundary. Once a supported approval is
available, verify a real guest capture and disk result before declaring the
launch correction effective for qualification.
