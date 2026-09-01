# Engineering Specification 24: Software Write Protection

## Milestone

BetterCP/M now implements BDOS function 28 (Write Protect Disk) and function
29 (Get Read-Only Vector). This completes the transient protection state that
function 13 is required to clear.

## Function 28

Write Protect Disk takes no function-specific parameter and sets the current
drive's bit in BDOS's 16-bit read-only vector. The current system has only
drive A, so the implemented transition is `0000h` to `0001h`. Repeated calls
are idempotent.

Protection is transient BDOS state. It does not modify a directory attribute,
write a marker to the disk, or otherwise alter media. Function 28 has no
guaranteed function-specific return value; the current zero result is not a
compatibility promise.

## Function 29

Get Read-Only Vector returns the 16-bit state in `HL`, with bits 0 through 15
corresponding to drives A through P. It uses the same 16-bit return path as the
function-24 login vector, including `A=L` and `B=H` aliases.

## Reset interaction

Function 13 now explicitly stores `0000h` into the read-only vector after a
successful drive-A login. Its other required effects remain intact: drive A,
login vector `0001h`, DMA `0080h`, and preservation of the current user.

If reset cannot log in drive A, it does not commit the reset state. This keeps
the existing provisional disk-error policy consistent across drive-state
operations.

## Enforcement boundary

No mutating BDOS file operation exists yet, so this milestone establishes and
reports protection state but has nothing to reject. Make, sequential write,
random write, delete, and rename must consult this vector before their first
media mutation when those functions are added.

The initial implementation sets bit 0 directly because A is the only drive the
BIOS can select. Multiple-drive work must generalize this to the current-drive
bit without changing the public function contract.

## Verification

Direct and page-zero tests verify:

- the initial vector is zero;
- function 28 sets drive A's bit;
- function 29 returns `HL=0001h`;
- protecting a disk does not alter the physical media fixture; and
- function 13 clears the vector back to zero.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce the
same 295-byte BDOS binary. Growth of the dispatcher required widening three
relative branches; this is an internal placement change with no visible ABI
effect.

## Next increment

Implement function 27 (Get Allocation Vector Address) and function 31 (Get
Disk Parameter Block Address). These read-only introspection calls will expose
the current drive's existing DPH-derived state before file mutation begins.
