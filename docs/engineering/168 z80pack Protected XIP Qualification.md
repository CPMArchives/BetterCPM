# z80pack protected XIP qualification

## Decision

The integrated z80pack ROM profile executes directly from `DF00h..FFFFh` while
cpmsim enforces that region as read-only common memory. The focused
qualification passes normal cold boot, directory access and transient execution
and deterministically rejects CPU, DMA and guest-control attempts to modify or
disable the protected region.

This completes the protected-XIP portion of Implementation Item 2. Engineering
Specification 169 supplies the subsequent stack measurements. Workspace-
lifetime evidence and the focused Item 2 regression remain separate closure
work.

## Reconstructed CCP carrier

The first guarded boot reported:

```text
ROM WRITE VIOLATION
PC=B58C
ADDRESS=ECF3
DATA=00
SOURCE=CPU
```

`ECF3h` is the conventional profile's `LY_FCB`. The CCP is reconstructed from
disk and therefore was not part of the resident-code relocation performed by
Engineering Specifications 165–166.

The same dual shifted-layout comparison used for resident code and the command
reloader finds exactly 63 external layout references in the CCP. Sixty-one
target live RAM and two target immutable ROM. Twenty-three values change in the
ROM profile; the remainder already name stable low-RAM state. None overlaps the
CCP's 475 internal module-relocation words.

`tools/build_z80pack_rom_boot.py` now emits `rom/rom-ccp.rlm` and its complete
`rom/rom-ccp.json` reference record. Only the ROM-profile system disk receives
that carrier. The conventional CCP carrier and system disk remain unchanged.

## Locked qualification environment

`tools/test_cpmsim_rom_guard.py` builds a disposable cpmsim with the narrow
qualification patch and locks the existing common-segment boundary at `DF00h`.
The guard:

- permits instruction fetches and reads from `DF00h..FFFFh`;
- rejects CPU and controller-DMA writes with exit status 86;
- rejects attempts to change the MMU boundary or disable protection;
- reapplies protection across emulator reset; and
- remains inactive in an ordinary cpmsim build.

The guard primitives now use the final derived `DF00h` boundary rather than the
earlier planning address.

## BetterCP/M qualification

`tools/test_z80pack_rom_xip.py` verifies the ROM-image hash and boundary, builds
the guarded simulator, reruns every guard primitive, and boots the actual
BetterCP/M `rom-boot.hex` artifact with `CPMSIM_ROM_START=DF00`.

The protected run proves:

1. the activation banner reports the exact locked boundary;
2. the ROM cold entry executes in the protected region;
3. the writable RAM template and page-zero gateway initialize successfully;
4. relocated BIOS BOOT and the disk-loaded reloader reach `A0>`;
5. A: directory access succeeds;
6. a transient program loads, runs and returns; and
7. no CPU or DMA write touches the immutable image during those paths.

It records the image identity and results in
`rom/rom-xip-qualification.json`. The independently generated build manifest
continues to avoid claiming qualification before this test runs.

The same build also passes the ordinary z80pack disk-boot regression, including
file creation/readback, cpmtools interoperability, RSX load/unload and the 53 KiB
TPA gate.

## Remaining Item 2 work

Protected execution and stack capacity are no longer open implementation
questions. Item 2 still needs explicit workspace-lifetime evidence and one
focused regression that collects the ROM, RAM, TPA and protection results into
the final acceptance record.
