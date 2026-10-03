# Once-only cold startup dispatch

## Scope

The first reconstructed CCP now reads the saved version-1 `BCST` record from
protected logical records 1 and 2 on boot drive A, validates the complete
record, and dispatches its command through the ordinary CCP command path. An
empty, disabled, corrupt or incompatible record falls through to the prompt.
Command failure also returns to the prompt without retry.

The CCP reads the record only after CPX and CCP reconstruction has completed.
It uses the public BIOS jump table discovered through page zero and borrows the
shared sector/overlay buffer at `LY_BUF`. This avoids carrying a 256-byte record
through the command reloader and introduces no persistent allocation or
platform-specific port access in the CCP.

## Once-only state

Bit 0 of the formerly reserved persistent CPX-profile flag byte at
`LY_SYS+095h` records that cold startup has been consumed. Cold resident state
initializes the byte to zero. The first CCP sets the bit before reading,
validating or dispatching the saved command. WBOOT and command reconstruction
preserve it, so a transient that terminates through warm boot cannot cause a
loop. Read or validation failure is likewise not retried during that boot.

This byte is fixed gateway state and does not add a PDS owner. The remaining
bits stay reserved.

## Validation

`tools/test_startup_dispatch.py` installs a private `MARK` transient and an
enabled `BCST` record in a disposable z80pack image. It proves that the marker
appears exactly once across cold boot followed by `WARM`. A second case corrupts
the record checksum and proves that the command is not dispatched. The complete
z80pack image build and ROM relocation checks also pass.

The documented cold-boot recovery gesture remains the next bounded increment;
this change implements once-only dispatch without claiming that recovery UI.
