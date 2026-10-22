# REN / REN.COM — BetterCP/M Engineering Specification

Status: resident behavior is documented in
[Resident REN Selection](Resident%20REN%20Selection.md). Transient REN Build 005
implements the workflow below. Native assembler parity and representative
cpmsim and Model 4 media qualification passed on 2026-10-13; see
[REN Qualification](REN%20Qualification.md). The user interface is in user-guide
section 4.3.

Uses the shared [DU syntax](208%20Extended%20DU%20Syntax.md),
[COPY template rules](COPY%20Specification.md), and
[interactive prompt convention](Interactive%20Prompt%20Convention.md).
This contract supersedes earlier target assumptions where they conflict;
implementation and qualification must follow separately.

## Implementation policies and remaining boundaries

- Switches are separate whitespace-delimited tokens in any position. All
  options and operand syntax are validated before mutation. Repetition is
  permitted; the last `/Y` or `/N` wins, and the last `/Q` or `/QQ` wins.
- `/N` suppresses writes even without `/C`. `/DRY` suppresses writes regardless
  of confirmation policy or switch order.
- `/QQ` never prompts. It supplies assume-Yes only when no explicit confirmation
  policy exists; it preserves explicit `/N`. The one-time notice is omitted
  when explicit `/Y` occurs anywhere, or when `/DRY` is active.
- Unattended `/Y` and `/QQ` skip existing targets without overwrite. `/N` and
  `/DRY` also report/skip collisions without prompting.
- Collision replacement input accepts only literal, locationless 8.3 names.
  Invalid input reprompts; blank returns to the collision menu; Ctrl-C aborts
  the remainder. Operational failures offer retry/skip/abort with inline help;
  unattended failures are counted and skipped.
- Source enumeration uses lexical progression and a per-DU ledger of successful
  destinations, preventing repeated renaming even after arbitrary interactive
  replacement names. Positional mappings also remain idempotent. Targets overlapping
  still-existing selected sources remain collisions; no cycle solving or
  overwrite is authorized.
- `/P` preserves original attributes and refuses inconsistent per-extent
  attributes before mutation. Attribute restoration failure aborts the remainder.
  Native build parity and representative physical platform qualification passed.

## 1. Purpose

`REN` changes file names without changing file location.

BetterCP/M supports two equivalent forms:

```text
REN filespec template
REN template=filespec
```

where:

- `filespec` is the source selector;
- `template` is the destination-name template;
- every file remains in its original DU;
- the template never carries a location specification.

Examples:

```text
REN B[-]:*.DOC *.TXT
REN *.TXT=B[-]:*.DOC
```

These are equivalent.

`REN` is not a relocation command. Moving files between DUs belongs to `MOVE`.

---

## 2. Resident and transient forms

Resident `REN` is deliberately smaller.

Transient `REN.COM` is the full implementation.

Resident REN should support the core rename operation and `/VER`, using the common RCP selector infrastructure where applicable, but richer interaction/reporting modes belong to `REN.COM`.

Transient-only features include:

```text
/C
/Y
/N
/DRY
/P
/Q
/QQ
```

Resident REN does not need to support protected-file override directly. A user can temporarily remove attributes with `STAT`, perform the resident rename, then restore them.

Example:

```text
STAT FOO.DOC $RW
REN FOO.DOC FOO.TXT
STAT FOO.TXT $RO
```

---

## 3. Source selector

The source operand uses the common BetterCP/M selector syntax.

Examples:

```text
A0:FOO.DOC
B[-]:*.DOC
[A0,B[3-5],C7]:*.BAK
B[-]:*.DOC[$ARC]
```

The shared selector may include:

- one or many DUs;
- bounded wildcard filespecs;
- attribute predicates.

Example:

```text
REN [A0,B[3-5],C7]:*.DOC[$ARC] *.TXT
```

renames the selected ARC-marked `.DOC` files in place within each source DU.

---

## 4. Template operand

The rename template is always locationless.

Valid:

```text
*.TXT
NEWNAME.DOC
F?*.BAK
```

Invalid:

```text
B:*.TXT
B3:*.TXT
B[-]:*.TXT
[A0,B3]:*.TXT
```

The template controls only the resulting 8.3 filename.

It never selects or determines a destination DU.

---

## 5. Rename-template semantics

REN must use the same positional filename-template rules already established for COPY.

Do not create a REN-specific transformation language.

Rules:

- literals replace the corresponding source position;
- `?` copies one source position;
- terminal `*` copies the remainder of that field;
- repeated terminal stars collapse;
- positions do not shift;
- the resulting filename must be a valid CP/M 8.3 name.

Examples:

```text
REN *.DOC *.TXT
```

changes only the extension.

```text
REN FOO?.DOC BAR?.TXT
```

applies `?` positionally.

Any template accepted/rejected by COPY's destination-template engine should behave the same way in REN.

Where practical, use the same shared transformation code.

---

## 6. In-place semantics

Each selected file remains in its original DU.

For:

```text
REN B[-]:*.DOC *.TXT
```

the mapping is conceptually:

```text
B0:FOO.DOC -> B0:FOO.TXT
B3:BAR.DOC -> B3:BAR.TXT
B7:BAZ.DOC -> B7:BAZ.TXT
```

REN never maps files between DUs.

---

## 7. Attribute selection and protection

The source selector decides which files are candidates.

REN independently applies protection rules.

Protected classes currently include:

```text
$RO
$SYS
```

Attribute selectors remain selection-only.

Examples:

```text
REN /P *.DOC[$RO] *.TXT
```

means:

> Select only RO `.DOC` files and allow their protection to be overridden.

```text
REN /P *.DOC[$SYS] *.TXT
```

means:

> Select only SYS `.DOC` files and allow protection override.

Without `/P`, protected files are skipped.

---

## 8. `/P` — override protection

Syntax:

```text
/P
```

`/P` allows REN to operate on protected selected files.

It overrides both currently protected classes:

- read-only;
- system.

It does not broaden the selection.

Thus:

```text
REN /P *.DOC *.TXT
```

renames matching files including protected ones.

```text
REN /P *.DOC[$RO] *.TXT
```

renames only selected RO files.

```text
REN /P *.DOC[$SYS] *.TXT
```

renames only selected SYS files.

The separation is:

```text
[...]  = which files
/P     = whether protection may be overridden
```

---

## 9. Default behavior

With no confirmation/reporting switches, REN immediately performs eligible renames and reports results.

Examples:

```text
A0>REN A.DOC A.TXT
A.DOC -> A.TXT success
```

Equivalent assignment form:

```text
A0>REN A.TXT=A.DOC
A.DOC -> A.TXT success
```

Protected file:

```text
A0>REN A.DOC A.TXT
A.DOC -> A.TXT $RO skipped
```

Naming collision:

```text
A0>REN A.DOC A.TXT
File exists. N/S/A/?
```

Plain REN is not a confirm-every-file mode and is not silent.

It performs ordinary eligible renames and pauses only when a decision is actually required.

---

## 10. Collision handling

If a generated target name already exists, REN pauses:

```text
File exists. N/S/A/?
```

`?` displays:

```text
N New name, S Skip file, A Abort remainder.
```

then repeats the prompt.

Actions:

- `N` — supply a new name;
- `S` — skip this file;
- `A` — stop processing the remaining files;
- `?` — display one-line help and reprompt.

Use **Abort remainder**, not **Abort all**, because earlier renames are not rolled back.

---

## 11. New-name entry after collision

If the user chooses:

```text
N
```

prompt:

```text
New name?
```

The response must be:

- locationless;
- valid 8.3;
- legal under REN's template/name rules.

If the new target also exists, display the collision prompt again.

Example:

```text
E.DOC -> E.TXT File exists. N/S/A/? N
New name? E2.TXT
E.DOC -> E2.TXT
```

---

## 12. Incremental execution

REN does not require a full batch-preflight collision map before ordinary execution.

Example:

```text
A.DOC -> A.TXT    success
B.DOC -> B.TXT    success
C.DOC -> C.TXT    File exists. N/S/A/?
```

If the user chooses `A`, the earlier successful renames remain.

This behavior is intentional.

Transient REN may perform additional lookahead where convenient, but full atomic preflight is not required as a semantic contract.

---

## 13. `/C` — confirm each

Syntax:

```text
/C
```

`/C` enters a step-through mode.

For each otherwise eligible rename:

```text
A.DOC -> A.TXT Y/N
```

The user answers each operation.

A typical session:

```text
A.DOC -> A.TXT Y/N Y - A.DOC -> A.TXT
B.DOC -> B.TXT Y/N N - User Skipped
C.DOC -> C.TXT Y/N Y - C.DOC -> C.TXT
D.DOC -> D.TXT [SKIPPED - READ ONLY]
E.DOC -> E.TXT File exists. N/S/A/?
```

Protected files do not display synthetic user input.

Use direct status such as:

```text
D.DOC -> D.TXT [SKIPPED - READ ONLY]
```

or:

```text
D.DOC -> D.TXT [SKIPPED - SYSTEM FILE]
```

This keeps true user responses distinct from automatic protection decisions.

---

## 14. `/Y` — assume Yes

Syntax:

```text
/Y
```

`/Y` automatically answers Yes to ordinary confirmation points.

It does not override protection.

Thus:

```text
REN /Y *.DOC *.TXT
```

renames all eligible files without confirmation but skips protected files unless `/P` is also present.

`/Y` also resolves `/C` confirmation points automatically.

Example:

```text
REN /Y /C *.DOC *.TXT
```

performs the step-through mapping using automatic Yes.

Routine mapping output remains visible unless `/Q` or `/QQ` changes reporting.

---

## 15. `/N` — assume No

Syntax:

```text
/N
```

`/N` is the opposite confirmation policy.

Within `/C`, it automatically answers No.

Example:

```text
REN /C /N *.DOC *.TXT
```

does not rename files.

Instead it displays the proposed mappings:

```text
A.DOC -> A.TXT
B.DOC -> B.TXT
C.DOC -> C.TXT [SKIPPED - READ ONLY]
D.DOC -> D.TXT
```

No artificial `N` is printed on each ordinary line.

The absence of write activity is implied by the option.

If `/Y` and `/N` are both used without `/DRY`, normal option precedence applies: later confirmation policy wins.

Thus:

```text
REN /C /N /Y ...
```

executes eligible renames.

```text
REN /C /Y /N ...
```

does not.

---

## 16. `/DRY` — guaranteed dry run

Syntax:

```text
/DRY
```

`/DRY` provides a hard no-write guarantee.

Its display behavior resembles:

```text
/C /N
```

but it is not merely an alias.

`/DRY` cannot be overridden by `/Y`, regardless of switch order.

Thus all of these remain dry runs:

```text
REN /DRY ...
REN /DRY /Y ...
REN /Y /DRY ...
REN /DRY /C /Y ...
```

At the end of a visible dry run:

```text
Dry run only: no files were renamed.
```

`/DRY` should be treated internally as a dedicated safety mode.

---

## 17. Multi-DU output grouping

When output spans multiple DUs, group results by DU rather than repeating the DU on every line.

Example:

```text
A0:
   A.DOC -> A.TXT
   B.DOC -> B.TXT
A2:
   A.DOC -> A.TXT [SKIPPED - READ ONLY]
B1:
   D.DOC -> D.TXT
   E.DOC -> E.TXT
C4:
   E.DOC -> E.TXT [SKIPPED - TARGET EXISTS]
```

This format is used for:

- normal reporting;
- `/Y`;
- `/C`;
- `/C /N`;
- `/DRY`;

subject to `/Q` and `/QQ`.

For a single-DU operation, the DU heading may be omitted unless needed for clarity.

---

## 18. `/Q` — quiet

Syntax:

```text
/Q
```

Quiet mode suppresses routine successful rename lines.

It retains noteworthy outcomes and the final summary.

Example:

```text
A2:
   A.DOC -> A.TXT [SKIPPED - READ ONLY]
C4:
   E.DOC -> E.TXT [SKIPPED - TARGET EXISTS]

17 FILES RENAMED, 2 SKIPPED
```

`/Q` does not change confirmation behavior.

---

## 19. `/QQ` — super-quiet

Syntax:

```text
/QQ
```

Super-quiet mode suppresses all normal REN-generated output.

This includes:

- successful mappings;
- skip messages;
- target-exists notices;
- no-match messages;
- syntax diagnostics;
- final summaries.

`/QQ` is intended to strive for zero REN output.

Because a silent interactive prompt would be unsafe, `/QQ` implies `/Y` if `/Y` was not explicitly specified.

If `/Y` is absent, print exactly once:

```text
REN: /Y not specified. /QQ assumes /Y.
```

Then enter super-quiet operation.

If `/Y` was explicitly supplied:

```text
REN /Y /QQ ...
```

even that message is omitted.

`/QQ` does not imply `/P`.

Protected files therefore remain protected unless `/P` is supplied.

---

## 20. `/QQ` and dry run

`/DRY` remains dominant over `/QQ` and `/Y`.

Example:

```text
REN /DRY /QQ ...
```

performs no writes and suppresses the usual dry-run display and footer.

No output is required from REN.

---

## 21. Runtime failure handling

For an operational rename failure after processing has begun, use:

```text
REN A.DOC - Failed. R/S/A/?
```

`?` displays:

```text
R Retry, S Skip file, A Abort remainder.
```

then reprompts.

Semantics:

- `R` — retry current rename;
- `S` — skip current file and continue;
- `A` — stop processing remaining files;
- `?` — inline help.

Under `/Y`, recoverable failure handling defaults to Skip.

Under `/QQ`, REN itself remains silent.

Lower-level operating-system diagnostics may still appear independently where the OS reports them.

---

## 22. Self-mapping

If template expansion produces exactly the same filename:

```text
A.DOC -> A.DOC
```

treat this as a no-op/skip, not a failure.

It may contribute to SKIPPED accounting.

---

## 23. No source matches

If no files match, ordinary REN may report:

```text
NO FILE
```

`/QQ` suppresses this.

---

## 24. Final summary

Normal and `/Q` modes should report a compact summary:

```text
12 FILES RENAMED, 2 SKIPPED, 1 FAILED
```

Omit zero-count categories.

Examples:

```text
12 FILES RENAMED
```

```text
12 FILES RENAMED, 2 SKIPPED
```

`/QQ` suppresses the summary.

For `/DRY`, the dry-run footer replaces normal execution semantics:

```text
Dry run only: no files were renamed.
```

unless `/QQ` suppresses it.

---

## 25. `/VER`

All BetterCP/M utilities support:

```text
/VER
```

REN follows the same format.

Resident example:

```text
BetterCP/M REN 1.0 (Resident, Build 002)
```

Transient:

```text
BetterCP/M REN 1.0 (Build 004)
```

`/VER` prints the banner and exits without performing any rename.

---

## 26. Transient REN.COM switch set

The complete transient switch set is:

```text
/C
/Y
/N
/DRY
/P
/Q
/QQ
/VER
```

Meaning:

```text
/C      confirm each / step-through mode
/Y      assume Yes
/N      assume No
/DRY    guaranteed no-write dry run
/P      override protected-file restrictions
/Q      quiet
/QQ     super-quiet; implies /Y if absent
/VER    show version banner and exit
```

---

## 27. Resident REN subset

Resident REN remains deliberately smaller.

It should support:

- core rename syntax;
- shared source selector infrastructure where resident code already permits it;
- COPY-compatible template transformation;
- normal protection behavior;
- `/VER`.

It need not support:

```text
/C
/N
/DRY
/P
/Q
/QQ
```

unless later implementation work shows one is exceptionally cheap and worthwhile.

Protected-file rename can be achieved manually using STAT where needed.

---

## 28. Explicit exclusions

REN 1.0 must not implement:

- relocation between DUs;
- destination-location selectors;
- destination attribute changes;
- recursion;
- path traversal;
- regex renaming;
- arbitrary substring replacement;
- automatic case conversion;
- numbering sequences;
- automatic overwrite of existing targets;
- temporary-name cycle solving.

REN is deliberately a bounded filename transformation utility.

---

## 29. Qualification expectations

Test at minimum:

### Syntax forms

```text
REN A.DOC A.TXT
REN A.TXT=A.DOC
REN B[-]:*.DOC *.TXT
REN *.TXT=B[-]:*.DOC
```

### Template behavior

Use COPY-equivalent positional tests involving:

```text
*
?
literal positions
repeated terminal *
invalid nonterminal *
```

### Multi-DU grouping

```text
REN [A0,A2,B1,C4]:*.DOC *.TXT
```

Verify grouped output.

### Protection

```text
REN *.DOC *.TXT
REN /P *.DOC *.TXT
REN /P *.DOC[$RO] *.TXT
REN /P *.DOC[$SYS] *.TXT
```

### Confirm mode

```text
REN /C *.DOC *.TXT
REN /Y /C *.DOC *.TXT
REN /N /C *.DOC *.TXT
```

### Dry run

```text
REN /DRY *.DOC *.TXT
REN /DRY /Y *.DOC *.TXT
REN /Y /DRY *.DOC *.TXT
```

Verify no writes.

### Quiet

```text
REN /Q *.DOC *.TXT
REN /QQ *.DOC *.TXT
REN /Y /QQ *.DOC *.TXT
```

Verify bare `/QQ` emits only:

```text
REN: /Y not specified. /QQ assumes /Y.
```

then silence.

### Collision

Force:

```text
E.DOC -> E.TXT
```

where `E.TXT` already exists.

Verify:

```text
File exists. N/S/A/?
```

and help/new-name flow.

### Failure recovery

Verify:

```text
REN A.DOC - Failed. R/S/A/?
```

with help and reprompt.

### Summary

Verify:

```text
n FILES RENAMED, n SKIPPED, n FAILED
```

with zero-valued categories omitted.

---

## Transient implementation progress — 2026-10-12

REN.COM now links the shared DU/filespec/predicate library and resident REN
selection/mapping engine at build time. Both operand orders, locationless
templates, multi-DU source selections and predicates are supported. RO/SYS
protection is aggregated across physical extents, attributes are preserved,
and the caller DU is restored. Source rescanning uses lexical progression and
idempotent positional mapping; existing destinations stop this initial core
without overwrite or cycle solving.

Standalone `/VER` identifies REN Build 001. A leading `/DRY` validates and checks
selected mappings while suppressing every rename; this initial increment emits
the no-write footer but does not yet list proposed mappings. Other switches and
rich grouping, summaries, collision/new-name and failure-recovery prompts remain
pending. This is an implementation milestone, not full REN.COM qualification.

Cross assembly succeeds at 3,255 bytes. `tools/test_ren_core.py` executes the
assembled transient with a directory/BDOS fixture and checks operand orders,
multi-DU selection, predicates, attribute retention, protection, dry-run
immutability, syntax rejection, caller-DU restoration and `/VER`. The native
build now expands the same source as the cross build, but parity could not be
run here because the configured cpmsim executable is unavailable. Physical
platform and full workflow qualification remain pending.

## Confirmation and reporting increment — 2026-10-12

REN Build 002 adds `/C`, `/Y`, `/N`, `/DRY`, `/Q` and `/QQ` in any token position,
with complete option validation before execution. Normal mappings and dry-run
previews are grouped by source DU. Successful rename and skipped-file counts
are reported with zero categories omitted; `/Q` suppresses successful mappings,
and `/QQ` suppresses routine diagnostics and summaries. RO/SYS and self-mapping
skips are reported. `/C` offers a simple Y/N prompt; Ctrl-C exits immediately
after restoring the caller DU. `/Y` and `/QQ` skip existing targets and continue.
Interactive collision/new-name handling, recoverable failure menus, failed-file
accounting and `/P` are not yet implemented; an interactive collision or an
operational failure still stops the core.

Cross assembly succeeds at 4,285 bytes. Core and workflow execution tests pass,
including option ordering/repetition, all dry-run combinations, invalid trailing
options before mutation, protected files, multi-DU grouping, unattended collision
skips, quiet output, notice policy, confirmation and Ctrl-C. The tests use an
assembled Z80 image with a directory/BDOS fixture; they do not establish native
assembler parity or physical disk behavior.

## Interactive collision increment — 2026-10-12

REN Build 003 implements `File exists. N/S/A/?` with one-line inline help,
skip and abort-remainder actions. `N` reads a literal locationless 8.3 replacement
name; lowercase is normalized. Wildcards, DU prefixes, qualifiers, invalid
fields and overlong input reprompt with `Invalid filename.`. Blank returns to
the collision menu; Backspace/DEL edits and Ctrl-U clears input. Ctrl-C aborts
from either prompt, restores the caller DU and retains earlier successful
renames. The replacement is checked for existing targets before mutation;
a self-name is skipped, and `/C` still authorizes an eligible replacement.

A per-DU ledger records successful destination names, including arbitrary
interactive replacements. Rescans exclude these entries even when they continue
to match the source selector and are not fixed points of the template. The
ledger occupies 11 bytes per successful rename, starts above program/stack
storage, and is bounded below the current BDOS entry with a 256-byte margin.
Space is checked before each mutation; exhaustion aborts without performing
that rename. The ledger resets between DUs. No cross-DU relocation, overwrite
or temporary-name cycle solving is introduced.

Cross assembly succeeds at 4,875 bytes. Core, workflow and collision execution
tests pass, including repeated existing-name collisions, help with no state
change, edited and overlong input, blank, Ctrl-C, self-mapping, selected-source
overlap, `/C`, and prevention of interactive-target reselection. Native and
physical platform qualification remain pending, as do `/P`, operational failure
recovery and failed-file accounting.

## Operational failure recovery increment — 2026-10-12

REN Build 004 adds `REN filename - Failed. R/S/A/?`. Help prints
`R Retry, S Skip file, A Abort remainder.` and reprompts without affecting
counts. Retry preserves the current source/target mapping, rechecks target
existence and drive read-only status, and does not repeat `/C` authorization.
If a target has appeared, normal collision handling applies before any new
mutation. `/Y` and `/QQ` count a failed file and continue without prompting;
`/QQ` remains silent. A file recovered by retry counts as renamed, while a
failure abandoned with skip, abort or Ctrl-C counts once as failed. Abort
restores the caller DU and retains earlier successful changes. Final summaries
include nonzero FAILED counts independently of ordinary SKIPPED counts.

Drive read-only rejection uses the same failure policy. `/DRY` never prompts
for such a failure and still cannot mutate. `/P` remains unimplemented and does
not yet permit protected-file renames.

Cross assembly succeeds at 5,142 bytes. Core, confirmation/reporting, collision
and injected-failure execution tests pass. Failure cases cover repeated retry,
help, no repeated confirmation, skip, partial-success abort/Ctrl-C, unattended
quiet behavior, a target appearing between failure and retry, and read-only
drives. Native assembler parity and physical platform qualification remain
pending; the fixture tests are not a claim of real-media qualification.

## Protection override increment — 2026-10-13

REN Build 005 implements `/P` for both RO and SYS without broadening selection.
Before mutation it snapshots every high attribute bit in the eleven filename
bytes across all physical source extents. Uniform attributes are preserved;
inconsistent per-extent bits are refused before writes because public Function
30 cannot reconstruct distinct per-extent assignments. No normalization or raw
directory rewrite is attempted.

Read-only files are temporarily made writable using Function 30, renamed using
Function 23, and restored under the resulting name. A failed rename restores
attributes under the original name before offering ordinary failure recovery.
A failed unprotect operation also attempts repair before reporting failure.
Restoration failure emits an explicit diagnostic (subject to `/QQ`) and aborts
the remainder; it does not retry an already moved source or silently continue.
The affected file is counted as failed, even if its directory name was changed.
`/P` does not override drive-level read-only status. `/DRY`, `/N`, self-mapping,
collision skips and negative confirmation perform no attribute writes.

Cross assembly succeeds at 5,553 bytes. Protection execution tests cover all
eight RO/SYS/ARC combinations, selection independence, failed-rename repair,
unprotect/restoration failures, differing extent attributes, drive protection
and no-write policy precedence. All preceding execution regressions pass.
Native parity, real BDOS/media behavior and physical platform qualification
remain outstanding; fixture tests alone do not establish release completion.


## Qualification — 2026-10-13

The Build 005 native ZSM4/LINK result is byte-identical to the cross-assembled
5,553-byte image. Real BetterCP/M BDOS qualification passed under cpmsim and
trs80gp, including all eight RO/SYS/ARC combinations, multi-extent contents and
whole-media dry-run immutability. cpmsim additionally passed collision help,
replacement-name validation, confirmation, destination-ledger exclusion,
multi-DU selection and invalid-command immutability. Failure injection remains
covered by the assembled-code fixture suite rather than real disk faults.
See [REN Qualification](REN%20Qualification.md) for scope and reproduction.

## Build 007 shared-input integration

Transient REN's Y/N confirmation, N/S/A/? collision and R/S/A/? recovery choices
use the shared choice-only controller through a compatibility binding. Existing
keys, echo, retry/help behavior, Ctrl-C abort and option precedence remain
unchanged. Enter/ESC do not acquire new meanings. Rename and recovery operations
remain caller-owned. The replacement-name text editor is unchanged in this
increment. See [REN Shared Input Qualification](REN%20Shared%20Input%20Qualification.md)
for memory costs, compatibility comparisons and native evidence.
