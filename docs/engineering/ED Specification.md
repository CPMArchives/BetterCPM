# ED.COM Engineering Specification

Status: accepted 1.0 specification; ED.COM is implemented and selected for both
System Disks. Command, file-lifecycle, memory, failure and initial Model 4
qualification are recorded separately. Final release-wide validation remains.
This is a behavioral Z80/ZSM4 reimplementation, not a PL/M build dependency.
The source and stock-binary baseline is pinned in
[ED Reference Baseline](ED%20Reference%20Baseline.md) and
[provenance.json](../../third_party/dri-ed/provenance.json).
The operator-facing chapter is user-guide section 4.17. The exit-DU contract
here supersedes the earlier roadmap's unconditional caller-DU restoration rule.


## 1. Purpose and Compatibility Target

`ED.COM` is the BetterCP/M line-oriented context editor.

BetterCP/M ED shall be a **behavioral reimplementation** of the official Digital Research ED supplied with CP/M 2.2.

The implementation shall be written in Z80 assembly and shall use as primary references:

- the official DRI CP/M 2.2 ED PL/M source;
- the corresponding official CP/M 2.2 `ED.COM` binary;
- the CP/M 2.2 ED documentation.

The compatibility target is **externally observable behavior**, not DRI's original internal implementation.

BetterCP/M ED may use different:

- data structures;
- buffer organization;
- procedure boundaries;
- memory layout;
- temporary internal representations;
- optimization strategies;

provided user-visible behavior remains compatible, except for documented
corrections to confirmed DRI bugs. Compatibility is not a requirement to
reproduce defects. Confirm a defect with source/binary evidence, correct it,
and record the changed behavior in source comments and engineering/user
documentation. This rule supersedes stricter bug-preservation wording below.

The PL/M source is expected to be the fastest and safest implementation reference, and a relatively direct translation is encouraged where convenient, but internal structural equivalence is **not** itself a requirement.

The objective is:

> **Official CP/M 2.2 ED functionality, with BetterCP/M DU addressing, `/VER`, and documented corrections to confirmed DRI bugs.**

---

## 2. Provenance

Before implementation is frozen, the repository shall record:

- the exact official DRI CP/M 2.2 source archive used;
- the exact `ED.PLM` reference source;
- its hash;
- the exact official DRI CP/M 2.2 `ED.COM` binary used for qualification;
- its hash;
- the manual edition used for documentation;
- any known discrepancy between source, binary, and manual.

Unofficial optimized, reconstructed, patched, or third-party-derived ED binaries are not part of the compatibility target.

If source, documentation, and shipped binary disagree, the official CP/M 2.2 binary is the final behavioral oracle.

---

## 3. BetterCP/M Extensions

BetterCP/M adds exactly two user-visible extensions:

1. **simple `DU:` addressing** for ED filespecs;
2. **standalone `/VER`**.

No other enhancements are part of this specification.

In particular, ED does **not** acquire BetterCP/M's shared multi-file selector language.

---

## 4. Why ED Does Not Use the Full Selector Grammar

ED edits one source file at a time.

Therefore constructs such as:

```text
B[-]:FOO.TXT
B[3-7]:FOO.TXT
[A0,B3,C7]:FOO.TXT
FOO.TXT[$RO]
```

are invalid.

Supporting them would add syntax without defining a meaningful editing operation and could make it unclear which file is being edited.

The rule is:

> **Every ED filespec resolves to exactly one DU and one unambiguous 8.3 filename.**

---

## 5. Simple DU Grammar

ED accepts only simple BetterCP/M location forms:

```text
FILE.TXT        current drive, current user

B:FILE.TXT      drive B, current user
B7:FILE.TXT     drive B, user 7
7:FILE.TXT      current drive, user 7
```

Valid user numbers are:

```text
0..31
```

Drive letters are case-insensitive.

Leading-zero user numbers may follow the normal BetterCP/M simple-DU convention.

No:

- ranges;
- lists;
- compound selectors;
- attribute predicates;
- wildcards

are accepted.

---

## 6. Historical Invocation Syntax

The original DRI forms remain valid:

```text
ED filename.typ
ED d:filename.typ
ED filename.typ d:
ED d1:filename.typ d2:
```

The optional second drive/location identifies the output/work destination.

---

## 7. BetterCP/M Invocation Syntax

The historical forms are extended from drive-only addressing to simple DU addressing:

```text
ED filespec
ED filespec output-du:
```

Examples:

```text
ED TEST.ASM

ED B:TEST.ASM

ED B7:TEST.ASM

ED 7:TEST.ASM

ED B7:TEST.ASM C3:
```

The last form means:

- source: `B7:TEST.ASM`;
- output/work DU: `C3:`.

The source and output locations are explicit single DUs, never sets.

---

## 8. Default Output DU

If no output DU is supplied, the output/work DU is the source DU.

Thus:

```text
ED B7:TEST.ASM
```

uses conceptually:

```text
source     B7:TEST.ASM
temporary  B7:TEST.$$$
backup     B7:TEST.BAK
result     B7:TEST.ASM
```

---

## 9. Drive-Only and User-Only Locations

Historical drive-only syntax retains its meaning:

```text
ED B:TEST.ASM
```

means drive B, caller's current user.

Similarly:

```text
ED TEST.ASM C:
```

means output on drive C, caller's current user.

BetterCP/M's user-only extension:

```text
ED 7:TEST.ASM
```

means current drive, user 7.

Likewise:

```text
ED B:TEST.ASM 7:
```

means source on drive B/current user and output on caller's current drive/user 7.

All implicit current-drive/current-user values shall be captured at invocation before ED begins changing BDOS state.

---

## 10. Unambiguous Filespec Requirement

The edited source must be a single exact filename.

Invalid:

```text
ED *.ASM
ED FOO?.TXT
ED B[-]:FOO.TXT
```

No multi-file editing semantics shall be added.

---

## 11. Existing-File Edit Model

For an existing source, ED shall reproduce the DRI file-state behavior involving:

```text
source     X.TYP
work       X.$$$
backup     X.BAK
```

During editing:

- unread source material remains in the source file;
- current editing material resides in ED's working state;
- material written out during the session accumulates in the temporary output file.

The exact internal representation need not match DRI's.

Only the resulting observable behavior, file transitions, errors, buffer boundaries, and commands are normative.

---

## 12. Successful Normal Completion

For same-DU editing:

```text
ED B7:X.ASM
```

successful `E` shall produce the DRI-equivalent result:

```text
old B7:X.ASM  -> B7:X.BAK
B7:X.$$$      -> B7:X.ASM
```

For split-DU editing:

```text
ED B7:X.ASM C3:
```

successful `E` shall preserve the historical alternate-output behavior, conceptually:

```text
old B7:X.ASM  -> B7:X.BAK
C3:X.$$$      -> C3:X.ASM
```

Exact ordering of delete/rename/close operations shall match the behavior of the official ED binary, not merely this conceptual description.

---

## 13. Existing Output-File Collision

When an alternate output DU is specified and the final target filename already exists there, ED shall reproduce DRI's collision protection.

Example:

```text
ED B7:X.ASM C3:
```

must not silently replace an existing:

```text
C3:X.ASM
```

The historical behavior/diagnostic shall be reproduced from the official source/binary.

No BetterCP/M overwrite option or modern collision prompt is added.

---

## 14. New Files

If the specified source does not exist, ED shall reproduce DRI's documented new-file creation behavior.

A missing source that is valid as a new ED file shall not be treated as a generic fatal "file not found."

Exact prompts, initialization, temporary-file behavior, and completion semantics shall be qualified against the original binary.

---

## 15. Backup Handling

Existing `.BAK` behavior shall reproduce official DRI ED exactly.

BetterCP/M shall not add:

- numbered backups;
- multiple backup generations;
- backup directories;
- backup confirmation;
- timestamped backups;
- configurable backup policy.

---

## 16. Abort Safety

ED shall preserve the DRI guarantee that abandoning or interrupting an edit does not destroy the original source file before a successful normal completion.

Exact residual temporary-file behavior shall match DRI ED.

BetterCP/M shall not invent additional cleanup behavior if doing so changes observable compatibility.

---

## 17. Read-Only Source Files

DRI ED's handling of Read-Only source files shall be reproduced.

BetterCP/M shall not:

- automatically clear RO;
- prompt to override RO;
- add an RO force switch.

The source/binary are normative for the exact diagnostic and permitted read-only operations.

---

## 18. System Source Files

DRI ED's treatment of SYS files shall be reproduced.

No BetterCP/M `$SYS` override or attribute-expression syntax is added.

---

## 19. Editing Model

ED remains a line-oriented context editor.

Its behavior is defined in terms of:

- a source stream;
- an editable text working area;
- a current character/line context;
- an output/work stream.

The original implementation used a memory buffer and specific pointer structures.

BetterCP/M may reproduce these directly if that simplifies translation, but **those structures are not normative**.

What is normative includes:

- which commands succeed;
- which commands fail;
- what text they produce;
- buffer-full behavior;
- source/output progression;
- command pointer behavior;
- resulting files.

---

## 20. Command Prompt

ED retains the historical command prompt:

```text
*
```

The original command language remains intact.

No menus, slash-command editor mode, or full-screen interface are added.

---

## 21. DRI ED Command Set

The official CP/M 2.2 ED command set shall be reproduced.

Historical absolute line addressing is included. `n:` moves to line `n` by
converting the global line number to an ordinary relative L operation. A leading
colon, as in `:nT` or `:nK`, derives the command's direction and distance from the
current global line number. Forward ranges include the target line; backward
and equal-line ranges retain the corresponding DRI zero/backward semantics.
References use the current line including lines already written out of memory,
and movement remains bounded by the text currently in the buffer. They do not
implicitly reread previously written text. Numeric parsing retains the ordinary
16-bit count behavior. Commands may follow `n:` on the same command line.


The compatibility target includes the historical commands for:

- append;
- beginning/end-of-buffer movement;
- character movement;
- character deletion;
- end/save;
- find;
- head/save-restart;
- insert;
- juxtaposition;
- line deletion;
- line movement;
- macros;
- find-next/autoscan;
- return to original;
- page/type;
- quit;
- library read;
- substitution;
- type;
- uppercase translation control;
- verification control;
- write;
- temporary-library transfer;
- delay;
- carriage-return movement/type forms.

The exact accepted command letters, counts, defaults, signs, special numeric forms, and string syntax shall come from the official CP/M 2.2 source/binary.

The specification shall not reinterpret later ED documentation as though it necessarily described the 2.2 command set.

---

## 22. Numeric Command Semantics

All historical numeric-prefix semantics shall be preserved, including where applicable:

- omitted counts;
- positive counts;
- negative counts;
- zero;
- `#`;
- command-specific special values.

No generalized BetterCP/M numeric parser shall alter ED's original interpretation.

---

## 23. Destructive-Command Protection

The original restrictions on dangerous commands such as:

```text
E
H
O
Q
```

shall be reproduced.

If DRI requires such commands to appear alone rather than inside compound command lines, BetterCP/M ED shall do the same.

---

## 24. Command-Case Semantics

ED shall preserve all historical cases where uppercase versus lowercase command entry changes text-handling semantics.

BetterCP/M must not simply uppercase the entire ED command line before interpretation.

This is particularly important to DRI ED's historical case-conversion behavior associated with string-oriented commands.

---

## 25. Insert Mode

Insert mode shall reproduce the official CP/M 2.2 ED behavior, including its line-editing controls.

No new editing facilities are added.

---

## 26. ED Editing/Input Control Characters

Historical ED control-character behavior shall be reproduced from the official source/binary.

This includes the appropriate behavior of controls such as:

```text
^C
^E
^H
^J
^L
^R
^U
^X
^Z
DEL/RUB
```

where applicable.

The exact meaning depends on command, insert, or string-entry context and shall not be generalized beyond DRI behavior.

---

## 27. Search, Substitute, Juxtaposition and Macro Commands

The historical facilities associated with:

```text
F
N
S
J
M
```

shall be reproduced without redesign.

This includes:

- string termination;
- case treatment;
- search progression;
- substitution behavior;
- macro repetition;
- source/buffer crossing behavior;
- failure diagnostics.

No regex or wildcard search is added.

Compatibility finding: counted `J` retains DRI's internal backward movement
state between iterations. It can therefore duplicate text rather than apply
the apparent find/insert/delete operation independently at successive matches.
This behavior is confirmed against the pinned CP/M 2.2 binary. The initial
implementation preserved it; BetterCP/M now resets movement state before each
iteration. Counted J behaves like successive independent J operations, and a
missing later match reports failure while preserving completed edits.
For example, from the beginning of `A old B A more B`, `2jA^ZX^ZB` produces
`AXXXB A more B` in DRI, while BetterCP/M produces `AXB AXB` (`^Z` denotes
the actual Ctrl-Z byte).

---

## 28. Verification Mode

The official CP/M 2.2 initial verification state and the behavior of:

```text
V
-V
0V
```

shall be reproduced exactly.

The source/binary determine the normative default.

---

## 29. `R` — Library File Read

`R` names another single file.

BetterCP/M extends that filespec using the same **simple DU grammar** as the main source operand.

Examples conceptually include:

```text
RB7:HEADER.LIB
R7:HEADER.LIB
```

subject to the original ED command/string terminator syntax.

Invalid:

```text
RB[-]:HEADER.LIB
R[A0,B3]:HEADER.LIB
```

The command still reads one library file at a time.

An unqualified library name uses the current source DU, extending DRI's
source-disk lookup. For a qualified operand, missing components inherit the
captured caller DU, consistent with the documented simple-DU grammar.
An omitted extension defaults to LIB;
an explicitly supplied extension is retained by the BetterCP/M simple-filespec
extension. Parsing a library operand must not replace the primary source's
filespec or the captured caller DU.

This is not a multi-file selector facility.

---

## 30. `X` — Temporary Library Facility

The official CP/M 2.2 `X` command behavior shall be preserved, including its historical temporary-library semantics.

Where DRI uses a file such as:

```text
X$$$$$$$.LIB
```

the BetterCP/M implementation shall reproduce its observable naming/location/lifetime behavior.

Its internal implementation need not match DRI.

Approved compatibility exception: fix DRI's split-restart transfer bugs rather
than reproduce corrupted text, a lost transfer lookup or orphaned files.
An active transfer remains bound to the DU where its first X created it across
O/H, even when H swaps source/output DUs. Bare R reads that bound file and its
preserved pending bytes. Zero X clears the active transfer; normal or fatal
exit removes it from its bound DU. A subsequent new transfer binds to the
then-current source DU. The pinned DRI failure states are retained as evidence,
not as the required BetterCP/M output for these cases.

---

## 31. Internal Work-File Locations

The locations of:

- source;
- `.$$$`;
- `.BAK`;
- transfer-library files;
- `R` library files

shall be tracked explicitly as DUs.

BetterCP/M shall not rely on whichever drive/user happens to be currently selected in BDOS.

Where the DRI algorithm derives a work-file location from source/output drive state, BetterCP/M shall extend that rule naturally to DU state.

---

## 32. `E` Command

`E` shall reproduce official DRI behavior:

- finish processing remaining source material as required;
- complete the work output;
- perform historical file transition/backup operations;
- exit ED.

No additional confirmation prompt is added.

---

## 33. `H` Command

`H` shall reproduce official DRI "save and restart from head" behavior.

It is behaviorally equivalent to the DRI operation, regardless of whether BetterCP/M implements it internally as literal close/reopen steps or through another equivalent mechanism.

---

## 34. `O` Command

`O` shall reproduce official DRI "return to original" behavior.

The observable requirements include:

- current editing changes are abandoned as DRI specifies;
- source/output states are restored/reinitialized as DRI specifies;
- editing resumes against the original file state.

Exact internal rollback mechanics are implementation-defined.

---

## 35. `Q` Command

`Q` exits without committing the current edit, with the same observable file state and temporary-file behavior as official DRI ED.

No BetterCP/M "unsaved changes?" prompt is added.

---

## 36. Disk and Directory Failures

ED shall reproduce DRI behavior for conditions including:

- disk full;
- directory full;
- input read failure;
- output write failure;
- create failure;
- rename failure;
- illegal filespec;
- buffer exhaustion.

Diagnostics and recoverability shall follow the official behavior except for
confirmed bug corrections documented here.

DRI FINIS ignores rename return codes. BetterCP/M shall stop after either save
rename fails, print:

```text
Rename failed. Edited text retained in work file.
```

and return to the captured caller DU with default DMA restored. It shall not
retry the rename sequence, roll back, or delete the remaining source, backup
or work files. If original-to-BAK fails, the original and edited work file
remain. If work-to-original fails, the original remains under BAK and the
edited work file remains. This applies to both E and H; H shall not restart
after failed publication. Known read-only handling retains its specific
diagnostic. The correction avoids DRI's duplicate-name failure state.

---

## 37. Command Diagnostics

DRI ED's distinctive command-error reporting shall be preserved where observable.

For example, the historical:

```text
BREAK "x" AT c
```

style is part of ED's interface.

Exact wording and formatting shall be qualified against the official binary.

---

## 38. DU State During Editing

ED may switch BDOS drive/user state as required to access:

- the source DU;
- the output/work DU;
- a library DU;
- temporary transfer files.

Those switches are internal implementation details.

Every open logical ED file must retain its own explicit location state.

---

## 39. Final Current DU

Historical ED exit-drive behavior shall be preserved and extended naturally to user areas.

Where DRI leaves the system logged on the explicitly selected output drive after successful completion, BetterCP/M shall leave the system on the corresponding output **DU**.

Example:

```text
A0>ED B3:X.ASM C7:
...
E
```

may return to:

```text
C7>
```

where this is the DU extension of verified DRI behavior.

Exit-state behavior for:

- `E`;
- `H`;
- `Q`;
- `O`;
- errors;
- aborts

shall be qualified against the reference binary before freezing exact DU results.

---

## 40. `/VER`

BetterCP/M adds:

```text
ED /VER
```

which prints:

```text
BetterCP/M ED 1.0 (Build nnn)
```

and exits.

`/VER` is standalone-only.

Invalid:

```text
ED /VER TEST.ASM
ED TEST.ASM /VER
```

It is not part of ED's editing command language.

---

## 41. No Shared Selector Engine Requirement

ED does not need the full BetterCP/M selector engine.

A small bounded parser is sufficient for:

```text
filename.typ
d:filename.typ
du:filename.typ
u:filename.typ
```

and output-location forms:

```text
d:
du:
u:
```

plus the equivalent simple library-file filespecs.

The implementation may reuse a common simple-DU parser if one exists, but it must not accidentally accept selector syntax that ED cannot meaningfully use.

---

## 42. Explicit Exclusions

BetterCP/M ED does not add:

- wildcard editing;
- multi-file editing;
- user ranges;
- drive sets;
- compound selectors;
- attribute predicates;
- RO/SYS override syntax;
- full-screen behavior;
- cursor-key navigation;
- regex;
- undo;
- multiple active buffers;
- multiple open source files;
- numbered backups;
- configurable backup policy;
- modern collision prompts;
- syntax highlighting;
- text-format conversion;
- character-set conversion.

---

## 43. Later DRI ED Versions

Later DRI ED revisions may be studied for historical context and potential future ideas.

They do **not** alter this baseline.

Any feature imported later must be documented explicitly as a BetterCP/M extension.

The baseline remains:

> **Official DRI CP/M 2.2 ED behavior + simple DU support + `/VER`.**

---

## 44. Implementation Strategy

Recommended approach:

1. obtain and freeze the official `ED.PLM` and `ED.COM` reference pair;
2. establish behavioral fixtures against the original binary;
3. translate PL/M procedures to Z80 assembly;
4. preserve PL/M data structures where doing so is convenient;
5. freely restructure internals where that produces a clearer or smaller Z80 implementation without changing behavior;
6. reach CP/M 2.2 behavioral equivalence;
7. add simple DU handling;
8. add `/VER`;
9. rerun the full differential campaign.

The important rule is:

> **Use the source as an implementation aid, not as an internal-layout specification.**

---

## 45. Behavioral Compatibility Testing

Testing shall emphasize externally observable behavior.

At minimum cover:

- create new file;
- edit existing file;
- source on another drive;
- alternate output drive;
- same-DU BetterCP/M extension;
- cross-DU input/output;
- user 0;
- user 15;
- user 16;
- user 31;
- user-only syntax;
- output-file collision;
- existing `.BAK`;
- RO source;
- SYS source;
- `E`;
- `H`;
- `O`;
- `Q`;
- interruption;
- disk full;
- directory full;
- buffer limits;
- every editing command;
- numeric prefixes;
- negative prefixes;
- zero cases;
- `#` cases;
- compound command strings;
- protected standalone commands;
- command case;
- insert-mode controls;
- search/substitute/macro commands;
- `R` ordinary library;
- `R` DU-qualified library;
- `X` transfer library;
- verification state;
- malformed commands;
- `/VER`.

---

## 46. Differential Qualification

Where practical, run identical scripted sessions under:

```text
official DRI CP/M 2.2 ED.COM
BetterCP/M ED.COM
```

Compare:

- console output;
- resulting edited file;
- backup file;
- temporary files;
- current drive/user state;
- diagnostics;
- failure behavior.

BetterCP/M-specific DU tests shall be reduced to equivalent historical single-drive/user scenarios for comparison where possible.

---

## 47. Internal Differences Allowed

A differential test failure may **not** be excused merely because the BetterCP/M implementation is internally cleaner.

Conversely, an internal difference is irrelevant if externally observable behavior remains compatible.

For example, BetterCP/M ED may:

- use a different buffer structure;
- use different pointer representation;
- use different subroutine decomposition;
- use Z80 instructions unavailable to DRI's original 8080-targeted compiler;
- use a different temporary in-memory representation;

provided behavior visible to programs or users is unchanged.

---

## 48. User Manual Positioning

The BetterCP/M manual should describe ED as:

> **The standard CP/M 2.2 context editor, reimplemented for BetterCP/M with drive/user addressing.**

The manual should teach DRI ED operation rather than present ED as a newly designed editor.

BetterCP/M-specific documentation should concentrate on:

```text
B7:FILE.TXT
7:FILE.TXT
output DU forms
/VER
```

---

## 49. Distribution

`ED.COM` belongs on the **BetterCP/M System Disk**.

It becomes BetterCP/M's standard supplied editor.

The planned full-screen editor belongs on the **Utilities Disk** and remains a separate project.

---

## 50. Design Principle

The governing rule is:

> **Behavioral equivalence to official CP/M 2.2 ED is normative. Internal equivalence is not.**

The PL/M source is expected to be the most efficient route to that goal, so a direct translation is entirely appropriate where useful.

But BetterCP/M is reproducing **what ED does**, not requiring itself to reproduce **how DRI happened to implement it**.

The only deliberate user-visible extensions are:

```text
simple DU: addressing
/VER
```

Everything else should be traceable to the official CP/M 2.2 ED source, binary, or documentation.
## Implementation qualification notes — 2026-10-15

The initial front end and stock-oracle fixtures are recorded in
[ED implementation qualification](ED%20Implementation%20Qualification.md).
Historical behavior must come from the stock binary on stock CP/M, not solely
from running that binary under BetterCP/M. In particular, the initial collision
case returns on the caller drive under stock CP/M but on the output drive under
the current BetterCP/M host. ED error exits must reproduce the former, extended
to explicit DU state. Reserved S1 publication also differs and requires audit.
These are qualification findings, not new editor features.
