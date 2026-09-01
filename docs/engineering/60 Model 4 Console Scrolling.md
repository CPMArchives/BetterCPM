# Engineering Specification 60: Model 4 Console Scrolling

## Milestone

The resident TRS-80 Model 4 BIOS now treats the display as a bounded 80-column,
24-row console. Output that advances beyond the final row scrolls rows 2 through
24 upward, clears the new bottom row, and resumes at the same column there.

Both explicit line feed and automatic column wrap use the same boundary rule.
No console output may write at or above `FF80h`, the byte immediately following
the Model 4's 1,920-byte display region at `F800h`.

Platform initialization now clears exactly those 1,920 bytes rather than the
bring-up routine's former 2K range.

## Loader separation

The size-constrained ROM loader and one-sector diagnostics retain the original
small `M4_OUT` routine. They emit only short startup messages and do not need a
resident terminal's scrolling behavior. The compatibility BIOS binds CONOUT to
`M4_SCROLL_OUT`, a wrapper which preserves that established primitive while
adding the operating-system boundary and scroll operation.

This separation avoids spending scarce loader bytes on behavior needed only
after the resident system has loaded.

## Verification

The executable BIOS test writes 25 labelled lines through the public CONOUT
vector and verifies their ordering after two scrolls, the cleared bottom row,
and an unchanged sentinel at `FF80h`. A second case fills all 1,920 character
positions without line feeds and verifies automatic-wrap scrolling and the same
out-of-range sentinel.

Native CP/M assembly and the cross build must continue to produce byte-identical
BIOS binaries.
