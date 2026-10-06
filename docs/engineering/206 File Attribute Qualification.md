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
