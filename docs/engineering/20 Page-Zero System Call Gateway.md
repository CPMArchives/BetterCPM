# Engineering Specification 20: Page-Zero System Call Gateway

## Milestone

BetterCP/M now executes a CP/M application-style `CALL 0005h` through page
zero, the initial BDOS dispatcher, System Services, and the BIOS disk path.
This establishes the first complete resident system-call route without yet
placing that resident image into the TRS-80 boot disk.

## Provisional resident layout

This original bring-up layout is superseded by Engineering Specification 29.
It remains here as the historical placement under which the page-zero gateway
was first proved.

The independently built components occupy non-overlapping provisional ranges:

| Component | Base | Current extent |
| --- | ---: | ---: |
| Initialization and page-zero gateway | `E500h` | 28 bytes |
| BDOS dispatcher and private stack | `E600h` | 123 bytes |
| Directory/System Services | `E800h` | 869 bytes |
| BIOS | `F000h` | 1,040 bytes |

`tools/build_system.py` validates component ordering and overlap, then creates
`build/system/resident.bin`, whose address span is `E500h` through `F40Fh`.
Zero-filled gaps remain deliberate placement space, not assigned interfaces.
These addresses are engineering placements and do not decide the final memory
size, CCP base, or boot image organization.

## Initialization contract

The entry at `E500h` logs in default drive A before publishing any page-zero
entry. Only after successful login does it install:

- `0000h`: `JP F003h`, the BIOS warm-boot vector; and
- `0005h`: `JP E600h`, the BDOS entry.

If drive login fails, initialization returns the storage error and leaves page
zero unchanged. An application therefore cannot enter a resident system whose
allocation and directory state was only partly initialized.

The dated patch comment in the gateway preserves the transition from direct
dispatcher testing to the conventional page-zero interface.

## Verification

The executable resident-system test supplies a CP/M directory fixture through
the BIOS physical-read boundary, runs initialization, and verifies both
page-zero jump vectors byte for byte. A four-byte application fragment then
executes `CALL 0005h` with function 15 in `C` and an FCB in `DE`.

The call finds and activates the file, returns the correct `A/L` and `B/H`
aliases, and restores the application's stack exactly. A separate simulated
disk failure proves that initialization does not publish either vector.

The host assembler and native CP/M ZSM4/Digital Research LINK must produce the
same 28-byte gateway binary.

## Deferred work

This is not yet a complete bootable operating system. The resident image has
no CCP, the BIOS `BOOT` and `WBOOT` entries remain stopping scaffolds, only BDOS
function 15 is implemented, and stage one does not yet load this composition.

## Next increment

Engineering Specification 21 completes this increment with functions 12, 25,
26, and 32, verified through `CALL 0005h`. The next increment can establish
default-drive selection and its login-state transition before widening file
operations.
