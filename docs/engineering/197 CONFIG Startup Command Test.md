# CONFIG startup-command test

## Scope

CONFIG option `J`, command `T`, immediately tests the pending startup command
without saving the pending `BCST` record. The test uses the stock CCP command
path: CONFIG writes one counted command to `A:$$$.SUB`, selectively relogs A:
and warm boots. The CCP then reads, parses and dispatches the command exactly as
it would any other submitted command. This exercises resident commands, CPXs
and transient programs without adding another private BDOS interface.

CONFIG refuses the test when the pending command is disabled or when
`A:$$$.SUB` already exists. It therefore never replaces an active submitted
command stream. Creation or write failure removes any partial stream and
reports the failure before returning to CONFIG.

## Length boundary

The version-1 startup record admits 126 command bytes. The stock submission
record has one count byte and reserves its final two bytes, leaving room for at
most 125 command bytes. CONFIG consequently refuses Test now for a 126-byte
pending command and explains that the same command remains valid for cold-boot
execution. This limitation belongs only to the interactive test mechanism; it
does not narrow the saved startup-command contract.

## Qualification

Focused trs80gp cases prove that a disabled command is rejected, an edited
pending `VER` command executes through the CCP and a 126-byte command receives
the boundary diagnostic. The tests also prove that Test now leaves the saved
`BCST` records byte-for-byte unchanged.

The first execution probe created a valid one-record submission stream but the
warm CCP did not see the newly created directory entry. Media inspection and a
cold boot of that exact image proved that the record and CCP path were valid.
A selective BDOS Function 37 relog of A: before warm boot made the command
visible while preserving the current default drive. This is the production
path covered by the passing test.
