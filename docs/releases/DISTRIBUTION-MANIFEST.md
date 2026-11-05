# BetterCP/M 1.0 delivered inventory

The [five-package lock](non-documentation-lock-1.0/README.md) and [exact eight-image/file inventory](non-documentation-lock-1.0/CONTENTS.json) control delivered membership. This is a readable projection, not authority to add/remove files or rebuild packages. Source software revision is `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`. The sixth Documentation ZIP has [separate provenance](DOCUMENTATION-PUBLICATION.md).

## Disk images

| Package | Image | Role | Files |
| --- | --- | --- | ---: |
| system-model4 | `BetterCPM-Distribution-trs80gp-80T-DS-System.dmk` | System | 32 |
| system-model4 | `BetterCPM-Work-800K.dmk` | blank formatted work image | 0 |
| system-cpmsim | `BetterCPM-Distribution-z80pack-332K.dsk` | System | 36 |
| system-cpmsim | `BetterCPM-Work-332K.dsk` | blank formatted work image | 0 |
| utilities-model4 | `BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk` | Utilities/companion | 7 |
| utilities-model4 | `BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk` | Utilities/companion | 26 |
| utilities-cpmsim | `BetterCPM-NOAH-z80pack-332K.dsk` | Utilities/companion | 7 |
| utilities-cpmsim | `BetterCPM-Utilities-z80pack-332K.dsk` | Utilities/companion | 26 |

## Selected file membership

Each list follows the locked image inventory, including support/overlay files. Implemented or buildable code outside these lists is not supplied disk content.

### system-model4 — System

`README.TXT`, `STARTUP.SUB`, `DIR.COM`, `ERA.COM`, `TYPE.COM`, `REN.COM`, `VER.COM`, `COPY.COM`, `CONFIG.COM`, `DUP.COM`, `TIME.COM`, `SYSGEN.COM`, `STAT.COM`, `SUBMIT.COM`, `CPX.COM`, `RSX.COM`, `FDB.COM`, `FDBVIEW.OVL`, `DISK.FDB`, `RCP.CPX`, `FREHDCLK.RSX`, `R3PACK.RSX`, `PIP.COM`, `ED.COM`, `ADM3A.RSX`, `ADMTST.COM`, `VT52.RSX`, `VT52TST.COM`, `ANSI.RSX`, `ANSITST.COM`, `M4SCRN.RSX`, `P2DOS.RSX`.

### system-cpmsim — System

`README.TXT`, `STARTUP.SUB`, `DIR.COM`, `ERA.COM`, `TYPE.COM`, `REN.COM`, `VER.COM`, `COPY.COM`, `CONFIG.COM`, `DUP.COM`, `TIME.COM`, `SYSGEN.COM`, `STAT.COM`, `SUBMIT.COM`, `CPX.COM`, `RSX.COM`, `FDB.COM`, `FDBVIEW.OVL`, `DISK.FDB`, `RCP.CPX`, `ZPRTC.RSX`, `R3PACK.RSX`, `PIP.COM`, `ED.COM`, `BYE.COM`, `ADM3A.RSX`, `ADMTST.COM`, `VT52.RSX`, `VT52TST.COM`, `ANSI.RSX`, `ANSITST.COM`, `ANSISCRN.RSX`, `MOUNT.COM`, `R.COM`, `W.COM`, `P2DOS.RSX`.

### utilities-model4 — Companion Utilities

`NOAH.COM`, `NOAH.OVL`, `NOAH.TXT`, `PATCH.COM`, `PATCH.TXT`, `COMPARE.COM`, `COMPARE.TXT`.

### utilities-model4 — Primary Utilities

`DDT.COM`, `DUMP.COM`, `XSUB.COM`, `BATCHIO.RSX`, `SQ.COM`, `USQ.COM`, `UNCR.COM`, `CR.COM`, `UNLZH.COM`, `LZH.COM`, `ZSM4.COM`, `LINK.COM`, `TOOLINFO.TXT`, `ZSM4COPY.TXT`, `LINKCOPY.TXT`, `DASM.COM`, `DSYM.COM`, `DLINK.COM`, `DASM.TXT`, `DASMCOPY.TXT`, `TED.COM`, `TED.TXT`, `TEDCOPY.TXT`, `SEARCH.COM`, `CRCKSUM.COM`, `MD5SUM.COM`.

### utilities-cpmsim — Companion Utilities

`NOAH.COM`, `NOAH.OVL`, `NOAH.TXT`, `PATCH.COM`, `PATCH.TXT`, `COMPARE.COM`, `COMPARE.TXT`.

### utilities-cpmsim — Primary Utilities

`DDT.COM`, `DUMP.COM`, `XSUB.COM`, `BATCHIO.RSX`, `SQ.COM`, `USQ.COM`, `UNCR.COM`, `CR.COM`, `UNLZH.COM`, `LZH.COM`, `ZSM4.COM`, `LINK.COM`, `TOOLINFO.TXT`, `ZSM4COPY.TXT`, `LINKCOPY.TXT`, `DASM.COM`, `DSYM.COM`, `DLINK.COM`, `DASM.TXT`, `DASMCOPY.TXT`, `TED.COM`, `TED.TXT`, `TEDCOPY.TXT`, `SEARCH.COM`, `CRCKSUM.COM`, `MD5SUM.COM`.

## Startup, modules and identity

Model 4 STARTUP.SUB loads M4SCRN then ADM3A, clears the screen and runs `:VER /BANNER`, reporting 50K TPA. cpmsim runs the banner with no personality/clock, reporting unloaded 53K. Neither loads a clock or P2DOS. Native providers are optional to load; both are read-only. P2DOS.RSX is supplied in A0; 104/105 adapters are deferred.

FDB 1.0 (001) and its matching FDBVIEW.OVL are on both System disks with the 108-entry DISK.FDB. Interactive work needs unloaded 53K; use the documented unload/restore workflow on Model 4. Current main's FDB 1.01 is development. CLS/USER/MOVE transients and FDF.RSX are not selected System files. SYSBUILD is a build/composition tool, not an ordinary selected System command.

XSUB.COM and BATCHIO.RSX are primary Utilities files; activation requires copying the matching BATCHIO companion to writable A0 alongside R3PACK.RSX. NOAH/PATCH/COMPARE are on the companion disk; keep NOAH.COM/NOAH.OVL matched. ZSM4/LINK retain their original identities/interfaces and complete permission/source companions. CP/M Tools binaries in source snapshots are outside selected disk inventories.

Distribution 1.0 does not replace utility/module/API versions. The locked inventories and final identity receipts control; current development counters and old survey/candidate revision numbers must not overwrite them. Ordinary user-area zero contents, file hashes, byte sizes and images are recorded in CONTENTS.json.

## Formats, licensing and release status

Release media use CCS 332K, Model 4 800K DATA and BCPM780 System. Optional historical 790K is distinct. Catalogue admission is not universal physical qualification. All five archives retain their license/provenance/source notices; the original Montezuma catalogue, utility binaries and disassemblies remain excluded. See [format scope](../platform/FORMAT-SUPPORT-1.0.md) and [licensing inventory](../LICENSING-INVENTORY.md).

Earlier membership checkpoints remain in Git/engineering history. No component is added by moving its manual into the Command Reference. The dedicated Documentation selection now presents four manuals and supporting references; final acceptance of the exact Documentation bytes is recorded in a companion receipt, while tagging and publication remain held.
