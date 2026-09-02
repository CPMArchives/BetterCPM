# Engineering Specification 116: CLR Command

Date: 2026-09-03

## Command

`CLR` clears the console display and leaves a fresh BetterCP/M prompt. It is a
no-argument resident command supplied by the default `BASIC.CPX`; operands are
rejected as command syntax errors.

## Current platform binding

The TRS-80 Model 4 console clears its screen when byte 1CH is written. The
command emits that byte through BDOS Console Output, so normal console routing
remains in effect, while the Model 4 console driver interprets it by clearing
video memory and homing its software cursor. This control byte is a platform
fact rather than a portable CP/M convention. A future terminal-capability
service should let CLR request the operation without embedding a
machine-specific byte in BASIC.CPX.

## Verification

The cross and native CPX builds must remain byte-identical. A physical
trs80gp test first places marker text on the screen, invokes `CLR`, and requires
the marker to disappear while a new `A0>` prompt remains visible.
