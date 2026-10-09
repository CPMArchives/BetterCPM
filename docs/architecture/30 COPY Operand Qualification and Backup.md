# COPY operand qualification and backup

Accepted design: 2026-10-09. Operand qualifiers, leading global options and
/BACKUP are not yet implemented. Multi-DU sources, trailing /O /S /B /V,
attribute preservation and global mapping preflight already exist.

## Command structure and scope

```text
COPY [global-options] source[source-qualifiers] destination[destination-qualifiers] [global-options]
COPY [global-options] destination[destination-qualifiers]=source[source-qualifiers] [global-options]
```

Free-standing slash options govern the entire command regardless of leading or
trailing placement. Operand-attached brackets define local scope. Whitespace
around `=` is optional. Existing trailing option forms remain valid; no
arbitrary options between operands are introduced by this contract.

Source DU selector brackets and attribute qualifiers are distinct:

```text
COPY /V /BACKUP B[-]:*.COM[$ARC] D0:
```

This selects .COM files across all B: users whose ARC bit is set, copies them to
D0:, verifies them, and clears ARC on both copies after successful completion.
The source can span multiple DUs; the destination resolves to one DU. Existing
inherited-DU forms remain supported. Destination sets are invalid.

## Attribute vocabulary and role

Canonical names are `$RO`, `$RW`, `$SYS`, `$DIR`, `$ARC`. Accept `$R/O` and `$R/W`
as compatibility aliases. Positive bits are RO, SYS and ARC; RW means !RO and
DIR means !SYS.

Source brackets are predicates, with `!` NOT, `+` AND, `,` OR, in that precedence
order. For example `[$ARC+!$SYS]`, `[$RO,$SYS]` and `[!$ARC]`. This is a bounded
attribute grammar, not a general query language.

Destination brackets are a modification list, such as `[$RW,!$ARC]`. They
change the completed destination's attributes; unspecified bits retain source
values. Opposite assignments to one bit, including aliases, are rejected before
writes. Equivalent repeated assignments are idempotent. Destination lists do
not interpret comma as Boolean OR or admit source expression operators.

Destination overrides never permit overwriting an existing read-only file.

## ARC and backup completion

ARC set means changed since the last completed backup. Ordinary COPY preserves
ARC on the destination and leaves the source unchanged. A source predicate only
selects files; it does not clear ARC.

/BACKUP is explicit operation behavior, not an implicit ARC filter. /B retains
its existing noninteractive batch meaning. /BACKUP copies every selected file,
regardless of its initial ARC state, and clears ARC on both copies after copy,
close and any requested verification succeed.

/BACKUP has final precedence over destination ARC qualifiers: a destination
`[$ARC]` is accepted but backup completion clears ARC. Contradictions within the
destination list itself remain invalid.

Completion is per file. Skip, failure or abort retains source ARC. Apply the
final destination attributes first, then clear source ARC while preserving its
other attributes. If metadata completion fails, keep any valid copied data and
report data copied but backup status incomplete. Do not count a completed backup.
Cross-disk metadata updates are not atomic; earlier completed backups are not
rolled back after a later failure.

Automatic ARC setting on later writes is a separate OS decision. This work
must not require BDOS growth or changes to frozen resident architecture.

## Implementation boundaries and qualification

Parse the complete invocation before operations. Filter directory metadata
before attribute bits are masked from filenames and before collection. The
64-file limit and global preflight apply to the filtered source set. Duplicate
destination mappings and overlap with any selected source reject the operation
before writes; /O and /BACKUP cannot override this protection.

No shared DIR attribute-expression parser exists yet. A shared internal component
can compile source predicates into an eight-state RO/SYS/ARC truth mask and
destination lists into disjoint set/clear masks. This is an implementation
proposal to measure, not a published ABI. Keep runtime work in transient COPY
and reusable parser components; no new resident service is required.

Qualify both operand orders, nested DU selector versus qualifier boundaries,
aliases, precedence over all eight attribute states, malformed input, destination
contradictions, backup precedence, source/destination metadata failures,
read-only protection, caller DU/DMA restoration and cancellation. Resident
handoff is still a separate implementation and qualification item.

The complete amendment, resolved decisions and implementation sequence are in
[COPY Specification](../engineering/COPY%20Specification.md#operand-qualified-attributes-and-backup-amendment--accepted-2026-10-09).
Implementation evidence belongs in [COPY Utility](../engineering/COPY%20Utility.md).
The [user guide](../user/users_guide.md) contains a planned-feature explanation
that must remain marked unimplemented until native qualification passes.
