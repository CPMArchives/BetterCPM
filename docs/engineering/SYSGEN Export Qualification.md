# SYSGEN named package export — Build 004

## Implemented contract

SYSGEN now exports the canonical installed 160-record system image and accepts
exact 8.3 package filenames for both export and installation. The default
source-only form saves SYSTEM.SYS in the caller DU:

```
SYSGEN A:
SYSGEN A: B:BASE090.SYS
SYSGEN B:BASE090.SYS C:
```

The existing 128-byte BCSY header/schema is reused, with header source binding
from the saved resident image. Payload bytes are preserved, including saved
configuration; this is not a snapshot of unsaved live state or ordinary files.
It is not a hardware-independent boot image or a MyZ80 boot-file generator.

Publication and recovery are normative in specification section 32: preserve
pre-existing SYSGEN.$$$/SYSGEN.BAK, confirm ordinary-file replacement, protect
RO/SYS output, verify temporary and final contents, and retain remaining files
after failed rename/final verification. No automatic rollback of an uncertain
multi-extent rename is attempted. Recoverable pre-publication failures attempt
temporary-file cleanup and explicitly report failed deletion. Existing disk
installation confirmations and record-zero-last verification remain in place.

## Size and source ownership

Final SYSGEN Build 004 is **5,518 bytes**, SHA-256
`a2e95af631cb218c9afa0576598fd92ef8ac461b714376b3600caa5d937efa79`.
ZSM4/LINK and cross assembly are byte-identical. The new private helpers are
`sysgen-parse.inc` and `sysgen-export.inc`, expanded by both build paths.

The existing 4000h–8FFFh payload workspace requires 36K TPA. A pre-init boundary
guard now enforces it; standalone /VER remains pure. The addition is transient,
with no new BIOS/BDOS/RCP allocation and no change to the unloaded 53K target.

## Focused emitted-code checks

- 32 valid/invalid counted-tail cases: canonical/named input, named/default
  export, exact drive limits, no DU/wildcards/extra operands, full validation
  before either source loader, and standalone/invalid-combined /VER.
- 24 export cases: new/default output, replacement/decline, recovery-name
  collisions, RO/SYS protection, source/create/write/close/verify failures,
  incomplete-temp deletion failure, rename failures, partial rename effects,
  final verification failure, retained backup, Ctrl-C, invalid descriptor,
  out-of-range saved pointer and geometry mismatch.
- TPA guard boundary tests and all 166 shared utility identity/purity checks.
- Existing BIOS-vector regression checks pass after adding RR E support to
  the bounded instruction runner; production BIOS is unchanged.

Tests execute assembled SYSGEN instructions with controlled file/BIOS results.
They do not claim atomicity for real disk errors or power loss.

## cpmsim round trip

`test_z80pack_sysgen_export.py` uses disposable copies derived from the qualified
Build 011 System Disk with the current SYSGEN installed explicitly. A nonempty
saved VER /BANNER startup record is retained while avoiding SUBMIT filesystem
writes that would obscure the source-preservation assertion. This is functional
utility qualification, not a fresh 0.90 distribution qualification.

Passed: exact named export, confirmed replacement and refusal, default export
in caller drive B, no residual recovery names on success, exact 161-record
length/header/payload, saved startup bytes, named reinstall confirmation and
refusal, installation verification, source preservation, target filesystem
preservation, and restored-system cold boot. The known command filesystem is
supplied separately before cold boot, after the preservation comparison;
SYSGEN does not install distribution files.

## Model 4 round trip

`test_model4_sysgen_export.py` boots current generated core/RCP and exports a
named package using private source/output DMKs. Host extraction independently
checks all 160 payload records, exact header/length, unchanged source, unchanged
output protected area, and preservation of existing output files.

`test_sysgen_install.py --package .../BASE090.SYS --package-name BASE090.SYS`
then installs that exported package onto a private populated compatible target,
checks byte preservation of its filesystem, and cold-boots it successfully.
The installation fixture now waits for confirmation/completion screen text and
allows warm reconstruction to finish rather than typing into an incomplete
reboot. Earlier unsynchronized attempts are not passing evidence.

## Remaining release work

Final fresh distribution qualification and the new conformance-suite campaign
remain part of system-wide validation. The broader historical cross-format,
error and platform matrices are not all repeated by these focused tests.
Use [installation qualification](SYSGEN%20Conformance%20Qualification.md) for
retained installation evidence and the current specification for authority.
