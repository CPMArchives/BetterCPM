# Engineering Specification 03: Initial Hardware Abstraction Interface

Status: Implemented and verified  
Date: 2026-09-01

## Result

Stage one now separates the hardware-independent bring-up diagnostic from
TRS-80 Model 4 device code. The core prints only through a platform interface
and verifies a known 512-byte physical-sector read without referring to a
controller port, video address, or disk-image layout.

```text
BetterCP/M
TRS-80 Model 4 platform initialized
raw disk read verified
```

This is the first executable architectural boundary in BetterCP/M. It is a
bring-up interface, not the CP/M BIOS ABI.

## Source boundary

- `src/core/bringup.inc` contains the hardware-independent diagnostic.
- `src/platform/trs80m4/hal.inc` contains Model 4 video and controller code.
- `src/platform/trs80m4/stage1.mac` establishes the stack and joins the parts.

Using one assembly unit preserves the one-sector loader and simple native
ZSM4 build while keeping source ownership and dependencies explicit.

## Initial platform calls

`HAL_INIT` establishes platform state, installs the floppy NMI vector, selects
the video-visible map, clears the display, and initializes the console cursor.
It has no inputs and clobbers AF, BC, DE, and HL.

`HAL_CONOUT` writes the ASCII character in C. It interprets carriage return and
line feed and clobbers AF and HL.

`HAL_READ0` reads one 512-byte physical sector from drive 0, track 0, side 0.
C contains the physical sector number and HL the destination. It returns A=0
with Z set on success, or controller status with NZ set on failure, and
clobbers AF, BC, DE, and HL.

`HAL_READ0` is deliberately narrow. Later work will replace it with the proper
physical-I/O contract for arbitrary drives, cylinders, sides, and sectors.
Logical CP/M records, allocation, directories, and formats do not belong here.

## Verification fixture

The image builder places a deterministic signature in physical sector 5. The
portable diagnostic reads it at `6000h` and compares the signature. This is
test data, not a proposed BetterCP/M filesystem structure.

The stage-one stack is at `7000h`, in RAM stable across the Model 4 video-map
transition. Bring-up demonstrated that a platform initializer must not return
across a mapping change with its return address in a remapped region.

Run:

```sh
python3 tools/build_trs80_boot.py
python3 tools/test_trs80_boot.py
python3 tools/build_native_trs80.py
```

The emulator checks the entire 2,048-byte display and the successful disk-read
message. Native ZSM4 and Digital Research LINK 1.3 output matches the host
cross-build byte for byte.

```text
c9d73093405f49e2545774dd2bcfabb795fa01b35e3487d8447318754fe23221  boot.bin
e60d729dc351995367d969e11cc4a66f3c760b2a3765b8d4a5c29d6c0e1e2cb5  stage1.bin
5145568307bb24e1efe34567f02a0a5f2dc4cc822cae0658d763e57b81050dae  BetterCPM-Extended-80T-DS-System-790K.dmk
```

## Next increment

Implement console-input status and character input behind this boundary, then
exercise them from the portable diagnostic before generalizing disk I/O.
