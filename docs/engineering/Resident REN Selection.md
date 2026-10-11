# Resident REN selection contract

The shared file selector describes source locations and files. Each command
separately constrains what its destination means:

| Command | Source | Destination |
| --- | --- | --- |
| REN | One or many DUs/files | Location-free filename template; applied in each source DU |
| COPY, MOVE | One or many DUs/files | Exactly one resolved DU |

Resident REN implements the settled core subset. It does not change COPY or MOVE.

## Interface

`REN source template` accepts source-first ordering; `REN template=source`
retains destination-first CP/M ordering. An underscore
separator is accepted when no equals sign appears. With an equals separator,
underscores in names remain literal characters.

The source uses the common selector implementation: compound DU selections,
bounded filename wildcards and attribute expressions. The caller DU is captured
once for inherited locations. RO and SYS files are skipped, even when explicitly selected. Protection is
checked across every physical extent, independently of the selection predicate.

The template has no location qualifier, even if that qualifier names the same
DU as a source. Literal positions replace source positions; question marks copy
source positions; terminal star runs copy the rest of the field. Name and
extension are independent. Generated names must be nonempty and contain no
internal padding spaces. Empty extensions are allowed.

## Preflight and execution

Validate the full syntax and selected drive domain before the first rename.
Process sources in lexical order within each DU. Reject invalid concrete names
and stop on existing targets, including other selected sources. Never overwrite
an existing file. A duplicate generated target produces FILE EXISTS when reached;
earlier successful renames remain. No batch collision preflight or rollback is
promised. Identity mappings are no-ops. RO/SYS files are skipped; drive read-only
state still prevents changes to otherwise eligible files.

Execution uses BDOS rename and preserves contents and attributes. Restore the
caller DU on every return. Unexpected execution failures stop processing.

## Implementation

`src/cpx/ren-select.inc` replaces the legacy resident REN body during RCP source
expansion. It reuses the shared selector, bitmap iterator and attribute filter.
Transient source expansion retains its existing body; this is not an
implementation of the future extended REN.COM contract.

Fixed scratch storage and lexical directory rescans avoid allocating a list of
all selected files. Physical extents are deduplicated by name. Positional substitution is idempotent:
a renamed target that still matches the source pattern maps to itself on a
subsequent rescan. It therefore cannot be renamed repeatedly.

RCP Build 006 occupies 6,880 bytes, with the existing 6,912-byte rounded
allocation. Its carrier uses 744 relocation entries within the existing header
limit. No BDOS, BIOS, protected-data or CPX descriptor changes are required.

## Qualification

`tools/test_resident_ren_mapping.py` checks positional substitution, invalid
concrete names, the fixed-point property, and protection merged across all
physical extents (including a protected later extent). `tools/test_resident_ren_select.py`
checks 22 public-command cases on cpmsim and Model 4, including both syntax forms, compound/inherited DUs, attribute selection,
multi-extent files, identity mappings, collisions, incremental completion,
RO/SYS skips and invalid locations. Final directory names, attributes and file
payloads are inspected independently. Rejected syntax and no-op commands leave
the cpmsim image unchanged.

Native ZSM4/LINK and cross assembly produce 6,880 byte-identical bytes.
The 124 utility identity/dispatch checks and positional mapping checks pass.
