# BetterCP/M 1.0 transient ERA specification

Status: target contract recorded on 2026-10-10. Expanded ERA.COM implementation
has not started. The existing resident/basic transient ERA is not claimed to
provide the interface below. Destructive erase `/D` is transient-only.

This contract uses the shared [DU-selector specification](208%20Extended%20DU%20Syntax.md),
operand attribute predicates, and [interactive prompt convention](Interactive%20Prompt%20Convention.md).
Implementation follows COPY, RCP shared-selector work, and DIR. The planned
user-facing interface is in the user guide, section 4.2.

## Implementation questions retained for resolution

Before coding destructive operations, make these boundaries precise without
weakening the protections below:

- Define “explicitly admit SYS/RO” for compound predicates, including negation,
  aliases and OR branches. A truth table alone cannot distinguish `$ARC` from
  a deliberate protected-file admission. `/R` authorizes selected RO files;
  it must not silently broaden selection.
- Define the exact RO-specific per-file authorization prompt and its interaction
  with `/C`, plus cancellation at confirmation, paging and destructive-write
  boundaries. Failure recovery already defines R/S/A/?.
- Define target-set storage limits and preflight overflow behavior, option
  placement/repetition, and whether a wildcard matching one file follows the
  manifest or exact-file presentation. No syntax error may cause partial erasure.
- Define recovery after a partial directory scrub, shared/corrupt allocation
  maps, raw-write permission checks and filesystem cache/allocation-state
  reconciliation. The specified overwrite-before-scrub order remains mandatory.
- The manual `STAT ... !$ARC` example is a proposed composition, not a command
  implemented by today's STAT. Its ARC mutation contract needs separate work.
  Do not present it as equivalent to COPY's per-success transactional backup:
  after any failed or skipped copy, clearing a whole selected source set is unsafe.

The supplied contract follows. These notes retain implementation questions;
they do not replace its agreed protection or switch semantics.

## 1. Purpose

`ERA.COM` is the full transient BetterCP/M file-erasure utility.

It preserves the familiar CP/M `ERA filespec` model while adding BetterCP/M's common file-selection language, safer multi-file handling, protected-file semantics, unattended operation, per-file confirmation, and an optional destructive erase.

The command is intentionally narrow. It is an erase utility, not a general file-management program.

The resident ERA remains the smaller common implementation. The shared RCP selector service may allow resident ERA to understand the common BetterCP/M file selector syntax, but **destructive erase `/D` is transient-only**.

---

## 2. Basic syntax

```text
ERA [options] filespec[attribute-expression]
```

Examples:

```text
ERA *.DOC
ERA B7:*.BAK
ERA B[-]:*.DOC
ERA [A0,B[3-5],C[-]]:*.BAK
ERA B[-]:*.DOC[$ARC]
ERA /R B[-]:*.DOC[$RO+$ARC]
ERA /D /Y /Q B7:TEMP*.DAT
```

Options are command-wide.

The filespec, DU selector, and bracketed attribute expression use the common BetterCP/M selector syntax.

---

## 3. Shared file-selection syntax

ERA must use the common BetterCP/M selection machinery rather than implementing a private parser.

That includes:

```text
B7:
B[1,3,8-10]:
B[-]:
[A0,B[3-5],C[-]]:
```

and bounded filespecs such as:

```text
*.DOC
FOO.*
F?*.DAT
```

and attribute predicates such as:

```text
[$ARC]
[$RO]
[$SYS+$ARC]
[$RW,$RO]
[$ARC+!$SYS]
```

The common Boolean operators are:

```text
!    NOT
+    AND
,    OR
```

with precedence:

```text
! > + > ,
```

The supported 1.0 attribute vocabulary is:

```text
$RO
$RW
$SYS
$DIR
$ARC
```

with:

```text
$RW  == !$RO
$DIR == !$SYS
```

Historical `$R/O` and `$R/W` aliases may be accepted where supported by the shared parser.

Wheel semantics are post-1.0 and are not part of ERA 1.0.

---

## 4. ERA protection model

ERA has safety rules in addition to ordinary file selection.

The important principle is:

> The selector describes the desired file class, while ERA separately enforces its protections against accidentally erasing SYS and RO files.

These protections should not be weakened merely to permit every possible erase operation to be expressed in one command.

That is deliberate.

---

## 5. Default protection

With no attribute qualification:

```text
ERA *.DOC
```

ordinary writable, non-SYS files are eligible.

SYS and RO files are protected from an ordinary broad erase.

Conceptually, this corresponds to ERA's safe default treatment of:

```text
$RW + !$SYS
```

but this is ERA policy, not text synthetically appended to the user's command line.

---

## 6. Explicit SYS selection

SYS files must be deliberately called out by the selector before ERA will erase them.

For example:

```text
ERA *.DOC[$SYS]
```

selects only SYS `.DOC` files.

```text
ERA *.DOC[$SYS+$ARC]
```

selects SYS `.DOC` files with ARC set.

A predicate which does not explicitly admit SYS does not accidentally erase SYS files merely because some other condition matches them.

Thus:

```text
ERA *.DOC[$ARC]
```

does not turn ARC into a back door around SYS protection.

---

## 7. Explicit RO selection

RO protection is similarly deliberate.

A broad ERA does not erase RO files.

To bring RO files deliberately into the erase set, the command should explicitly call them out, for example:

```text
ERA *.*[$RO]
```

or:

```text
ERA *.*[$RW,$RO]
```

The latter means ordinary non-SYS files regardless of whether the RO bit is set.

Explicit selection alone does **not** mean "erase RO without protection."

Without `/R`, explicitly selected RO files require special per-file authorization.

---

## 8. `/R` — override read-only protection

Syntax:

```text
/R
```

`/R` authorizes erasure of selected read-only files without the extra RO-specific authorization step.

It does not broaden the filespec or attribute predicate.

Examples:

```text
ERA *.*[$RO]
```

selects RO files but retains their protection.

```text
ERA /R *.*[$RO]
```

selects the same files and authorizes their erasure.

Crucially:

```text
/Y
```

does **not** imply:

```text
/R
```

This separation is intentional.

`/Y` answers normal confirmation questions.

`/R` overrides the semantic protection represented by the RO attribute.

---

## 9. Protected-file behavior

For files matched by a broad operation but not explicitly admitted by the relevant protection policy:

- protected SYS files are skipped;
- protected RO files are skipped.

A skipped RO file may be reported as:

```text
TINA.DOC [SKIPPED - READ ONLY]
```

particularly during `/C` processing.

An explicitly selected RO file without `/R` receives the required per-file RO authorization rather than being silently erased.

No unattended mode may pause for an RO decision. Therefore `/Y` without `/R` must skip RO files rather than interact.

---

## 10. `/Y` — assume Yes

Syntax:

```text
/Y
```

`/Y` means:

> Assume Yes to ERA's normal confirmation questions.

It suppresses the preflight manifest and ordinary confirmation prompts.

It is appropriate for SUBMIT files but is equally valid interactively.

Examples:

```text
ERA /Y *.BAK
ERA /D /Y B7:TEMP*.DAT
```

`/Y` does not override RO protection.

Therefore:

```text
ERA /Y *.BAK
```

does not silently erase protected RO files.

To authorize selected RO files noninteractively:

```text
ERA /Y /R ...
```

is required.

---

## 11. `/Q` — quiet mode

Syntax:

```text
/Q
```

`/Q` suppresses normal informational output.

It does **not** suppress interaction.

Thus:

```text
ERA /Q *.DOC
```

does not print the preflight heading or filename list, but still prompts:

```text
ERASE THESE FILES? Y/N
```

Likewise:

```text
ERA /D /Q *.DOC
```

prompts:

```text
DESTRUCTIVELY ERASE THESE FILES? THIS IS UNRECOVERABLE. Y/N
```

`/Q` suppresses:

- preflight manifest heading;
- preflight file listing;
- ordinary informational chatter;
- normal completion summary.

Errors and significant diagnostics remain visible.

`/Q /Y` is therefore the fully unattended quiet form.

---

## 12. `/C` — confirm each file

Syntax:

```text
/C
```

`/C` adds per-file confirmation for files ERA is otherwise authorized to erase.

It does not override protection.

Typical flow:

```text
ERASE THESE FILES? Y/N Y

BOB.TXT Y/N Y
TINA.DOC [SKIPPED - READ ONLY]
FRED.COM Y/N N
JANE.TXT Y/N Y
```

A protected file which ERA is not authorized to erase is skipped rather than turned into a `/C` prompt.

With:

```text
/R
```

a selected RO file becomes erasable and therefore participates normally in `/C`.

Example:

```text
ERA /C /R *.*[$RO]
```

asks the ordinary `/C` Y/N question for each selected RO file.

`/Y` dominates `/C`; if `/Y` is specified, no ordinary confirmations are issued.

`/Q` does **not** dominate `/C`. Quiet mode suppresses informational output, not requested interaction.

---

## 13. Multi-file preflight manifest

For a multi-file operation in normal interactive mode, ERA first displays the complete target set before asking for confirmation.

Ordinary erase begins with:

```text
THE FOLLOWING FILES WILL BE ERASED:
```

Destructive erase begins with:

```text
THE FOLLOWING FILES WILL BE DESTRUCTIVELY ERASED:
```

The listing is filename-only and should be formatted densely.

Use as many columns as fit cleanly; six columns are expected to be practical on an 80-column display for ordinary 8.3 filenames.

For multiple DUs, group filenames under DU headings.

Example:

```text
THE FOLLOWING FILES WILL BE ERASED:

A0:
OLD1.BAK     OLD2.BAK     TEST.BAK     TEMP.BAK     SAVE.BAK     JUNK.BAK

B3:
FOO.BAK      BAR.BAK      BAZ.BAK      TRY1.BAK     TRY2.BAK     TRY3.BAK

12 FILES, 47K TOTAL

ERASE THESE FILES? Y/N
```

`TOTAL` refers to allocated space represented by the target files.

---

## 14. Manifest paging

A long manifest must page automatically.

Paging is a safety feature here and does not require a separate option.

Use:

```text
MORE -- Space/ENTER for next page.
```

Do not add `?` to this prompt; the available action is already stated explicitly.

The introductory heading is printed **before** the filename list so the user knows that the list represents files which have not yet been erased.

---

## 15. Ordinary multi-file confirmation

After the manifest:

```text
12 FILES, 47K TOTAL

ERASE THESE FILES? Y/N
```

No `?` help is needed for a simple Y/N prompt.

If the user answers No, nothing is erased.

---

## 16. Single exact file

An exact one-file operation does not need a one-item preflight manifest.

Example:

```text
ERA TOM.DOC
```

goes directly to:

```text
TOM.DOC - Erase? Y/N
```

For destructive erase:

```text
ERA /D TOM.DOC
```

goes directly to an explicit destructive single-file confirmation, e.g.:

```text
TOM.DOC - Destructively erase? This is unrecoverable. Y/N
```

No:

```text
THE FOLLOWING FILES WILL BE ERASED:
```

heading is needed for an exact single-file target.

---

## 17. `/D` — destructive erase

Syntax:

```text
/D
```

Transient-only.

Destructive ERA overwrites the file's allocated data and then destroys residual directory metadata.

The user-facing multi-file warning is:

```text
THE FOLLOWING FILES WILL BE DESTRUCTIVELY ERASED:
```

After the manifest:

```text
12 FILES, 47K TOTAL

DESTRUCTIVELY ERASE THESE FILES? THIS IS UNRECOVERABLE. Y/N
```

The warning wording is intentional.

Do not describe `/D` as cryptographically "secure erase."

---

## 18. Destructive-erase algorithm

For each logical file:

1. Locate all directory extents belonging to the file.
2. Capture all allocation information required to identify every allocated data block.
3. Preserve that information independently of the directory entries.
4. Overwrite every allocated data block with `00h`.
5. Do not alter the directory entries until all required data overwrites for that file have succeeded.
6. After successful data overwrite, scrub every directory entry associated with the file:
   - byte 0 = `E5h`;
   - bytes 1–31 = `00h`.

The final directory-entry pattern is therefore:

```text
E5 00 00 00 00 ... 00
```

This removes:

- filename;
- extension;
- attribute bits;
- extent metadata;
- record metadata;
- allocation map;
- other residual entry contents.

All extent entries belonging to the logical file must be scrubbed.

---

## 19. Destructive failure safety

If destructive overwriting fails before completion:

- do **not** scrub the directory entries;
- retain the directory metadata so the file remains identifiable;
- report the failure.

The file may of course contain partially zeroed data after a physical write failure. ERA must not pretend otherwise.

A Retry begins the current file's destructive operation again using the preserved allocation information.

A Skip leaves the directory entries intact.

---

## 20. Interactive operation failures

When an erase operation fails after execution has begun, use the common BetterCP/M multi-action recovery style:

```text
ERA TOM.DOC - Failed. R/S/A/?
```

Actions:

```text
R    Retry
S    Skip
A    Abort all
?    Help
```

Entering `?` prints:

```text
R Retry, S Skip, A Abort all.
```

and then repeats:

```text
ERA TOM.DOC - Failed. R/S/A/?
```

`?` does not change state or count as an action.

---

## 21. BetterCP/M interactive-help standard

ERA establishes/uses the following general engineering convention:

> Use `?` for interactive prompts offering several abbreviated actions whose meanings are not self-evident.

Do not add `?` mechanically to obvious Y/N prompts.

Therefore:

```text
ERASE THESE FILES? Y/N
```

does not become `Y/N/?`.

Likewise paging spells out its own control:

```text
MORE -- Space/ENTER for next page.
```

This convention should be used by future utilities and retrofitted into existing utilities where appropriate.

It is not a general command-help system.

A richer Z-System-style help facility remains post-1.0 work.

---

## 22. `/Y` failure policy

`/Y` must never stop for:

```text
R/S/A/?
```

When an interactive recovery prompt would otherwise be required, `/Y` automatically chooses the equivalent of **Skip**:

- report the failed file;
- count it as FAILED;
- continue to the next file where continuing is safe.

Conceptually:

```text
interactive failure  -> R/S/A/?
/Y failure           -> automatic Skip
fatal condition       -> abort remainder
```

For destructive ERA, a failed wipe retains the directory entries and counts as FAILED.

Only a genuinely fatal condition which makes further modification unsafe should abort the remaining operation automatically.

---

## 23. No-match behavior

If no files qualify:

```text
NO FILE
```

Do not ask for confirmation.

For multi-DU selection, an empty DU does not prevent later selected DUs from being examined.

---

## 24. Final summary

Normal ERA reports one compact line:

```text
12 FILES ERASED, 2 SKIPPED, 1 FAILED, 47K FREED
```

Destructive ERA reports:

```text
12 FILES DESTRUCTIVELY ERASED, 2 SKIPPED, 1 FAILED, 47K FREED
```

Omit zero-valued categories.

Examples:

```text
12 FILES ERASED, 47K FREED
```

```text
8 FILES ERASED, 2 SKIPPED, 31K FREED
```

`FREED` means:

> actual allocated disk space released by successfully erased files.

It is not logical byte length.

A skipped or failed file contributes nothing to `FREED`.

`/Q` suppresses the normal final summary.

---

## 25. Summary accounting

Use the following broad classifications:

**ERASED**
- successfully deleted files.

**SKIPPED**
- files deliberately not erased due to protection or user choice;
- `/C` files answered No;
- protected files not admitted for erase.

**FAILED**
- files on which ERA attempted an operation but encountered an operational failure.

For destructive ERA, only files whose overwrite and final directory scrub complete successfully count as destructively erased.

---

## 26. Switch interactions

The command-wide switch set is:

```text
/D    destructive erase
/Y    assume Yes
/Q    quiet informational output
/R    authorize selected read-only files
/C    confirm each erasable file
```

They are orthogonal.

Important combinations:

```text
ERA /Y ...
```

unattended ordinary erase, but does not override RO.

```text
ERA /R ...
```

permits selected RO erasure, but ordinary confirmation still occurs.

```text
ERA /Y /R ...
```

noninteractive erase including deliberately selected RO files.

```text
ERA /Q ...
```

quiet output, but confirmation remains.

```text
ERA /Y /Q ...
```

quiet and unattended.

```text
ERA /D /Y /R /Q ...
```

destructive, unattended, RO-authorized, and quiet except for diagnostics.

---

## 27. Archive-cleanup workflow

Do not distort ERA's safety model merely to make "erase every ARC file regardless of protection" fit on a single command line.

A deliberate multi-command sequence is acceptable and preferred.

Example:

```text
COPY B[-]:*.*[$ARC] D0:
ERA    B[-]:*.*[$ARC]
ERA    B[-]:*.*[$SYS+$ARC]
ERA /R B[-]:*.*[$RO+$ARC]
```

This intentionally handles ordinary, SYS, and RO archived files separately.

The documentation should explain this explicitly because the interaction between ARC selection and ERA's protections is not necessarily intuitive.

---

## 28. Manual reconstruction of COPY `/BACKUP`

BetterCP/M's primitives are intended to be comprehensive enough to express useful workflows manually.

The manual equivalent of the source-side ARC behavior of:

```text
COPY /BACKUP ...
```

can be expressed as:

```text
COPY B[-]:*.DOC[$ARC] D0:
STAT B[-]:*.DOC[$ARC] !$ARC
```

That means:

1. copy ARC-marked files;
2. after satisfactory completion, clear ARC on those same source files.

`COPY /BACKUP` is the convenient transactionally safer form because it performs ARC clearing only after successful copy/close/verification.

This example is useful documentation of the composability of the BetterCP/M command system.

---

## 29. Validation

Before mutation begins, validate:

- command syntax;
- DU selector;
- filespec;
- attribute expression;
- switch syntax;
- selected target set where practical.

For destructive erase, collect all required allocation information before destroying any directory metadata.

No parser error should result in partial erasure.

---

## 30. Qualification cases

Work should test at minimum:

#### Normal exact erase

```text
ERA TOM.DOC
```

#### Wildcard erase

```text
ERA *.DOC
```

#### DU selection

```text
ERA B[-]:*.BAK
ERA [A0,B[3-5],C[-]]:*.BAK
```

#### Attribute selection

```text
ERA *.DOC[$ARC]
ERA *.DOC[$SYS+$ARC]
ERA *.DOC[$RO+$ARC]
ERA *.*[$RW,$RO]
```

#### RO behavior

```text
ERA *.*[$RO]
ERA /R *.*[$RO]
ERA /Y *.*[$RO]
ERA /Y /R *.*[$RO]
```

Confirm `/Y` alone does not override RO protection.

#### SYS behavior

Verify SYS files are not accidentally erased by broad commands and are erasable when deliberately selected.

#### Per-file confirmation

```text
ERA /C *.DOC
ERA /C /R *.*[$RO]
```

#### Quiet behavior

```text
ERA /Q *.DOC
ERA /Y /Q *.DOC
```

Confirm `/Q` does not suppress required interaction.

#### Destructive erase

```text
ERA /D TOM.DOC
ERA /D *.BAK
ERA /D /Y /Q B7:TEMP*.DAT
```

Verify:

- all allocated data blocks become zero;
- directory metadata is scrubbed only after successful overwrite;
- every extent entry becomes `E5 00 ... 00`.

#### Failure recovery

Force a recoverable failure and verify:

```text
ERA TOM.DOC - Failed. R/S/A/?
```

and `?` help/reprompt.

#### Unattended failure

Verify `/Y` converts recoverable interactive failures to automatic skip-and-continue.

#### Summary accounting

Verify:

```text
n FILES ERASED, n SKIPPED, n FAILED, nK FREED
```

and destructive equivalent.

---

## 31. Scope exclusions

Do not add for ERA 1.0:

- wheel semantics;
- date selection;
- generic size/date query expressions;
- undelete;
- recycle-bin semantics;
- general command help;
- extra "force absolutely everything" shortcuts designed merely to collapse deliberate protected-file workflows into one line.

The protections are part of ERA's design.

---
