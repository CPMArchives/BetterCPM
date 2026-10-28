# Installing BetterCP/M on a TRS-80 Model 4

Status: release-candidate instructions; fresh-package manual verification pending.
These instructions describe the supplied Model 4 media. They do not establish
physical-hardware or emulator qualification of a newly packaged candidate.

## Prepare the media

Extract the System package into a new directory, check SHA256SUMS.txt and retain
original images unchanged. Make writable copies for use. The Utilities package
is a separate optional download; choose its Model 4 DMKs, not cpmsim raw images.

| Drive | Image / role |
| --- | --- |
| A: / physical 0 | BetterCPM-Distribution-trs80gp-80T-DS-System.dmk |
| B: / physical 1 | BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk, when installed |
| C: / physical 2 | BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk, when installed |
| D: / physical 3 | Supplied blank 80-track double-sided work disk |

All images use 80 cylinders, two sides and ten 512-byte sectors per side.
A: uses the BetterCP/M extended SYSTEM layout, with two reserved cylinders and
780 KiB of allocation space before directory/file use. B:-D: use the MM 800K
DATA layout with no reserved system area. The System image is bootable; the
Utilities and work images are data media. Blank work media can occupy B:/C:
when Utilities are absent. Do not substitute a different geometry by filename.

C: retains its historical NOAH name and also contains PATCH and COMPARE.
Use NOAH.COM and NOAH.OVL from the same package. CRCKSUM and MD5SUM are on B:.

## Start trs80gp manually

Use the maintainer's working manual trs80gp launch procedure. Select Model 4
and attach the writable copies to physical drives 0 through 3 as above, with
80-track double-sided drive support. For a local command-line installation:

```sh
/path/to/trs80gp -m4 \
  -d0 /path/to/system-copy.dmk \
  -d1 /path/to/primary-utilities-copy.dmk \
  -d2 /path/to/companion-utilities-copy.dmk \
  -d3 /path/to/work-copy.dmk
```

Replace paths with the extracted copies. If Utilities are not installed, attach
matching blank data disks instead. FreHD is optional: use the emulator's FreHD
configuration only when testing that provider. Its presence is not required
for ordinary disk/console operation.

The supplied startup script loads M4SCRN, then ADM3A, clears the display and
shows the banner. A clock provider is not loaded automatically. Wait for the
A0 prompt, inspect the System Disk and confirm its identity:

```text
VER /BANNER
DIR A:
RSX LIST
```

When Utilities are installed, inspect DIR B: and DIR C:, then run B0:DUMP /VER,
B0:CRCKSUM /VER, B0:MD5SUM /VER, C0:NOAH /VER, C0:PATCH /VER and
C0:COMPARE /VER. Compare the actual banners and files with RELEASE.json.
Confirm return to the original drive/user after each query. These smoke checks
do not replace the full manual validation checklist.

## Work disks, installation and validation

Keep personal files on work media. Back up the System image before changing
CONFIG defaults or STARTUP.SUB. TYPE A0:STARTUP.SUB shows the startup script.
For copying/installing system tracks to compatible prepared media, consult the
User's Guide DUP/SYSGEN procedures; copying ordinary directory files alone does
not install a bootable system. Do not format a disk containing wanted data.

On physical hardware, DMK is an emulator container and must first be transferred
using equipment/software appropriate to the actual media and controller.
Do not assume a generic raw-image write transfers DMK correctly. Physical
installation and hardware-specific transfer steps require their own validation.

Record package/image/component hashes, trs80gp version, drive setup, commands,
expected results and actual outcomes for the fresh-package test. Work from the
[Model 4 release checklist](../engineering/Model%204%20Release%20Checklist.md).
Preserve earlier blocked/deferred records and append actual results. Do not
retry the automated LaunchServices path merely to execute these manual checks.
