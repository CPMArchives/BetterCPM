# BCPM780 named binding and installation qualification

The shared CONFIG/FDB runtime conversion resolves the named BCPM780 rejection
without changing BIOS, the catalogue, or the locked resident system. Source fix
`6e3980b647c2a5c9a76c7d5f2ee451e0300f0bf1` and integration receipt
`bbcdaa3f98e83ebe9abba7a35035c7b0d486a0a8`, followed by name-lookup fix
`a54dc243b549d54154488d31a2b318b54d8d6bfc`, were coordinated with the FDB
integration workstream. The package freeze remains **on hold**.

BCPM780 retains its cylinder-based definition in DISK.FDB. Only the temporary
runtime binding changes from SPT 80/OFF 2 to SPT 40/OFF 4, with DSM 389 unchanged.
Both representations put the directory at byte 20480. Unsupported topology,
zero/odd SPT and reserved-area overflow are refused without committing a binding.

## Tested inputs

These are isolated integrations into private copies of the qualified
`35c56a03f253c10d85ccb110ca34c1f368f319a1` System images, not rebuilt release
packages. Only CONFIG.COM is replaced for these independent installation tests;
all other candidate components, including DISK.FDB and SYSGEN, stay unchanged.

| Input | SHA-256 |
| --- | --- |
| Original cpmsim System image | `6b6e9035b5e6933fd38edd21ab4f611c065b1740c5e6eb83d53f03ace940892d` |
| Original Model 4 System DMK | `4e661bab569b81ac583f74aabedf41001a76b28d9721ab911e6ff0995feaf5cd` |
| cpmsim CONFIG.COM | `29db48952a559454003b92874740cd7f15b53451f9cf9876b893f06b1820919b` |
| Model 4 CONFIG.COM | `4b8f39baa0fa3ac2f57a580f815d49c308293a766a716038fcf96b6de225793a` |
| FDB.COM, separate shared-path tests | `c38439969b3fe1fc2a9a9fbc9a73b0c091b4bd29005f659fe58586c1e031616c` |
| cpmsim executable | `0f6b256cd6beea2ab7bf0eab8a9cc2a5241ed772408e811150c3f6e0f5cff4e8` |
| trs80gp executable | `8f967e640927af1fb9de3a178bbf0bc4d687124780405885a6daa33a3fee1d9f` |

Both platform CONFIG binaries were independently assembled from the committed
source using their matching generated resident validation and I/O records. The
hashes match the integration workstream's binaries; CONFIG layout checks pass.

## cpmsim

PASS: a raw sector extraction of the qualified Model 4 System DMK was mounted
as physical drive 3. Its 80-track, double-sided physical profile was set before
selecting the named BCPM780 format:

```
CONFIG /PHYSICAL=3 /TRACKS=80 /SIDES=2
CONFIG /LOGICAL=D /PHYSICAL=3 /FORMAT="BetterCP/M Model 4 System 780K"
DIR D:
TYPE D:README.TXT
```

The assignment succeeds and the read returns the Model 4 System README. The
780K disk remains byte-identical. The default 40-track cpmsim physical profile
correctly refuses this 80-track format; that preliminary refusal was a test
setup mismatch, not a normalization failure.

Installation uses the platform-native 332K cpmsim boot layout. B: is assigned
by its catalogue name, `California Computer Systems`, a named package is
exported with `SYSGEN A: B:INSTALL.SYS`, then installed onto populated C: with
`SYSGEN B:INSTALL.SYS C:` and confirmation Y. The entire destination filesystem
is byte-identical across installation. Cold boot from that destination reads
KEEP.TXT, displays CONFIG settings and runs RSX LIST. Every original shipped
file and the sentinel match after cold boot; the reserved system area is
unchanged by boot. Normal startup/SUBMIT leaves deleted scratch records, so
whole-image equality after boot is not an appropriate preservation test.

## Model 4

PASS: the final CONFIG selects B: by the exact BCPM780 display name on a
private 780K System target in physical drive1. DIR B: and TYPE B:KEEP.TXT
succeed, followed by SYSGEN named export and confirmed installation on B:.
All30 shipped files and the pre-existing sentinel are preserved; INSTALL.SYS
is the only additional live file. The exported20608-byte package has a valid
BCSY header. Its20480-byte payload differs from the installed reserved area
at exactly offset7030: E0h becomes A0h, the expected installed A: bootstrap
binding conversion already asserted by the existing SYSGEN regression.

The target then cold-boots alone in physical drive0. TYPE KEEP.TXT, CONFIG
/SHOW (saved IOBYTE149), and RSX LIST (ADM3A present) all succeed. Native
screens and the all-file audit are retained beside the machine receipt.
See the updated shipped-installation walkthrough for the named command and
platform-native destination geometry.

## Scope and release status

The integration workstream's independent 109-entry sessions verify CONFIG named
selection and actual file reads on both platforms, source/catalogue preservation,
unchanged reserved tracks and no backup/temp residue. Reader, CONFIG CLI,
validation-record, FDB editor, session and binary/text round-trip regressions
pass. The independent review checkout also reran the native reader and named
CONFIG CLI tests and reproduced both CONFIG hashes.

The passing receipts close the BCPM780 normalization issue at the tested ref. Final FDB.COM/CONFIG/DISK.FDB integration acceptance, rebuilding
all six candidates, checking the resulting inventories and hashes, and final
documentation sign-off still precede any package freeze. No freeze, tag or
release is authorized by this qualification.
