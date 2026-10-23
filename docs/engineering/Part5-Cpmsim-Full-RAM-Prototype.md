# Part 5: experimental full-RAM cpmsim profile

This isolated assessment branch starts at accepted core 1.0 commit
`3b2d2d7f4fe0472438465165f11fb550d79c8662`. It is not a replacement release.
Part 4 was approved on 2026-10-23. Model 4 upper-RAM mapping is a separate
post-1.0 roadmap investigation.

The resident layout moves upward by 0C00h, preserving all component capacities.
The exclusive RAM endpoint is 10000h in host arithmetic. `LY_TOPRSV` gives STAT
a 16-bit-safe condition for omitting an empty platform-reserved row. CONFIG,
SYSGEN and SYSBUILD derive both instructions and serialized header words from
the selected layout. Three RSX test fixtures derive their FCB addresses too.

## Build

In a fresh checkout, with the existing z80asm and cpmtools prerequisites:

```sh
python3 tools/assessment_fullram_cpmsim.py
```

The result is `assessment-media/system.raw`, with diskdefs, extracted-file
checks, source/artifact hashes, and logs. Each profile requires its own complete
source/build directory. The prototype does not provide a production profile
selection API. The builder rejects an existing cpmsim output disk directory;
use a fresh checkout for a reproducibility run.

The existing clean-build dependency cycle still constructs Model 4 artifacts
for common utility metadata. Those artifacts are not qualified or usable as a
Model 4 full-RAM system. Only the final cpmsim RAM media is the deliverable.
`--ram-only` skips ROM construction and requires `--system-tracks-only`.
No Model 4 or ROM acceptance is implied.

## Measured result

cpmsim cold boot and a patterned maximum-size application both establish
57,344 bytes (56 KiB), up 3,072 bytes from the pinned core. With ANSISCRN and
ADM3A manually loaded, capacity is 54,272 bytes (53 KiB). The pinned startup
script itself runs only `VER /BANNER`; it does not load those providers.
Four module slots, two callable services per module, the 1 KiB shared manager,
history, disk workspaces and reclaimable CCP/RCP allocations are unchanged.

The focused campaign covers maximum-size and oversized COM files, RET/JP 0/
Function 0/BIOS WBOOT, stateful RSX relocation and preparation failures,
monitor load/unload, CONFIG save/cold restore, cross-drive I/O, disk and named
package installation with filesystem preservation, and 800 KiB data geometry.
A legacy control matches 43 checked baseline artifacts byte for byte.

## Adoption blockers and limits

The existing R3PACK reader accepts all fifteen helper slots from the old
layout. A CPU fixture observed the foreign bytes being installed and stopped
before executing them. A checked private build/layout identity is required
before supporting interchangeable profile artifacts. SYSGEN does reject a
foreign-layout system package before confirmation and writes.

Native/cross assembler parity, a production profile build interface, broader
release acceptance and Model 4 mapping remain unqualified. The measured gain
has no identity-check overhead yet; it is not a promise that subsequent
hardening is free. Transaction workspace remains capped at 7000h.

The Part 5 report and evidence bundle retain commands, transcripts, fixtures,
patch, profile metadata and binary hashes. Pause after reviewing this part;
do not merge this experimental branch into the core baseline.
