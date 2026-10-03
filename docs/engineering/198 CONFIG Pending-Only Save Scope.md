# CONFIG pending-only save scope

## Scope

CONFIG option `H` now presents the two adopted save meanings explicitly. Scope
`A` saves pending cold-boot changes only. This increment has one pending-state
owner, the version-1 `BCST` startup-command record, so scope `A` writes only
protected logical records 1 and 2. It does not read active physical or logical
drive definitions and therefore cannot capture temporary session disk changes.

Scope `B` retains the established save-current-drive path when no startup edit
is pending. CONFIG refuses that scope when a pending command exists because the
current drive writer cannot yet combine both categories into one validated and
rollback-protected operation. The next save-scope increment will remove that
temporary restriction by completing the all-current merge.

## Write protection

Before writing, CONFIG reads and preserves both installed records and validates
the complete proposed `BCST` record. It writes and immediately rereads each
record. An ordinary write or comparison failure attempts to restore and verify
both original records, including the record whose failed write may have been
partial. The existing limitation remains: loss of power during the operation
is not atomic.

The save workspace overlaps CONFIG's transient FDB catalogue buffer. Every
save outcome reloads the catalogue before returning to the menu. Successful
save clears the private dirty flag; declining or failing the operation does
not silently alter the pending command.

## Qualification

The complete system and disk utilities build successfully. `CONFIG.COM` is
11,625 bytes and remains below its `3E00h` private-stack boundary. A focused
trs80gp case edits the pending command to `VER`, selects scope `A`, and verifies
the success report. Host-side media comparison proves that the resulting
canonical `BCST` record is the only changed region. A fresh CONFIG invocation
then reads `VER` from the saved record.

The earlier aggregate startup-control test stalled in its pre-existing Test-now
case without reporting a product assertion. Per the bounded diagnostic rule,
qualification was narrowed to the two new save/reload cases rather than opening
an unrelated emulator session. Fault-injection coverage for the rollback path
remains part of completion of the combined save-scope work.
