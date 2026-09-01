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

Stage one selects the Model 4 video-visible mapping, writes its diagnostic message to video memory at `F800h`, and enters a stable loop. It is currently 56 bytes.

The `5000h` address and one-sector stage-one limit are bring-up values, not final resident-system decisions.

## Reproducibility

Run:

```sh
python3 tools/build_trs80_boot.py
python3 tools/build_native_trs80.py
python3 tools/test_trs80_boot.py
```

The second command assembles and links both stages under CP/M using ZSM4 and Digital Research LINK 1.3, then compares them with host cross-assembled output. Any byte mismatch fails the build.

The third command boots the generated DMK in `trs80gp`, captures video RAM, and requires the exact stage-one message.

Verified hashes for this milestone are:

```text
c9d73093405f49e2545774dd2bcfabb795fa01b35e3487d8447318754fe23221  boot.bin
b9aa226e6214d01198a654cabf391046bd60818f37e6b64c27fb9a3680d6c7d8  stage1.bin
84c701c021c4bd52fa983d5d7c758880f0eddba99bbe9930c17cea2bfcb202fe  BetterCPM-Extended-80T-DS-System-790K.dmk
```

Generated binaries, logs, and disk images remain under `build/` and are not committed as source.
