# BYE

BYE exits the z80pack cpmsim emulator. It is supplied on the cpmsim system
disk and is specific to that platform.

```text
BYE [/Y]
BYE /VER
BYE /HELP
```

With no operational switch, BYE asks `Exit cpmsim? [y/N] `. Press Y or y to
exit immediately. N, n, Enter, Escape or Ctrl-C cancels and returns to the
caller. Other keys repeat the prompt. No Enter is required after Y or N.

`/Y` bypasses confirmation, including in automated command sequences. Switches
are case insensitive and separated by spaces or TABs. Invalid arguments show
short syntax and return without prompting or shutting down. Repeated `/Y`
switches are accepted.

`/VER` displays utility identification. `/HELP` displays a compact reference.
These exact query tokens follow the common utility contract: they ignore other
arguments, never prompt or shut down, and `/HELP` takes precedence over `/VER`.

BYE requests shutdown by writing AAh and then 80h to cpmsim's hardware-control
port A0h. DI followed by HALT remains as a fallback. This does not invoke an OS
cache-flush service or save work belonging to another program.

Build with `python3 tools/build_z80pack_bye.py`. The cpmsim image builder uses
the same source and builder rather than embedding a separate exit byte string.
Qualify the command with `python3 tools/test_z80pack_bye.py`.

For a generated System Disk, also run
`python3 tools/test_z80pack_bye_cpm.py --image-dir <release>/z80pack`,
using the immutable release directory printed by the distribution builder.
The test boots private copies, verifies the shipped binary, exercises both
queries and cancellation keys, and checks confirmed and `/Y` shutdown.
Automated platform checks use `BYE /Y` to avoid waiting for confirmation.
