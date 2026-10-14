# ADM-3A provider foundation qualification

## Status

This records the development stages of the Model 4 MM-style ADM-3A provider,
not a released terminal personality. It is deliberately excluded from the
system disk, ordinary RSX build output and cold-boot startup.

`tools/build_adm3a.py` builds `ADM3A.RSX` and `ADMTST.COM` under
`build/monitor-development/`, using the current Model 4 BIOS listing for the
backend cursor and column addresses. Rebuild the provider whenever that BIOS
changes. This is a backend-specific dependency, not a new portable BIOS ABI.

The carrier uses STATEFUL reconstruction, one MCON 1.0 descriptor, Model 4
compatibility bit 0001h, and an ordinary pass-through BDOS entry. The current
payload is 583 bytes, with 55 static relocation slots and a 768-byte allocation
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

The second stage implements printable output, cross-row backspace, 8-column
cursor-only tabs, down/scroll, clamped up, wrapping right, carriage return,
EOL/EOS erasure and home. Printable output at the bottom-right scrolls, while
line feed preserves the current column. EOL/EOS erase includes the cursor cell
and does not move it. The renderer shares advancement, scrolling and bounded
fill routines rather than depending on the basic console's control meanings.

The third stage implements 0Eh reverse OFF, 16h reverse toggle and the Model 4
bell. Reverse mode sets video-memory bit 7 on printable output and blank cells
created by EOL/EOS erase, clear and scrolling. Parser reset and clear preserve
this persistent mode. Clear/home shares the mode-aware EOS erase routine,
avoiding a separate mode-aware clear implementation. Bell writes
256 bounded high/low cycles to port 90h, with
100 writes per half-cycle, without changing screen, cursor or terminal modes.
Automated pulse checks establish the output pattern, not audible emulator or
hardware qualification.

The fourth stage implements 0Fh reverse ON and whole-row insert/delete.
These now match the selected original MM 2.32 binary, including bottom-row
clearing, unchanged cursor and reverse-mode blank fills. Unassigned controls
are consumed rather than passed to the basic renderer. See
[original MM console qualification](Original%20MM%202.32%20Console%20Qualification.md).
Application/emulator qualification remains necessary before distribution.

## Automated and manual checks

`tools/test_adm3a_foundation.py` executes the assembled provider at two load
addresses, checks all 65,536 wire row/column pairs at each address, and checks
reset, visibility, clear/home, printable output and raw bypass. It also runs
the assembled development utility with controlled BDOS lookup and input,
checking missing-provider preflight, marker placement, partial-address reset
and both key pauses. This fixture does not replace RSX lifecycle qualification.

`tools/test_adm3a_screen.py` checks all 1,920 cursor positions for twelve screen
operations at both load addresses (46,080 cases). Each case checks complete
framebuffer contents, cursor/column coherence and guard bytes immediately
outside video memory. It also checks ignored controls and containment of the
unfinished controls. It additionally checks reverse OFF/toggle, persistent mode
across reset/clear, reverse blank fills and bottom-row scrolling, and all 51,200
bell writes at each load address. These tests establish the specified screen operations;
they do not settle the explicitly unresolved historical behaviors.

For a manual development check, load only this ADM3A provider and run ADMTST.
The marker should appear at zero-based row 5, column 10. Press a key, confirm
the parser-reset message remains readable, then press a key again. The final
clear should put the completion message at the top. ADMTST looks up MCON; it
does not identify the personality, so another MCON provider must not be used
for this check.

## Remaining release gates

Expand the dedicated test utility, qualify keyboard/cursor presentation and run
native and ROM-backed Model 4 builds with representative ADM-3A software.
The selected binary now settles 0Fh and insert/delete-line behavior, and the
actual carrier has passed controlled production lifecycle execution. Those
checks do not substitute for actual-media and application qualification. Add
the provider and test utility to distribution only after remaining gates pass.
