# Shared resident COPY/MOVE selection

Resident COPY and MOVE share one selector driver and one record-copy engine in
RCP.CPX. The MOVE flag adds source erasure after successful destination close
and attribute application. No source is erased after a failed copy. A source
erase failure reports `COPY MADE; SOURCE NOT ERASED`.

## Operand contract

- Source: one or many DUs/files using the common DU, bounded-filespec and
  attribute-expression parsers.
- Destination: exactly one resolved DU. Set notation is accepted only when its
  bitmap contains one DU. A DU-only target preserves each source filename.
- An exact target filename requires exactly one selected source file.
- Destination wildcard substitution and attribute assignments remain transient
  COPY features. Resident COPY retains trailing `/O`; MOVE does not overwrite.
- Destination-first COPY uses `destination=source`; historical MOVE uses
  `destination:=source`. Source-first syntax works for both.

Preflight covers the full source set before any destination changes. Reject
multiple sources with the same generated destination, destinations overlapping
selected sources, protected existing targets and read-only MOVE sources.
Repeated selector terms are deduplicated. Empty source DUs contribute no files;
an entirely empty selection reports `NO FILE`. System files are eligible unless
excluded by the source predicate. Caller drive/user are restored.

Execution stops on an unexpected copy/close/attribute/delete failure. Earlier
successful operations are not rolled back. Existing per-file cleanup and MOVE
source-deletion ordering are retained.

## Implementation and memory

`src/cpx/copy-select.inc` is included once in the resident RCP expansion. It
uses REN's lexical directory scanner, fixed scratch workspace, shared selector
and predicate evaluator. Collision checks rescan other selected DUs instead of
allocating an unbounded source list. COPY leaves originals intact; MOVE erases
only the completed original, so lexical progress remains valid.

The replaced operand parser and wildcard driver are omitted from the resident
image. Legacy transient expansion remains unchanged. BIOS, BDOS, protected
state and CPX descriptors are unchanged.

RCP Build 003 is 6,856 bytes, 51 bytes more than Build 002. Rounded allocation
remains 6,912 bytes. Its 744 relocations fit the existing 1,536-byte carrier
header. Native and cross builds produce identical code.

## Qualification

`tools/test_resident_copy_move_select.py` covers 24 public-command cases on
z80pack and Model 4. It independently checks final directory names, source
retention/deletion, RO/SYS/ARC preservation and payloads including multi-extent
files. Rejected z80pack operations leave their media unchanged. Cases include
multiple source DUs, a deduplicated single-DU target, multi-DU target rejection,
invalid patterns, duplicate names, later-source collisions, self-copy,
read-only protection, explicit replacement, destination-first MOVE, and newly
created targets which match the original selector. An initially empty destination DU is excluded from
execution rescans; an exact target performs the single preflight operation once.

The shared relocated-selector checks, utility identity/dispatch checks and REN
regression provide coverage for routines reused by the new driver.
