# 126 — Packed Resident Layout

Date: 2026-09-04

The unified-core reduction is now reflected in the production memory map.
No BDOS services or CPX/RSX facilities were removed for this packing step.

## Measured result

| Quantity | Previous layout | Packed layout |
| --- | ---: | ---: |
| System base | C000h | D200h |
| Fixed core entry | C100h | D300h |
| No-RSX gateway / exclusive TPA ceiling | BDFDh | CFFDh |
| TPA beginning at 0100h | 48,381 bytes | 52,989 bytes |
| Resident disk image span | 13,121 bytes | 8,513 bytes |

The gain is **4,608 bytes (4.5 KiB)**. CPX/RSX LIST's whole-K display is
now 51K with no RSXs installed; the exact amount is 51K + 765 bytes.
The standard BDOS remains **3,373 bytes**, including its private state/stack.

The Model 4 hardware-mapped region begins at F400h, not 10000h. All protected
code, persistent data, buffers, and stacks occupy/reserve 8,960 bytes. The
protected span from CFFDh through F3FFh is 9,219 bytes, including 259 bytes
of gaps/end padding. Another **4,355 bytes** of resident reduction would be
needed for a 56K TPA on this configuration. Packing alone does not meet that
longer-term target.

## Protected layout

| Range | Bytes | Owner |
| --- | ---: | --- |
| CFFD–CFFF | 3 | Dynamic gateway, no RSXs |
| D000–D1FF | 512 | Persistent history |
| D200–D2F7 | 248 | System gateway, ECB and persistent extension state |
| D300–E02C | 3,373 | Unified BDOS |
| E030–E107 | 216 | Protected filename loader |
| E110–E47A | 875 | RSX loader/manager |
| E480–E6F6 | 631 | Protected extension controls and adapters |
| E700–E897 | 408 | BIOS disk descriptors/workspaces |
| E8A0–EBBB | 796 | Command-environment reloader |
| EBC0–EBE8 | 41 | Active RSX reconstruction table |
| EBF0–EC6F | 128 | Reload/CCP stack |
| EC80–ECFF | 128 | Directory transfer buffer |
| ED00–EEFF | 512 | Physical-sector/module transfer buffer |
| EF00–F340 | 1,089 | BIOS/platform implementation |

Installed RSXs allocate downward beneath history and move the gateway down
by their allocations. CPXs and the CCP allocate beneath that gateway and
remain reclaimable. The CCP uses the top of the reload stack after reload
has completed; no command code is active during reconstruction.

## Build contract

`src/system/layout.inc` is the canonical build map. Eight-character-safe
assembly symbols are shared by host z80asm and native ZSM4; Python builders
and tests read them through `tools/system_layout.py`. The include is expanded
before either assembler runs. No old C000h/C100h compatibility trampoline is
retained inside the newly exposed TPA.

Application and bundled CPX/RSX BDOS calls use CALL 0005h. Core-private loader
addresses are build dependencies, not permanent public addresses. Rebuild the
system and bundled modules together; older binaries that directly called
C100h must not be mixed into this image. Module formats and public API
versions are unchanged. Implementation versions are incremented in the TSV.

Stage one loads **17 physical 512-byte sectors** from D200h through F3FFh.
The disk still reserves 28 resident sectors, so the CCP's raw disk slot does
not move. Builders reject code/workspace overlap, insufficient load counts,
and loads extending into hardware-mapped memory.

The 3.5K BDOS budget still has 211 bytes available, but the current packed
BDOS slot has only three padding bytes. Future growth requires adjusting the
shared layout and rebuilding/rechecking everything; the builder must fail
rather than overwrite the following loader. The budget is not permission to
write past a component's current placement.

Run `python3 tools/report_memory_layout.py` for exact ranges, allocations,
padding, and the remaining distance to the larger-TPA target.

## Verification

- Focused BIOS, unified BDOS, system-vector/adapter, CCP editing/parsing, and
  one-/two-CPX reconstruction tests pass at the new addresses.
- Physical emulator boot, directory listing, command-tail execution, BASIC
  command/transient parity, CPX load/unload, and RSX chaining/unload pass.
- `test_packed_tpa.py` builds a transient that fills and verifies every byte
  from 0200h up to the live exclusive TPA ceiling. Its own code/stack remain
  in 0100h–01FFh. This destroys the old C000h/C100h kernel locations and the
  current CCP/CPX images. It then calls BDOS and warm-boots successfully.
  The test repeats with HELLO.RSX installed, verifies the RSX still answers,
  unloads it, and confirms the original TPA/CPX inventory is restored.
- Native assembler parity is required for relocated binaries and modules.

This is targeted integration verification, not a completed rerun of the
independent historical CP/M compatibility catalog. That remains on the backlog.
