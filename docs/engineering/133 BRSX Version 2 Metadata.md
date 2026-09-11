# Engineering Specification 133: BRSX Version 2 Metadata

## Status

Stage-2 carrier and tooling implemented; resident loader and Function 208
integration pending.

## Compatibility

BRSX version 2 preserves the fixed 48-byte version-1 carrier prefix where its
meaning remains applicable. Byte 4 is 2. Flags bits 0-1 contain the
reconstruction class: 0 STATELESS, 1 STATEFUL, 2 STATE_PRESERVING, and 3
COLD_ONLY. Version-1 images retain their existing untyped numeric-service tail
and are treated as legacy stateless numeric interceptors.

## Typed metadata stream

The word at carrier offset 30 points to a metadata envelope following the
linked payload. The envelope is little-endian:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 4 | `BMET` signature |
| 4 | 1 | metadata major version: 1 |
| 5 | 1 | metadata minor version: 0 |
| 6 | 1 | envelope header length: 12 |
| 7 | 1 | record count |
| 8 | 2 | total metadata length including envelope |
| 10 | 2 | reserved; zero |
| 12 | variable | typed records |

Each record begins with a one-byte type and one-byte payload length. Zero
length records are invalid. Metadata version 1 defines:

| Type | Payload |
|---:|---|
| 1 | one byte per intercepted numeric BDOS service |
| 2 | one 10-byte callable-service advertisement |
| 3 | sorted, unique 16-bit runtime-pointer slot offsets |

A callable advertisement is a four-byte service ID, ABI major, ABI minor,
16-bit entry offset from the RSX base, and 16-bit capability flags. Stage 2
allows at most two callable advertisements per provider.

## Runtime provider descriptor

Validated advertisements must be available without disk I/O while Function
208 executes. They are not duplicated in the PDS. A BRSX-v2 provider reserves
this loader-owned header at the beginning of its live allocation:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 2 | next dispatch address |
| 2 | 2 | this module's dispatch address |
| 4 | 1 | callable-service count |
| 5 | 1 | reserved; zero |
| 6 | 2 | offset of materialized service descriptors |

The loader materializes each validated 10-byte advertisement at the top of the
provider's allocation and sets the offset at +6. That range is loader-owned
and excluded from module workspace and STATEFUL pointer slots. Function 208
walks active RSX headers and these descriptors, deriving each callable address
as provider base plus entry offset. This retains no flat absolute-address table
in the PDS and charges metadata to the provider that supplies it.

The carrier builder includes the descriptor bytes when calculating the minimum
page-rounded allocation. BRSX-v2 dispatch and callable entries must lie beyond
the eight-byte runtime header and within the emitted payload.

