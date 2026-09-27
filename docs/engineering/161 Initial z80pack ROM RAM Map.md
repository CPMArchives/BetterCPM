# 161 — Initial z80pack ROM RAM Map

Date: 2026-09-27  
Status: initial placement implemented; source relocation pending

## Purpose

This increment turns the z80pack ownership inventory into the first enforced
RAM placement for the 1.0 ROM profile. It assigns addresses and derives a
protection boundary without moving source objects, constructing the immutable
image or claiming unproven workspace and stack reductions.

The map is `metadata/rom-profile-ram-z80pack.tsv`. The z80pack image builder
validates it after validating the source-derived ownership inventory.

## Placement rules

The map preserves `D501h..D6BBh` as the fixed gateway/PDS envelope. This keeps
the writable dispatch gateway, 192-byte history object, system stack, live
descriptor and CPX profile at their current ABI addresses. Its 158 bytes not
owned by writable objects remain reserved for live descriptor constants, stable
entry trampolines, COM handoff and gateway growth. Their reservation makes no
claim that ordinary immutable gateway routines will remain in RAM.

The remaining objects follow contiguously by natural owner:

| Range | Bytes | Owner group |
| --- | ---: | --- |
| `D6BCh..D728h` | 109 | BDOS state and stack |
| `D729h..D72Dh` | 5 | Extension state |
| `D72Eh..D753h` | 38 | z80pack disk state |
| `D754h..D75Fh` | 12 | BIOS disk state |
| `D760h..D783h` | 36 | File-stream FCB |
| `D784h..D9C3h` | 576 | Live disk tables |
| `D9C4h..D9ECh` | 41 | RSX profile |
| `D9EDh..DA6Ch` | 128 | Directory buffer |
| `DA6Dh..DE6Ch` | 1,024 | Physical/module/CONFIG workspace |

No workspaces overlap in this map. The full 1,024-byte area remains allocated,
and both existing stack sizes remain unchanged.

## Derived boundary and budgets

The 2,254 bytes of owned RAM plus 158 reserved bytes occupy 2,412 contiguous
bytes from `D501h` through `DE6Ch`. Rounding the exclusive end upward to the
cpmsim protection granularity derives `DF00h` as the initial ROM boundary.

This provides:

- 147 spare bytes between the last assigned byte and the derived `DF00h`
  boundary;
- 1,171 bytes between the last assigned byte and the former `E300h` planning
  limit;
- 8,448 bytes of protected address space from `DF00h` through `FFFFh`; and
- 54,273 usable TPA bytes from `0100h` through `D500h`, preserving the 53 KiB
  floor and the 54,272-byte record-aligned COM ceiling.

`DF00h` replaces `E300h` only as the derived implementation input for this
initial z80pack map. It is not public ABI. Later source relocation must still
prove that the immutable image, templates and cold initializer fit its 8,448
bytes; otherwise the builder must report the measured conflict rather than
silently move the boundary.

## Enforced checks

`tools/test_rom_profile_ram_map.py` rejects:

- a missing or extra owned object;
- a size disagreement with the ownership inventory;
- overlapping or noncontiguous placement;
- an unexplained reserved range;
- a changed owned or reserved byte total;
- a derived boundary other than `DF00h` or above the former `E300h` planning
  limit; and
- a TPA below 53 KiB.

The next bounded step is to generate the RAM initialization template and cold
initializer for this map. Executable and constant relocation follows only after
the initializer has a focused representation test.
