# Engineering Specification 122: Resident Size Budget and Relocation Gate

Status: adopted design constraint; optimization in progress; relocation pending

## Objective

A minimal BetterCP/M configuration must provide approximately the same TPA as
an equivalent stock CP/M system. CPX and CCP memory remains reclaimable.
Optional RSXs reduce the TPA only by their actual protected allocation.

The current `C000h/C100h` addresses are development placements, not permanent
architecture. Final physical addresses are to be calculated by system
generation and published through page zero and versioned system metadata.

## Measured baseline

The current Model 4 protected components and required work areas occupy:

| Component | Bytes |
|---|---:|
| System gateway and ECB | 248 |
| BDOS core and private data | 2,968 |
| Protected file loader | 216 |
| RSX manager | 875 |
| Directory/filesystem services | 4,822 |
| Command-environment reloader | 796 |
| BIOS | 1,089 |
| Persistent command history | 512 |
| Directory transfer buffer | 128 |
| Protected module buffer | 512 |
| **Total** | **12,166** |

The Model 4 hardware-facing ceiling is `F400h`. Even with impossible
byte-perfect packing and no alignment or guard space, the measured payload
would begin at `C47Ah` and expose only about 48K of TPA above `0100h`.
Therefore removing the present address holes is necessary but insufficient.

### First compaction pass (2026-09-03)

The first byte-level pass removed the `C9FEh..CAFFh` bring-up gap before the
DPH/DPB unit and replaced the linear standard-function dispatcher with a
direct 0..40 table. The protected payload fell by 344 bytes, from 12,166 to
11,822 bytes. Native and cross assemblies remain byte-identical; all 17 BIOS
contracts, all 39 defined CP/M 2.2 BDOS functions, and the complete resident
system smoke test pass.

This result establishes that address packing and local instruction cleanup
cannot by themselves meet the target. The remaining reduction for a genuine
56K TPA is 6,958 bytes. The decisive work is architectural:

1. retain only the installed-RSX dispatch hook in protected memory and run
   RSX installation/removal logic transiently;
2. make WBOOT invoke a temporary command-environment reconstruction overlay,
   rather than retaining the full reloader and module buffer;
3. replace the separate 2.6K dispatcher and 4.8K directory implementation
   with one shared file-state engine comparable in size class to the complete
   3.5K CP/M 2.2 BDOS;
4. preserve enhanced persistent command state as an explicitly charged build
   feature, never as hidden base-system overhead.

## 1.0 budgets

| Class | Target |
|---|---:|
| Minimal protected operating system | no more than 4.75K for 56K TPA on the Model 4 |
| Default RSXs | zero |
| CPXs and CCP | reclaimable; excluded from transient-time protected cost |
| Persistent command/input state | explicitly budgeted, initially no more than 1K |
| Model 4 target TPA | at least 56K |

The exact portable target depends on the platform's true RAM ceiling and BIOS
requirements. Every platform build must report its occupied resident bytes,
alignment loss, extension allocation, and resulting TPA.

## Required work before final relocation

1. Separate code bytes, persistent state, buffers, alignment, and historical
   padding in every resident component.
2. Remove fixed internal gaps, especially the BDOS table padding.
3. Reduce or consolidate the 4.8K directory service and 3K BDOS
   implementations while retaining their compatibility tests.
4. Determine which loaders and work buffers can overlap safely by lifetime.
5. Move configuration and installation logic out of the permanently resident
   core wherever possible.
6. Generate component bases from measured release artifacts and a platform RAM
   ceiling, then assemble native and cross variants from the same layout file.
7. Publish the calculated BDOS entry, ECB, RSX boundary, and TPA gateway without
   retaining a protected low-address locator.

The generated layout must fail the release build when components overlap,
exceed their budgets, or produce less than the configured minimum TPA.

`tools/report_memory_layout.py` reproduces the occupied-size audit from current
artifacts. It deliberately reports the theoretical packed result separately
from the current published TPA so address compaction cannot hide code growth.
