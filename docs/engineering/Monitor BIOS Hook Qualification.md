# Monitor BIOS hook foundation qualification

Implemented 14 October 2026 against merged PR 281. BIOS API 1.7,
implementation 1.12, adds the settled private monitor vectors at +66, +69
and +72. Existing public vectors and private entries through +63 retain
their offsets. This is the dispatch foundation, not a loaded terminal provider.

## Installed behavior

Console output, status, input and cursor presentation route through the
BIOS-owned MP_MON binding. Character routes that use the console backend,
including logical list output, share that dispatch. Public status and input
wrappers retain normalization and the seven-bit input mask. Non-console
physical printer/punch/reader routes remain independent.

MONCALL dispatches operations 0–5. MONRAW reaches the basic backend directly,
so a future provider can avoid recursive dispatch. MONBASE selects the basic
backend. Cold BOOT calls MONBASE before platform initialization or console use.
Operation 4 retains basic clear/home; operation 5 is a basic no-op. Unknown
operations return FFh. No BDOS calls, overlay loads or allocations occur in
the dispatcher.

No production manager binds a provider in this stage. Thus warm boot retains
a usable basic-console binding, and existing RSX load/unload behavior is
unchanged. The synthetic provider tests deliberately set the binding directly;
that is a test fixture, not an installation interface.

## Memory and ROM

Model 4 BIOS is 757 bytes of its 757-byte allocation, native ZSM4/LINK and
cross-assembled bytes identical. Unloaded TPA remains 53K. The two-byte binding
is explicitly inventoried as writable state on both platforms. The ROM profile
places it at D681h–D682h within the former gateway-tail reserve; all existing
live-state placements and the 2,412-byte template extent remain unchanged.

The cpmsim ROM layout contains 5,518 immutable bytes and has 462 bytes spare
after initialization and cold-boot entry. All 799 packed-code references and
818 discovered layout words are accounted for; 788 words and 1,558 bytes
change under relocation. No unexplained references or overlapping owners
remain. The binding is written in protected RAM rather than ROM.

## Qualification

- Production hook tests execute both platform builds with a synthetic provider:
  console/list/cursor dispatch, status/input normalization, operations 4/5,
  raw bypass, fallback after destroying a detached target, stack balance and
  unknown-operation rejection.
- Existing 17 BIOS-vector contracts pass, including disk transfers and keyboard
  behavior; the disk component is rebuilt against the moved private symbols.
- 5,376 IOBYTE routing cases pass. Isolated scheduler/publisher movement and
  rejection probes still pass with the corrected MONBASE vector offset.
- Native Model 4 BIOS matches all 757 cross-assembled bytes.
- Both final System Disks build and boot-qualify: cpmsim has 22 files and
  178K free; trs80gp has 21 files and 626K free. PIP device regression and
  distribution tests pass.
- ROM ownership, RAM map, packing, reference classification and relocation
  gates pass. Real cpmsim ROM cold boot reaches the prompt; DIR, transient
  execution and CPX/RSX load/reconstruction/unload lifecycle checks pass.

Reproduce using build_system.py, test_bios.py, test_monitor_bios_hooks.py
(with --z80pack-build for the host build), audit_monitor_hooks.py,
audit_monitor_binding.py, test_monitor_hooks.py, audit_iobyte_routing.py,
test_iobyte_routing_audit.py, build_native_bios.py and
build_z80pack_image.py/test_z80pack_rom_boot.py.

## Next stage

Before enabling a real monitor, implement MCON metadata validation and the
single-provider/platform rule, prospective address preparation, pre-movement
detach and final publication, including retained monitor relocation and
self-retirement. Then integrate command-return sequence reset and explicit
internal clear/home callers. MM ADM-3A and VT52 provider implementation,
rendering/input/reply qualification and startup loading remain separate work.

The initial provider set is MM-style ADM-3A and VT52, each accompanied by a
dedicated test utility. Together they establish the implementation and
qualification pattern for later monitor personalities, using the shared hook
and lifecycle contract and common code where practical.
