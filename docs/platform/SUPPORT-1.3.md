# BetterCP/M 1.3 candidate platforms

| Platform | Maintained baseline | Default unloaded maximum COM |
| --- | --- | ---: |
| cpmsim | Patched z80pack, flat 64 KiB RAM | 57,344 bytes |
| TRS-80 Model 4 | Existing trs80gp keyboard/video reservation | 54,272 bytes |
| TRS-80 Model II | 64 KiB, trs80gp, single-sided eight-inch BCM2SS IMDs | 57,344 bytes |

The platform and hardware boundaries remain those of
[1.2](SUPPORT-1.2.md). Physical hardware and additional models or ports have not
been newly qualified. The default PDS composition is HISTORY 192 bytes, MCL
Off and VAR Off, with 12 metadata bytes and 204 total bytes. Enabling optional
owners can reduce COM capacity; CONFIG and STAT MEM show the cost.

The [1.3 readiness record](../releases/1.3-READINESS.md) distinguishes focused
engineering evidence from final combined-package acceptance. This candidate
is not a release acceptance or publication claim.

Installation: [cpmsim](CPMSIM-INSTALLATION.md),
[Model 4](MODEL4-INSTALLATION.md), [Model II](MODEL2-INSTALLATION.md).
