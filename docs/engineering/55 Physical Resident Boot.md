# Engineering Specification 55: Physical Resident Boot

## Milestone

The generated Montezuma Micro Extended 790K DMK now boots the complete initial
BetterCP/M resident system under `trs80gp` and reaches the CCP `A>` prompt.

## Disk placement and loader

The Model 4 ROM loads the 146-byte stage-zero record at `4300h`. Stage zero
loads the 271-byte stage-one loader at `5000h`. Stage one then reads 26
successive 512-byte sectors from logical system-sector positions 2 through 27
into `BF00h` and enters BIOS BOOT.

Those sectors contain the composed sparse resident image: system gateway, BDOS,
directory services, CCP, reserved workspaces, and BIOS. The image occupies
13,123 bytes and is padded only to the loader's 13,312-byte transfer boundary.
All 28 sectors used by stage zero, stage one, and the resident image remain
inside the format's two reserved cylinders, which provide 40 sectors total.
The CP/M filesystem area therefore remains untouched.

## Hardware-safe resident map

Physical testing exposed that the earlier provisional BIOS at `F000h` extended
through `F400h`, the Model 4 keyboard-matrix region. The corrected map places:

- CCP at `EA40h`;
- BIOS directory/check/allocation workspaces at `EBC0h` through `EC91h`;
- the BIOS 512-byte physical buffer at `ED00h` through `EEFFh`; and
- BIOS code at `EF00h` through `F242h`.

The 26-sector loader padding ends at `F2FFh`, safely below keyboard memory.
Page-zero WBOOT and all internal BIOS vector references were updated to the new
`EF00h` base. The CP/M-visible vector organization remains unchanged.

## Cold boot

Stage one enters the BIOS BOOT vector rather than bypassing it. BIOS BOOT clears
and initializes the Model 4 console, then invokes portable reconstruction,
drive login, disk reset, and CCP entry.

Initial directory/allocation reconstruction scans all 128 directory entries.
The automated emulator snapshot therefore allows enough time for both the
26-sector resident load and the complete cold-login scan.

## Verification

The updated test boots the actual generated DMK through `trs80gp` and requires a
clean `A>` prompt. The resident execution test separately scripts `WARM` and
`VER`, proving command processing and WBOOT reconstruction after the physical
loader boundary.

The first manual `VER` run exposed that the following prompt used LF without CR
and therefore inherited the version line's ending column. The CCP prompt now
uses CR/LF so every prompt begins in column zero; this small post-milestone patch
is retained here as part of the physical-boot history.

Native CP/M ZSM4/Digital Research LINK and the host assembler must continue to
produce byte-identical boot, stage-one, BIOS, BDOS, directory, CCP, and gateway
components.

## Next increment

Implemented by [`Engineering Specification 56`](56%20Transient%20COM%20Loader.md).
