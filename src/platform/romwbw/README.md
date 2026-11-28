# RomWBW / HBIOS engineering port

28 November 2026: initial emulator bring-up and focused acceptance pass.
This is an engineering target, not a published platform release.

## Target

| Item | Selected configuration |
| --- | --- |
| Emulator | avwohl/romwbw_emu `b4a7ee6566e5418e386e1d97c35ff29de02d66d3` (1.51) |
| Z80 core | avwohl/cpmemu `976a0c1c9c0d1700d57b45c101b9b213d4546391` |
| ROM | emu_avw, RomWBW 3.5.1; SHA-256 `4b11402a29fad22de304775b7c415eb6a74600df06bd57828b9931a7e9693258` |
| Boot | Unmodified RomWBW ROM loader, disk unit 2, slice zero, no MBR |
| Console | HBIOS character unit zero, basic serial/ANSI clear screen |
| Disk | One A: drive, fixed hd512: 8,519,680 bytes, 512-byte physical sectors |
| CP/M geometry | 1040 tracks, 64 logical 128-byte records/track, 16 reserved tracks |
| Allocation | 2048 blocks of 4096 bytes, 512 directory entries, no CSV |
| Proxy | FE00h–FFFFh reserved for HBIOS |
| Unloaded COM capacity | 57,344 bytes (56 KiB); transient origin 0100h, gateway E101h |
| Banked storage | One 512-byte allocation from the HBIOS heap, allocated once at cold boot |

The emulator runs Z80 instructions for the ROM loader and the BetterCP/M
shared core. Its ROM bank zero and C++ HBIOS implementation replace the real
hardware drivers. Acceptance therefore establishes this emulator configuration,
not physical RomWBW hardware or other firmware versions. The native emulator
preparer verifies every staged upstream file against its pinned Git blob and
checks the ROM checksum. It builds its Z80 core statically into the executable;
normal macOS system libraries remain dynamically linked.

## Implementation

The shared BDOS, CCP, reconstruction worker and RSX machinery are reused.
`romwbw-hbios` reserves the proxy and recovers its 512 bytes by reducing the
resident disk-service allocation. The BIOS allowance grows for HBIOS console
calls; a single DPH/DPB and 256-byte ALV replace the four floppy-drive tables.
All resident components retain independent build-time size checks.

Every device operation uses standard `CALL FFF0h` HBIOS functions. There are no
emulator-specific I/O ports in the adapter. Cold boot discovers the boot device,
BIOS bank and current user bank, then allocates sector staging through SYSALLOC.
The boot loader requires slice zero and exactly 16,640 physical 512-byte sectors.

Each logical read stages a full physical sector in the HBIOS bank, then copies
one 128-byte quarter to caller DMA. Each write pre-reads, replaces its quarter,
re-seeks and writes through. Failed pre-reads leave caller DMA unchanged. The
adapter rejects unsupported drives, tracks and sector numbers before transfer.
DMA spanning 8000h uses one-byte interbank copies to honor HBIOS's prohibition
on copying across the bank/common boundary; ordinary DMA uses one block copy.

RomWBW's metadata occupies physical sector 2; sector 3 loads the bootstrap at
1000h. The common 160-record checked carrier layout is stored at byte 32768.
Its resident starts at physical sector 66. Records 1 and 2 at the start of the
disk hold the saved PDS/startup record used by the shared reconstruction worker.
The bootstrap loads the resident above E1D0h, entirely below the proxy. Subsequent
CCP/control/RSX carrier loads use the shared checks and the new record adapter.

Existing RSXs still occupy ordinary address space. ECHO load/call, warm-boot
reconstruction, unload and restoration of the 56 KiB floor are tested. Banked
RSX execution is deferred as a separate future project.

## Reproduce

Use the upstream repositories at the exact revisions above. The ROM is also
available in avwohl/romwbw_emu commit
`c9d8183c8ed4b791341a3c83ece1199bd9191ac8`, path `roms/emu_avw.rom`;
the preparer checks it against the checksum above. Dependencies are a C++11
compiler, make, Python 3.9+, `~/bin/z80asm`, and cpmtools (`cpmcp`) for host
extraction during acceptance. Keep output directories fresh.

```sh
python3 tools/prepare_romwbw_emulator.py \
  --source /path/to/romwbw_emu --cpu-source /path/to/cpmemu \
  --rom /path/to/emu_avw.rom --output build/romwbw-emulator
python3 tools/build_romwbw.py --work build/romwbw-engineering
python3 tools/test_romwbw_system.py \
  --image-dir build/romwbw-engineering/profiles/romwbw-hbios/romwbw/build/romwbw \
  --simulator build/romwbw-emulator/romwbw_emu/src/romwbw_emu \
  --rom build/romwbw-emulator/emu_avw.rom --output build/romwbw-acceptance
```

Acceptance always copies the built image before writing to it. It uses a private
NVRAM configuration directory and prompt/echo-paced PTY input, with transcripts,
checksums and explicit pass/fail output. It requires no manual guest commands.
`build/romwbw-emulator/provenance.json` identifies the verified sources, compiler,
build commands and executable hash.

For an interactive session, use the native emulator with the same ROM and a
private writable copy of `system.img`, `--boot=2 --no-config`. Enter Ctrl-E for
its debugger, then type `quit` to exit. Do not attach one writable image to two
emulators simultaneously.

## Acceptance and remaining scope

The retained [initial acceptance evidence](../../../docs/engineering/evidence/2026-11-28-romwbw/README.md)
covers boot, DIR, transient execution, patterned BDOS I/O, host extraction,
invalid drive/track/sector rejection, read-DMA canaries, last-sector RMW,
bank-boundary DMA, TPA overwrite and WBOOT, ECHO lifecycle and cold persistence.
A wrong-capacity image is rejected by the bootstrap before OS entry.

Runtime geometry configuration is not implemented: Function 181 discovery
returns NULL and other operations return unsupported (HL=2). The wider 64-byte
binding area is reserved, with only the standard DPB populated. No CONFIG,
SYSGEN, DUP, filesystem installation or SYSTEM.SYS package is delivered yet.
The disk images and executables are development artifacts. Full utility and
compatibility qualification, terminal personalities, publication packaging,
other ROM versions/devices/slices, injected HBIOS I/O failures and physical
hardware remain outside this initial acceptance.
