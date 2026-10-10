# Resident REN selection contract

The shared file selector describes source locations and files. Each command
separately constrains what its destination means:

| Command | Source | Destination |
| --- | --- | --- |
| REN | One or many DUs/files | Location-free filename template; applied in each source DU |
| COPY, MOVE | One or many DUs/files | Exactly one resolved DU |

This increment implements resident REN. It does not change COPY or MOVE.

## Interface

`REN template=source` retains destination-first CP/M ordering. An underscore
separator is accepted when no equals sign appears. With an equals separator,
underscores in names remain literal characters.

The source uses the common selector implementation: compound DU selections,
bounded filename wildcards and attribute expressions. The caller DU is captured
once for inherited locations. System files are eligible by default.

The template has no location qualifier, even if that qualifier names the same
DU as a source. Literal positions replace source positions; question marks copy
source positions; terminal star runs copy the rest of the field. Name and
extension are independent. Generated names must be nonempty and contain no
internal padding spaces. Empty extensions are allowed.

## Preflight and execution

Validate all selected DUs before the first rename. Reject invalid concrete
names, duplicate generated targets within a DU, existing targets (including
other selected sources), and changes to read-only files or drives. Identical
names in different DUs do not collide. Identity mappings are no-ops.

Execution uses BDOS rename and preserves file contents and attributes. Restore
the caller DU on every return. Unexpected execution failures stop processing;
this is not rollback of previously completed renames.

## Implementation

`src/cpx/ren-select.inc` replaces the legacy resident REN body during RCP source
expansion. It reuses the shared selector, bitmap iterator and attribute filter.
Transient source expansion retains its existing body; this is not an
implementation of the future extended REN.COM contract.

Fixed scratch storage and lexical directory rescans avoid allocating a list of
all selected files. Physical extents are deduplicated by name. Pairwise mapping
checks are performed within each DU. Positional substitution is idempotent:
a renamed target that still matches the source pattern maps to itself on a
subsequent rescan. It therefore cannot be renamed repeatedly.

RCP Build 002 grows from 6,053 to 6,805 bytes. Rounded allocation increases from
6,144 to 6,912 bytes, a 768-byte increase in reclaimable command memory. No BDOS,
BIOS, protected-data or CPX descriptor changes are required. Native and cross
assembly produce identical RCP payloads.

## Qualification

`tools/test_resident_ren_mapping.py` checks positional substitution, invalid
concrete names and the fixed-point property. `tools/test_resident_ren_select.py`
exercises 16 public-command cases on z80pack and Model 4: exact and compound-DU
renames, inherited locations, bounded stars, attributes, multi-extent files,
identity mappings, duplicate targets, later-DU collisions, source overlap,
read-only protection and invalid locations. Final directory names, attributes
and file payloads are checked independently. z80pack also checks unchanged
images after rejected and no-op commands.
