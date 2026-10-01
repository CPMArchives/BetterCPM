# Engineering Specification 188: Native FDB Descriptor Enumeration

## Result

CONFIG's native FDB reader now walks every advertised descriptor rather than
accepting only the file-level envelope. For each descriptor it validates the
fixed version-1 prefix required for safe enumeration:

- the ID is one through eight uppercase ASCII letters or digits followed only
  by space padding;
- the 32-byte description is printable and nonempty;
- physical-sector count and cylinder count are nonzero;
- the repeated sector-ID count agrees with the physical-sector count;
- the physical-sector size code is one of the four version-1 values;
- the sector-ID list starts in the object pool and ends within the file; and
- the extension-present flag agrees with a zero or nonzero extension offset.

The reader exposes bounded indexed routines for obtaining a descriptor and its
space-padded display description. An index equal to or greater than the
catalogue count fails with carry. CONFIG still uses its historical text names
after validation because the binary catalogue and text parser presently share
the same transient workspace.

CONFIG is 10,414 bytes after this increment, leaving 5,202 bytes below its
15,616-byte transient ceiling. No resident memory or TPA is consumed.

## Focused evidence

`tools/test_native_fdb_reader.py` executes the new enumeration and lookup code
in the Z80 test machine. It validates all 107 canonical descriptors, checks
description addresses and bytes at the first, middle, and final entries, and
rejects an out-of-range index. CRC-repaired negative fixtures independently
exercise each fixed-prefix and sector-ID-reference rejection listed above.

A fresh z80pack image then passes `tools/test_config_fdb_runtime.py`, proving
that the expanded native validation accepts the catalogue installed on actual
release media and reaches CONFIG's main menu under cpmsim.

## Remaining Step 4 boundary

Engineering Specification 189 completes native extension framing, object
ownership and overlap, sector-ID uniqueness, assigned-extension validation,
and unsupported-required-extension marking. Semantic DPB/geometry validation
and normalized binding construction still remain. CONFIG's menus stay on the
transitional `DISK.FDF` path until binary lookup and `FPARSE` can be replaced
together.
