# Post-1.0 third-platform assessment

Assessment date: 20 September 2026.

## Decision

BetterCP/M 1.0 retains its two agreed qualification targets: TRS-80 Model 4
under trs80gp and z80pack/cpmsim. A third conventional 64 KiB platform would
provide useful evidence, but neither candidate justifies another 1.0 release
gate.

After 1.0, z80pack Cromemco is the preferred conventional third-platform
candidate. No release number is assigned here. This work remains separate from
the bounded RomWBW/HBIOS port proposed for 1.1 or 1.2 and the bank-aware
RomWBW architecture reserved for 2.0. Altair/Tarbell remains a lower-cost
demonstration option; IMSAI/FIF is worth reconsidering when controller-interface
diversity matters more than disk-format diversity.

## Evidence and limits

This source-level assessment inspected BetterCP/M's current platform and disk
contracts and z80pack revision `b7a6fa36a2ee185a73727dc5b56ac1af40679e81`.
Relevant upstream evidence includes:

- [z80pack](https://github.com/udo-munk/z80pack);
- [Tarbell controller](https://github.com/udo-munk/z80pack/blob/dev/iodevices/tarbell_fdc.c);
- [Cromemco controller](https://github.com/udo-munk/z80pack/blob/dev/iodevices/cromemco-fdc.c);
- [IMSAI FIF controller](https://github.com/udo-munk/z80pack/blob/dev/iodevices/imsai-fif.c); and
- [z80pack removable-media behavior](https://github.com/udo-munk/z80pack/discussions/450).

This is not evidence that BetterCP/M has booted or passed qualification on
these machines. A selected port must pin its exact z80pack revision and retain
reproducible test artifacts.

## Comparison

| Property | Altair/Tarbell | Cromemco Z-1 |
|---|---|---|
| Proposed invocation | `altairsim -z -F -M1 -d ...` | `cromemcosim -z -F -M1 -R -d ...` |
| BetterCP/M memory use | One 64 KiB address space | Bank 0 only |
| Console | 88-2SIO A, 10h/11h | TU-ART, 00h-02h |
| Floppy controller | Tarbell 1011D, WD1791-style | 4FDC/16FDC, WD-style |
| Media layouts | One fixed layout | Nine recognized layouts |
| Live media replacement | Host links | Disk manager, web UI, or links |
| Estimated implementation and qualification | Two to three weeks | Three to five weeks |
| Public BetterCP/M ABI change | None expected | None if hybrid formats wait |
| Additional evidence | Moderate | High |

The estimates include bootstrap, console and disk adapters, image construction,
CONFIG/DUP integration, cold/warm boot, error and media-change tests, and
applicable compatibility-suite runs. They are planning ranges, not schedules.

## Altair/Tarbell

The smallest target uses Z80 mode, memory configuration 1, RAM at
0000h-FBFFh, the external ROM at FC00h-FFFFh with entry at FE00h, the 88-2SIO
A console at ports 10h/11h, and the Tarbell controller at F8h-FCh.

The ROM copies its active loader to 1000h, reads track 0 sector 1 into address
zero, and enters at 007Dh. A Tarbell-specific 128-byte stage-zero sector would
continue loading the ordinary BetterCP/M resident carriers. BetterCP/M's
resident image ends below F400h, so the ROM does not conflict with it.

The four emulated drives use one uniform layout: 77 tracks, one side, 26
128-byte FM sectors, for a 256,256-byte image. The controller implements
write-track formatting. This needs no deblocking or FDB extension.

The port would validate 8-inch binding, direct 128-byte sectors, serial console,
ROM bootstrap and another WD179x attachment. It would not stress the format
catalogue substantially, and it shares z80pack's CPU core with cpmsim.

## Cromemco Z-1

The smallest target uses Z80 mode, memory configuration 1, bank 0 only, the
RDOS 3.08 ROM, TU-ART console channel 0A, the 4FDC/16FDC interface, and an
8-inch single-sided, single-density system disk.

RDOS initially overlays C000h-DFFFh. Its first sector runs at 0080h, where a
stage-zero loader can select bank 0 and remove the ROM overlay before loading
the resident image. BetterCP/M then stays inside its present 64 KiB model.

The controller recognizes:

| Medium | Recorded layout |
|---|---|
| 5.25-inch SS/DS SD | 40 tracks, 18 x 128 bytes per side |
| 5.25-inch SS/DS DD | SD track 0 side 0, then 10 x 512 bytes |
| 8-inch SS/DS SD | 77 tracks, 26 x 128 bytes per side |
| 8-inch SS/DS DD | SD track 0 side 0, then 16 x 512 bytes |
| 8-inch DS DD uniform | 77 tracks, 16 x 512 bytes on every side |

It therefore exercises drive size, sides, FM/MFM selection, sector size,
formatting, side selection, motor behavior, read-only media and live media
replacement. This is the stronger disk and platform test.

### FDF/FDB implication

Several historical Cromemco double-density layouts retain a single-density
track 0, so sector count, sector size and encoding vary by track. FDF version 1
deliberately leaves track-range layouts, per-track sector maps and mixed FM/MFM
recording for future required extensions.

This is a missing format capability, not a controller-boundary failure. It must
not be hidden as private Cromemco behavior in portable format data. Initial
Cromemco work can use single-density media and uniform 8-inch double-density
media without changing FDF v1. Hybrid-density layouts wait for an approved,
required track-range extension.

Controller ports, motor control, density selection, boot-ROM handling, retry
policy and image realization remain platform-adapter responsibilities. The
existing BIOS configuration ABI should be sufficient for this bounded target.

## Removable media

Altair permits replacement through host drive links. Cromemco additionally has
z80pack's disk manager and web interface. Cromemco is therefore better for
testing absent, inserted and read-only media; replacement while logged in;
directory-checksum detection; reset/relogin; and wrong-format failures.

Automated replacement tests must close files and perform the defined CP/M
reset/relogin sequence before writing the replacement disk.

## IMSAI and SIMH

IMSAI's FIF controller uses DMA command descriptors rather than WD-style
registers, making it the stronger controller-abstraction test. Its fixed
77-track, 26-by-128-byte layout adds little FDF/FDB evidence. Its supplied BIOS
and loader make it a practical later specialized test, but no full feasibility
study is needed now.

SIMH AltairZ80 would provide an independent emulator implementation, but would
also add another build, control and image-management integration. No capability
identified here requires it, so emulator diversity alone does not justify it.

## Entry criteria

Before beginning a Cromemco port:

1. qualify both 1.0 platforms;
2. finish the production FDF compiler/FDB reader and cross-platform tests;
3. pin an exact headless z80pack configuration;
4. select supported boot and data formats explicitly;
5. exclude hybrid-density formats unless their required FDB extension has been
   approved; and
6. decide whether the result is a demonstration or a continuing qualification
   target, since the latter adds permanent release obligations.

## Conclusion

A third target before 1.0 would add more release work than risk reduction.
After 1.0, Cromemco is preferred because it supplies the most useful disk,
controller and media evidence without requiring bank-aware OS architecture.
Altair is the smaller demonstration; IMSAI is the specialized choice for
proving independence from WD-style controllers.
