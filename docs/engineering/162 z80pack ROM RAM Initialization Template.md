# 162 — z80pack ROM RAM Initialization Template

Date: 2026-09-27  
Status: representation implemented; executable initializer pending

## Purpose

This increment generates the deterministic writable image that a later ROM cold
entry will instantiate in the RAM map accepted by Engineering Specification 161.
It verifies representation and pointer relocation without adding executable
initialization code or claiming protected boot.

`tools/build_rom_ram_template.py` writes `rom/ram-init.bin` and a hash-bearing
`rom/ram-init.json` beside each generated z80pack target. The target builder then
regenerates and verifies both artifacts with `tools/test_rom_ram_template.py`.

## Initialization policies

The RAM map now assigns every range one explicit policy:

- `copy` transfers immutable default bytes into the new live object;
- `copy-fixup` transfers defaults and repairs declared internal pointers;
- `zero` clears stacks, scratch storage and reserved ranges; and
- `runtime` leaves the dynamic gateway and command-history signature invalid for
  their existing owners to construct during cold entry.

The template is 2,412 bytes covering `D501h..DE6Ch`. Copied defaults include the
descriptor header and fields, CPX profile, BDOS state, physical-drive profiles,
disk session, BIOS disk state and live disk tables. Stacks, file and directory
scratch, the RSX profile and the full 1,024-byte transfer workspace begin zero.

## DPH pointer relocation

Each of the four copied 80-byte DPH/binding records contains four live pointers.
The generator rewrites all sixteen to the new map:

- directory buffer: `D9EDh`;
- per-drive DPB: record base plus 17;
- per-drive CSV: `D944h` plus 32 bytes per drive; and
- shared ALV: `D8C4h`.

The focused test checks all sixteen values. A copied old-layout pointer therefore
fails artifact generation before any ROM boot is attempted.

## Boundary

This representation does not change the `DF00h` protection boundary, RAM sizes,
stack sizes, workspace allocation or TPA. The template will ultimately reside in
ROM as initialization data; the later immutable-image budget must count it until
the implementation proves that a smaller encoded form is required and correct.

The current z80pack resident component files contain 5,365 bytes outside their
identified mutable ranges. Conservatively counting all of those bytes plus the
2,412-byte template uses 7,777 of the 8,448 protected bytes and leaves 671 bytes
for cold-entry code and image metadata. The generator rejects a negative budget,
and the focused test freezes these current measurements so later growth requires
an explicit placement or representation decision. The estimate deliberately
retains padding and possible template duplication; later immutable-image
construction may remove them but cannot depend on that saving yet.

The next bounded step is executable cold-entry code that copies this exact
template into RAM, completes the runtime-owned gateway and history lifecycle,
and can be tested in isolation before the resident code is relocated.
