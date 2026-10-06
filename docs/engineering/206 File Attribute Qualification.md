# Engineering Specification 206: File Attribute Qualification

## Native set and clear qualification

`test_z80pack_attributes.py` executes Functions 30 and 17 through the actual
BDOS under cpmsim. The native probe sets R/O, SYS and ARC on a disposable file
and checks the returned directory entry. All eight combinations pass, including
clearing bits after all three were set.

The host independently reconstructs the raw directory from the shipped
bettercpm-default geometry and skew table. Only the requested attribute bits
change; filename, extent metadata and allocation remain intact. cpmtools
extracts the unchanged payload for every combination, including R/O and SYS.
This establishes the tested raw-format interoperability rather than assuming
that successful native calls imply correct on-disk metadata.

The harness retains private images, probe source/listing, transcripts, extracted
payloads, raw entries and hashes. Report directories are not overwritten.
The production unified-BDOS regression also passes its attribute, rename,
read-only rejection and record-transfer cases (3,555-byte BDOS).

No OS implementation change is required by this increment. Attribute
qualification remains open for copy/rename on actual media, final read-only
operation checks, and filesystem metadata preservation through installation
and disk operations.

## COPY and MOVE preservation correction

A native probe found that the shared RCP copy engine created the destination
without transferring source attributes. The source remained intact, but the
copy lost R/O, SYS and ARC. The engine now transfers the source FCB's attribute
bits to the destination and calls Function 30 after successful close. Applying
R/O only after copying prevents it from blocking destination writes. A failed
attribute update follows the existing copy-failure path and does not erase the
source through MOVE.

`test_z80pack_copy_attributes.py` tests all eight combinations in both rebuilt
RCP.CPX and transient COPY.COM/MOVE.COM against the qualified z80pack system.
The harness explicitly unloads the old resident RCP, then loads the new module
for the resident profile or leaves it unloaded for the transient profile.
This avoids accidentally testing an older resident command instead of the
updated transient binary.

Raw entries and host extraction prove that COPY preserves attributes, payload
and source metadata. MOVE preserves SYS and ARC when R/O is clear; with R/O
set it leaves the source intact and reports `COPY MADE; SOURCE NOT ERASED`.
Native ZSM4/LINK and host builds produce byte-identical 3,047-byte RCP code,
34 bytes larger than the previous version. Its 3,072-byte resident allocation
is unchanged, with 25 bytes remaining inside that allocation.

Evidence is retained under `build/test-results/z80pack-copy-attributes-cpx-v2`
and `build/test-results/z80pack-copy-attributes-transient`. Final rename,
additional read-only operation checks, and installation/disk metadata
qualification remain separate bounded checks.

## Native rename and read-only operation qualification

`test_z80pack_attribute_operations.py` exercises the released BDOS through
ordinary `CALL 5` from an assembled CP/M transient under cpmsim. The fixtures
cover all eight R/O, SYS and ARC combinations. Function 23 renames writable
files from ATTR.DAT to NEW.BIN while retaining the attribute bits, extent and
allocation metadata, and exact payload. Read-only rename and delete requests
return failure and leave the complete data-disk image unchanged.

Functions 21, 34 and 40 attempt sequential, random and random zero-fill writes
to read-only files. The expected `File R/O` diagnostic and warm restart occur;
the probe's post-call failure marker must not execute. Whole-image comparisons
prove that neither payload nor filesystem metadata changes. Tests run with
both R/O alone and all three attributes set.

The report retains the native probe source, listing, binary, per-case media,
transcripts, raw entries and disk hashes under
`build/test-results/z80pack-attribute-operations`. These are native BDOS
operation checks, not a new claim about every command frontend. No OS source
change is needed. Installation/disk-operation metadata preservation and
applicable Model 4 media qualification remain open.

## z80pack disk-source installation metadata preservation

`test_z80pack_sysgen_attributes.py` seeds eight payload files and sets each
R/O, SYS and ARC combination through native Function 30. Raw directory
inspection confirms those combinations before `SYSGEN A: B:` installs from
the bootable source onto the populated data disk.

Installation must replace the reserved system area while leaving every byte of
the filesystem area unchanged, including directory attributes and allocation
metadata. All eight payloads are extracted with cpmtools after installation
and compared exactly. The installed disk must cold-boot to the prompt.
The test retains before/installed images, working media, native probe
source/listing/binary, transcripts, extracted payloads, geometry manifest and
hashes under `build/test-results/z80pack-sysgen-attributes-disk`.

An initial attempt to qualify the file-source path revealed that the selected
z80pack fixture has no SYSTEM.SYS file. SYSGEN refused that request before
confirmation or writes. This was a harness setup error; it is not evidence
against a supplied compatible package. The failed attempt is retained under
`build/test-results/z80pack-sysgen-attributes`. The completed disk-source
increment makes no file-source claim. File-source metadata preservation, DUP
and applicable Model 4 media checks remain open. No OS source change is needed.
