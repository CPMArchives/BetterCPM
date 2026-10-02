# CONFIG pending startup command

## Scope

CONFIG option `J` now maintains a private pending `BCST` record for the life of
the utility. The first visit loads and validates the installed record. Later
visits reuse the pending copy, so an edit survives movement through CONFIG's
other menus without changing protected media.

The panel can replace the command through the ordinary 126-byte BDOS counted
line editor or clear it to a canonical disabled record. An empty edit keeps the
current value. CONFIG accepts printable ASCII command bytes only. Every accepted
edit reconstructs the complete canonical record, zeros its reserved area and
recalculates its 16-bit checksum.

CONFIG labels changed state as not saved. Neither Edit nor Clear writes the
system disk. Immediate command testing and explicit save scopes remain later
bounded increments of Step 5 deliverable 2.

## Qualification

The disk-utility build remains below CONFIG's `3E00h` private-stack boundary;
`CONFIG.COM` is 10,058 bytes and adds no resident memory use. Focused trs80gp
cases prove that an edit to `VER` survives return to the main menu and re-entry,
that Clear disables an enabled command, and that both operations leave the
protected `BCST` records byte-for-byte unchanged. The existing disabled,
enabled and invalid-record display cases continue to pass.
