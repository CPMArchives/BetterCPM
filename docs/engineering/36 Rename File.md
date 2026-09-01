# Engineering Specification 36: Rename File

## Milestone

BetterCP/M now implements the exact-name form of BDOS function 23 (Rename
File). Every extent of the source file in the current user area receives the
new name in one operation.

## Rename FCB and result

The source drive and eleven-byte source filename/type occupy normal FCB bytes
0 through 11. The destination drive byte is at byte 16 and its eleven-byte
name/type is at bytes 17 through 27. Both drive bytes currently accept current
drive or drive A.

`A=00h` reports that all matching extents were renamed. `FFh` reports invalid
input, absent source, existing target, software or file protection, wildcard
input, or a pending-allocation conflict. Storage failure is carried internally
and currently also maps to `FFh` at the BDOS boundary.

This milestone deliberately rejects `?` in either name. CP/M-style wildcard
rename requires positional substitution plus collision analysis for every
derived target and will be added separately rather than approximated.

## Preflight

Before modifying media, Rename:

- validates both drive fields;
- requires an empty pending-allocation journal;
- rejects an existing destination filename in the current user area;
- scans every source extent; and
- rejects the complete operation if any source extent has its T1 read-only
  attribute set.

The duplicate check applies across all destination extents, while the source
scan intentionally ignores `EX`, `S1`, and `S2` so the whole file moves
together.

## Mutation and attributes

The second directory pass replaces the low seven bits of all eleven source
name/type bytes. Each byte's high attribute bit is preserved from the original
directory entry, so Rename cannot silently clear read-only, system, archive,
or future attribute assignments.

Only changed directory records are written. Completion invalidates cached disk
state. As with multi-record Delete, a physical failure after an earlier record
write cannot be globally rolled back on CP/M media; BetterCP/M reports failure
and rebuilds state from the actual directory on the next filesystem operation.

## Verification

Executable tests rename two extents together and verify byte-level attribute
preservation. Separate preflight fixtures prove that an existing target and a
read-only second extent leave every source entry unchanged. Software protection
is also tested through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services and BDOS binaries.

## Next increment

Engineering Specification 37 implements function 30 (Set File Attributes),
completing the current function 12-through-32 range. Wildcard Rename remains a
separate compatibility enhancement; the next core work begins random-record
support with function 35 (Compute File Size).
