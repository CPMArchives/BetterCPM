# ADM-3A provider foundation qualification

## Status

This records the development stages of the Model 4 MM-style ADM-3A provider,
now qualified for the native Model 4 target. Its release artifacts and test
utility are integrated into the Model 4 system-disk manifest and cold startup.

`tools/build_adm3a.py` builds release `ADM3A.RSX` under `build/rsx` and
`ADMTST.COM` under `build/utilities`, keeping development copies/listings under
`build/monitor-development`, using the current Model 4 BIOS listing for the
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
and the expanded visual/keyboard phases. This fixture does not replace RSX lifecycle qualification.

`tools/test_adm3a_screen.py` checks all 1,920 cursor positions for twelve screen
operations at both load addresses (46,080 cases). Each case checks complete
framebuffer contents, cursor/column coherence and guard bytes immediately
outside video memory. It also checks ignored controls and containment of the
unfinished controls. It additionally checks reverse OFF/toggle, persistent mode
across reset/clear, reverse blank fills and bottom-row scrolling, and all 51,200
bell writes at each load address. These tests establish the specified screen operations;
they do not settle the explicitly unresolved historical behaviors.

## Expanded ADMTST

Load only ADM3A.RSX and run ADMTST. Four pauses present addressing/reset,
movement and video pages. Movement includes backspace, tab, right, carriage
return, line feed and up. The video page exercises reverse ON/OFF/toggle,
EOL/EOS erase, insert/delete line, bell, and cursor OFF/ON service queries.
The line pattern should read A, a blank row, C and D: B is deleted. Cursor query
checks do not establish visible blinking/presentation by themselves.

Then type uppercase A, colon, opening bracket and closing bracket, without
ENTER. A mismatch reports the test incomplete; successful input prints
`ADMTST keyboard checks passed.` Visual appearance and audible bell require
separate observation. The utility resolves MCON rather than identifying a
personality; do not use another provider for these checks.

Coordinate streams use zero termination and BDOS character output: encoded
coordinates may contain 24h, so BDOS's dollar-terminated output cannot safely
send them. Automated utility checks cover marker placement, both visual pages,
line results, bell writes, successful keyboard input and the mismatch path.

## Qualification scope

Native visual, keyboard, bell and original-application opening-screen checks
now pass as recorded in the follow-up below. The carrier and test utility are
integrated into the Model 4 distribution. These checks do not certify physical
hardware, every historical keyboard configuration, all functions of the MM
application, or a ROM-backed Model 4 target. The cpmsim ROM backend is distinct.

## Native trs80gp execution

The expanded utility ran from private media based on the Model 4 distribution
image, with the current ADM3A.RSX, ADMTST.COM and corrected R3PACK.RSX installed.
The test loaded ADM3A, advanced all four pauses, supplied `A:[]`, unloaded the
provider, and captured the final screen. The capture contains:

```
ADMTST keyboard checks passed. Confirm visual pages and bell separately.
A0>RSX UNLOAD ADM3A
A0>
```

The generated capture is `build/monitor-development/admtst-native-screen.bin`.
This establishes actual service lookup, execution of the visual-control streams
and cursor queries, character input and return/unload on the native Model 4
build. It does not establish the intermediate pages' visible appearance or
an audible bell, because the capture is taken after their pages are cleared.
Those remain separate observation gates, along with a representative real
ADM-3A application.

The existing protected ROM qualification target is cpmsim. ADM3A.RSX advertises
Model 4 backend compatibility only; loading it into that ROM target cannot
qualify Model 4 rendering. A ROM-backed Model 4 rendering claim requires an
appropriate target rather than relabeling the cpmsim campaign.


## Native visual and application follow-up

The subsequent native campaigns capture intermediate pages, check raw TAB
placement and reverse-video bytes, record the provider bell, exercise the
original MM CONFIG opening screen, and confirm 53K TPA after unload. See
[ADM-3A native qualification](ADM3A%20Native%20Qualification.md) for reproducible
runs and limits. ADMTST now uses BDOS 6 raw output for its control streams;
ordinary BDOS character output would expand TAB before reaching the provider.
Distribution integration remains a separate step.
