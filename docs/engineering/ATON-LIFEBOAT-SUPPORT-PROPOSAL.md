# ATON/Lifeboat support: implementation decision

Status: proposed, 2026-11-06. This does not amend the FDF/FDB contract or
qualify a runtime format. Original-media evidence is in
[the Model II investigation](evidence/2026-11-06-model2/README.md).

## Recommended scope

Implement file interchange for single-sided ATON/Lifeboat and double-sided
ATON on cpmsim, retaining original sector identities and data. Keep the
Model 4 binding unsupported until an appropriate 8-inch recording adapter is
implemented and tested. This is not a Model II OS port. Booting and formatting
the historical system surface are outside the initial file-interchange claim.

There are two substantive changes: an explicit reserved-surface exception in
the format contract and enough protected directory-checksum storage for CKS 48.
Neither can be replaced by a catalogue-only change.

## Required reserved-surface description

Add a bounded required extension for the first physical surface only,
cylinder 0/head 0. Require that it is inside the reserved area (`OFF >= 1`
with the applicable logical-track mapping). The existing physical fields
continue to describe the remaining surfaces; SPT and the OEM DPB remain
unchanged. Do not introduce general track ranges or arbitrary layout tables.

Proposed text fields, supplied together:

```text
BOOT_PSECTORS   26
BOOT_SECSIZE    128
BOOT_ENCODING   FM
BOOT_SECTOR_IDS 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26
```

Proposed required TLV kind 3 (83h; not yet assigned): encoding, size code,
sector count, followed by that many distinct sector IDs. The observed profile
needs 29 payload bytes. The implementation must validate all sizes, counts,
reserved-area constraints and topology interactions. Older readers must mark
the descriptor unsupported, not ignore the exception.

Update host and native compilation, decompilation, validation, CONFIG binding,
FDB editing and round trips together. A new CONFIG running against an older
BIOS must also refuse the binding; recognition by the catalogue reader alone
is insufficient. The disk-service capability/binding contract must carry and
validate this requirement explicitly before any image access.

For initial cpmsim interchange, a reversible host adapter can expand the
3,328-byte first surface into an explicitly defined 8,192-byte canonical slot.
All later cylinder/head/sector addresses remain unchanged. The added padding
is container representation, never newly discovered disk content. Keep the
original IMD and verify that the entire reserved prefix remains unchanged
when mapping guest-written data back into it. Guest operations on the
exceptional surface must be refused until its actual layout is implemented;
formatting must not silently turn it into an ordinary MFM surface.

This would qualify file I/O through the documented adapter, not direct use of
the original variable-length raw stream or physical-media interchange. The
adapter and backend capability are part of the qualification receipt.

## Checksum storage and memory constraints

Both current platform table builders allocate four persistent 32-byte CSVs.
The Model 4 validator rejects CKS > 32. The cpmsim validator previously tested
only the high byte and could accept CKS 33–255, despite the same buffer bound.
The accompanying narrow fix rejects values above 32 before publishing a
binding. It does not enable double-sided ATON or change memory allocation.

Measured default cpmsim resident build after that fix:

| Component | Used bytes | Region capacity | Unused bytes |
|---|---:|---:|---:|
| BIOS | 623 | 757 | 134 |
| Disk service | 916 | 942 | 26 |
| Configuration overlay | 915 | 1,024 | 109 |
| Disk tables | 576 | 576 | 0 |

The preferred bounded implementation is four 48-byte CSVs, preserving the
full OEM checksum coverage and current TPA/history. Two vectors can occupy
96 bytes of the existing 128-byte CSV region. The other two would need an
explicitly reserved, initialized 96-byte mutable region taken from cpmsim's
134-byte BIOS-region headroom. This leaves 38 bytes for BIOS growth. It must
have checked ownership and build bounds; anonymous writable padding is not
acceptable. The shared ALV remains 128 bytes and retains its existing limit.

Review cold initialization, restart/install carriers, checked profiles and
ROM/RAM ownership before adopting that placement. ROM code must never be
treated as writable CSV storage. If these contracts cannot accommodate the
region safely, return to the memory-layout decision instead of silently
reducing TPA or the number of checksum entries. A general dynamic CSV allocator
is a competing approach, but adds allocation, movement and failure semantics
for four small fixed objects; it is not the first choice for this scope.

## Admission checks

1. Preserve old FDF/FDB encodings and existing catalogue output. Exercise
   new/old reader and BIOS capability combinations, malformed required TLVs,
   native edit/export/import, and unsupported-operation rejection.
2. Prove each CSV fits its assigned mutable region. Test CKS 32 and 48,
   rejection beyond the new bound, simultaneous drive use, media-change
   detection and no overlap with BIOS, other vectors, or ALV. Keep TPA and
   history unchanged; rebuild all affected platform components together.
3. Check every original sector before/after adapter round trips, including
   the exceptional boot surface, alternating heads and skew-3 data mapping.
   Retain the malformed ATON image as a rejection fixture.
4. Run five independent BetterCP/M guest trials concurrently with private
   writable media. Each trial reads all original files, fills free space,
   writes and reads block 299 or 607, and preserves existing file contents,
   directory metadata, all reserved bytes and image bounds.
5. Extract every resulting IMD independently and compare hashes. Rerun the
   existing CPC/PCW interchange set against the changed backend. Only then
   admit the entries to the supplemental catalogue, explicitly scoped to
   the qualified cpmsim adapter. Record Model 4 as unsupported, not passed.

## Validation of the immediate fix

`python3 -B tools/test_z80pack_checksum_binding.py` assembles and executes the
actual configuration overlay. CKS 0/16/32 are accepted; 33/48/255 are rejected;
256 is invalid. Rejected requests preserve every resident table/vector byte.
Running the same test against the previous source confirms that CKS 33 was
incorrectly accepted. The resident-only default cpmsim build also passes its
existing component bounds. These are machine-code and build checks, not a
new guest disk-format pass.
