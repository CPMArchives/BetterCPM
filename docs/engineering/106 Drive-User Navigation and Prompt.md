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

The same DU forms may qualify the resident `DIR` command.  `DIR B:`, `DIR 5:`,
and `DIR C3:` search another drive/user area without changing the active DU;
an optional filespec may follow the colon, as in `DIR B0:*.COM`.  This is
deliberately different from a navigation command: after `DIR B:`, an `A0>`
caller receives the `A0>` prompt again.

DU selectors may also prefix a transient command name: `A:CPX LIST`,
`5:UTILITY`, and `C3:PROGRAM ARG`.  The named `.COM` file is located in that
DU, but the caller's default drive/user remains the command environment seen
by the program and restored after its warm boot.  A command prefix is therefore
a lookup qualification, not an implicit navigation command.

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

The evolving editor, history, and DU parsers currently place the relocatable
CCP in a 2816-byte page-rounded allocation at calculated base `B2FDh`.  No
fixed CCP ceiling or address was changed: this downward movement is the
intended behavior of the calculated command region during implementation.

## Verification

The focused CCP test covers `B:`, `5:`, and `C31:` and verifies that a combined
request for an unavailable drive does not partially change the user.  Complete
system and physical-emulator tests use the new `A0>` prompt.  A physical
two-drive run also verifies that `DIR B0:` lists the drive-B fixtures while
leaving the caller at `A0>`, and that `DIR B0:*.TMP` applies its wildcard in
the selected DU.  Focused tests cover `A:CPX LIST` and `A0:CPX LIST`, including
temporary-user restoration.  A two-drive physical run verifies the complete
`B0>A0:CPX LIST` path and returns to `B0>` after WBOOT.
