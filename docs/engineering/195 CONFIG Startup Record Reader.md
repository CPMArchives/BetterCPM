# CONFIG startup-record reader

## Scope

This increment begins Step 5's CONFIG startup controls without changing saved
media. CONFIG option `J` reads the version-1 `BCST` record from protected
logical records 1 and 2 and reports the saved command, disabled state or an
invalid record. Editing, clearing and saving the command remain the next
bounded increment.

## Validation

CONFIG accepts only the representation frozen in Engineering Specification
193. It checks the `BCST` magic, major and minor version, 16-byte header,
enabled flag, command length, 126-byte capacity, 256-byte record size,
resident-system binding and zero 16-bit word sum. Enabled state and length must
agree, command bytes must be printable ASCII and every unused byte must be
zero. Any failure reports the record as invalid; CONFIG neither repairs nor
writes it.

The reader selects boot drive A through the running BIOS and uses the existing
protected-record I/O path with a zero record origin. CONFIG H retains its
previous record origin and its previously qualified save path unchanged.

## Qualification

`tools/test_config_startup_read.py` builds private media and verifies three
cases under trs80gp: the canonical disabled record, an enabled `VER` command
and a checksum-corrupt record. All three cases pass. The utility build and
Python syntax checks pass, and the source diff is whitespace-clean.

The older CONFIG H regression relies on trs80gp `-iw` text waits. Under the
LaunchServices wrapper documented by Engineering Specification 194, that test
can stall before its requested post-confirmation capture. Two bounded probes
reproduced the automation stall, including after CONFIG H's original source
path was restored. This increment therefore does not claim a new CONFIG H
runtime qualification result and does not migrate that test to the wrapper.
