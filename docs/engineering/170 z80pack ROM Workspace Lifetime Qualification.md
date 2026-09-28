# z80pack ROM workspace-lifetime qualification

## Decision

The z80pack 1.0 ROM profile retains the complete 1,024-byte workspace at
`DA6Dh..DE6Ch`. Its current static sharing is safe, but none of the reservation
can be reclaimed. Three mutually exclusive lifetime classes account for it:

| Operation | Lower 512 bytes | Upper 512 bytes |
| --- | --- | --- |
| 1,024-byte physical-sector transfer | physical-sector staging | physical-sector staging |
| CPX/RSX carrier reconstruction | four-record module block | fixed-A: 512-byte sector staging |
| CONFIG or disk-control overlay | executing overlay | executing overlay |

The z80pack CONFIG overlay is 864 bytes in the qualified image. It therefore
proves directly that a 512-byte overlay allocation would be insufficient.
The 1,024-byte physical-sector path independently requires the full area.

## Lifetime evidence

`ZR_STAGE` places 256- and 512-byte transfers in the upper half so that the
protected carrier reader can retain four accumulated CP/M records in the lower
half. A 1,024-byte transfer begins at the lower boundary and owns both halves.

The carrier stream is forced to bootstrap drive A:. That drive has a fixed
512-byte physical format and cannot be rebound through CONFIG. Carrier reads
therefore use only the upper half while the reloader consumes the lower half.
The reloader's relocation manifest proves that `MODBUF` maps to `DA6Dh` and its
`MODBUF+0200h` boundary maps to `DC6Dh`.

CONFIG and the disk-control overlays execute from `LY_CFG`, which aliases the
workspace base. Their contract forbids filesystem sector reads while the
overlay is resident. Loading finishes before entry and the area has no durable
state after return, so the overlay owns the complete idle workspace exclusively.

## Enforced checks

`tools/test_rom_workspace_lifetimes.py` rejects:

- workspace halves that cease to be contiguous 512-byte ranges;
- a CONFIG overlay that does not fit 1,024 bytes or no longer proves the need
  for more than 512 bytes;
- loss of the 1,024-byte and upper-half staging choices;
- loss of the fixed-A: carrier-stream rule, its 512-byte maximum sector size,
  or CONFIG's refusal to rebind A:;
- loss of CONFIG's no-filesystem-read execution contract; or
- ROM relocation manifests that no longer map the lower and upper workspace
  references to their accepted RAM addresses.

The test emits `rom/rom-workspace-lifetimes.json`. Protected-XIP qualification
incorporates that report beside the stack measurements and binds both to the
qualified ROM image. This is evidence for safe static sharing, not permission
for dynamic allocation or for reducing the retained workspace.
