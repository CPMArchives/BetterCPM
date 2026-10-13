# Resident memory repack qualification

## Scope and result

The qualified BDOS and Model 4 disk-service savings are now production source.
The unloaded TPA remains `0100h..D500h`: 54,273 bytes, or 53K plus one byte.
No CP/M service was removed and no optional RSX became mandatory.

The BIOS allocation grows from 638 to 757 bytes. Its current 636-byte image
leaves **121 bytes** for the separately qualified routing/monitor work. The
combined prototype is 756 bytes, leaving one byte if adopted at this layout.
This change reserves space; it does not install IOBYTE routing or monitor hooks.

The original 122-byte recovery calculation included a spare extension byte.
Stamping BIOS implementation 1.10 instead of 1.9 consumes that byte. BDOS is
implementation 1.7. Public interface versions remain BDOS 1.2 and BIOS 1.5.

| Region | Previous base | New base | Production bytes | Allocation |
| --- | --- | --- | ---: | ---: |
| BDOS | D6BC | D6BC | 3,452 | 3,454 |
| Extension services | E49F | E43A | 425 | 425 |
| Model 4 disk service | E648 | E5E3 | 942 | 942 |
| BIOS | EA08 | E991 | 636 | 757 |
| File loader | EC86 | EC86 | 145 | 145 |

Gateway, TPA, history, file-loader, table and workspace boundaries are unchanged.
Components and internal adapters must be rebuilt together: private code/state
addresses have moved. Public BIOS vector offsets and calling conventions remain
unchanged; callers derive the BIOS base from the standard low-memory vector.

## Adopted implementation savings

BDOS saves 101 bytes through shared bit-mask, bounds, return, completion,
division, position, name and attribute helpers. The private stack retains its
40-byte allocation. The Model 4 disk service saves 18 bytes through shared
geometry and transfer-length calculations. Controller transfer timing loops
are unchanged. No buffers, drive profiles, directory capacity or retry policy
were removed.

The original audit transformations remain available for historical experiments.
`MEMORY_SAVINGS_V1` identifies adopted source, so subsequent memory audits check
that source without applying the same transformations twice or counting the
already recovered bytes again.

## Address and ROM qualification

Ownership addresses and ROM initialization template sources were regenerated
from current listings. Template-source drift is now checked against ownership
metadata; retaining an old BDOS template address could otherwise misclassify a
new extension entry as live RAM.

The z80pack immutable ROM source shrinks by 100 bytes, including the extra
version character. The packed ROM uses 7,702 bytes and leaves 746 bytes before
boot integration. The integrated cold-entry image leaves 712 bytes. Its address
inventory accounts for 739 packed relocation words and 105 CONFIG overlay
words, with no unresolved targets. Per-operand validation, independent rebuild
and inverse-relocation checks remain enabled; updated totals reflect the emitted
source rather than relaxing these checks.

Both platform ownership campaigns still report the same live RAM requirements:
Model 4 needs 2,256 bytes and z80pack needs 2,254 bytes in the ROM profile.

## Validation

- Complete Model 4 resident, command and boot builds passed, including the
  ownership drift check and SYSTEM.SYS package construction.
- The BDOS/filesystem campaign, grouped extents, recovery and 112 disk retry
  cases passed. Differential geometry covered 8,400 cases plus four transfer
  setup lengths. Observed BDOS private stack use was 28 of 40 bytes.
- Native ZSM4/LINK reproduced the 3,452-byte BDOS, 942-byte disk service and
  756-byte combined routing/monitor audit image byte for byte at the new layout.
- All 15 RSX container slots, partial input, bounds and scratch-frame checks
  passed at the relocated extension entry.
- Model 4 real-media full-TPA overwrite passed both unloaded and with HELLO.RSX
  loaded, including warm boot, CPX reconstruction, RSX survival and restored 53K.
- cpmsim RAM boot passed directory access, cpmtools-supplied files/transients,
  file creation/write/close/open/read, and RSX load/unload with restored 53K.
- cpmsim ROM cold boot passed RAM initialization, relocated BIOS/disk reloader,
  transient execution, CPX reconstruction and RSX lifecycle checks.
- Combined monitor/routing dispatch still passes 5,376 endpoint-stubbed cases.

The Model 4 overwrite harness now uses SUBMIT rather than timed typing of every
command, so a slow warm boot cannot drop an entire test command. The cpmsim I/O
harness frees one unused diagnostic directory slot on its private disk copy:
the development image plus IOTEST otherwise fills all 64 entries. Failures now
identify the file-operation stage. Neither harness modifies source media.

The older `test_system.py` console fixture still assumes a redundant CONOUT jump
and fails its Print String check. A separate pre-repack baseline reproduced its
fixture failures; it is not claimed as passing here. Its hardware stubs also scan
instruction bytes rather than using stable service vectors. Repair of that
legacy fixture is separate; the dedicated BDOS campaigns and real-media RAM/ROM
checks above provide the qualification for this change.

## Remaining work

Production IOBYTE routing, BAT status policy and monitor provider publication /
rebind lifecycle remain pending. PIP physical aliases remain unavailable until
the corresponding platform endpoint is qualified. This repack does not close
PIP's final qualification or introduce full terminal emulation.
