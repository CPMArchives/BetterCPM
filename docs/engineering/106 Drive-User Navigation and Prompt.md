# Engineering Specification 106: Drive-User Navigation and Prompt

## Decision

The core CCP accepts compact drive/user navigation as command-processor
syntax:

- `B:` selects drive B and retains the current user;
- `5:` selects user 5 and retains the current drive;
- `C3:` selects drive C and user 3.

Drive letters are parsed over the CP/M namespace A through P.  The active
platform still decides which drives actually exist; the Model 4 development
configuration currently exposes A through D.  User numbers are decimal 0
through 31.

The CCP prompt displays the current pair without padding, for example `A0>`,
`B5>`, or `C31>`.

## State ownership

Navigation does not introduce private CCP copies of the current drive or user.
The parser uses BDOS Function 14 to select a drive and Function 32 to select a
user.  Each prompt is generated from Function 25 and the query form of
Function 32.  This keeps the command environment, transient programs, FCB
operations, and reconstructed CCP synchronized with the same authoritative
BDOS state.

The complete syntax is validated before any state is changed.  For a combined
drive/user request, the drive is selected first; if the platform rejects it,
the requested user is not installed.  Recognized navigation syntax is consumed
even when its drive is unavailable rather than being treated as a `.COM`
filename.

## Memory result

The added parser and prompt move the relocatable CCP from a 1280-byte to a
1536-byte page-rounded allocation.  The command loader consequently calculates
its new base at `B9FDh` in the no-extra-CPX test configuration.  No fixed CCP
ceiling or address was changed: this downward movement is the intended behavior
of the calculated command region.

## Verification

The focused CCP test covers `B:`, `5:`, and `C31:` and verifies that a combined
request for an unavailable drive does not partially change the user.  Complete
system and physical-emulator tests use the new `A0>` prompt.
