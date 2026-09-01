# Engineering Specification 29: Resident Memory Layout Revision

## Milestone

BetterCP/M has replaced its exhausted `E500h`/`E600h`/`E800h` bring-up
placements with an explicit provisional resident memory plan. The revision
provides meaningful BDOS and System Services growth space, separates logical
and physical disk workspaces, and makes the build reject region overflow.

The CP/M application ABI is unchanged: page zero still provides warm boot at
`0000h` and BDOS calls at `0005h`.

## Revised layout

| Range | Owner | Current use |
| --- | --- | --- |
| `BF00h–BF7Fh` | System Services workspace | 128-byte directory record |
| `BF80h–BFFFh` | Reserved workspace | future resident state |
| `C000h–C0FFh` | Initialization gateway | 28 bytes from `C000h` |
| `C100h–D7FFh` | BDOS region | 409 bytes from `C100h` |
| `D800h–EDFFh` | System Services region | 1,407 bytes from `D800h` |
| `EE00h–EFFFh` | BIOS disk workspace | 512-byte physical-sector scratch |
| `F000h–FFFFh` | BIOS region | 1,040 bytes from `F000h` |

The lowest resident-owned address is now `BF00h`. This leaves the conventional
transient program area below it and does not yet assign a CCP placement. The
final memory ceiling and CCP size remain design decisions; this map is an
engineering layout with enough room to continue implementation safely.

## Growth budgets

The gateway has a fixed 256-byte region. BDOS has 5,888 bytes between `C100h`
and `D800h`; System Services has 5,632 bytes between `D800h` and BIOS scratch
at `EE00h`. The two workspaces are outside both executable growth regions.

These are region limits, not targets. Code should remain compact, and later
composition may recover unused gaps. Their purpose is to prevent every feature
increment from forcing another absolute-address move.

## Internal relocation

The implementation changes are coordinated:

- initialization gateway: `E500h` to `C000h`;
- BDOS: `E600h` to `C100h`;
- System Services: `E800h` to `D800h`; and
- directory buffer: `E400h` to the explicit workspace at `BF00h`.

All System Services vector offsets remain unchanged relative to their base.
BDOS and the gateway now reference the relocated vectors. BIOS remains at
`F000h`, so the page-zero warm-boot target remains `F003h`.

The BDOS page-zero vector now contains `JP C100h` rather than `JP E600h`.
Applications still execute `CALL 0005h` and therefore do not observe or depend
upon the internal address.

## Composition enforcement

`tools/build_system.py` now reserves the image from `BF00h`, composes every
component at its assigned base, and checks each binary against the end of its
region:

- gateway must end before `C100h`;
- BDOS must end before `D800h`;
- System Services must end before `EE00h`; and
- BIOS must remain within the 64K address space.

The resulting sparse `resident.bin` spans `BF00h–F40Fh` and deliberately
contains zero-filled gaps. A component that outgrows its reservation fails the
build rather than overwriting its neighbor or a work area.

## Development history

The old map was valuable: executable tests detected both the `EC00h` and
`ED00h` directory-buffer collisions as soon as code crossed them. Dated source
comments retain the buffer's placement history and the reason for this broader
relocation instead of erasing those architectural lessons.

## Verification

The complete directory, BDOS, and resident tests execute from the new
addresses. Initialization logs in drive A, installs `JP C100h` at page zero,
and all implemented calls continue through `CALL 0005h`, including directory
search and transactional Close.

Native CP/M ZSM4/Digital Research LINK and host cross builds must remain
byte-identical after relocation; absolute call and data operands are therefore
verified in both build environments.

## Next increment

Engineering Specification 30 completes this increment with DPB-driven Read
Sequential, DMA transfer, EOF, and automatic extent transition. The next
increment can implement Write Sequential with allocation and protection.
