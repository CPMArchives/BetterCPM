# RCP shared file-selector integration

Status: integration started on 2026-10-10. The shared selector is not yet exposed
to resident commands. This work precedes expanded DIR.COM implementation.

## Placement and scope

The current package is RCP.CPX. Include the common selection implementation once
inside that package for its sequential command handlers. Transient utilities
remain self-contained, linking the same source privately. This is an internal
RCP calling convention, not a new cross-package CPX service or BDOS function.

Reuse the [extended DU contract](208%20Extended%20DU%20Syntax.md): a 64-byte map,
four bytes per drive, one bit per user, with a shared iterator. Capture caller
DU once, validate the full operand before mutation, clear results on failure,
and retain a meaningful error position. Include bounded 8.3 wildcard parsing
and the shared attribute predicate grammar. Command-specific operation and
protection policy remains with DIR, ERA, COPY, REN or TYPE.

Scratch/results may be package-owned because commands execute sequentially.
COPY must preserve its source result before parsing the destination. No pointer
into reconstructable CPX memory may survive transient execution or WBOOT.

## Audit measurements

The pre-integration audit measured the current RCP as 3,795 executable bytes,
3,840 allocated bytes, and 425 relocation entries. Appending a single DU engine
and workspace produces 4,442 bytes, a 4,608-byte allocation, and 511 relocations.
Appending DU, operand qualifiers and attribute predicates produces 4,800 bytes,
4,864 allocated bytes, and 544 relocations. These are prototypes, not the final
integrated command implementation or a qualified expanded RCP.

The DU component uses 571 code bytes plus 76 map/workspace bytes. Qualifier
splitting uses 106 bytes; attribute predicate parsing uses 252 bytes. Existing
bounded filespec code is already shared among RCP handlers and must be refactored
for common use rather than duplicated. The current qualifier splitter's failure
position also needs attention when assembling the combined error contract.

A larger shared parser does not by itself implement multi-DU COPY: its frozen
batch/preflight storage and operation contract require separate accounting.
Other modifying commands also need their own protection and preflight contracts.
Parsing acceptance must not silently broaden destructive behavior.

## First increment: carrier capacity

The former host packer limit was a 1,024-byte relocation header, allowing 488
entries. Both appended prototypes exceed that limit. The native loader already
uses declared aligned header size and streams relocation records; no loader or
BDOS change is required for a third header group.

The host builder now permits up to 1,536 header bytes (744 relocation entries).
One- and two-group output remains unchanged, and excess capacity is rejected.
The header is file storage, not extra runtime allocation. Version-1 fields and
ABI remain unchanged; see [Engineering Specification 119](119%20BCPX%20Version%201%20Module%20Format.md).

`tools/test_cpx_large_header.py` builds a private HELLO-derived probe with 489
additional relocated words. It compares every word with the actual loaded
message address on three invocations: initial load, WBOOT reconstruction, and
explicit unload/reload. It also checks packer boundaries at 232/233, 488/489,
744/745. This probe qualifies header handling, not the future selector API.

The probe passed on z80pack and Model 4. Current RCP.CPX and HELLO.CPX rebuilt
byte-for-byte unchanged; the existing carrier-format checks also passed.
Evidence bundle: `/private/tmp/rcp-header-qualification-bundle-20261010`.
All 42 inventoried files passed size/hash verification. Manifest SHA-256:
`2ec5f4c23954caa64e4c9c21753e813b192d73349dd13348b30cbd1d764ef612`.

## Following increments

1. Integrate one shared parser/result/iterator implementation and qualify its
   syntax, relocation and error atomicity.
2. Migrate resident read-only listing behavior first, with command-specific
   options outside the generic selector handled separately.
3. Migrate modifying commands only with their explicit operation contracts,
   accounting for complete preflight and protection semantics.

Measure actual final executable size, rounded allocation, relocation count,
reconstruction and recovered TPA at each increment. BDOS growth remains zero.
