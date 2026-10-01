# Engineering Specification 183: FDF v1 Compiler Foundation

## Result

Implementation Step 4 has begun with a deterministic host-side implementation
of the approved FDF version-1 language and FDB version-1 serializer. The new
`tools/fdfcomp.py` command reads only the new `FDF_VERSION 1` grammar and writes
the frozen `BFDB` framing. It does not reinterpret the historical Montezuma
Micro numeric source.

The implementation validates identities, descriptions, DPB fields, derived BLM
and EXM rules, allocation and directory capacity, recorded geometry, byte-valued
IDs, topology and required extension construction. It emits:

- the 16-byte header and zero-filled first record;
- fixed 64-byte descriptors;
- per-descriptor sector-ID lists;
- required `81h` mixed-sector and `82h` cylinder-track TLVs;
- zero pool and record padding; and
- CRC-16/CCITT-FALSE over the complete serialized file.

Output is deterministic. The command writes and verifies a temporary host file
before replacing its destination. The serializer refuses the 16-bit FDB envelope
rather than truncating a catalogue.

## Focused evidence

The qualification source contains one uniform-sector descriptor, one
mixed-sector descriptor and one cylinder-track descriptor. Tests verify exact
header fields, pool placement, required TLVs, record padding, the published
`123456789 -> 29B1h` CRC check vector, deterministic regeneration and CP/M `1Ah`
source termination.

Negative fixtures reject duplicate fields and IDs, invalid identities, duplicate
sector IDs, geometry/SPT disagreement, missing directory reservations, unknown
fields and invalid cylinder topology.

## Remaining Step 4 work

This increment freezes executable compiler behavior; it does not claim CONFIG
integration or complete the historical catalogue migration. Engineering
Specification 184 supplies the independent FDB reader/validator. The remaining
increments must convert the 107 admitted reference definitions without changing
the five excluded source records, build the native/catalogue packaging path,
and integrate descriptor selection with CONFIG's normalized-binding transaction.
