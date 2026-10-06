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
