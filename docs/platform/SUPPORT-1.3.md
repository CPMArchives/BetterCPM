# BetterCP/M 1.3 maintained platforms

| Platform | Maintained baseline | Default unloaded maximum COM |
| --- | --- | ---: |
| cpmsim | Patched z80pack, flat 64 KiB RAM | 57,344 bytes |
| TRS-80 Model 4 | Existing trs80gp keyboard/video reservation | 54,272 bytes |
| TRS-80 Model II | 64 KiB, trs80gp, single-sided eight-inch BCM2SS IMDs | 57,344 bytes |
| Altair Z80 / Tarbell | Pinned serial-only z80pack, flat 64 KiB, 88-2SIO, Tarbell 1011D single-density | 57,344 bytes |

The original platform and hardware boundaries remain those of
[1.2](SUPPORT-1.2.md). Altair was added on 28 November 2026 with a separately
qualified emulator configuration and fixed Tarbell geometry. Physical hardware
and other models or controller configurations remain unqualified. The default PDS composition is HISTORY 192 bytes, MCL
Off and VAR Off, with 12 metadata bytes and 204 total bytes. Enabling optional
owners can reduce COM capacity; CONFIG and STAT MEM show the cost.

The [published 1.3 release](https://github.com/CPMArchives/BetterCPM/releases/tag/v1.3)
and [publication record](../releases/evidence/1.3-publication/publication.json)
bind the original platforms to frozen source `51e1092d`. The Altair addition
has its own [publication record](../releases/evidence/altair-1.3-publication/README.md)
and frozen source `6bfb621b`. The
[readiness record](../releases/1.3-READINESS.md) retains the focused evidence.

Installation: [cpmsim](CPMSIM-INSTALLATION.md),
[Model 4](MODEL4-INSTALLATION.md), [Model II](MODEL2-INSTALLATION.md),
[Altair](ALTAIR-INSTALLATION.md).
