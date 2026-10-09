# BetterCP/M 1.0 COPY Specification

Status: target contract supplied on 2026-10-08; implementation and
qualification are incremental. Pending decisions are listed at the end.

The common COPY implementation qualified in PR #164 predates this consolidated
contract. The first subsequent increment implements plain `destination=source`
in both common COPY forms; the retired `destination:=source` spelling is rejected.
MOVE retains its separately defined `:=` syntax. Transient-only features, Ctrl-C cleanup, handoff
and protected session-policy controls are not claimed implemented by that
qualification. See [COPY implementation and qualification record](COPY%20Utility.md)
and [Engineering Specification 119](119%20BCPX%20Version%201%20Module%20Format.md).

## 1. Purpose and scope

BetterCP/M provides two implementations of `COPY`:

1. a compact **resident/CPX COPY** containing the common everyday subset; and
2. a fuller **transient `COPY.COM`**, which is a strict functional superset.

The resident implementation exists to make ordinary file copying available without loading a transient. `COPY.COM` provides richer batch, wildcard-renaming, interactive collision-management, verification, and reporting facilities.

`COPY` is deliberately a **file-copy utility**, not a replacement for PIP. Device transfers, concatenation, text transformations, printer/console operations, archive manipulation, compression, and disk-image copying are outside its scope.

`DUP` remains responsible for disk copying. PIP remains available for the broader traditional PIP functionality.

---

# 2. Command syntax

Both forms are accepted:

```text
COPY source destination [switches]
COPY destination=source [switches]
```

The two forms are semantically equivalent.

The assignment operator is:

```text
=
```

It is **not** `:=`.

Thus:

```text
COPY C3:=A4:*.COM
```

is parsed as:

```text
destination: C3:
operator:    =
source:      A4:*.COM
```

The colon belongs to the drive/user specification.

Examples:

```text
COPY A4:FOO.COM C3:FOO.COM

COPY C3:FOO.COM=A4:FOO.COM

COPY A4:*.COM C3:

COPY C3:=A4:*.COM
```

Drive/user specifications use BetterCP/M DU notation:

```text
A:
A0:
B4:
C15:
```

Source and destination may independently specify DUs.

If a destination consists only of a DU:

```text
COPY C3:=A4:*.COM
```

the source filename is preserved.

---

# 3. Resident/common COPY feature set

The CPX implementation must support:

- exact single-file copying;
- source wildcards and multiple-file copying;
- independent source and destination DU qualification;
- exact rename-on-copy;
- destination-DU shorthand;
- `/O` overwrite control;
- preservation of all source file attributes;
- incomplete-destination cleanup after failure;
- restoration of the caller's original drive/user and other temporary state.

Examples:

```text
COPY A4:FOO.COM C3:FOO.COM

COPY A4:FOO.COM C3:BAR.COM

COPY A4:*.COM C3:

COPY C3:=A4:*.COM

COPY C3:FOO.COM=A4:FOO.COM /O
```

For a wildcard batch in the common subset, the destination may be a DU and the original source names are preserved.

Destination wildcard transformation is **not** part of the common CPX subset.

For example:

```text
COPY C3:*.DOC=A4:*.COM
```

belongs to transient `COPY.COM`.

---

# 4. Wildcard grammar

The same bounded wildcard grammar applies independently to the eight-character name field and three-character extension field.

`?` represents one position.

A terminal `*` represents the remainder of that field.

Multiple consecutive terminal stars collapse to one:

```text
F***.DAT
```

is equivalent to:

```text
F*.DAT
```

`?` may precede the terminal star:

```text
F?*.DAT
```

is valid.

Once `*` occurs within a field, no non-star character may follow it.

Examples:

| Valid | Invalid |
|---|---|
| `*.COM` | `F*A.DAT` |
| `FOO.*` | `F**?.DAT` |
| `F?*.DAT` | `B*C*.DOC` |
| `F.??*` | `F.*A` |
| `F***.DAT` | `F?**?.DAT` |

This wildcard grammar is frozen for BetterCP/M 1.0.

---

# 5. Transient destination wildcard transformation

`COPY.COM` extends the common COPY implementation by allowing wildcard patterns in the destination filespec.

For example:

```text
COPY C3:*.DOC=A4:*.COM
```

might produce:

```text
A4:FOO.COM -> C3:FOO.DOC
A4:BAR.COM -> C3:BAR.DOC
```

Both filename fields are treated independently as fixed-width, space-padded fields:

```text
name:      8 characters
extension: 3 characters
```

Destination substitution is strictly positional.

A literal destination character replaces the corresponding source position.

Destination `?` copies exactly one source position.

A terminal destination `*` copies all remaining positions of that source field, including padding.

Positions never shift.

For example:

```text
COPY C3:X?*.BAK=A4:*.COM
```

with:

```text
A4:FOOBAR.COM
```

produces:

```text
C3:XOOBAR.BAK
```

A transformation that produces an empty filename is invalid.

A transformation producing embedded spaces in a filename field is invalid.

The resulting destination must always be a legal BetterCP/M/CP/M 8.3 filename before any file is created.

---

# 6. Batch-internal destination collisions

A wildcard operation must never silently allow two source files from the same COPY invocation to map to the same destination.

For example, if two source names transform into:

```text
C3:FOO.DOC
```

the operation must reject that collision.

This rule applies even under `/O`.

`/O` authorizes replacement of a destination that existed **before** the COPY operation. It does not authorize one file in the current batch to overwrite the result of another file from that same batch.

For every multi-file operation, preflight is mandatory before the first destination is modified. Expand and retain the complete initial source set, generate every destination name, and reject the entire batch before mutation if two sources map to the same destination or any destination overlaps another selected source file. `/O` cannot override either rejection. Same-DU outputs must not become new inputs during rescanning.

Existing unrelated destinations are handled later by `/O`, `/S`, or interactive collision processing. Interactive rename must retain the same protection of selected sources and batch destination uniqueness.

---

# 7. Exact self-copy

An exact self-copy is rejected.

Source and destination are the same file only when all of the following match:

```text
drive
user
8.3 filename
```

Thus:

```text
COPY A4:FOO.COM A4:FOO.COM
```

is invalid.

Copying on the same DU under a different destination name remains valid:

```text
COPY A4:FOO.COM A4:FOO.BAK
```

Likewise, wildcard transformation on the same DU is permitted when it produces distinct legal destination names.

---

# 8. Attribute preservation

COPY preserves **all file attributes** belonging to the source file.

On successful copy:

```text
source attributes -> destination attributes
```

When overwriting an existing destination, the old destination attributes do not survive merely because they belonged to the old file. The completed destination receives the source file's attributes.

Attributes are applied only after:

1. the data copy has completed successfully; and
2. `/V` verification has succeeded, if verification was requested.

This prevents a failed partial destination from becoming R/O or otherwise difficult to clean up.

COPY must not confuse ordinary file attributes with internal extent/directory bookkeeping fields.

---

# 9. Read-only destinations

An existing R/O destination is **never overwritten**.

This remains true for:

```text
interactive Y
interactive O
/O
```

None of these override read-only protection.

COPY must never silently clear the destination R/O attribute merely to perform an overwrite.

A read-only destination is reported explicitly, for example:

```text
A4:FOO.COM -> C3:FOO.COM [READ ONLY]
```

Count that file as failed and continue with the batch. Neither `/O` nor interactive `Y` or `O` overrides this rule.

---

# 10. Command-line switches

For BetterCP/M 1.0:

```text
/O    overwrite existing writable destinations
/S    skip existing destinations
/V    verify copied data
/B    explicit noninteractive execution
```

Switches are:

- case-insensitive;
- placed after the operands;
- separated as ordinary command-line tokens.

Examples:

```text
COPY C3:=A4:*.COM /O

COPY C3:=A4:*.COM /S

COPY C3:=A4:*.COM /O /V
```

`/O` and `/S` are mutually exclusive.

`/V` may be combined with either. `/B` may be combined with `/O`, `/S` and `/V`; SUBMIT alone does not imply `/B`.

Repeated identical switches may be treated as idempotent.

Unknown switches are syntax errors.

---

# 11. Interactive destination collision handling

Transient `COPY.COM`, when operating interactively without `/O` or `/S`, prompts when the destination already exists.

SUBMIT retains ordinary interactive semantics and may pause for this prompt; execution from SUBMIT alone does not make COPY noninteractive.

In a genuinely noninteractive execution, an existing destination without `/O` or `/S` is reported as `FILE EXISTS`, counted as failed, and processing continues with the next file. COPY must neither silently overwrite nor silently skip it, and must not wait for collision input.

The prompt is:

```text
[Destination exists. Overwrite? Y/N/O/S/R/?]
```

Choices:

```text
Y   overwrite this destination only
N   skip this file only
O   overwrite this and all subsequent writable collisions
S   skip this and all subsequent collisions
R   rename this destination
?   display help
```

`O` and `S` apply only to the remainder of the current COPY invocation.

They do not persist to the next COPY command.

The `?` help line is:

```text
Y - Yes  N - No  O - Overwrite All  S - Skip All  R - Rename
```

After displaying help, COPY repeats the same collision prompt.

---

# 12. Interactive rename-on-collision

If the user chooses:

```text
R
```

COPY prompts:

```text
New Name:
```

The user supplies an ordinary exact 8.3 filename only.

The already-selected destination DU remains unchanged.

Example:

```text
A4:BAS.COM -> C3:BAS.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] R
New Name: BAS2.DOC
A4:BAS.COM -> C3:BAS2.DOC [4K]
```

Invalid rename input, including DU qualifiers or wildcards, reports `Invalid filename.` and repeats `New Name:`. A blank response cancels the rename and returns to the collision prompt for the current destination. Ctrl-C aborts the entire COPY invocation.

If the valid replacement name also exists, normal `Y/N/O/S/R/?` destination-collision processing occurs again for that new destination, subject to the read-only rule. A rename must not overwrite another selected source or collide with another batch destination.

`R` affects only the current file.

Scripted rename-on-copy does not require `R`; scripts can directly specify the required destination name/pattern in the original command.

---

# 13. Explicit rename-on-copy

Single files may always be copied under another name:

```text
COPY A4:FOO.COM C3:BAR.DOC
```

or:

```text
COPY C3:BAR.DOC=A4:FOO.COM
```

This is ordinary COPY functionality, not a special rename mode.

The source file remains intact.

---

# 14. Per-file reporting

Transient `COPY.COM` reports each successful copy using:

```text
source -> destination [nK]
```

Example:

```text
A4:FOO.COM -> C3:FOO.DOC [6K]
A4:BAR.COM -> C3:BAR.DOC [12K]
```

`[nK]` means:

> actual allocation occupied by the completed file on the **destination disk**.

It is not source allocation and not merely logical file size.

Destination allocation block size therefore determines the reported allocation.

`K` means 1024 bytes.

For an overwritten file, the displayed size is the allocation occupied by the new completed destination, not the net change in free space.

---

# 15. Collision reporting examples

Overwrite:

```text
A4:BAR.COM -> C3:BAR.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] Y
A4:BAR.COM -> C3:BAR.DOC [8K]
```

Skip:

```text
A4:BAZ.COM -> C3:BAZ.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] N
A4:BAZ.COM -> C3:BAZ.DOC [Skipped]
```

Help:

```text
A4:BAR.COM -> C3:BAR.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] ?
Y - Yes  N - No  O - Overwrite All  S - Skip All  R - Rename
A4:BAR.COM -> C3:BAR.DOC [Destination exists. Overwrite? Y/N/O/S/R/?]
```

Rename:

```text
A4:BAS.COM -> C3:BAS.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] R
New Name: BAS2.DOC
A4:BAS.COM -> C3:BAS2.DOC [4K]
```

---

# 16. Verification — `/V`

`/V` requests direct verification after each copy.

The sequence is:

```text
copy destination
close destination
reopen source
reopen destination
compare contents record-for-record
```

The comparison covers the complete CP/M logical file contents using 128-byte logical records and verifies that source and destination contain the same record sequence and terminate at the same logical end.

A checksum alone is not sufficient for `/V`.

If verification succeeds, normal attribute application and success reporting follow.

No extra success marker is required:

```text
A4:FOO.COM -> C3:FOO.DOC [6K]
```

is sufficient.

---

# 17. Interactive verify failure

On verification failure:

```text
A4:FOO.COM -> C3:FOO.DOC [VERIFY ERROR] R/S/?
```

The available responses are:

```text
R   Retry
S   Skip
?   Help
```

Help output:

```text
R - Retry  S - Skip
```

`?` then repeats the verify-error prompt.

`R` deletes/recreates the destination as necessary, repeats the copy from the beginning, and then verifies again.

If the retry succeeds, the file is reported normally and counted as copied.

`S` deletes the failed destination and continues with the next source file:

```text
A4:FOO.COM -> C3:FOO.DOC [VERIFY ERROR] R/S/? S
A4:FOO.COM -> C3:FOO.DOC [Skipped]
```

That file counts as skipped, not copied.

---

# 18. Noninteractive verify failure

When COPY is operating noninteractively, `/V` failure must not wait indefinitely for user input.

The failed destination is:

1. deleted;
2. reported as failed;
3. excluded from copied-file and destination-K totals.

COPY then continues with the next file.

No automatic retry occurs.

---

# 19. `^C` abort behavior

`^C` is the explicit abort mechanism.

No separate `Abort` prompt choice is necessary.

On `^C`:

- abort the entire current COPY invocation;
- remove any incomplete or failed destination for the file currently being processed;
- leave already completed files untouched;
- restore the caller's drive/user;
- restore DMA and other temporary COPY state;
- return cleanly to the command processor.

Completed earlier copies are not rolled back.

---

# 20. Batch error policy

For a multi-file COPY:

### Source read error

Report the current file as failed.

Do not leave an incomplete destination.

Continue with the next source file.

### Destination write or close error

Delete the incomplete destination.

Report the current file as failed.

Continue with subsequent files where possible.

### Destination disk full

Delete the incomplete current destination.

Report the disk-full condition.

Abort the remaining COPY batch because subsequent writes to the same destination are not expected to succeed.

Already completed files remain intact.

### Verification error

Use the interactive or noninteractive `/V` rules above.

---

# 21. No source matches

If the source pattern matches no files:

```text
NO FILE
```

No copied/skipped/failed summary is required.

---

# 22. Final summary

For multi-file operations, successful copies are summarized as:

```text
3 FILES COPIED [18K]
```

The `K` total is the sum of actual destination allocation occupied by successfully copied files.

Skipped files are reported separately:

```text
1 FILE SKIPPED
```

Failed files are reported separately:

```text
1 FILE FAILED
```

Zero-count summary lines are omitted.

Only successful copies contribute to:

```text
FILES COPIED
[nK]
```

Interactive verify failures ultimately answered `S` count as skipped.

Read/write/close errors and noninteractive verification failures count as failed.

Files never attempted because a disk-full condition aborted the remainder of the batch are not counted as failed.

Pluralization should be grammatically correct where convenient:

```text
1 FILE COPIED
2 FILES COPIED
```

---

# 23. Example complete interactive session

```text
A4:FOO.COM -> C3:FOO.DOC [6K]

A4:BAR.COM -> C3:BAR.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] ?
Y - Yes  N - No  O - Overwrite All  S - Skip All  R - Rename
A4:BAR.COM -> C3:BAR.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] Y
A4:BAR.COM -> C3:BAR.DOC [8K]
A4:BAZ.COM -> C3:BAZ.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] N
A4:BAZ.COM -> C3:BAZ.DOC [Skipped]
A4:BAS.COM -> C3:BAS.DOC [Destination exists. Overwrite? Y/N/O/S/R/?] R
New Name: BAS2.DOC
A4:BAS.COM -> C3:BAS2.DOC [4K]

3 FILES COPIED [18K]
1 FILE SKIPPED
```

---

# 24. Resident-to-transient handoff

The resident COPY implementation must not be required to understand `COPY.COM`'s full grammar.

It knows only its own grammar and capabilities.

If resident COPY recognizes the command but cannot process the invocation, and handoff is enabled:

1. resident COPY prints its own normal/local diagnostic;
2. the handoff mechanism appends/prints that it is handing off to `COPY.COM`;
3. the CCP bypasses further resident handling and enters normal transient lookup directly;
4. `COPY.COM`, if found, receives the original command and original caller context;
5. `COPY.COM` becomes authoritative for interpreting the invocation.

Example:

```text
A0>COPY B2:B*C*.DOC D2:
Invalid filespec -- handing off to COPY.COM
```

If `COPY.COM` is found, it executes and determines whether the command is valid under its own grammar.

If it is absent:

```text
COPY.COM not found
```

The CPX does not need knowledge of which transient features exist.

Handoff must occur before COPY creates, deletes, or modifies files.

---

# 25. COPY handoff policy control

The user may explicitly disable automatic handoff for resident COPY:

```text
COPY /HANDOFF=OFF
```

Once disabled, the setting remains disabled for subsequent COPY invocations.

Resident COPY then reports only its own error and does not attempt `COPY.COM`.

The user may restore normal behavior with:

```text
COPY /HANDOFF=ON
```

The setting:

- is per-command;
- is not automatically changed after a failed transient lookup;
- survives ordinary transient execution;
- survives warm boot;
- survives CCP/CPX command-environment reconstruction;
- resets to enabled on cold boot;
- resets when RCP is explicitly removed/unloaded;
- starts enabled when RCP is freshly loaded.

Ordinary CPX shutdown before transient execution must **not** clear this policy, because shutdown is part of normal transient execution.

---

# 26. Handoff-state storage

The audit identified existing protected storage suitable for the RCP policy byte.

The gateway has seven currently unused zero-filled bytes immediately after the CPX profile table.

One may be designated:

```text
LY_SYS+00B6h
```

as the RCP runtime-policy byte.

Naming/reserving this byte has already been shown to produce a byte-identical gateway:

- no layout shift;
- no descriptor expansion;
- no BDOS growth.

A bit in this byte will represent COPY handoff policy.

The core need not understand COPY semantics; the byte is RCP-owned protected shadow state.

Reset/control code still requires implementation and size qualification.

---

# 27. Handoff signaling requirements

The CPX→CCP handoff result must be distinct from:

```text
command unrecognized
command handled
```

The third state means:

```text
recognized command; proceed directly to transient lookup
```

It must be encoded in an ABI-safe manner.

Existing CPXs may return arbitrary register contents under the original two-state interface, so no previously unspecified register value may silently acquire handoff semantics without negotiation/versioning or another safe mechanism.

No BDOS growth is permitted.

---

# 28. Resident/common vs transient boundary

For 1.0, common/resident COPY supports source wildcards but not wildcard destination transformation.

Thus:

```text
COPY A4:*.COM C3:
```

is resident-capable.

But:

```text
COPY C3:*.DOC=A4:*.COM
```

belongs to `COPY.COM`.

Other transient-only facilities include the richer interactive collision-management behavior, rename-on-collision, destination wildcard substitution, verification, and richer reporting where those would make the CPX unacceptably large.

The exact size boundary remains subject to implementation measurement, but functionality should not be duplicated in the CPX merely so it can predict what `COPY.COM` understands.

---

# 29. Safety invariants

COPY must never:

- overwrite an R/O destination;
- leave a partial destination after a detected copy failure;
- permit two source files in one batch to overwrite the same generated destination;
- mutate files before a CPX→transient handoff;
- lose the caller's DU because of an error;
- leave temporary DMA or parser state active after termination;
- treat `/O` as permission to defeat read-only protection;
- count failed or skipped files as successfully copied.

---

# 30. Explicit non-goals for COPY 1.0

Do not add:

```text
file concatenation
logical-device copying
console/printer redirection
text-mode transformations
tab expansion
case conversion
line numbering
EOF/text filtering
archive operations
compression/decompression
disk duplication
```

Those belong to PIP, DUP, archive/compression utilities, or other specialized programs.

---

# 31. Implementation/qualification expectations

Qualification should cover at least:

```text
exact same-DU copy
cross-drive copy
cross-user copy
cross-DU copy
rename-on-copy
source wildcard expansion
destination DU shorthand
destination wildcard transformation
? substitution
* substitution
multiple terminal * normalization
invalid wildcard grammar
empty/invalid transformed names
self-copy rejection
batch-internal destination collision
existing writable destination
existing R/O destination
Y/N/O/S/R/? collision responses
/O
/S
/V
/O + /V
/S + /V
read errors
write errors
close errors
disk full
interactive verify failure
retry after verify failure
skip after verify failure
noninteractive verify failure
^C cleanup
attribute preservation
attribute replacement on overwrite
destination allocation reporting
summary accounting
no-match behavior
resident-to-transient handoff
handoff transient found
handoff transient absent
COPY /HANDOFF=OFF
COPY /HANDOFF=ON
warm-boot handoff-policy persistence
cold-boot reset
RCP-unload reset
command-environment reconstruction
original command/context preservation
zero BDOS growth
```

The implementation should also verify that the protected policy byte at `LY_SYS+00B6h` is never incorrectly reset during ordinary transient shutdown/reconstruction.


## Implementation decisions still pending

The collision, mandatory preflight, read-only-target and rename-input decisions above are settled. These engineering details remain:

Noninteractive admission is settled: `/B` selects it explicitly; SUBMIT alone retains interactive prompting.

1. Choose a bounded representation of the complete initial source set and destination mappings. If capacity is exceeded, fail before mutation.
2. Define cleanup-failure reporting. A failed/unavailable disk can also prevent deletion of an incomplete destination. Suggested rule: explicitly report cleanup failure, never claim success, and stop a batch when destination safety is uncertain. This suggestion remains pending. Replacement is nontransactional: deleting an old target for `/O` does not promise restoration after later failure or abort.

The underlying data-copy, close, attribute and verification error cases must
remain distinct from interpretation failures that permit automatic handoff.
The exact safe handoff signal and the interactive-input/cancellation mechanism
remain engineering choices to measure and qualify within the agreed behavior.


## Extended source DU sets — accepted and implemented 2026-10-09

Transient COPY admits Specification 208 selectors on its source operand in
both source/destination and destination=source forms. The destination remains
one resolved DU, optionally with a destination filename/template. The original
caller DU supplies inherited components independently of previous terms.

```text
COPY [A0,B[5-7],C[3,5,6],5]:*.COM D3:
COPY [A[-],B[-],C[-]]:*.COM D0:
```

Each frozen source record retains its own DU. Collection unions duplicate
locations and visits drive-major/user-minor order with name order within each
DU. A no-match DU contributes zero files. No overall matches reports NO FILE.
An unavailable source drive aborts the complete collection before destination
work. Capacity is 64 matched files across the complete selector.

Mapping preflight covers the complete combined source list: duplicate generated
destinations and targets overlapping any selected source DU/name reject the
batch even with overwrite enabled. Ordinary overwrite, skip, read-only,
interactive and batch behavior applies only after successful preflight.
The resident COPY and MOVE implementations are unchanged.


### Implementation update — 2026-10-09

Transient COPY now implements the section 12 interactive R contract, including
exact-name validation, repeated prompts, blank cancellation, Ctrl-C, existing
replacement collision handling and batch/source overlap protection. The native
cpmsim qualification includes read-only replacement protection. This does not
add resident handoff or change the CPX implementation. See COPY Utility.md for
measurements and evidence; verification and final reporting remain pending.
