# Booting BetterCP/M on the TRS-80 Model II

Use the 1.1 engineering candidate for the 64 KiB Model II in trs80gp 2.5.8.
The System and Utilities images use the BCM2SS single-sided eight-inch format.
Keep the original IMDs and work on copies. The release qualification record is
in the [Model II port notes](MODEL2-PORT.md#what-passes-and-what-remains).

## Start the emulator

From the folder containing the two candidate images, run the following on macOS.
The first command creates a fresh folder for the writable disks and prints its
location so you can reopen the same disks later.

```sh
workdisks=$(mktemp -d "$HOME/BetterCPM-Model-II.XXXXXX") && echo "$workdisks"
cp Model-II-System-candidate.imd "$workdisks/System.imd"
cp Model-II-Utilities-candidate.imd "$workdisks/Utilities.imd"
"$HOME/Applications/trs80gp.app/Contents/MacOS/trs80gp" -m2 -mem 64 \
    -d0 "$workdisks/System.imd" -d1 "$workdisks/Utilities.imd"
```

Use the emulator's built-in Model II ROM. Drive 0 is A and drive 1 is B.
Keep the System Disk mounted in drive 0 during the session. A cold boot reads
its startup settings. A warm boot, including Ctrl-C at the command line,
reconstructs the command environment from A.

## At the prompt

When `A0>` appears, enter each command on its own line.

| Command | What to look for |
| --- | --- |
| `DIR` | The System Disk directory in user area 0. |
| `DIR B:` | The Utilities Disk directory. This candidate carries the management utilities and disk catalogue. |
| `CPX LIST` | The resident command package RCP.CPX and 56K of available TPA on an unloaded startup. |
| `PATH` | The current command search order. Use `A0:PATH /DEFAULT` to restore the default. |
| `TIME` | With the standard startup it reports that no TIME provider is loaded, with service status 01. |
| `CONFIG /SHOW` | The saved drive bindings. The default maps A through D to units 0 through 3. |

The basic console is ready at startup. Applications using a terminal personality
can load the Model II screen backend and one of the supplied ADM3A, VT52 or
ANSI modules. For VT52 use the following commands before and after the
application.

```text
RSX LOAD M2SCRN
RSX LOAD VT52
RSX LIST
RSX UNLOAD VT52
RSX UNLOAD M2SCRN
```

## Mount the full Utilities set

The separate candidate Utilities package contains a primary disk and a companion.
The small Utilities image in the System build is a management disk. For the full
collection, place writable copies of the following IMDs in these drives before
booting. The same `-d0`, `-d1` and `-d2` options select them in trs80gp.

| Drive | Image |
| --- | --- |
| A (0) | `Model-II-System-candidate.imd` |
| B (1) | `BetterCPM-Utilities-trs80m2-77T-SS-584K.imd` |
| C (2) | `BetterCPM-NOAH-trs80m2-77T-SS-584K.imd` |
| D (3), optional | A writable BCM2SS work disk |

B contains the debugger, editor, assembler, compression and checksum utilities,
SUBMIT, XSUB and the Model II BATCHIO provider. C contains NOAH and its overlay,
PATCH, COMPARE and the supplemental disk catalogue. Change to C before running
NOAH so it can find its matching overlay. For submitted input with BATCHIO on B,
use `B0:XSUB B0:` in the job. Keep the source companions and notices in the host
Utilities archive when distributing the disks.

## Make a bootable duplicate

Use a separate, expendable, preformatted BCM2SS image in drive 1. Eject the
Utilities Disk from that drive first. With the source System Disk in drive 0,
enter `DUP /COPY A: B:`. Check the source and destination letters before
confirming. This overwrites the whole destination, including its files and
startup settings. Then enter `DUP /CHECK B:` to read the copy. To try it as a
System Disk, mount the copy in drive 0 and cold boot the emulator.

To reinstall the system tracks on an existing BCM2SS disk while preserving its
filesystem, place matching copies of `RCP.CPX`, `R3PACK.RSX` and `R3CACHE.RSX`
in user area 0 on the destination. With that disk in B and the matching source
System Disk in A, enter `SYSGEN SYSTEM.SYS B:` at A0 and confirm the target.
SYSGEN checks the destination companions and verifies the install. Keep the
original available until the new disk boots independently.

The supported candidate geometry uses an FM boot surface and 16 × 512-byte MFM
data tracks. Other Model II images can have the same CP/M logical track size
and still require different physical reads. Use BCM2SS for all mounted disks
in this configuration. Low-level formatting, double-sided media and Model
12/16/16B configurations are outside this candidate.
