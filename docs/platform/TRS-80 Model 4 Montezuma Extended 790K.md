# TRS-80 Model 4: Montezuma Extended 790K System Disk

Status: Initial development-media definition  
Date: 2026-09-01

This is the initial BetterCP/M development and test medium for the TRS-80 Model 4. Montezuma Micro calls the format **Extend System 790K**; “Extended” is used descriptively in filenames.

## Physical format

| Property | Value |
| --- | --- |
| Cylinders | 80 |
| Heads/sides | 2 |
| Recording | MFM / double density |
| Sectors per track per side | 10 |
| Sector size | 512 bytes |
| Logical sector order | 1, 3, 5, 7, 9, 2, 4, 6, 8, 10 |
| Raw formatted capacity | 819,200 bytes |
| Conventional usable label | 790K |
| DMK track length | 6,378 bytes (`18EAh`) |
| DMK image size | 1,020,496 bytes |

Tracks are ordered by cylinder and then side in the DMK image.

## CP/M disk parameters

| Parameter | Value |
| --- | ---: |
| BSH | 4 |
| BLM | 15 |
| EXM | 0 |
| DSM | 394 |
| DRM | 127 |
| AL0 | `C0h` |
| AL1 | `00h` |
| OFF | 2 |

The two reserved tracks occupy 20,480 bytes. The filesystem therefore contains 395 allocation blocks of 2,048 bytes, conventionally described as 790K. The first two blocks are reserved for the 128-entry directory.

## Generated image and bootability

Run:

```sh
python3 tools/build_montezuma_extended_790k.py
```

The generated image is placed at `build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk`. It has valid DMK address/data fields and CRCs and an empty CP/M directory and data area.

The initial generated image is **system-layout media, not yet a bootable operating-system disk**. A bootable BetterCP/M image requires the TRS-80 Model 4 stage-zero loader and the BetterCP/M system image to be installed in the reserved tracks. Those bytes must be project-built outputs; the image generator shall not silently copy Montezuma Micro proprietary system code.

Once the loader exists, the image build shall fail unless the system payload fits within the 20,480-byte reserved area and the completed image boots under the pinned TRS-80 emulator.
