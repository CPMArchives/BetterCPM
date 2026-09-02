# Engineering Specification 102: Multiple CPXs and HELLO.CPX

Date: 2026-09-02

## Purpose

This increment proves that BetterCP/M can load, reconstruct, dispatch, and
selectively unload more than one CPX. It adds `HELLO.CPX`, generalizes the
active proof profile, and verifies behavior with BASIC and HELLO installed
together.

## HELLO.CPX

`HELLO.CPX` implements one command:

```text
HELLO : HELLO
```

Its linked payload is 141 bytes and its runtime allocation is one 256-byte
page. The complete `BCX1` carrier occupies 653 bytes. It is stored beginning
at command-module slot seven; BASIC occupies slots four through six. Slot nine
remains available.

When active, HELLO.CPX intercepts `HELLO` and its optional argument tail before
`.COM` lookup. Thus `HELLO TOM` prints `Hello from HELLO.CPX TOM`; it does not
fall through merely because arguments are present. Unrelated command names
such as `HELLOX` are declined. When HELLO.CPX is absent, the command falls
through to the existing transient `HELLO.COM`.

## Active profile

The provisional profile flags now use bit zero for BASIC and bit one for
HELLO. Function 200 accepts a known-module selector in `D` (`1` BASIC, `2`
HELLO) and an operation in `E` (`0` query, `1` load, `2` unload).

The cold-boot default remains BASIC alone. `HELLO.CPX` is present in the
command image as an available module, but it is not loaded until the user
issues `CPX LOAD HELLO`. Runtime loading does not add HELLO to the saved
cold-boot profile.

Every mutation regenerates the ordered reconstruction table. Canonical order
is BASIC followed by HELLO, independent of the order in which the user loaded
them. WBOOT then loads and links that table in order before relocating the
CCP beneath it.

`CPX.COM` accepts `LOAD HELLO` and `UNLOAD HELLO` in addition to the BASIC
forms. `CPX LIST` queries and reports both known modules.

## Private fixed-core relocation

The generalized Function 200 dispatcher exhausted the bring-up padding before
the private disk descriptors at `C900h`. The DPH/DPB/CSV/ALV block therefore
moved intact to `CB00h..CC97h`, within the existing protected gap below
Directory Services. This private relocation changes neither the public CP/M
interface nor the `BFFDh` development TPA boundary. It is retained as another
explicit reason that the current layout is a diagnostic development profile,
not the final compact release link.

## Verification

One physical `trs80gp` session verifies:

1. `CPX LOAD HELLO` reconstructs BASIC and HELLO together.
2. `CPX LIST` reports both command inventories and 47K TPA.
3. `HELLO` is handled by HELLO.CPX.
4. unloading BASIC leaves HELLO installed; `TYPE` then falls through as `?`.
5. HELLO remains callable after BASIC is removed.
6. unloading HELLO produces an empty CPX list with the same 47K TPA.
7. `HELLO` then runs the transient `HELLO.COM` fallback.

HELLO.CPX, CPX.COM, BIOS, BDOS, and the resident system retain native/cross
binary parity.
