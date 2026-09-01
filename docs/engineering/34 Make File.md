# Engineering Specification 34: Make File

## Milestone

BetterCP/M now implements BDOS function 22 (Make File). Applications can
create an empty canonical first extent through the ordinary `CALL 0005h`
interface and then populate it with Write Sequential.

## Call and result contract

Function 22 receives an FCB address in `DE`. BetterCP/M accepts drive byte zero
(current drive) or one (drive A in FCB notation), and uses the current BDOS
user number. On success it returns the new entry's directory slot, 0 through 3,
with the normal CP/M aliases. `FFh` reports duplicate name, invalid/wildcard
FCB, software write protection, or directory full. Internal storage failure is
carried separately and currently also maps to `FFh` at the BDOS boundary.

## Validation and initialization

Before changing the caller FCB or media, System Services:

- rejects unavailable drives and software-protected drive A;
- rejects `?` in the eleven-byte filename/type field;
- performs an exact current-user filename search with attribute bits masked;
  and
- rejects creation when any extent of that user/name already exists.

The FCB drive, filename, type, and attribute bits are preserved. `EX`, `S1`,
`S2`, `RC`, all sixteen allocation bytes, and `CR` are cleared to activate an
empty first extent. No data block is allocated until a later Write Sequential.

## Directory transaction

Make reuses the free-slot scanner introduced for automatic sequential extents.
Only an `E5h` entry is eligible; reserved metadata entries remain untouched.
The original 32-byte private-buffer slot is saved before constructing the new
entry. A successful BIOS directory write invalidates cached login/allocation
state. A failed write restores the private buffer and invalidates uncertain
media state.

The complete original 33-byte caller FCB is restored for duplicate, invalid,
directory-full, and storage-failure results. Thus callers never receive a
partly normalized FCB for a file that was not successfully created.

## Verification

Executable tests verify successful creation in a later directory record,
zeroed extent/allocation/position fields, directory-slot return, duplicate
rejection without mutation, software-protected rejection, directory-full FCB
rollback, and dispatch through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services and BDOS binaries.

## Next increment

Implement BDOS function 19 (Delete File). It should use wildcard-compatible
matching, enforce drive and file protection, mark all matching extents deleted
transactionally, and keep allocation state coherent across partial failures.
