# REN.COM qualification — 2026-10-13

REN 1.0 Build 005 implements the transient workflow in
[REN Specification](REN%20Specification.md). The image is 5,553 bytes with
SHA-256 `8c689fa395dfae97b97261e94cf3797c3eb6c01e1445aa48b11a62afa28a6e66`.

## Native build

`tools/build_native_ren.py` builds the same expanded source with CP/M ZSM4 and
LINK and compares the executable bytes with the cross build. Reserved workspace
and stack bytes are explicitly initialized to FF in the native source to match
the cross assembler's reservation fill. The native result passed byte-for-byte
comparison; this changes build reproducibility, not command behavior.

The native campaign used z80pack's `cpm22-62khd.dsk`, the compatibility suite's
IBM-3740 blank media and its ZSM4.COM/LINK.COM. Set PATH to cpmsim's `srctools`
and supply their locations using `--cpmsim`, `--system-disk`, `--disk-template`
and `--tools`. The transcript is saved as `build/utilities/NATIVE-REN-BUILD.LOG`.

## Real BDOS and media

`tools/test_z80pack_ren.py --image-dir <build/z80pack> --report <new-directory>`
copies qualified BetterCP/M runtime media and installs the current REN image.
It passed against a clean build of the current system sources as well as the
previous qualified runtime. It checks:

- all eight RO/SYS/ARC combinations, preserved across every physical extent;
- unchanged contents, including a 20,096-byte multi-extent file;
- ordinary protection skips and `/P` override;
- whole-disk immutability for `/DRY` and invalid trailing options;
- collision `?` help, invalid replacement input, replacement confirmation;
- exclusion of previously generated destinations from later source scans;
- compound DU selection, both operand orders and Build 005 identification.

`tools/test_model4_ren.py --report <new-directory>` runs SUBMIT on disposable
Model 4 DMK images through trs80gp. Both `/P /DRY` and `/P` campaigns passed.
It verifies the completion marker, all eight attribute combinations, every
physical extent, copied-out contents and disappearance of old names. Dry-run
validation compares the complete data-disk image. Allow the directory scans to
finish; lack of immediate screen output alone does not establish a hang.

Both tools retain command transcripts or screen captures, media and JSON
evidence with the REN image hash. They do not alter the user's emulator disks.

## Fault coverage and limits

The assembled-code fixture suites `test_ren_core.py`, `test_ren_workflow.py`,
`test_ren_collision.py`, `test_ren_failure.py` and `test_ren_protection.py` all
passed. They cover retry/skip/abort, Ctrl-C, policy precedence, ledger capacity,
target races, read-only drives, differing extent attributes and failures while
clearing or restoring protection. Real-media campaigns do not inject hardware
faults; those recovery paths are qualified by the fixture tests.

This qualification does not implement automatic resident-to-transient handoff.
That remains a separate command-processor task after TYPE/TYPE.COM.
