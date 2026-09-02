# Engineering Specification 113: Stock-Compatible REN

Date: 2026-09-02

## Compatibility baseline

BetterCP/M supplies REN as both a resident `BASIC.CPX` command and an ordinary
`REN.COM` fallback. The baseline follows the original CP/M 2.2 CCP rather than
only the shorter user-manual synopsis.

The accepted form is:

```text
REN NEWNAME.TYP=OLDNAME.TYP
```

The historical CP/M left-arrow separator is also accepted. BetterCP/M uses
underscore (`_`, ASCII 5Fh) as its character representation. Blanks may
surround the separator, but a blank alone is not a separator and another
operand after the old name is an error.

Both names must be exact, unambiguous 8.3 names. `*` and `?` are rejected.
An explicit drive may qualify the operation, but old and new must resolve to
the same drive. A qualified REN is temporary and does not alter the current
drive/user.

REN reports `FILE EXISTS` when the destination already exists and `NO FILE`
when the source does not exist. Syntax, wildcard, trailing-operand, and
cross-drive errors report `?`. A successful rename is silent.

BDOS Function 23 performs the mutation. It renames every extent of the exact
source, retains attribute bits, refuses to replace an existing destination,
and preflights read-only extents so a multi-extent file cannot be partially
renamed.

## Transient fallback

The normal system disk contains `REN.COM`. Unloading `BASIC.CPX` therefore
removes the resident command without removing REN functionality. The utility
parses the equals-separated old name from its command tail and constructs the
public old/new rename FCB before calling BDOS.

`tools/build_ren.py` creates the cross build. `tools/build_native_ren.py`
assembles and links the same source with ZSM4 and LINK under native CP/M and
requires the resulting executable to be byte-identical.

## Model 4 input correction

The Model 4 console decoder previously translated Shift-minus as `*`, which
made an equals sign unavailable through the physical matrix path. The decoder
now follows the keyboard legends: Shift-colon produces `*`, Shift-minus
produces `=`, and Shift-slash produces `?`. The automated keyboard driver uses
the same mapping and holds Shift through the base-key release to avoid a
spurious second character.

## Verification

`tools/test_ren_compatibility.py` uses disposable physical DMKs under
`trs80gp` to verify exact rename, destination-exists and missing-source
diagnostics, rejection of the former space syntax and trailing operands,
same-drive qualification, cross-drive rejection, preservation of the current
DU, and the transient fallback after unloading `BASIC.CPX`.

The BDOS suite separately verifies all-extent rename, attribute preservation,
existing-target protection, and atomic read-only preflight.
