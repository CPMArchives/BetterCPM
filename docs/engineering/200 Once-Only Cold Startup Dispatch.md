# Once-only cold startup dispatch

## Scope

The first reconstructed CCP now reads the saved version-1 `BCST` record from
protected logical records 1 and 2 on boot drive A, validates the complete
record, and dispatches its command through the ordinary CCP command path. An
empty, disabled, corrupt or incompatible record falls through to the prompt.
Command failure also returns to the prompt without retry.

The CCP reads the record only after CPX and CCP reconstruction has completed.
It uses the public BIOS jump table discovered through page zero and borrows 256
bytes beginning at `LY_LOAD` (`0100h`). Command reconstruction has finished and
no transient program exists yet, so this completed-loader workspace is free.
The CCP validates the record and copies its command into ordinary CCP storage
before dispatch, after which a transient may safely overwrite `0100h`.

The destination deliberately does not use `LY_BUF`: Model 4 uses its lower 512
bytes as a physical-sector buffer, while platform control overlays can occupy
the full shared workspace. The TPA placement avoids both aliases and introduces
no persistent allocation, CCP growth or platform-specific port access. The
resident boundary, CCP allocation and 54,273-byte unloaded TPA do not change.

## Once-only state

Bit 0 of the formerly reserved persistent CPX-profile flag byte at
`LY_SYS+095h` records that cold startup has been consumed. Cold resident state
initializes the byte to zero. The first CCP sets the bit before reading,
validating or dispatching the saved command. WBOOT and command reconstruction
preserve it, so a transient that terminates through warm boot cannot cause a
loop. Read or validation failure is likewise not retried during that boot.

This byte is fixed gateway state and does not add a PDS owner. The remaining
bits stay reserved.

## Recovery gesture

Before reading `BCST`, the first CCP polls the physical console through the
public BIOS `CONST` and `CONIN` vectors. A queued Ctrl-C (`03h`) suppresses the
saved command for this boot without changing the disk record. The consumed bit
has already been set, so WBOOT cannot retry a suppressed command. Direct BIOS
input avoids invoking BDOS's ordinary Ctrl-C warm-boot behavior during this
special cold-start window.

## Validation

`tools/test_startup_dispatch.py` installs a private `MARK` transient and an
enabled `BCST` record in a disposable z80pack image. It proves that the marker
appears exactly once across cold boot followed by `WARM`, that a queued Ctrl-C
suppresses it, and that a corrupt checksum prevents dispatch. The complete
system build, ordinary z80pack regression and protected ROM boot also pass.

A bounded Model 4 control run proves that the same `BCST` record is read and
dispatches `VER` with the private buffer. Existing Model 4 console tests cover
the BREAK-to-Ctrl-C mapping. Automated timing of BREAK inside the short cold-
start window remains unreliable under trs80gp batch scheduling and is not
claimed as independent end-to-end evidence here.
