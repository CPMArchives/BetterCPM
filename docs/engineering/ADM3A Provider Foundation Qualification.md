# ADM-3A provider foundation qualification

## Status

This is the first development stage of the Model 4 MM-style ADM-3A provider,
not a released terminal personality. It is deliberately excluded from the
system disk, ordinary RSX build output and cold-boot startup.

`tools/build_adm3a.py` builds `ADM3A.RSX` and `ADMTST.COM` under
`build/monitor-development/`, using the current Model 4 BIOS listing for the
backend cursor and column addresses. Rebuild the provider whenever that BIOS
changes. This is a backend-specific dependency, not a new portable BIOS ABI.

The carrier uses STATEFUL reconstruction, one MCON 1.0 descriptor, Model 4
compatibility bit 0001h, and an ordinary pass-through BDOS entry. The current
payload is 208 bytes, with 19 static relocation slots and a 256-byte allocation
including its runtime descriptor. Loading it also incurs the existing RSX
manager allocation if that manager is not already present.

## Implemented foundation

- ESC `=` receives row-plus-32 and column-plus-32, clamped to 24 rows and
  80 columns using unsigned byte subtraction.
- ESC `0` and ESC `1` suppress and restore the private cursor query.
- Unknown escape selectors are consumed.
- Operation 5 discards partial parser state while preserving screen, cursor and
  visibility mode.
- Operation 4 and control 1Ah clear all 1,920 cells and home the cursor without
  invoking platform initialization or resetting keyboard state.
- Other operations use MONRAW directly, avoiding dispatch recursion.

Ordinary output currently delegates to the basic renderer. Consequently this
stage does **not** promise MM tab, cursor movement, erase, reverse-video,
insert/delete-line or bell semantics. In particular, forwarding a control byte
to the basic renderer can produce different behavior from MM CP/M. Do not use
this foundation to qualify an application or describe it as a completed ADM-3A
emulation.

## Automated and manual checks

`tools/test_adm3a_foundation.py` executes the assembled provider at two load
addresses, checks all 65,536 wire row/column pairs at each address, and checks
reset, visibility, clear/home, printable output and raw bypass. It also runs
the assembled development utility with controlled BDOS lookup and input,
checking missing-provider preflight, marker placement, partial-address reset
and both key pauses. This fixture does not replace RSX lifecycle qualification.

For a manual development check, load only this ADM3A provider and run ADMTST.
The marker should appear at zero-based row 5, column 10. Press a key, confirm
the parser-reset message remains readable, then press a key again. The final
clear should put the completion message at the top. ADMTST looks up MCON; it
does not identify the personality, so another MCON provider must not be used
for this check.

## Remaining release gates

Implement the full MM renderer and input contract; qualify actual installation,
retained-state relocation and unload; run the dedicated utility on native and
ROM-backed Model 4 builds. Resolve control 0Fh reverse-video behavior and
insert/delete-line edge semantics against an original MM binary before freezing
those behaviors. The reconstructed reference source alone does not settle
those two historical questions. Add completed provider builds and test utilities
to the distribution only after these gates pass.
