# z80pack ROM stack-capacity qualification

## Decision

The three stacks retained by the z80pack 1.0 ROM profile keep their existing
capacities. A protected execution campaign measures their high-water use during
cold boot, command-environment reconstruction, directory work, transient
execution and WBOOT reconstruction:

| Stack | Range | Capacity | High-water | Reserve |
| --- | --- | ---: | ---: | ---: |
| Command reloader | `0480h..04FFh` | 128 | 20 | 108 |
| System reconstruction | `D618h..D637h` | 32 | 14 | 18 |
| Unified BDOS | `D701h..D728h` | 40 | 26 | 14 |

The independent unified-BDOS recovery campaign also reaches 26 bytes while
covering its success, ignore and abort paths. No measured stack approaches its
lower boundary, and the qualification gate requires at least eight bytes of
reserve. The evidence supports the existing capacities; it does not claim or
perform a reduction.

## Measurement method

The qualification-only cpmsim patch observes CPU memory writes while the stack
pointer is within one of the three accepted ranges. This distinguishes actual
stack operations from the cold initializer's ordinary writes across the RAM
template. The observer records the lowest stack pointer, reports capacity and
remaining reserve at emulator exit, and terminates with status 87 upon the
first write below a stack's lower bound.

`tools/test_z80pack_rom_boot.py` parses the three records, verifies the accepted
addresses and capacities, and rejects a missing record, zero observed use, or
less than eight bytes of reserve. It writes the result to
`rom/rom-stack-qualification.json`. `tools/test_z80pack_rom_xip.py` incorporates
the same records into `rom/rom-xip-qualification.json`, binding the stack result
to the protected ROM image hash and the other XIP evidence.

The protected campaign performs:

1. ROM cold initialization and reconstruction through `A0>`;
2. directory access;
3. transient `HELLO.COM` execution and return;
4. `WARM.COM` and complete WBOOT reconstruction; and
5. directory access after reconstruction.

The guard continues to reject CPU and DMA writes to `DF00h..FFFFh`, so stack
measurement does not weaken the protected-XIP result. The measurement logic is
absent from an ordinary cpmsim build and changes no BetterCP/M production code
or guest memory.

## Isolated follow-up

An attempted extension of this campaign stopped at the first unrelated failure:
`RSX LOAD ECHO` trapped on opcode `ED AE` at `D62Fh`, inside the system-stack
range, after the protected ROM profile reached a normal prompt. The conventional
disk regression continues to pass RSX
load/unload. This increment records the exact boundary and does not expand into
a general RSX investigation. The final focused Item 2 regression must isolate
and correct that ROM-profile path before it can close the item.

## Result

Retained stack capacity is now measured rather than inferred. Workspace-
lifetime evidence and the isolated ROM-profile RSX path remain before the final
Item 2 acceptance regression.
