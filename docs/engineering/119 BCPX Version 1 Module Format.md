# Engineering Specification 119: BCPX Version 1 Module Format

## Decision

The `BCX1` proof carrier is superseded by the versioned `BCPX` format. Version
1 is a general relocatable Command Processor Extension carrier: the protected
loader selects an arbitrary eight-character filename stem from the persistent
reconstruction table and does not identify BASIC or HELLO itself.

The first 512-byte record group contains the structural header and relocation
directory. Executable code follows at byte 512. Command metadata follows the
executable bytes and is not copied into command-environment memory.

## Version 1 header

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 4 | `BCPX` signature |
| 4 | 1 | format version, `1` |
| 5 | 1 | module class, `1` for CPX |
| 6 | 1 | required CPX ABI major, `1` |
| 7 | 1 | required CPX ABI minor, `0` |
| 8 | 2 | flags; all undefined bits must be zero |
| 10 | 2 | link base |
| 12 | 2 | executable byte count |
| 14 | 2 | page-rounded runtime allocation |
| 16 | 2 | command-entry offset |
| 18 | 2 | initialization offset, or `FFFFh` |
| 20 | 2 | shutdown offset, or `FFFFh` |
| 22 | 2 | relocation count |
| 24 | 2 | header size, currently 512 |
| 26 | 2 | payload offset, currently 512 |
| 28 | 2 | relocation-directory offset, currently 48 |
| 30 | 2 | command-metadata offset |
| 32 | 8 | uppercase, space-padded module name |
| 40 | 2 | module major and minor version bytes |
| 42 | 1 | number of exported command names |
| 43 | 1 | reserved |
| 44 | 2 | additive 16-bit payload checksum |
| 46 | 2 | reserved |

Each relocation is a little-endian 16-bit offset into the executable image.
Each command-metadata record is an uppercase, space-padded eight-byte name.
Version 1 permits at most 232 relocation records in its first header group.

## Loader behavior

The loader validates signature, format, class, required ABI, nonzero size,
page-rounded allocation, aligned section boundaries, relocation count and
sites, and command-entry bounds before publishing the runtime entry. It loads
only the executable byte count, applies each relocation against the calculated
runtime base, writes the validated entry address into the common runtime
header, and links the module in persistent-table order.

`BCM1` remains the private CCP carrier and is normalized into the loader's
internal descriptor rather than being mistaken for a CPX header. This explicit
split preserves CCP compatibility while allowing the CPX format to evolve.

## Verification

`tools/test_cpx_format.py` checks both shipped modules' identity, ABI, section
layout, relocation bounds, names, command metadata, and payload checksums.
The reloader tests exercise arbitrary filename-driven restoration and
relocation; physical `trs80gp` tests verify BASIC/HELLO ordering, unloading,
reloading, WBOOT reconstruction, and directory-write integrity.
