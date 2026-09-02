# Engineering Specification 108: Reverse-Video Command Cursor

## Decision

The CCP shall not manipulate platform video memory or emit terminal escape
sequences to present its editing cursor. BetterCP/M Function 204 and the
private BIOS vector immediately following `BIOPHREAD` provide an optional
cursor-character operation instead.

- `E=0` queries support and returns nonzero when available.
- A nonzero `E` writes that character using the platform cursor presentation.
- The operation advances the physical cursor and BDOS console column once.
- An unsupported implementation returns zero without producing output.

The CCP falls back to its visible underscore when the query is unsupported.

## Model 4 binding

The Model 4 BIOS sets bit 7 on the supplied character and passes it through the
bounded scrolling console. The video mode established during initialization
interprets that bit as reverse video. An interior cursor therefore reverses the
actual character under it; an end-of-line cursor reverses a blank cell.

The private BIOS entries at `EF33h` and `EF36h` are both explicit jump vectors.
This preserves the existing physical-read ABI while allowing the cursor service
to remain behind the hardware boundary.

## Redraw rule

When reverse video consumes the character at the logical cursor, redraw resumes
with the following command byte. At end of line, or when using the underscore
fallback, no command byte is consumed. Console calls are still assumed to
destroy working registers, so the tail address is reconstructed afterward.

## Verification

The physical `trs80gp` boot test requires byte `A0h`—a reverse-video space—at
the final empty `A0>` prompt. This verifies the complete path through the CCP,
BDOS Function 204, the private BIOS vector, and Model 4 video memory.
