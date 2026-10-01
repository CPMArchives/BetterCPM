# Engineering Specification 190: Native FDB Binding Construction

## Result

CONFIG's native reader can now decode any selected supported descriptor into
the existing self-contained 64-byte normalized BIOS binding. The constructor:

- copies the standard 15-byte CP/M DPB;
- installs cylinders, physical-sector count, and maximum sector-size code;
- translates normalized FDB topology flags to the established MM-compatible
  binding bits;
- copies up to 32 ordered sector IDs;
- maps required cylinder-track extension `82h` to the established internal
  cylinder-profile bit; and
- packs required mixed-sector extension `81h` into the existing two-bit-per-
  sector explicit size map used by FDF.RSX and the platform disk layers.

Descriptors marked unsupported by an unknown required extension refuse binding.
Descriptors requiring more than the current binding's 32 sector-ID slots also
refuse binding rather than truncating. The BIOS remains the final validator of
hardware capability and the completed binding when CONFIG submits it.

The constructor adds 307 bytes over Engineering Specification 189. CONFIG is
11,481 bytes, leaving 4,135 bytes below its 15,616-byte transient ceiling. It
does not change resident memory or the 53 KiB TPA contract.

## Focused evidence

`tools/test_native_fdb_reader.py` executes the native constructor for all 107
admitted descriptors and compares every byte of every resulting binding with
an independently decoded expected binding. This covers uniform FM and MFM
formats, every normalized topology flag, the cylinder-track descriptor, and
all four mixed-sector SUPER descriptors. The same test proves that a descriptor
carrying an unknown required extension remains catalogued but refuses binding.

A fresh z80pack release image passes `tools/test_config_fdb_runtime.py`, proving
that the expanded CONFIG loads, validates the packaged catalogue, and reaches
its main menu under cpmsim.

## Remaining Step 4 boundary

Engineering Specification 191 switches CONFIG's format-selection UI, live-name
matching, and attachment transaction to native FDB names and bindings. Dead
legacy parser code still enters CONFIG through the shared utility include, and
release media still package `DISK.FDF`; their removal and cross-platform closure
remain the final Step 4 work.
