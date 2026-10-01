# Engineering Specification 187: Native CONFIG FDB Framing Gate

## Result

CONFIG now opens `DISK.FDB` on the current drive, falls back to drive A, and
loads the complete file into its existing catalogue workspace. Before entering
the utility, native Z80 code validates the version-1 signature, major version,
header and descriptor stride bounds, first-descriptor offset, descriptor-pool
arithmetic, reserved header bytes, complete-record length, and whole-file
CRC-16/CCITT-FALSE. Missing or invalid catalogues are rejected explicitly.

This is a transitional integration boundary. After the binary catalogue passes
the gate, CONFIG still loads `DISK.FDF` and uses the established text parser for
its menus and binding construction. The increment therefore proves native file
I/O and validation against the catalogue actually shipped on the media without
changing disk-state semantics in the same step.

CONFIG is 10,152 bytes after integration, below its 15,616-byte transient
ceiling. The catalogue occupies the existing `4000h` workspace and does not
consume resident memory or reduce the TPA.

## Focused evidence

`tools/test_native_fdb_reader.py` executes the native validator in the Z80 test
machine. It accepts the 107-descriptor canonical catalogue and its compatible
newer minor version, verifies the descriptor-pool offset and restored CRC
bytes, and rejects truncation, CRC damage, invalid framing, bad offsets, and
nonzero reserved bytes.

`tools/test_config_fdb_runtime.py` boots freshly built release media under
cpmsim, invokes CONFIG, and requires the main menu. This proves that CONFIG
opens and validates the packaged `DISK.FDB` through the real BDOS path.

## Remaining Step 4 boundary

Engineering Specification 188 adds bounded descriptor enumeration, fixed-prefix
validation, sector-ID-reference bounds, and indexed description lookup. Native
extension/object validation and normalized binding construction still remain;
only after those are qualified can `FNAME` and `FPARSE` be replaced together
and the transitional runtime dependency on `DISK.FDF` removed.
