# 166 — z80pack Executable ROM Relocation

Date: 2026-09-28  
Status: executable image implemented; boot integration pending

## Purpose

This increment applies the complete address inventory from Engineering
Specification 165 to the packed z80pack ROM artifact. It emits
`rom/rom-image.bin` and `rom/rom-image.json` from every complete z80pack build.

The new artifact is address-complete and may be entered at its recorded ROM
addresses after its RAM template has been initialized. It is not yet connected
to cold boot and has not yet passed enforced write-protected XIP qualification.
The manifest records those two facts separately so executable relocation cannot
be mistaken for completed ROM qualification.

## Relocation

`tools/build_rom_relocated_image.py` begins with the exact hash-identified
`rom-pack.bin` and `rom-references.json`. For each of the 759 disjoint packed
operands, it verifies the recorded old word before writing the resolved
destination:

- 429 operands target packed immutable ROM; and
- 330 operands target accepted live RAM.

Relocation occurs after packing because the protected image compacts multiple
immutable fragments around removed mutable objects. No single linear assembler
origin represents that final fragment layout; the two source-derived shifted
builds instead provide the complete relocation directory.

Of the 759 words, 748 change value and eleven already contain their final
stable RAM address. The relocation changes 1,496 bytes. No byte outside the
1,518 operand-byte positions may change.

The remaining nineteen layout-dependent words discovered by the shifted-layout
comparison reside in mutable source objects rather than packed code. All are
accounted for before the image may claim executable status:

- sixteen DPH pointer fields are the existing verified RAM-template fixups; and
- the three gateway descriptor words already contain their final stable RAM
  values: `D504h`, `D501h`, and `D501h`.

The relocation therefore accounts for all 778 layout-dependent words found by
the two independent shifted builds.

## Resulting entries

Relocation does not change the protected-region packing or its 649-byte spare
budget. The manifest publishes these address-complete inputs for the next boot
increment:

| Address | Purpose |
| --- | --- |
| `DF00h` | relocated resident system initializer |
| `DF20h` | relocated resident system BOOT entry |
| `F225h` | relocated BIOS BOOT vector |
| `DF9Eh` | relocated immutable BDOS entry |
| `F3F5h` | RAM initialization template |
| `FD61h` | position-independent cold initializer |

`rom-pack.bin` and its manifest remain the byte-exact non-executable packing
evidence. `rom-image.bin` is a separate derived artifact and its manifest sets
`executable` true, `boot_integrated` false, and
`protected_xip_qualified` false.

## Enforced evidence

`tools/test_rom_relocated_image.py` independently regenerates the image and
proves:

- the source pack and address inventory identities match;
- all 759 operands are disjoint and contain their recorded old values;
- every relocated operand contains its recorded new value;
- exactly 748 word values and 1,496 bytes change;
- every byte outside an inventoried operand remains byte-exact;
- inverse relocation reproduces `rom-pack.bin` exactly;
- all nineteen mutable layout words are accounted for by stable values or
  existing template fixups;
- component and ROM/RAM target totals retain their accepted values; and
- the executable manifest does not claim boot integration or protected-XIP
  qualification.

The next bounded increment connects cold boot to the initializer, RAM template,
relocated system entry and writable gateway. It must boot the relocated image
before enforced write protection is introduced as a separate qualification
step.
