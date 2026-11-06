# cpmsim terminal-size launch guard

For v1.0.1 the maintainer approved a cpmsim-only host check that refuses launch
below the existing 80-column, 24-row minimum. The screen backend remains fixed
at 80x24. This is an enforcement of that prerequisite, not smaller-screen
support or a diagnosis of the previously reported graphical garbling.

## Behavior and integration

`tools/cpmsim_terminal.py -- cpmsim [arguments]` measures the actual standard-output
terminal through the host OS. Either dimension below the minimum refuses launch
with status 1, before cpmsim starts:

```text
Terminal is 77x20; BetterCP/M requires at least 80x24.
Enlarge the terminal window or reduce its font size, then launch again.
cpmsim was not started.
```

Unmeasurable or zero terminal dimensions also refuse launch with an explanatory
message. Environment variables COLUMNS and LINES cannot override the measured
size. Output redirected to a pipe or file has no terminal geometry and retains
the existing automation path. A test harness using a PTY must set its dimensions.
There is no small-window bypass switch.

Both generated RAM and ROM cpmsim launchers carry a local copy of the guard and
invoke it before the emulator. They preserve working directory, helper PATH,
arguments and emulator exit status. After a successful check, exec replaces the
host Python process with cpmsim; there is no monitoring parent. A rebuild of the
platform output is needed to update an existing generated launcher, including
one used by the maintainer's bcpm script. The fresh-package/source-kit invocation
is documented separately, and the future cpmsim System host kit includes the
standalone guard. Invoking cpmsim directly bypasses this host wrapper.

The check is only at launch. Keep the terminal at least 80x24 during operation.
After shrinking an active session, exit the affected utility, enlarge the host
window, and restart the utility to redraw. Model 4, its 40-column mode, physical
terminals and the guest SCRN/monitor interfaces are outside this host-only change.
No guest code, component identity, resident memory allocation or TPA is changed.
No locked 1.0 archive or image is rebuilt or replaced.

## Validation

`tools/test_cpmsim_terminal.py` uses actual PTYs and OS window-size updates:

- Refusal at 77x20, 79x24, 80x23, 100x20 and 40x24; zero/unavailable dimensions
  refuse too. The emulator fixture must not execute.
- Launch at 80x24 and 100x40; retry after enlarging the same PTY from 77x20 to
  80x24. Deliberately false COLUMNS/LINES settings are ignored.
- Redirected-output automation, exact argument forwarding, cwd, nonzero exit
  status and helper PATH preservation.
- Both generated launchers, including paths containing spaces and apostrophes,
  and an exact copied guard, without booting or rebuilding a ROM guest.

`tools/qualify_cpmsim_terminal.py` starts real cpmsim through the generated RAM
launcher, using a private copy of released System media. It loads ANSISCRN and
ANSI, enters/exits CONFIG at 80x24 and 100x40, then shrinks to 77x20 and enlarges
to 80x24 with fresh redraws. It unloads both modules, verifies 53K TPA recovery
and a subsequent CCP file read, and audits original file hashes, reserved tracks,
filesystem consistency and untouched original media. All checks pass.

The resize test verifies guest lifecycle and emitted menu text, not graphical
rendering or safe operation at 77x20. The earlier baseline replay is retained
with the same limitation; no new reproduction or repair of the low-level
Terminal rendering fault is claimed. Live resizing remains an operating
requirement, not a feature of this preflight check.

Results, transcripts, generated launchers and their checksums are preserved in
[evidence](evidence/2026-11-06-cpmsim-terminal-size/). Existing packaging integrity
and bcpm media-selection tests are also checked without regenerating locked
packages. Exact replacement v1.0.1 package acceptance remains release work.
