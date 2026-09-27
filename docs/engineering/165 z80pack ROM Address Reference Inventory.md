# 165 — z80pack ROM Address Reference Inventory

Date: 2026-09-27  
Status: complete; source relocation pending

## Purpose

This increment identifies every layout-dependent 16-bit word emitted inside the
immutable fragments of the z80pack resident system. It resolves each word to
one destination in the accepted packed-ROM or live-RAM map before any source is
rewritten. The result is `rom/rom-references.json` in each complete z80pack
build.

The inventory is diagnostic evidence. It does not alter resident code and does
not make `rom-pack.bin` executable.

## Discovery method

`tools/build_rom_reference_inventory.py` makes two disposable source copies and
rebuilds the resident components after shifting the linked resident layout by
`0101h` and `0203h`. These unequal, non-page-aligned deltas distinguish complete
16-bit address words from individual bytes and constants. Every changed byte
must be reproduced by applying the corresponding delta to a discovered word in
both alternate images. An unexplained byte, changed component size or
non-reproducible alternate image fails the build.

The alternate layouts shift the resident system, BDOS, extensions, disk, BIOS,
file loader, tables, resident state, buffers and current TPA boundary together.
They deliberately keep `LY_RSX` fixed because the optional RSX region is
already RAM rather than code that will enter the protected ROM image. Transient
load and stack addresses and boot-sector counts also remain fixed.

The comparison discovered 778 layout-dependent words in the complete source
components. Nineteen have operand bytes in objects already classified mutable:
three in the gateway and sixteen in the live disk tables. The remaining 759
words occur in packed immutable fragments:

| Component | Packed-code references |
| --- | ---: |
| Gateway | 23 |
| BDOS | 520 |
| Extensions | 57 |
| Disk service | 82 |
| BIOS | 64 |
| File loader | 13 |
| Disk tables | 0 |
| **Total** | **759** |

The measured extension count is 57. The source emits one fixed-RAM
`LY_RSX+03FDh` stack address; because `LY_RSX` does not move in either alternate
layout, that word is correctly absent from the ROM-relocation inventory.

## Destination resolution

Every packed operand resolves against the exact fragment map from
`rom-pack.json`, the source-derived ownership inventory, and the accepted
z80pack RAM map. The result contains:

- 429 references to immutable code or constants in packed ROM; and
- 330 references to live objects in writable RAM.

Duplicate ownership descriptions for the same source range are merged only
when they produce the same destination. Any absent or conflicting destination
fails inventory generation.

One numeric address has two legitimate meanings in the current linked image:
`E49Fh` is both the extension entry and the exclusive end of the BDOS stack.
The emitted operand expression disambiguates them. Jumps to `LY_EXT` resolve to
packed ROM; `LD SP,UB_STKTOP` resolves to the exclusive end of the relocated RAM
stack. The same rule handles `SYS_STKTOP`. This is the only source-semantic
special case admitted by the inventory.

Each record retains the component, source address and offset, packed operand
address, old and proposed target, target class and owners, plus assembler source
line and text. This makes the subsequent source relocation reviewable one
operand at a time.

## Enforced evidence

`tools/test_rom_reference_inventory.py` freezes the component and target-class
counts and verifies that:

- both independent shifted layouts were used;
- every changed byte was explained and both alternate images reproduced;
- every recorded old target still matches its source binary;
- every operand lies wholly inside exactly one immutable packed fragment;
- the packed image still contains the source word at the recorded address;
- every target has a class and at least one owner; and
- every reference retains assembler source context.

The complete z80pack builder runs generation and validation after immutable ROM
packing. A focused `--resident-only` build mode exists solely to produce the
disposable alternate-layout artifacts without recursively constructing media or
another inventory.

The next bounded increment is source relocation using this frozen inventory.
It must update references in controlled owner groups and retain exact count and
destination checks; protected execution remains a later acceptance step.
