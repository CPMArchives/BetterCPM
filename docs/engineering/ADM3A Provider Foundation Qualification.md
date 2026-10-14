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
payload is 496 bytes, with 47 static relocation slots and a 512-byte allocation
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
keeping the allocation at 512 bytes including the descriptor. Bell writes
256 bounded high/low cycles to port 90h, with
100 writes per half-cycle, without changing screen, cursor or terminal modes.
Automated pulse checks establish the output pattern, not audible emulator or
hardware qualification.

Control 0Fh and insert/delete line remain qualification gates.
Those bytes are consumed in this development stage, not passed to the basic
renderer; that prevents 1Ch from accidentally clearing the screen. Consuming
required controls is temporary containment, not implementation of the MM
contract. No application compatibility claim is made yet.

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

Implement the full MM renderer and input contract; qualify actual installation,
retained-state relocation and unload; run the dedicated utility on native and
ROM-backed Model 4 builds. Resolve control 0Fh reverse-video behavior and
insert/delete-line edge semantics against an original MM binary before freezing
those behaviors. The reconstructed reference source alone does not settle
those two historical questions. Add completed provider builds and test utilities
to the distribution only after these gates pass.
