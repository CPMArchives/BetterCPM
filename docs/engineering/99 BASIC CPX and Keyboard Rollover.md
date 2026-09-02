# Engineering Specification 99: BASIC.CPX and Keyboard Rollover

Date: 2026-09-02

## Purpose

This increment supplies the first production Command Processor Extension and
uses it to prove that WBOOT reconstructs real command code rather than only a
synthetic loader fixture. It also corrects character loss exposed while
entering longer command sequences on the Model 4 console.

## BASIC.CPX

`BASIC.CPX` implements `DIR`, `ERA`, `TYPE`, `REN`, and `SAVE`. The commands use only
public BDOS functions. The early `REN new old` convenience syntax was removed
when REN was brought to its stock CP/M contract; specification 113 supersedes
that prototype behavior.

The `BCX1` file contains a 512-byte metadata and relocation header followed by
the linked image. Its allocation is rounded upward to a page. The saved CPX
profile names command-module slot four, after the four-slot CCP image. Cold
and warm reconstruction load the CPX downward beneath the movable gateway,
relocate it, publish the chain head, then place the CCP below it.

CPXs receive first refusal on upper-case commands. Carry set means handled;
carry clear passes to the next CPX and ultimately to the transitional CCP
commands and `.COM` loader. The older resident commands have deliberately not
yet been removed.

## Model 4 keyboard rollover

The earlier console input routine waited for the entire keyboard matrix to
become empty after detecting a key. If a second key was pressed before the
first was released, that wait could consume the second key as part of the
release cycle.

The revised routine retains release-based debounce, which remains important
for repeated letters, and adds a one-character pending queue. A different key
observed during release is saved and becomes the next console-input result.
The focused emulator test presses `B` before releasing `A` and verifies that
the command tail contains `AB`.

## Verification

- `BASIC.CPX` is byte-identical when assembled natively under CP/M and by the
  cross-build.
- The production DMK boots with the real CPX linked ahead of the CCP.
- `DIR`, `TYPE`, `REN`, and `ERA` completed their physical disposable-disk
  workflow, and WBOOT reconstructed the command environment.
- The retained CCP commands remain available if the CPX chain is empty.
- The overlapping-key regression preserves both characters.
