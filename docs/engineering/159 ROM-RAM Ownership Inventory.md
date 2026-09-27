# 159 — ROM/RAM Ownership Inventory

Date: 2026-09-27  
Status: implemented inventory baseline; relocation remains pending

## Purpose

Architecture Specification 27 requires a measured inventory before the ROM
profile assigns final RAM addresses, overlay groups or a protected boundary.
`metadata/rom-ram-ownership.tsv` is that implementation input. It records each
current writable object, its owner and lifetime, its cold- and warm-boot rules,
its storage class, any proposed static overlay group, its immutable template,
and its required disposition.

This increment classifies the current implementation. It deliberately does not
move an object, select final addresses, claim an overlay proof or freeze the
`E300h` planning boundary.

## Measured result

The inventory contains shared and platform-specific objects for both retained
1.0 targets. Seventeen TRS-80 high-memory objects require 2,252 bytes of
relocation. Sixteen z80pack high-memory objects require 2,251 bytes: its disk
adapter has three more bytes of session state, while its host console needs no
four-byte Model 4 cursor state. Both profiles also identify the writable
page-zero ABI and transient reconstruction stack that already reside in RAM.

The three-byte dynamic BDOS gateway at `D501h` is a separate shared RAM object.
Although the historical audit classified its `JP` instruction as code, system
initialization rewrites its target to BDOS or the active RSX chain. It therefore
remains executable RAM under fixed system-gateway ownership. Including it makes
the enforced ROM-profile RAM totals 2,255 bytes for TRS-80 and 2,254 bytes for
z80pack, while preserving the historical relocation totals below.

The 2,252-byte result independently preserves the measured relocation total in
Engineering Specification 130 and the cpmsim ROM qualification assessment:

| Ownership area | Bytes |
| --- | ---: |
| Command-history PDS | 192 |
| System gateway state and stack | 90 |
| BDOS state and stack | 109 |
| Extension state | 5 |
| Disk profiles and session state | 35 |
| BIOS disk and console state | 16 |
| File-stream FCB | 36 |
| Live disk tables | 576 |
| RSX reconstruction profile | 41 |
| Directory buffer | 128 |
| Physical/module/CONFIG workspace | 1,024 |
| **TRS-80 relocation total** | **2,252** |

The z80pack profile replaces the TRS-80 disk and BIOS rows with its own 38-byte
disk state and 12-byte BIOS state, producing its 2,251-byte total.

The table keeps fixed subsystem state, stacks and temporary workspaces distinct
even where later placement may make them physically adjacent. The command
history is the only bounded-PDS object. Candidate overlay names are hypotheses;
they do not establish mutually exclusive lifetimes.

## Enforced checks

`tools/test_rom_ownership_inventory.py` resolves current start and end anchors
from emitted assembler listings and the canonical system layout. It rejects:

- a missing or unrecognized inventory object;
- address or size drift;
- overlapping ranges;
- an unknown storage class;
- an omitted ownership, lifecycle, initialization or disposition field; and
- any change to the measured platform relocation or ROM-profile RAM total.

`tools/build_complete_system.py` checks the TRS-80 profile after regenerating all
resident listings. `tools/build_z80pack_image.py` checks the z80pack profile
against the target-specific listings in its requested output directory. Neither
retained platform can therefore silently accept inventory drift.

The check therefore turns source-layout drift into an explicit ROM-profile
decision. It cannot prove overlay exclusion or stack depth; those require the
later targeted measurements named by the implementation contract.

## Next bounded implementation step

Use this inventory to define the first ROM-profile RAM layout and cold
initializer. Relocation should proceed by natural owner, with a focused test for
each moved group. Workspace overlays and stack reductions must remain unclaimed
until their independent lifetime or high-water evidence exists.
