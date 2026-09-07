# Portable memory consolidation: 53 KiB checkpoint

September 7, 2026. Supersedes the intermediate layout in report 125.

The maximum TPA is **54,273 bytes**, from 0100h through D500h inclusive.
This is 53 KiB plus one byte, 2,820 bytes more than the preceding 51,453-byte
checkpoint. No RAM banking, hidden upper RAM or Model 4 console-map switching
is used to obtain this result. Hardware I/O remains in the platform adapter.

## Permanent allocation

| Region | Start | Bytes |
|---|---:|---:|
| Fixed BDOS jump | D501h | 3 |
| Command history | D504h | 512 |
| System gateway/state | D704h | 256 |
| Unified BDOS | D804h | 3,369 |
| Extension dispatcher | E52Dh | 399 |
| Runtime disk engine | E6BCh | 919 |
| BIOS/target adapter | EA53h | 659 |
| File stream reader | ECE6h | 145 |
| Four bindings/DPHs and shared ALV/CSV | ED77h | 480 |
| RSX profile state | EF57h | 41 |
| Directory buffer | EF80h | 128 |
| Physical-sector buffer | F000h | 1,024 |

The upper bound remains F400h. Component limits are exact, checked by the
builders; growth requires an explicit layout change. The resident image is
6,268 bytes, occupying 13 physical sectors. With two bootstrap sectors, three
two-sector overlays, and seven CCP-carrier sectors, the boot data uses 28 sectors.

## Where the savings came from

The warm-boot reloader now occupies finished transient RAM at 0100h instead
of permanent RAM. Its 817-byte body has a 896-byte limit and a separate
128-byte stack ending at 0500h. Fetching it initially uses a stack below 0100h.
The CCP likewise carries its own reconstructible stack.

Disk setters, format control and CPX control share a 909-byte overlay in the
idle 1,024-byte physical-sector buffer. Ordinary disk I/O and the common BDOS
filesystem remain resident. The overlay cannot read a filesystem sector while
executing in that buffer. Formatting writes the caller's supplied track stream.
The system disk must remain available for control overlays and warm boot.

The 875-byte RSX manager is loaded on demand. With an active profile it owns
one KiB, including its stack, in addition to module allocations. One one-KiB
RSX therefore leaves 51 KiB; two leave 50 KiB. Unloading the last RSX restores
the full 53 KiB. Empty queries need no manager. The manager's code limit is
893 bytes, leaving 128 stack bytes and the three-byte fixed gateway.

The stream reader now retains one FCB rather than duplicate name/state.
Four logical drives retain independent bindings while sharing allocation/check
workspace. BDOS rebuilds allocation ownership on drive changes; this is tested
with distinct allocated blocks across A/B/A. This design trades disk scanning
for resident RAM. Fixed BIOS vector slots remain three bytes wide.

## Regression evidence

- Unified BDOS: console, directory, allocation, extents, record mapping, and
  shared allocation-vector ownership across drive changes.
- BIOS: all 17 vectors, console transport, 80 default logical reads/writes,
  sector translation, disk state and failure paths.
- Full advertised TPA overwritten by a transient: resident BDOS survives;
  warm boot reconstructs CPX/CCP and preserves an installed RSX.
- RSX validation, ordered chaining, warm boot, middle unload and full TPA recovery.
- CPX list/unload/reload and warm-boot reconstruction.
- Runtime disk configuration, FDF bindings, aliases, rejection paths, formatting,
  read/write and adjacent-record preservation on disposable emulator images.
- Build guards reject an injected twelve-byte overrun and stale resident bytes
  without replacing the last good artifacts; reproducible disk rebuild checked.

Native ZSM4 parity for the new complete layout and real-hardware timing are not
claimed by these tests. CONFIG and DUP user interfaces remain separate work.

## Maintenance notes

Comments use concise register contracts and explanations at the non-obvious
boundaries. Two short historical patches remain commented out, dated honestly
07-Sep-2026: replacing the permanent warm-boot reloader and correcting the RSX
stack top. The latter is essential: a two-sector manager read covers the fixed
BDOS gateway. Restore that jump after the fetch, including errors, and keep
all stack pushes below it. The overwrite/recovery regression caught this bug.
