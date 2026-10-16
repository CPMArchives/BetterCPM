# BetterCP/M SYSGEN.COM Engineering Specification
**BetterCP/M 1.0**
**Utility:** `SYSGEN.COM`
**Status:** Consolidated engineering specification of the implemented utility and qualified 1.0 behavior

This specification consolidates the current `SYSGEN.COM` implementation and its qualification behavior. It documents the existing interactive and command-line installation paths, `SYSTEM.SYS` package installation, destination validation, system-area protection, write ordering, verification, and interruption behavior.

SYSGEN installs BetterCP/M into the reserved system area of compatible media. It does not format disks. Installation preserves the destination filesystem;
export writes a package file through ordinary filesystem services.

---

## 1. Purpose

`SYSGEN.COM` installs a BetterCP/M protected-system image onto a configured destination disk.

The system image may come from either:

1. a bootable BetterCP/M source disk; or
2. a `SYSTEM.SYS` package.

Installation operates directly on reserved system records through the BIOS.
Export reads those records and writes a package through ordinary CP/M file I/O.

Its installation contract is:

> **Replace the destination's BetterCP/M system area while preserving all data outside that reserved area.**

SYSGEN is not:

- a disk formatter;
- a general disk copier;
- a filesystem utility;
- a disk-format converter;
- a compiler/build-product composer (that remains SYSBUILD’s role).

`DUP` and `CONFIG` establish suitable media and drive bindings. `SYSBUILD` produces the canonical `SYSTEM.SYS` package. SYSGEN installs the system onto already compatible media and can export installed system records to a package.

---

# COMMAND INTERFACE

## 2. Supported invocation

BetterCP/M 1.0 supports:

```text
SYSGEN
SYSGEN source: destination:
SYSGEN [drive:]package destination:
SYSGEN source: [drive:]package
SYSGEN source:
SYSGEN /VER
```

Examples:

```text
SYSGEN
SYSGEN A: B:
SYSGEN C: D:
SYSGEN SYSTEM.SYS B:
SYSGEN C:SYSTEM.SYS B:
SYSGEN /VER
```

These forms provide installation and export:

| Form | Source | Destination |
|---|---|---|
| `SYSGEN` | bootable system on `A:` | prompted `B:`–`D:` |
| `SYSGEN A: B:` | explicit bootable source drive | explicit destination |
| `SYSGEN SYSTEM.SYS B:` | exact package file | explicit installation destination |
| `SYSGEN A: B:BASE090.SYS` | installed system records | package in B: current user |
| `SYSGEN A:` | installed system records | SYSTEM.SYS in caller’s current DU |

The command-line paths invoke the same installation, validation, confirmation, writing, and verification machinery as the interactive path.

---

## 3. Interactive mode

Running:

```text
SYSGEN
```

uses logical `A:` as the source system.

SYSGEN prompts:

```text
Destination drive [ B - D ], or BREAK (^C) to exit:
```

The destination is limited to:

```text
B:
C:
D:
```

`^C` exits without modifying any media.

The source is not prompted in this mode; `A:` is the established interactive source.

---

## 4. Explicit drive-source mode

Syntax:

```text
SYSGEN source: destination:
```

Examples:

```text
SYSGEN A: B:
SYSGEN C: D:
```

The source may be:

```text
A:
B:
C:
D:
```

The destination may be:

```text
B:
C:
D:
```

The source and destination logical drives may not resolve to the same physical drive.

This mode obtains the system image directly from the source disk's reserved system area.

---

## 5. `SYSTEM.SYS` package mode

Syntax:

```text
SYSGEN [drive:]package destination:
```

Examples:

```text
SYSGEN SYSTEM.SYS B:
SYSGEN C:SYSTEM.SYS B:
```

Package filenames are exact CP/M 8.3 names with an optional A:–D: drive
prefix. SYSTEM.SYS remains the default export name; arbitrary names permit a
library of system-track snapshots. No wildcards, compound selectors, DU/user
syntax, paths, or user switching are supported. Unqualified files use the
caller’s current drive and user. The parser validates the complete counted tail
and builds private FCBs rather than trusting the CCP-prepared FCBs.

The destination is:

```text
B:
C:
D:
```

Package mode does not require the source file's drive to differ physically from the destination, because the complete package is read into transient memory before destination writing begins.

---

## 6. Invalid command lines

Malformed or unsupported invocations report the usage form and return to the CCP.

The implemented usage is:

```text
Usage: SYSGEN | A: B: | package B: | A: package | /VER
```

This message illustrates the accepted forms; the drive letters shown are examples rather than a statement that the source must specifically be `A:`.

Examples of invalid syntax include:

```text
SYSGEN A: A:
SYSGEN SYSTEM.SYS
SYSGEN E: B:
SYSGEN A: E:
SYSGEN B7:OTHER.SYS B:
```

Some syntactically valid commands may subsequently fail because of physical-drive or geometry restrictions.

---

## 7. `/VER`

`/VER` uses the common BetterCP/M standalone utility-version mechanism.

```text
SYSGEN /VER
```

prints:

```text
BetterCP/M SYSGEN 1.0 (Build 004)
```

and returns directly to the CCP without disk installation activity. The version
and build number are owned by the common utility-version metadata, not by
SYSGEN’s operational code, and may advance in subsequent builds.

---

# SYSTEM IMAGE

## 8. Canonical system size

The BetterCP/M 1.0 protected-system payload installed by SYSGEN is:

```text
160 CP/M logical records
```

at 128 bytes per record.

Thus the installed package occupies:

```text
20,480 bytes
```

of reserved system space.

This is the canonical BetterCP/M 1.0 system payload size.

The input `SYSTEM.SYS` file contains one additional 128-byte header record:

```text
Installed payload: 160 records, 20,480 bytes
SYSTEM.SYS file:   161 records, 20,608 bytes
                   1 header + 160 payload records
```

The header is input metadata and is not installed as a destination system record.

---

## 9. Destination reserved-area requirement

The destination must provide at least:

```text
160 reserved logical records
```

before the filesystem allocation area begins.

SYSGEN calculates the destination capacity from its installed binding:

```text
reserved records = SPT × OFF
```

using the binding's CP/M logical-track units.

If fewer than 160 records are available:

```text
Destination reserved system area is too small (160 records required).
```

The operation is refused before confirmation and before any destination write.

A destination may reserve **more** than 160 records.

SYSGEN writes only the canonical 160-record package.

Any additional reserved records beyond the installed package are left unchanged.

---

## 10. Disk-source acquisition

When sourcing from a bootable disk, SYSGEN first obtains and validates the source binding.

The source reserved area must contain at least 160 logical records.

SYSGEN buffers exactly the canonical 160-record system image.

For real-floppy reliability, the implemented read order is:

1. records 1 through 159;
2. record 0 last.

This gives the drive a normal sector transfer before returning to the boot record.

All source records are successfully buffered before the first destination system-area write occurs.

A source read failure aborts installation.

---

## 11. Package-source acquisition

`SYSTEM.SYS` is a versioned BetterCP/M protected-system package.

Before any destination write, SYSGEN validates `SYSTEM.SYS` sufficiently for
installation. It reads the fixed header record, checks the expected BetterCP/M
package magic/version fields and advertised payload size, obtains the embedded
source binding, reads exactly 160 payload records, and requires end-of-file
immediately thereafter. It subsequently validates destination geometry and
whether the buffered package can be patched to represent the destination.

`SYSTEM.SYS` 1.0 does not contain or require a whole-payload checksum in this
path. Successful package validation establishes structural consistency and
complete readability of the expected package, not cryptographic or exhaustive
corruption detection.

A package failing these checks is rejected:

```text
The system package is invalid or cannot represent the destination.
```

No destination installation begins.

---

# DESTINATION VALIDATION

## 12. Destination drive protection

Physical drive 0 is protected as the running system disk.

SYSGEN refuses any destination logical drive whose binding resolves to physical drive 0:

```text
Physical drive 0 is protected as the running system disk.
```

The protection is based on physical drive identity, not merely logical drive letter.

This safeguard applies to all SYSGEN invocation modes.

---

## 13. Source/destination alias protection

In disk-source mode, source and destination must resolve to different physical drives.

If they alias:

```text
Source and destination refer to the same physical drive.
```

Installation is refused.

This check uses physical bindings, so two different logical letters do not evade it.

Package mode does not require this restriction because the package has already been completely buffered before destination writing.

---

## 14. Undefined or unavailable drives

If the source or destination binding cannot be obtained through the BetterCP/M disk API:

```text
The selected drive is undefined or unavailable.
```

The operation terminates without destination writes.

---

## 15. Bootstrap geometry normalization

BetterCP/M distinguishes between ordinary runtime bindings and the representation required by the bootstrap package.

In particular, a double-sided runtime binding may represent:

```text
one CP/M logical track = one physical surface
```

while the bootstrap representation uses:

```text
one CP/M logical track = one physical cylinder
```

Before comparing package/source geometry with the target, SYSGEN normalizes the source/bootstrap description to the equivalent ordinary surface-track representation.

For the established double-sided case, normalization includes:

- converting the bootstrap cylinder-based topology to surface-track topology;
- halving SPT from records per cylinder to records per surface;
- doubling OFF from reserved cylinders to reserved surface tracks.

This normalization is transient.

It does not modify:

- the source disk;
- the source package on disk;
- persistent source configuration.

---

## 16. Destination geometry compatibility

SYSGEN does not require the destination disk to have an identical complete filesystem definition to the source.

It compares the physical/bootstrap geometry needed to install and boot the package.

The current implementation compares the relevant normalized format geometry, IDs, and size-map information while permitting destination filesystem parameters to differ where they do not affect bootstrap compatibility.

This permits installation onto a larger compatible filesystem format, provided:

- bootstrap geometry is compatible; and
- the destination reserves at least 160 system records.

Cross-format installation of this kind is qualified.

If bootstrap geometry is incompatible:

```text
Destination bootstrap geometry is not supported by this system package.
```

The operation is refused before confirmation and before any write.

---

# DATA-ONLY MEDIA

## 17. Data-only destination behavior

A disk containing data files is not automatically a "data-only format."

The determining issue is whether its installed binding provides a compatible reserved system area.

### 17.1 Boot-compatible populated disk

If the destination:

- has compatible bootstrap geometry; and
- reserves at least 160 system records,

SYSGEN may install BetterCP/M even if the disk already contains files.

Only the reserved system area is replaced.

The filesystem area and its files are preserved.

This behavior is qualified on both Model 4 and z80pack installation tests.

### 17.2 True data-only format

If the destination format has no compatible BetterCP/M bootstrap/system geometry, SYSGEN refuses it:

```text
Destination bootstrap geometry is not supported by this system package.
```

The refusal occurs:

1. before the destructive confirmation;
2. before any destination write.

The qualified z80pack data-only refusal case verifies that the entire target remains byte-for-byte unchanged.

### 17.3 Insufficient reserved area

If the disk has compatible geometry but fewer than 160 reserved records:

```text
Destination reserved system area is too small (160 records required).
```

The target is rejected before any write.

Thus the rule is:

```text
compatible bootstrap area >= 160 records
        -> SYSGEN may install

no compatible bootstrap geometry
        -> refuse

compatible but reserved area < 160 records
        -> refuse
```

---

# DESTINATION PACKAGE PATCHING

## 18. Destination-specific patching

SYSGEN does not simply copy the source 160 records verbatim.

Before writing, it patches the buffered system package so that the installed system reflects the destination.

The patched information includes:

- physical drive-zero definition;
- installed `A:` drive binding.

SYSGEN obtains the appropriate live destination definitions through the public BetterCP/M disk API.

---

## 19. Runtime versus bootstrap binding

The disk-facing installed binding uses the normal destination representation.

Where required, SYSGEN constructs a separate bootstrap representation for the package.

For an established double-sided surface-based runtime binding, the bootstrap form is converted to the equivalent cylinder-track representation.

This includes the inverse adjustments of the compatibility normalization described above.

The package written to disk must therefore boot using the correct destination physical geometry while subsequently exposing the appropriate BetterCP/M runtime binding.

---

## 20. Package representability failure

If the current system package cannot be patched to represent the destination safely:

```text
The system package is invalid or cannot represent the destination.
```

No destination installation begins.

---

# CONFIRMATION

## 21. Installation summary

After all compatibility checks pass, SYSGEN reports the selected target, including its logical and physical drive identity, and the number of reserved system records to be installed.

It then warns:

```text
The destination system area will be replaced.
Files outside the reserved system tracks will be preserved.
Proceed (Y/N)?
```

Only `Y` begins installation.

Any other response returns without modifying the destination.

The same confirmation applies to:

- interactive mode;
- explicit drive-source mode;
- `SYSTEM.SYS` mode.

Command-line invocation selects source and destination noninteractively, but
does not make installation unattended. Every destructive installation form
stops at `Proceed (Y/N)?` and requires `Y` before any destination system record
is written. There is no BetterCP/M 1.0 confirmation-bypass option.

---

# INSTALLATION

## 22. Filesystem isolation

SYSGEN performs destination writes through raw BIOS logical-record operations.

It does not open, create, rename, erase, or modify destination filesystem files.

The installation range is confined to the canonical 160 protected-system records.

The file/allocation area is outside the SYSGEN write range.

---

## 23. Installation ordering

SYSGEN deliberately writes:

```text
records 1 through 159 first
record 0 last
```

Record 0 contains the first-stage boot material.

This ordering reduces the likelihood that a partially installed disk appears to have a new boot sector before the remainder of the system package has been successfully installed.

Record 0 is installed only after records 1–159 have each been written and verified successfully.

---

## 24. Record-level verification

For every destination record, SYSGEN:

1. writes the 128-byte record;
2. immediately rereads it;
3. compares all 128 bytes with the buffered source image.

A read-back mismatch is a failure.

Successful installation therefore requires byte-for-byte verification of every installed system record.

---

## 25. Completion

Only after all 160 records have been written and verified does SYSGEN reset logged-drive state and report:

```text
System installed and verified. The destination is bootable.
```

A successful installation qualifies the target as containing the installed BetterCP/M system package for the compatible geometry used.

---

# INTERRUPTION AND FAILURE

## 26. BREAK / `^C`

During installation SYSGEN polls for BREAK / `^C` at bounded points between record operations.

It does not attempt to cancel a BIOS disk transfer already in progress.

At the interactive destination prompt, `^C` exits cleanly before installation.

---

## 27. Interrupted installation

If installation is interrupted after writing has begun:

```text
Installation stopped. The destination may not boot.
Its file area was not changed.
```

SYSGEN does not claim successful installation.

The reserved area may contain a partial system.

The filesystem area remains outside the SYSGEN write range.

---

## 28. Destination I/O failure

On a write or read-back failure, SYSGEN reports the failing logical record and status, followed by:

```text
The destination may not boot. Its file area was not changed.
```

No attempt is made to represent a partial installation as successful.

Because the system records themselves are the object being replaced, SYSGEN does not promise transactional rollback of a partially written destination system area.

Its primary safety properties are instead:

- validate compatibility before writing;
- buffer the source before writing;
- write record 0 last;
- verify every record immediately;
- never touch the filesystem area.

---

## 29. Source read failure

In drive-source mode, if any required source system record cannot be read, installation is aborted before destination system records are written.

The diagnostic identifies the source logical record and status.

---

# BACKEND AND FORMAT BOUNDARY

## 30. SYSGEN does not format disks

SYSGEN requires the destination medium to already have an installed binding and compatible physical/bootstrap structure.

It does not:

- low-level format the disk;
- rewrite sector IDs;
- change density;
- alter physical geometry;
- create a reserved area where none exists.

A disk needing such preparation must first be configured/formatted using the appropriate disk utilities.

---

## 31. Format compatibility versus filesystem identity

SYSGEN's concern is whether the destination can hold and boot the protected BetterCP/M package.

It does not require source and destination to have identical filesystem capacities.

A destination may have:

- a larger allocation area;
- different filesystem capacity;
- more reserved records than the canonical package;

provided the bootstrap geometry is compatible.

The destination's existing filesystem definition remains otherwise intact.

---

# `SYSTEM.SYS` RESPONSIBILITY

## 32. Package production and disk export

SYSBUILD composes a new package from build products. SYSGEN instead snapshots
an installed disk’s canonical 160 protected records, preserving payload bytes,
saved startup command, IOBYTE defaults and saved drive configuration. It does
not capture unsaved live changes, whole-disk data or arbitrary track ranges.

```text
SYSGEN A:                     ; default SYSTEM.SYS in caller DU
SYSGEN A: B:BASE090.SYS        ; named snapshot
SYSGEN B:BASE090.SYS C:        ; install named snapshot
```

Source drives are A:–D:. Explicit package drives are A:–D:; an unqualified
package uses the caller drive. Source and output may share a physical disk
because all system records are buffered before any output file is created.
Only filesystem output changes; no protected source record is written.

Export emits the existing version-1 128-byte BCSY header plus the unmodified
20,480-byte payload: exactly 161 records, 20,608 bytes. Header fields use the
existing package magic/version/count/base contract. The source binding comes
from the saved A: binding inside the installed resident carrier, not unsaved
live settings. Validate descriptor version, binding bounds, reserved capacity
and normalized geometry against the binding used for reads before file output.
Structural checks and byte comparison do not establish a whole-payload checksum
or prove that an arbitrary source image is semantically sound.

Publication uses reserved names SYSGEN.$$$ and SYSGEN.BAK in the output DU.
These two names cannot be export targets. If either exists or cannot be checked,
stop and preserve it. Other exact filenames are permitted, including names
without an extension. A new final file needs no destructive confirmation.
Existing RO or SYS packages are not replaced. For an ordinary existing file:

```text
Replace existing package (Y/N)?
```

Only Y permits replacement. Write header/payload into SYSGEN.$$$, close it,
reopen and compare every byte, require immediate EOF, and check close status.
Rename the old final to SYSGEN.BAK if replacing, then rename the verified temp
to the requested final name. Reopen and byte-verify the final before reporting:

```text
Package exported and verified.
```

Delete the backup only after successful final verification. If that deletion
fails, report successful export and that SYSGEN.BAK remains.

On recoverable pre-publication write/close/verification failure or Ctrl-C, close
and attempt to delete the incomplete temporary file. If deletion fails, report
the retained incomplete SYSGEN.$$$. Never remove a pre-existing recovery file.
A read failure before output leaves output files untouched.

On any rename or final-verification failure, stop and retain remaining files;
report publication failure and direct inspection of the chosen output,
SYSGEN.$$$ and SYSGEN.BAK. Do not attempt automatic rollback after a failed
rename: multi-extent directory updates need not be atomic. Do not claim success
or power-loss safety. A nonreturning BDOS/media abort may likewise leave a
recovery file. Preserve/recover these files before retrying.

SYSGEN needs at least 36K TPA for its existing 4000h–8FFFh payload buffer.
A pre-initialization guard rejects a lower boundary; /VER remains pure.
Ctrl-C is checked between output records; in-flight BIOS/file calls are not
asynchronously cancelled.

---

## 33. No verify-only mode

BetterCP/M 1.0 does not define separate forms such as:

```text
SYSGEN /VERIFY B:
SYSGEN /CHECK SYSTEM.SYS
```

Package validation is performed automatically when a package is used.

Destination write verification is performed automatically during installation.

A separate diagnostic mode is unnecessary for the 1.0 SYSGEN contract.

---

# QUALIFICATION

## 34. Model 4 installation qualification

Current qualification demonstrates installation onto a populated compatible disk and verifies that:

- the system area changes;
- the filesystem area remains unchanged;
- existing files remain readable;
- the resulting disk cold-boots successfully.

Both disk-source and package-source paths are exercised.

---

## 35. Cross-format qualification

Qualification also demonstrates installation onto a larger compatible destination format using both:

```text
SYSGEN A: B:
```

and:

```text
SYSGEN SYSTEM.SYS B:
```

The target:

- preserves data outside its system area;
- receives the new protected system;
- cold-boots successfully.

Thus complete source/destination filesystem identity is not required.

---

## 36. z80pack installation qualification

The z80pack qualification installs BetterCP/M onto a populated destination using:

```text
SYSGEN A: B:
```

and verifies:

- system-area replacement;
- byte preservation of everything beyond the reserved area;
- preservation and recovery of an existing file;
- successful cold boot from the installed target.

---

## 37. Data-only refusal qualification

The z80pack refusal case uses a genuine data-only destination.

SYSGEN reports incompatible bootstrap geometry before displaying:

```text
Proceed (Y/N)?
```

and the qualification verifies that the target remains byte-for-byte unchanged.

This establishes the no-write guarantee for this qualified preflight refusal path.

---

# 1.0 COMMAND SUMMARY

## 38. Supported forms

```text
SYSGEN
SYSGEN source: destination:
SYSGEN [drive:]package destination:
SYSGEN source: [drive:]package
SYSGEN source:
SYSGEN /VER
```

Examples:

```text
SYSGEN
SYSGEN A: B:
SYSGEN C: D:
SYSGEN SYSTEM.SYS B:
SYSGEN C:SYSTEM.SYS B:
SYSGEN /VER
```

---

# 1.0 CORE CONTRACT

## 39. Source contract

SYSGEN accepts:

- interactive `A:` system-disk source;
- explicit A-D system-disk source;
- exact `[drive:]package` file source;
- disk-to-package export, defaulting to SYSTEM.SYS for a source-only invocation.

All required source data is validated and buffered before destination installation begins.

---

## 40. Destination contract

The destination:

- must be logical B-D;
- must not resolve to protected physical drive 0;
- must have a valid installed binding;
- must have compatible bootstrap geometry;
- must reserve at least 160 logical records;
- may have a larger filesystem or larger reserved area.

A true data-only format without compatible bootstrap geometry is refused before any write.

---

## 41. Preservation contract

SYSGEN writes exactly the BetterCP/M system package area.

It preserves:

- all filesystem records outside the reserved system area;
- any excess reserved records beyond the canonical 160-record package.

It does not alter destination filesystem metadata through BDOS file operations.

---

## 42. Installation contract

SYSGEN:

- patches the buffered package for the destination;
- writes records 1–159 first;
- writes record 0 last;
- rereads every written record;
- compares every byte;
- reports success only after complete verification.

---

## 43. Failure contract

If installation fails or is interrupted after writes begin:

- the destination may not boot;
- the filesystem area remains untouched by SYSGEN;
- successful completion is not reported.

If preflight validation fails, no destination system record is written.

---

## 44. Scope exclusions

BetterCP/M 1.0 SYSGEN does not:

- format disks;
- create or change disk geometry;
- install onto incompatible data-only formats;
- extract arbitrary track ranges or filesystem contents;
- provide a verify-only mode;
- provide an unattended confirmation-bypass switch;
- copy filesystem files.

---

## 45. Final 1.0 design status

Build 004 adds named package input and installed-system export under section 32.
Release qualification remains separate from focused export/installation tests.

The implemented command interface already provides direct source/destination selection:

```text
SYSGEN A: B:
SYSGEN SYSTEM.SYS B:
```

alongside the traditional interactive mode.

The 1.0 engineering work includes the bounded export addition and qualification. The existing command-line access, cross-format compatibility rules, data-only refusal, package validation, filesystem preservation, destination patching, record-zero-last installation order, and byte-for-byte read-back verification are the normative SYSGEN behavior.

## Consolidated package and preservation boundary

The 161-record package file is an input/output container; only its 160 payload
records enter the destination system area. Neither the header nor any ordinary
source file is installed. Preserve both the filesystem and reserved records
beyond payload record 159. Mandatory confirmation applies equally to disk and
package sources after preflight; `/VER` performs no installation.

Writing record zero last is an ordering safeguard, not a power-loss transaction:
an existing boot record can remain on a failed target, and the partially replaced
system area is not rolled back. Report the failure and require reinstallation.
See [conformance qualification](SYSGEN%20Conformance%20Qualification.md) for
command parsing, populated-target preservation, cold boot and data-only refusal
evidence; focused qualification does not declare a final release.

Current Build 004 export, native byte parity and focused platform evidence are
recorded in [export qualification](SYSGEN%20Export%20Qualification.md).

## Supporting references

- [Native installation qualification](204%20Native%20Installation%20Qualification.md)
- [SYSGEN implementation](../../src/utilities/sysgen.mac)
- [Utility versioning](../../specifications/UTILITY-VERSIONING.md)
- [CONFIG specification](CONFIG%20Specification.md)
- [DUP specification](DUP%20Specification.md)
