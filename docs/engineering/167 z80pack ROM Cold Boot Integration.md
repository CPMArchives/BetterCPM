# z80pack ROM cold-boot integration

## Decision

The z80pack ROM profile now boots the relocated immutable image without first
copying resident code into RAM. `tools/build_z80pack_rom_boot.py` produces the
ROM cold-entry artifact, a ROM-specific relocated command reloader, and an
Intel HEX image whose EOF address starts execution at the cold entry.

This increment proves boot integration without claiming enforced
write-protected XIP. The latter remains a separate qualification increment.

## Entry path

The address-complete image distinguishes three entries that had previously
been conflated:

| Address | Meaning |
| --- | --- |
| `DF00h` | system initializer (`SYS_INIT`) |
| `DF20h` | system BOOT entry |
| `F225h` | relocated BIOS BOOT vector |
| `FD77h` | ROM-profile cold entry |

The 34-byte cold entry occupies the first bytes of the accepted 649-byte spare
region. It establishes cpmsim's temporary 128-byte-slot boot geometry, invokes
the position-independent initializer at `FD61h` with the RAM template at
`F3F5h` and immutable BDOS entry at `DF9Eh`, then jumps to the relocated BIOS
BOOT vector. The completed image retains 615 spare bytes.

Intel HEX is required because cpmsim's Mostek format uses one address for both
the load base and initial PC. The HEX artifact loads `DF00h` through `FFFFh`
and uses the EOF-record address `FD77h` as the initial PC.

## Reconstructible command environment

BIOS BOOT still reads the command reloader from system records 60–67. A dual
shifted-layout comparison finds 43 external layout references in that
reloader. The ROM-profile carrier relocates all 43 to their accepted immutable
ROM or live-RAM destinations and rejects unexplained bytes or unresolved
targets. The conventional system disk and reloader remain unchanged.

The CCP was the only reconstructed command component that called `LY_BDOS`
directly. It now calls the stable CP/M page-zero gateway at `0005h`, as the RCP
and HELLO CPXs already do. This removes resident-placement knowledge from the
CCP and works in both conventional and ROM profiles.

## Build products

A z80pack build now adds:

- `rom/rom-boot.bin`, the integrated protected-region image;
- `rom/rom-boot.hex`, the cpmsim load and start artifact;
- `rom/rom-boot.json`, its identity and qualification status;
- `rom/rom-reloader.bin` and `rom/rom-reloader.json`, the measured carrier;
- a separate ROM-profile A: disk in `disks/library`;
- `rom-disks/`, which mounts that A: disk without altering normal media; and
- `launch-z80pack-rom.command`, the unprotected ROM-profile launcher.

The manifest states `boot_integrated: true` and
`protected_xip_qualified: false`.

## Evidence

`tools/test_z80pack_rom_boot.py` boots the HEX artifact and ROM-profile disk in
a private copy of the media. It proves that the cold entry initializes RAM,
enters relocated BIOS BOOT, loads the relocated command reloader, reaches the
`A0>` prompt, lists A:, runs a transient program, and exits cleanly.

Two bounded diagnostics isolated the integration corrections:

1. cpmsim status 3 identified omitted temporary boot geometry; and
2. an opcode trap at `D6D4h` identified the CCP's direct old-layout BDOS call.

No general dependency or alternate loader architecture was introduced.

## Remaining qualification

The next increment enables cpmsim's `DF00h` write-protection boundary and
proves that CPU and DMA writes into the protected region fail while the same
boot, command, filesystem and reconstruction paths continue to operate. Final
stack and workspace evidence remains part of Item 2 closure.
