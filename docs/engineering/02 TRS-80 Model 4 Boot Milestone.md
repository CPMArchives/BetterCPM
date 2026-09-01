# Engineering Specification 02: TRS-80 Model 4 Boot Milestone

Status: Implemented and verified  
Date: 2026-09-01

## Result

The first BetterCP/M-owned code boots from a Montezuma Micro Extended 80T DS SYSTEM disk under TRS-80 Model 4 emulation.

The verified path is:

```text
Model 4 ROM
  -> track 0, side 0, sector 1 at 4300h
  -> stage-zero execution address from three-byte load header
  -> track 0, side 0, sector 3 loaded at 5000h
  -> stage one
  -> "BetterCP/M stage 1 - TRS-80 Model 4"
```

## ROM entry contract

The boot sector begins with:

```text
01h
little-endian execution address
```

The first implementation executes immediately after that header. It does not depend on ROM-supplied register values.

## Stage zero

Stage zero:

1. disables interrupts;
2. establishes the Model 4 memory mapping and stack;
3. installs an NMI vector at `0066h`;
4. selects drive 0, track 0, side 0, sector 3;
5. reads one 512-byte sector through the WD179x-compatible controller;
6. checks controller status; and
7. transfers to `5000h` or displays a stable boot-error message.

The NMI handler terminates the controller data loop at command completion. The implementation is currently 146 bytes and fits in the first 512-byte sector.

## Stage one

Stage one selects the Model 4 video-visible mapping, clears all 2,048 bytes of video memory, writes its diagnostic message at `F800h`, and enters a stable loop. It is currently 69 bytes.

The `5000h` address and one-sector stage-one limit are bring-up values, not final resident-system decisions.

## Reproducibility

Run:

```sh
python3 tools/build_trs80_boot.py
python3 tools/build_native_trs80.py
python3 tools/test_trs80_boot.py
```

The second command assembles and links both stages under CP/M using ZSM4 and Digital Research LINK 1.3, then compares them with host cross-assembled output. Any byte mismatch fails the build.

The third command boots the generated DMK in `trs80gp`, captures video RAM, requires the exact stage-one message, and rejects any residual non-space characters elsewhere on the display.

Verified hashes for this milestone are:

```text
c9d73093405f49e2545774dd2bcfabb795fa01b35e3487d8447318754fe23221  boot.bin
c76b7a88e272936c218978a81a79d2a8ffc4c58fb54e93d9452820f56ad73470  stage1.bin
e24dce75d3dd2ad3a0e2e556428f3dcef9211c712c22d004ed5f1c81a5f566fe  BetterCPM-Extended-80T-DS-System-790K.dmk
```

Generated binaries, logs, and disk images remain under `build/` and are not committed as source.

## Deferred boot-loader enhancements

The following are useful later improvements, not requirements of the
current one-sector diagnostic milestone:

- load a multi-sector resident system across the established system tracks;
- follow the target format's sector order and advance across sides and tracks;
- retry failed reads and use bounded waits for controller states;
- report distinct header, timeout, read and checksum failures;
- validate a loader-owned system-image descriptor and checksum; and
- optionally try a recovery copy of the complete system image.

These facilities belong to the platform-specific packaging and boot path.
They shall not become requirements of the portable CCP or BDOS image.
BetterCP/M shall continue to produce independently linkable CCP and BDOS
artifacts that can replace their counterparts behind an existing machine's
boot loader and BIOS when that platform's addresses, entry points and size
constraints are satisfied. A BetterCP/M complete-system image and a drop-in
CCP/BDOS build are separate products of the same sources.
