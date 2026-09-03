# Engineering Specification 118: Completed BASIC Command Set

Date: 2026-09-03  
Status: Implemented and verified

## Command inventory

The default `BASIC.CPX` exports the six CP/M 2.2 CCP commands:

```text
DIR  ERA  REN  SAVE  TYPE  USER
```

It additionally exports BetterCP/M commands `CLR` and `VER`. `CPX LIST`
publishes all eight commands in the active BASIC inventory.

`USER` accepts one decimal user number from 0 through 31 and delegates the
state change to BDOS Function 32. Direct `5:` and `C3:` navigation remains an
additional CCP facility rather than a replacement for compatible USER.

`VER` currently prints `BetterCP/M 0.1`. Its presentation is shared with the
transient fallback; a later versioned system-information interface may expand
both together.

## Transient parity

The distribution includes `DIR.COM`, `ERA.COM`, `REN.COM`, `TYPE.COM`,
`USER.COM`, `CLR.COM`, and `VER.COM`. `SAVE` is the only BASIC command without
a transient counterpart because loading a program at `0100h` would overwrite
the TPA content it must save.

The first `DIR`, `USER`, `CLR`, and `VER` transient images are generated from
the same assembled command bodies as BASIC.CPX. They replace the CPX header
and dispatcher with a conventional `0100h` command-tail entry. This deliberately
favors exact behavioral parity over minimum file size. A later native source
refactoring may remove unreachable command bodies only if regression tests
continue to prove identical behavior.

All four new images assemble under native CP/M with ZSM4 and Digital Research
LINK and are byte-identical to their cross builds.

## Transitional CCP copies

The old CCP copies of DIR, USER, and VER remain temporarily available as
migration fallbacks. Drive-qualified `A:DIR`, `A:USER`, and `A:VER` invocations
bypass those exact core keywords and physically exercise the new transient
files. The core copies may be removed after the full compatibility rerun.

`WARM` is not part of BASIC.CPX. Transient-only `WARM.COM` supports scripts,
while visible `Ctrl-C` remains the canonical interactive warm boot. The old
core WARM command is now only a transitional fallback awaiting removal.

## Verification

`tools/test_basic_command_completion.py` physically verifies:

- the eight-command CPX inventory;
- resident and transient USER state changes;
- identical resident and transient VER presentation;
- transient DIR listing of all new command files; and
- transient CLR screen clearing and prompt restoration.
- transient WARM completion through Function 0 and a reconstructed prompt.

The ordinary boot, CPX manager, CPX reconstruction, and native/cross parity
tests remain required around this command-set change.
