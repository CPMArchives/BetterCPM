# CONFIG all-current save scope

## Scope

CONFIG H scope `B` now saves active physical and logical drive settings together
with any pending startup-command change. The pending value takes precedence
over the installed startup default. Scope `A` remains the narrower operation
which saves only pending cold-boot state and cannot capture temporary drive
changes.

The established `SYSGEN.DAT` carrier remains unchanged. Its 52 original
records occupy `4080h` through `5A7Fh`; the all-current operation uses the
existing gap at `5A80h` for the two installed startup records. The proposed
drive image remains at `6000h` and the readback buffer remains at `8000h`.
CONFIG consequently rejects a carrier larger than 52 records before it can
overlap transaction state.

## Transaction

CONFIG validates the complete pending `BCST` record and the complete proposed
drive carrier before asking for confirmation or writing. If pending state is
present, it preserves records 1 and 2, then writes and verifies the proposed
startup record before writing changed carrier records 8 through 59.

Any ordinary write or comparison failure rolls changed carrier records back
to their installed values and then restores and verifies both startup records.
A failure while writing the startup record restores those records without
touching the carrier. Success clears the pending dirty flag. Declining the
operation writes nothing. Loss of power remains outside the rollback guarantee.

## Qualification

The complete system builds successfully. `CONFIG.COM` is 11,822 bytes and
remains below its `3E00h` private-stack boundary. A focused trs80gp test changes
an active drive setting, edits the pending command to `VER`, and selects scope
`B`. Byte comparison permits changes only in the two `BCST` records and the
documented editable drive fields. Separate cold boots prove the saved drive
setting and startup command are both present.

The same test installs a guarded BIOS write hook which fails the second write.
This interrupts the startup-record portion of the combined transaction. CONFIG
reports successful restoration, and a byte-for-byte comparison proves that the
entire protected image matches its pre-save state.
