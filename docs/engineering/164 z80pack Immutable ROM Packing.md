# 164 — z80pack Immutable ROM Packing

Date: 2026-09-27  
Status: deterministic packing implemented; executable relocation pending

## Purpose

This increment proves that every accepted immutable byte, the RAM template and
the executable cold initializer fit together in the protected `DF00h..FFFFh`
region. It emits `rom/rom-pack.bin` and a hash-bearing `rom/rom-pack.json` from
each z80pack target build.

The artifact is deliberately marked non-executable. Resident code still carries
absolute references from the current RAM-linked layout. Calling the artifact a
bootable ROM before those references are relocated would conceal the remaining
engineering work.

## Classification and layout

The packer reads the source-derived ownership inventory rather than maintaining
a second hand-written list of writable offsets. For each resident component it
marks every overlapping z80pack mutable-owner range, packs the complementary
immutable fragments and records both their source and destination intervals.

The resulting protected-region budget is:

| Content | Bytes |
| --- | ---: |
| Immutable resident-source fragments | 5,365 |
| RAM initialization template | 2,412 |
| Position-independent cold initializer | 22 |
| Erased-state spare space | 649 |
| **Protected region** | **8,448** |

The corresponding packed intervals are:

| Range | Content |
| --- | --- |
| `DF00h..F3F4h` | immutable resident-source fragments |
| `F3F5h..FD60h` | RAM initialization template |
| `FD61h..FD76h` | position-independent cold initializer |
| `FD77h..FFFFh` | erased-state spare space |

The manifest publishes the candidate ROM addresses that a later entry stub will
pass for the RAM template and immutable BDOS entry, plus the initializer's own
address. The candidate immutable BDOS entry is `DF9Eh`. These are packing
results, not public ABI addresses.

## Enforced evidence

The focused verifier regenerates the artifact and proves:

- the complete image is exactly 8,448 bytes and hash reproducible;
- all 5,365 immutable bytes are drawn byte-for-byte from identified components;
- their complementary 866 source bytes are classified mutable content;
- the template and initializer match their independently hashed artifacts;
- segment ranges do not exceed the protected region;
- all remaining 649 bytes contain erased-state `FFh`; and
- the manifest continues to deny executable status until relocation succeeds.

Engineering Specification 165 completes the next bounded increment: all 759
address words in packed resident fragments resolve to either packed immutable
ROM or the accepted live-RAM map. Source relocation and protected execution are
still required before executable status can change.
