# Engineering Specification 04: Console Input Milestone

Status: Implemented and verified  
Date: 2026-09-01

## Result

The initial platform boundary now provides console-input status and blocking
character input. The portable bring-up diagnostic waits for a key and echoes
it using only platform calls:

```text
BetterCP/M
TRS-80 Model 4 platform initialized
raw disk read verified
key: K
```

## Interface

`HAL_CONST` scans the keyboard and returns A=0 with Z set when no supported
key is pressed, or a nonzero character with NZ set when input is available.

`HAL_CONIN` waits for a supported key, waits for its release to prevent a
single physical press from being repeated, and returns its ASCII value in A.

These calls are the bring-up interface, not yet the final CP/M BIOS entry
points. Their semantics will be reconciled explicitly with BIOS `CONST` and
`CONIN` when that interface is specified.

## Model 4 implementation

The keyboard matrix is visible at `F400h` in the same mapping that exposes
video memory at `F800h`. Rows are selected at `F401h`, `F402h`, `F404h`,
`F408h`, `F410h`, `F420h`, and `F440h`; each returned bit represents a column.

The initial table translates ordinary letters, digits, punctuation, Enter,
and Space. Shift, Control, Caps, function keys, arrows, Clear, and Break are
deliberately deferred. Those require defined translation and system-policy
semantics rather than ad hoc hardware behavior in the core.

The source retains a dated patch comment at the matrix scanner because the
address-bit row selection is non-obvious and historically important platform
knowledge.

## Automated verification

The emulator test injects `K` directly into Model 4 matrix row 1, column 3,
holds it for four frames, releases it, and requires `key: K` on the fourth
display row. This avoids relying on ROM or DOS keyboard routines, which are
not part of the BetterCP/M environment.

Native ZSM4 and Digital Research LINK 1.3 output remains byte-identical with
the host cross-build.

```text
c9d73093405f49e2545774dd2bcfabb795fa01b35e3487d8447318754fe23221  boot.bin
d975247b53a22735801679b8a3f469a332487305f08738fc85302ea262eced96  stage1.bin
db0b017800f50660c7c48f0cf9c7ed734b92158ded8f5f802456a97fbefcd393  BetterCPM-Extended-80T-DS-System-790K.dmk
```

Stage one is now 505 bytes. Only seven bytes remain in its temporary 512-byte
sector, so this diagnostic stage is closed to substantial new functionality.
New resident-system components will be assembled independently. Booting a
larger combined image will eventually require the already-deferred loader
enhancement, but that need not precede development of those components.

## Next increment

Specify the initial BIOS entry contract and create an independently assembled
resident-system scaffold using the verified console semantics. CCP and BDOS
will likewise remain independently buildable as drop-in components behind an
existing loader and BIOS. The future complete-system loader is a separate
integration milestone.
