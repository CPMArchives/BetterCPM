# Engineering Specification 101: CPX Inventory and TPA Report

Date: 2026-09-02

## Purpose

This increment makes `CPX LIST` useful as a runtime inspection command. It
reports the commands supplied by each known active CPX and the live transient
program area available to applications.

## Current output

With the default proof module installed, the manager reports:

```text
BASIC : DIR, ERA, TYPE, REN
TPA available: 47K
```

After `CPX UNLOAD BASIC`, it reports:

```text
No CPXs loaded
TPA available: 47K
```

The inventory names the commands actually implemented by the present
`BASIC.CPX`. `SAVE` is not reported because it has not yet been moved into or
implemented by that module. A future ZEX-style CPX will receive its own line
only when that module exists and is active.

The first manager has a built-in catalog for BASIC because the provisional
Function 200 interface currently recognizes only that proof module. General
CPX metadata must eventually expose module name, version, and command or
capability inventory so arbitrary installed modules can be listed without
hard-coded manager knowledge.

## TPA calculation

`CPX.COM` reads the live exclusive TPA ceiling from the conventional word at
`0006h`, subtracts the `0100h` transient origin, and reports the whole-kilobyte
floor. It does not assume a fixed boundary.

The value remains 47K when BASIC is loaded or unloaded. CPXs and the CCP are
reclaimable command-environment overlays below the dynamic gateway and do not
reduce the TPA. Installed RSXs will move the protected boundary downward and
will therefore reduce the reported value.

## Verification

The physical runtime workflow now requires the command inventory and the same
47K TPA report before unload, while no CPXs are active, and after reload.
`CPX.COM` remains byte-identical between native CP/M and cross builds.

> Subsequent note: Engineering Specification 102 adds the first second-module
> inventory line, `HELLO : HELLO`, and verifies both modules concurrently.
