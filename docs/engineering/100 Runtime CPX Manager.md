# Engineering Specification 100: Runtime CPX Manager

Date: 2026-09-02

## Purpose

This increment proves that BetterCP/M can change its active CPX configuration
while running. It adds the transient `CPX.COM` manager, a provisional fixed
BDOS control service, and physical verification that unloading and reloading
`BASIC.CPX` reconstructs both the CPX chain and CCP safely.

## Commands

The first manager accepts:

```text
CPX LIST
CPX LOAD BASIC
CPX UNLOAD BASIC
```

`LIST` distinguishes `BASIC.CPX loaded` from `No CPXs loaded`. This proof
manager recognizes only BASIC; general module discovery, names, dependencies,
and ordering remain later work.

`LOAD` and `UNLOAD` modify the active reconstruction profile only. They do not
change the saved cold-boot default that CONFIG will eventually maintain.

## Safe reconstruction boundary

`CPX.COM` is an ordinary transient and never moves code beneath itself. It
calls provisional BetterCP/M BDOS Function 200 to query or change the active
profile, then terminates through Function 0. BIOS WBOOT invokes the fixed
command reloader, which reconstructs the requested CPXs and places a fresh CCP
beneath them.

The proof service currently defines `E=0` as BASIC status, `E=1` as load BASIC,
and `E=2` as unload BASIC. It returns `FFh` for an unsupported operation or an
active profile that this first manager cannot describe. Function 200 is an
internal provisional interface, not a frozen third-party ABI.

## Verification

One `trs80gp` session executes this ordered workflow:

1. `CPX LIST` reports BASIC loaded.
2. `CPX UNLOAD BASIC` changes the active table and WBOOTs.
3. `CPX LIST` reports no CPXs.
4. bare `TYPE` falls through to the CCP and reports `?`.
5. `CPX LOAD BASIC` changes the active table and WBOOTs.
6. `CPX LIST` again reports BASIC loaded.
7. bare `TYPE` prints the BASIC.CPX usage message.

`CPX.COM`, BDOS, and the complete resident system are byte-identical between
native CP/M and cross builds.
