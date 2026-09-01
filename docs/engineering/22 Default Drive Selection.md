# Engineering Specification 22: Default Drive Selection

## Milestone

BetterCP/M now implements BDOS function 14 (Select Disk) and connects it to
function 25's current-default-drive state. Selection is performed through the
public `CALL 0005h` path.

## Current contract

Function 14 receives a zero-based drive number in `E`. The current provisional
BIOS exposes only drive A, so this increment accepts drive 0 and rejects all
other values before changing directory or BDOS state.

For drive A, BDOS invokes the directory login service. Only a successful login
commits the requested value as the current/default drive. Function 25 then
reports the stored state rather than returning a hard-coded A.

CP/M 2.2 does not specify a portable normal return value for an invalid
function-14 drive. BetterCP/M currently returns `FFh` for an unavailable drive
as an explicit provisional failure result; software must not treat that value
as a new compatibility guarantee.

If a storage error occurs while refreshing drive A's login, the default-drive
value remains A and the directory login remains invalid. A later filesystem
access can retry login after the underlying error is corrected.

## Compatibility and architecture

This increment does not manufacture drives B through P. Availability remains
owned by the BIOS and, eventually, its runtime drive-configuration tables.
Adding another BIOS drive descriptor will require widening the present
availability check, not replacing the BDOS current-drive contract.

Current drive, current user, and DMA address remain independent state. A drive
selection does not silently reset either user or DMA state.

## Verification

Direct and page-zero tests verify:

- function 14 selects and logs in drive A;
- function 25 reports A after successful selection;
- unavailable drive B returns the deliberate provisional failure;
- rejecting B does not change the current drive; and
- the remaining functions 12, 15, 26, and 32 retain their behavior.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce the
same 207-byte BDOS binary.

## Deferred work

The system still has one DPH/DPB and one allocation/login context. Login-vector
reporting, disk-system reset, explicit-drive FCB selection, and multiple live
drive contexts remain future work. CONFIG-style drive definitions will later
determine which drive numbers are available on each platform.

## Next increment

Implement function 13 (Reset Disk System) and function 24 (Return Login
Vector). This will make login membership observable and establish the reset
boundary for current drive, DMA, and directory/allocation state before a
second physical drive is introduced.
