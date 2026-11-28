# RomWBW / HBIOS engineering port

28 November 2026: shared configuration, cold-boot settings and portable utilities are integrated.
Focused emulator acceptance is retained with the port.
This is an engineering target, not a published platform release.

## Target

| Item | Selected configuration |
| --- | --- |
| Emulator | avwohl/romwbw_emu `b4a7ee6566e5418e386e1d97c35ff29de02d66d3` (1.51) |
| Z80 core | avwohl/cpmemu `976a0c1c9c0d1700d57b45c101b9b213d4546391` |
| ROM | emu_avw, RomWBW 3.5.1; SHA-256 `4b11402a29fad22de304775b7c415eb6a74600df06bd57828b9931a7e9693258` |
| Boot | Unmodified RomWBW ROM loader, disk unit 2, slice zero, no MBR |
| Console | HBIOS character unit zero, basic serial/ANSI clear screen |
| Disk | Protected boot A: and rebindable B:, fixed hd512: 8,519,680 bytes, 512-byte physical sectors |
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
calls; two DPH/DPB records and two 256-byte ALVs replace the four floppy-drive tables. Cold HBIOS initialization runs in the bootstrap, recovering BIOS padding for those tables.
All resident components retain independent build-time size checks.

Every device operation uses standard `CALL FFF0h` HBIOS functions. There are no
emulator-specific I/O ports in the adapter. The bootstrap discovers the boot device,
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

Test native configuration and installation with two private image copies:

```sh
python3 tools/test_romwbw_install.py \
  --image-dir build/romwbw-engineering/profiles/romwbw-hbios/romwbw/build/romwbw \
  --simulator build/romwbw-emulator/romwbw_emu/src/romwbw_emu \
  --rom build/romwbw-emulator/emu_avw.rom --output build/romwbw-install-acceptance
```

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

The RomWBW engineering target now advertises Function 181 **block ABI 6**.
The existing floppy targets retain ABI 5. The [block-device contract](../../../docs/engineering/RomWBW-Block-Device-Interface.md)
defines query/rebind semantics and the versioned saved configuration sector.
A remains the protected firmware boot unit. B can map to another exact-capacity
512-byte HBIOS device or be explicitly unbound; nonzero slices and MBR mappings
are not implemented.

```text
CONFIG /SHOW
CONFIG /LOGICAL=B /UNIT=3
CONFIG /LOGICAL=B /UNIT=3 /SAVE
CONFIG /LOGICAL=B /UNBIND /SAVE
SYSGEN B:
```

CONFIG now uses the shared startup-command and PDS menus with RomWBW block
bindings in place of floppy editors. No arguments opens the menu.
`CONFIG /STARTUP="HELLO"` and `CONFIG /IOBYTE=85` save confirmed cold-boot
settings; `/SHOW` distinguishes live and saved values. PDS edits leave live
owners unchanged until cold boot. Keep CONFIG.COM, BLOCKCFG.OVL and
PDSCONF.OVL together on A0:. BCST/PDS changes are mirrored into the checked
system package. IOBYTE and block saves preserve each other.

SYSGEN is an engineering platform variant. SYSGEN must run in user zero. It
requires an empty formatted hd512 destination, verifies its matched source,
copies and verifies the manifest files and system area, then commits boot
metadata last. It refuses existing files in any user area; it is not an in-place
upgrade or a formatter; SYSTEM.SYS package import/export is not implemented. The generated image includes the configured installer.
Use the host image helper/cpmtools to prepare an empty target for now; DUP and
filesystem formatting remain separate work.

The [installation acceptance record](../../../docs/engineering/evidence/2026-11-28-romwbw-install/README.md)
retains two-disk install/cold-boot, saved mappings, independent host extraction,
source corruption/refusal and injected HBIOS I/O failure results. Broader utility
and compatibility qualification,
release packaging, other ROM versions/boards/slices and physical hardware remain
outside this engineering acceptance. Banked RSX execution is still deferred.

## Portable utility image

The engineering image also builds the shared file, inspection, archive, batch,
PATH/NDR, RSX and assembler/debugger utilities. HELP.COM and HELP.LBR are
included. The fixed-block image excludes floppy CONFIG/DUP/SYSBUILD and FDB;
its CONFIG and SYSGEN use the block backend described above. The integrated ADM3A, VT52 and ANSI personalities are included; no separate
screen-backend RSX is required. TIME reports no provider.

Additional focused acceptance entry points are `tools/test_romwbw_config.py`
and `tools/test_romwbw_utilities.py`, with the same image-dir, simulator, rom and
output arguments shown above. Installation of the larger image can take several
minutes because every file is copied and read back through the guest BIOS.
The retained configuration/utility evidence is in
[the configuration acceptance record](../../../docs/engineering/evidence/2026-11-28-romwbw-config/README.md).
These checks do not constitute full utility, compatibility or screen qualification.

## Terminal and compatibility checks

`RSX LOAD ADM3A`, `RSX LOAD VT52`, or `RSX LOAD ANSI` selects an integrated
personality. Unload it before selecting another. Its renderer uses the protected
HBIOS character leaf and capability 32; cpmsim port-output modules are refused.
No personality loads at cold boot by default, and complete unload restores the
original 56 KiB COM capacity. The shared 81-command lifecycle and HELP PIP through
each personality are exercised by `tools/qualify_romwbw_display.py`. This runner
requires `pyte` in addition to the dependencies above.

`tools/qualify_romwbw_toolchain.py` exercises pinned native ZSM4/LINK with indexed
Z80 code, macro/include expansion and multiple linked modules. Both toolchain
and `tools/qualify_romwbw_compatibility.py` read the independent suite at revision
`a9a878fcd2e36698c7e856654a85847a004fdd20` from an explicit `--suite` checkout.
The suite runner never modifies the independent COM programs or their oracles.

The broader two-drive run has 262 qualified automatic assertions. Full suite
qualification remains **blocked**: DIRTEST 0200 and FILETEST 0158/0169/0242/0278
require C:, while RANDTEST 0556/0557 require the full-directory D: fixture.
Actual F/not-run results are retained. RANDTEST 0557's apparent P is excluded
because its absent-fixture path can return success without exercising the case.
The runner exits 2 for these missing-provider limitations and 1 for unexpected
failures; it never promotes blocked cards to passes. The retained record is
[terminal and compatibility evidence](../../../docs/engineering/evidence/2026-11-28-romwbw-display/README.md).
