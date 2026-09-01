# Engineering Specification 54: Initial CCP and WBOOT

## Milestone

BetterCP/M now has its first resident command processor and real BIOS BOOT and
WBOOT control paths. Resident-system execution reaches an `A>` prompt, accepts
an edited command through BDOS Function 10, and returns through Function 0 to a
fresh prompt.

## Command processor

The provisional CCP now resides at `EA40h`, above the current directory-services
image and below the BIOS physical buffer. Its first command loop provides:

- a current-drive prompt;
- case-insensitive command acquisition using the CP/M counted console buffer;
- `VER`, which prints `BetterCP/M 0.1`;
- `WARM`, which invokes BDOS Function 0; and
- `?` for an unrecognized command.

This is intentionally not yet the full CP/M command environment. Transient COM
loading and the conventional built-ins remain subsequent milestones.

## BOOT and WBOOT

BIOS BOOT and WBOOT now jump to stable portable-system gateways at `C020h` and
`C023h`. Reconstruction logs drive A, republishes the page-zero WBOOT and BDOS
gateways, invokes BDOS Disk Reset to restore DMA `0080h` and disk state, and
enters the CCP nonreturningly.

## Preserved patch history: reconstruction stack

The first integrated Function-0 test found that WBOOT initially arrived on the
BDOS private stack and then called BDOS Function 13 using that same stack. The
nested call overwrote WBOOT's return frames. BOOT/WBOOT now establish a distinct
32-byte system reconstruction stack before invoking resident services. The
source retains a dated patch comment because this failure records an important
resident-stack ownership boundary.

## Verification

The resident test deliberately corrupts both page-zero gateways and selects a
nondefault DMA address. It enters WBOOT, scripts `WARM` and `VER`, and verifies:

- three successive `A>` prompts;
- Function 0 returns through the complete WBOOT reconstruction path;
- the version response is printed;
- page-zero gateways are restored; and
- DMA returns to `0080h`.

The CCP is independently assembled both by the host toolchain and by native
CP/M ZSM4/Digital Research LINK, with byte-identical output required.

## Physical-boot status

Engineering Specification 55 replaces the stage-one diagnostic with a resident
loader and boots this CCP from the generated physical TRS-80 disk.

## Next increment

Implemented by [`Engineering Specification 55`](55%20Physical%20Resident%20Boot.md).
