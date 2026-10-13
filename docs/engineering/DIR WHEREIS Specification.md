# DIR /WHEREIS Engineering Specification

Status: implemented in DIR Build 003, 2026-10-13; platform qualification is
recorded below. This amendment extends the completed ordinary DIR contract.

## 1. Purpose

`DIR /WHEREIS` is the BetterCP/M transient-directory search mode for locating files by filespec across the CP/M drive/user namespace.

It searches **directory entries only**. It does not open matching files and does not search file contents.

Typical uses:

```text
DIR /WHEREIS ED.COM
DIR /WHEREIS *.COM
DIR /WHEREIS B[-]:*.DOC
DIR /WHEREIS [A[-],B[-],C[-]]:FOO.*
```

The design objective is:

> **DIR /WHEREIS answers “Where does this filespec exist?”**

It is not a text-search facility, file-content indexer, or general metadata query mode.

`/WHEREIS` exists only in transient `DIR.COM`. Resident `DIR` is unchanged.

---

## 2. Relationship to Normal DIR

Normal transient DIR answers:

> What files are in this selected location?

`DIR /WHEREIS` answers:

> At which locations does this filespec exist?

Accordingly, `/WHEREIS` changes three major defaults:

1. the default search scope becomes the global accessible drive/user namespace rather than the current DU;
2. `$SYS` files are included by default;
3. output becomes compact location-oriented `DU:FILENAME` results rather than ordinary directory presentation.

All other common filespec/selector semantics remain BetterCP/M DIR semantics unless explicitly overridden below.

---

## 3. Syntax

General form:

```text
DIR /WHEREIS filespec
```

Examples:

```text
DIR /WHEREIS ED.COM
DIR /WHEREIS *.COM
DIR /WHEREIS B[-]:*.DOC
DIR /WHEREIS B[-]:*.DOC[$ARC]
DIR /WHEREIS [A0,B[3-5],C7]:FOO.*
```

The position of `/WHEREIS` shall follow the normal transient DIR option-placement rules.

`/WHEREIS` requires exactly one filespec operand.

Invalid:

```text
DIR /WHEREIS
DIR /WHEREIS ED.COM PIP.COM
```

---

## 4. Common Selector Engine

`/WHEREIS` shall use the existing common BetterCP/M object-selector implementation.

It shall not introduce a separate filespec, DU, wildcard, or attribute parser.

Supported forms include:

```text
B3:FOO.COM
B[-]:FOO.COM
B[3-7]:*.DOC
[A0,B[-],C[4,7-9]]:*.COM
B[-]:*.DOC[$ARC]
```

The existing BetterCP/M wildcard rules apply:

```text
?
*
```

The common attribute predicates also apply:

```text
[$RO]
[$RW]
[$SYS]
[$DIR]
[$ARC]
[$SYS+$RO]
[!$ARC]
```

---

## 5. Default Search Scope

An explicit DU or DU selector searches exactly the selected namespace.

Example:

```text
DIR /WHEREIS B[3-7]:ED.COM
```

searches only users 3 through 7 on drive B.

Only a **completely unqualified filespec** invokes the defining WHEREIS behavior:

> Search all accessible BetterCP/M drives and all user areas `0..31`.

Thus:

```text
DIR /WHEREIS ED.COM
```

means conceptually:

```text
search ED.COM on every accessible drive, users 0..31
```

`B:FOO.COM` still means drive B at the caller's captured current user;
`B[-]:FOO.COM` means every user on B. User-only and compound selectors retain
the common parser's existing inheritance and normalized set semantics.

This default is specific to `/WHEREIS`. It does not alter ordinary DIR semantics or the normal current-DU interpretation of unqualified filespecs elsewhere in BetterCP/M.

---

## 6. Accessible Drives

Accessible drives are the drives already known/configured by BetterCP/M.
Use the authoritative configured-drive information; do not discover scope by
speculatively probing every theoretical drive letter. Configured does not imply
that readable media is currently present.

Before implementation, audit the existing BDOS selection and directory-read
paths to establish which unavailable-media/read failures can return safely,
which force a prompt or warm boot, and whether the existing interfaces expose
enough information to implement the recovery contract. Record any limitation
before claiming unattended recovery; do not add a new core interface implicitly.

---

## 7. User Areas

For each selected drive, the default global search covers:

```text
user 0 through user 31
```

Empty user areas are silently skipped.

DIR.COM shall preserve the caller's original current drive and user area.

On return from `/WHEREIS`, the original DU shall be restored after:

- successful search;
- no-match search;
- recoverable drive errors;
- recoverable directory errors;
- fatal errors where restoration remains possible.

---

## 8. Matching Semantics

`/WHEREIS` matches CP/M directory filenames using the common BetterCP/M 8.3 wildcard rules.

Examples:

```text
DIR /WHEREIS ED.COM
DIR /WHEREIS *.COM
DIR /WHEREIS F?*.DAT
DIR /WHEREIS FOO.*
```

It does not provide:

- substring filename search;
- regular expressions;
- fuzzy matching;
- approximate matching;
- file-content searching.

Filename comparison follows normal CP/M filename semantics.

---

## 9. System Files

Unlike normal DIR presentation, `/WHEREIS` shall include `$SYS` files by default.

This is intentional.

A file locator must be able to locate files that ordinary directory presentation may hide.

Thus:

```text
DIR /WHEREIS ED.COM
```

may report both directory-visible and system files matching `ED.COM`.

Attribute qualifiers may explicitly restrict the result:

```text
DIR /WHEREIS *.COM[$SYS]
DIR /WHEREIS *.COM[$DIR]
```

---

## 10. Attribute Predicates

All common source attribute predicates apply to `/WHEREIS`.

Examples:

```text
DIR /WHEREIS *.DOC[$ARC]
DIR /WHEREIS *.COM[$SYS+$RO]
DIR /WHEREIS *.BAK[!$ARC]
```

`/WHEREIS` never changes file attributes.

---

## 11. Logical Files vs. Extents

A CP/M logical file may occupy multiple directory extent entries.

`/WHEREIS` shall report each logical file **once**.

Multiple extents belonging to the same:

```text
DU + 8.3 filename
```

shall collapse into one result.

The result count likewise counts logical files, not extents.

---

## 12. Result Format

Each match shall be reported in compact canonical form:

```text
A0:ED.COM
B3:ED.COM
C17:ED.COM
```

The format is:

```text
DU:FILENAME
```

with:

- drive letter;
- decimal user number;
- colon;
- canonical 8.3 filename.

No space is inserted between DU and filename.

Examples:

```text
B7:FOO.COM
D12:README.TXT
```

---

## 13. Result Ordering

Results shall be emitted in deterministic namespace traversal order:

1. drive ascending;
2. user ascending;
3. native directory order within that DU.

Conceptually:

```text
A0
A1
...
A31
B0
B1
...
```

for the drives actually included in the search.

No global filename sort is required.

`/WHEREIS` shall report each logical file once, using existing DIR logical-file/extent handling where possible; implementation must remain bounded in memory. Audit the current collapsing and ordering machinery before choosing a streaming or buffering algorithm.

---

## 14. Compound Selector Ordering

A compound selector is a set, not an ordered traversal script.

For example:

```text
DIR /WHEREIS [C4,A0,B7]:FOO.COM
```

may normalize to canonical DU order:

```text
A0:FOO.COM
B7:FOO.COM
C4:FOO.COM
```

Traversal shall follow the common selector iterator's normalized order.

---

## 15. Exact Filespec Searches

An exact filespec does **not** cause `/WHEREIS` to stop at the first match.

Example:

```text
DIR /WHEREIS ED.COM
```

must search the entire selected namespace and report every logical match.

The semantic question is:

> Where are all copies of this file?

not:

> Find one copy and stop.

---

## 16. Wildcard Searches

Wildcards may produce many matches.

The implementation must remain bounded in memory and report logical files once.
Do not promise unbounded streaming until existing DIR extent handling has been
audited. Any supported capacity limit and its non-silent failure behavior must
be specified before implementation.

There is no `/WHEREIS`-specific paging mode in 1.0.

If output exceeds the visible terminal, ordinary console scrolling applies.

---

## 17. Summary

After one or more matches, print a compact count:

```text
1 MATCH
```

or:

```text
3 MATCHES
```

Example:

```text
A0:ED.COM
B3:ED.COM
D7:ED.COM
3 MATCHES
```

The count is the number of logical matching files.

---

## 18. No-Match Behavior

If no matching file exists, print:

```text
DIR: No matches found.
```

No-match is a normal completed search, not an internal error.

No ordinary DIR table or free-space summary is printed.

---

## 19. `/WHEREIS` Presentation Mode

When `/WHEREIS` is active, ordinary DIR presentation is suppressed.

Specifically, `/WHEREIS` does **not** display:

- normal multi-column directory layout;
- per-file sizes;
- attribute columns;
- free-space totals;
- ordinary DIR per-DU headings;
- ordinary `FILES, TOTAL, FREE` summary.

Instead it emits only:

```text
DU:FILENAME
...
n MATCH[ES]
```

plus substantive diagnostics. Any recoverable drive or directory failure marks
the search incomplete. After the match count or no-match message, print:

```text
Search incomplete.
```

For zero matches after a recoverable failure:

```text
DIR: No matches found.
Search incomplete.
```

A negative result must never imply exhaustive coverage after a skipped failure.

---

## 20. Interaction with Ordinary DIR Switches

`/WHEREIS` is a distinct DIR presentation/search mode.

The following ordinary transient DIR switches are **not meaningful** in `/WHEREIS` mode and should be rejected rather than silently ignored:

```text
/A
/P
/Z
/C=
/S=
```

Rationale:

- `/A` ordinary attribute display is replaced by compact location output;
- `/P` is not part of the WHEREIS contract;
- `/Z` size display is irrelevant;
- `/C=` column formatting is irrelevant;
- `/S=` sorting conflicts with canonical namespace traversal and streamed results.

Attribute **predicates inside the filespec** remain fully valid.

Example:

```text
DIR /WHEREIS *.COM[$RO]
```

is valid.

`/VER` retains the established standalone-only DIR contract: `DIR /VER` is
valid; combining it with `/WHEREIS`, operands or other switches produces the
existing invalid-usage diagnostic before searching.

---

## 21. Validation Before Search

DIR.COM shall validate the complete invocation before beginning directory traversal.

Invalid forms include:

```text
DIR /WHEREIS
DIR /WHEREIS ED.COM PIP.COM
DIR /WHEREIS /A ED.COM
```

Diagnostics should follow existing BetterCP/M DIR conventions, for example:

```text
DIR: Missing filespec.
DIR: Too many operands.
DIR: /A not valid with /WHEREIS.
DIR: Invalid selector.
DIR: Invalid filespec.
DIR: Invalid attribute expression.
```

Where the common selector parser returns an error position, use the standard BetterCP/M parser diagnostic convention.

---

## 22. Drive Errors

If an included drive cannot be examined, DIR.COM shall report the problem and continue with the remaining search set when safe.

Example:

```text
DIR: C: unavailable.
```

A recoverable unavailable-drive condition does not require an interactive Retry/Skip/Abort prompt.

`/WHEREIS` is observational and must remain naturally usable from `SUBMIT`.

---

## 23. Directory Read Errors

If a directory cannot be read reliably:

```text
DIR: B: directory read error.
```

DIR.COM shall abandon the affected drive or search unit as required by underlying BDOS semantics and continue elsewhere when safe.

A genuinely fatal internal/system error may terminate the command.

The caller's original DU must still be restored where possible.

---

## 24. Unattended Operation

`/WHEREIS` requires no user interaction.

There is no additional:

```text
/B
/Y
/Q
```

mode.

The error policy is:

- report recoverable failures;
- skip affected search areas;
- continue;
- restore caller DU;
- return.

This makes the mode suitable for `SUBMIT`.

---

## 25. No File Opening

`/WHEREIS` shall not open matched files merely to confirm them.

The directory entry itself is authoritative for this utility.

Therefore:

- file contents are not read;
- file size is not needed;
- logical byte EOF is irrelevant;
- matching files cannot affect the search by their contents.

---

## 26. No Content Search

`/WHEREIS` searches names only.

Explicitly outside scope:

```text
text search inside files
binary pattern search
grep-like behavior
regex over contents
recursive content scanning
```

A future content-oriented utility such as `SEARCH.COM` is separate.

The distinction is:

```text
DIR /WHEREIS   -> filenames/filespecs
SEARCH         -> file contents
```

---

## 27. No Mutation

`DIR /WHEREIS` is strictly read-only.

It shall never:

- create files;
- delete files;
- rename files;
- copy or move files;
- open files for write;
- change attributes;
- clear/set archive flags.

Temporary drive/user selection needed to inspect directories must be restored.

---

## 28. Examples

### Locate all copies of ED.COM

```text
A0>DIR /WHEREIS ED.COM
A0:ED.COM
B0:ED.COM
D7:ED.COM
3 MATCHES
```

### Locate all COM files on B:

```text
A0>DIR /WHEREIS B[-]:*.COM
B0:PIP.COM
B0:STAT.COM
B3:ED.COM
B7:ASM.COM
4 MATCHES
```

### Locate system COM files globally

```text
A0>DIR /WHEREIS *.COM[$SYS]
A0:CCP.COM
C0:TOOLS.COM
2 MATCHES
```

### Restrict search to selected DUs

```text
A0>DIR /WHEREIS [A0,B[3-5],C7]:FOO.*
B3:FOO.COM
C7:FOO.DOC
2 MATCHES
```

### No matches

```text
A0>DIR /WHEREIS MISSING.COM
DIR: No matches found.
```

---

## 29. Relationship to Normal DIR

Normal DIR defaults to the current DU and emphasizes directory presentation.

`DIR /WHEREIS` defaults to the searchable global namespace and emphasizes location.

Normal DIR:

```text
DIR *.COM
```

means approximately:

> Show the COM files in this selected directory context.

`DIR /WHEREIS *.COM`

means:

> Tell me every DU where matching COM files exist.

The two behaviors share the same underlying directory-selection machinery but answer different user questions.

---

## 30. Relationship to Future SEARCH.COM

A future `SEARCH.COM` may answer:

> Which files contain this text or byte pattern?

`DIR /WHEREIS` does not.

This boundary should remain firm to avoid turning DIR into a content-search utility.

---

## 31. Resident DIR

Resident `DIR` is unchanged.

It does **not** support `/WHEREIS`.

If resident DIR recognizes `/WHEREIS`, it reports exactly:

```text
DIR: Use :DIR.
```

It does not invoke a transient, search files, or change caller DU. Automatic
handoff and its policy controls remain post-1.0.

Force-transient syntax also remains available:

```text
:DIR /WHEREIS ED.COM
.DIR /WHEREIS ED.COM
```

---

## 32. Distribution

No new utility is added to the System Disk.

`/WHEREIS` is implemented inside the existing transient `DIR.COM`.

Accordingly, the previously planned standalone:

```text
WHEREIS.COM
```

is removed from the distribution manifest.

This reduces duplication while preserving the full locator behavior.

---

## 33. Design Principle

The implementation rule is:

> **`DIR /WHEREIS` is a namespace-search mode of DIR, not a second directory engine.**

It reuses the same selector, wildcard, attribute, directory-scan, and extent-collapsing machinery already present in transient DIR.COM.

The distinguishing behavior is deliberately limited to:

- global default scope;
- inclusion of `$SYS` files;
- compact `DU:FILENAME` output;
- complete result traversal;
- match counting.

That is sufficient to answer the user-facing question:

> **Where is this filespec?**

## Implementation audit and qualification — 2026-10-13

BDOS Search First/Next cannot provide the required unattended error policy:
UB_DIRLOAD calls UB_IOREAD, whose UB_IORET reads a console recovery response
and may warm boot. The implementation therefore privately links the existing
ERA public-BIOS read/snapshot adapter, excluding its write/permit routines.
No private cache addresses or new core selector are used.

Configured scope uses existing Function 181 operation 3 GETLOG for current
logical drives A–D; binding physical-drive values 0–3 are configured, while
unbound records are excluded from default global scope. An explicitly selected
unbound drive reports unavailable. Query failures mark the search incomplete.
Global enumeration queries configuration rather than probing media to discover
drive letters. Subsequent directory reads may encounter unavailable media.

One raw directory snapshot is retained per drive and reused across its selected
users. The snapshot is capped at 16 KiB, sufficient for the current 512-entry
maximum, and placed below the live TPA ceiling with a 256-byte guard. Before
reading, the utility confirms that snapshot placement leaves room above its
code and at least one 24-byte file record. Existing DT_STORE grouping collapses
selected extents into one record per logical name in native first-match order
within each DU. Collection is bounded to memory below the snapshot; overflow
reports `DIR: Directory capacity exceeded.`, emits already collected results,
and marks the search incomplete. It does not silently truncate a complete result.

No matching file is opened. Only configured-drive queries, BIOS directory
reads and console output are issued. Raw scans leave BDOS drive/user state
unchanged; completion restores BIOS drive selection and DMA to 0080h. Fatal
console warm boot follows ordinary BDOS semantics, with original BDOS DU still
intact. This does not promise recovery from every external emulator/hardware
failure or from fatal system faults.

`test_dir_whereis.py` covers inheritance, SYS/ARC, nonzero and duplicate extents,
canonical DU ordering, missing/unbound drives, directory-read failures, partial
search warnings, capacity guards and malformed invocations. Console-output
fixtures deliberately clobber loop registers, reproducing a real-platform
output bug found and corrected during qualification. Existing DIR option,
collection, sorting, attribute, column, free-space and paging tests pass.

Native ZSM4/LINK builds are compared byte-for-byte with host assembly. Physical
cpmsim and Model 4 evidence is retained in the WHEREIS qualification workspaces.
The reproducible campaign entry point is `tools/test_dir_whereis_media.py`.
Resident RCP Build 009 recognizes `/WHEREIS` and emits the agreed exact
`DIR: Use :DIR.` guidance. It also uses the concise corresponding form for
other recognized transient-only switches, without automatic dispatch.

Qualified artifact sizes: DIR Build 003 is 9,814 bytes; RCP Build 009 payload
is 7,143 bytes, allocated 7,168, with 744 relocations in the existing 1,536-byte
header. Neither CCP nor permanent system regions grow. Unloaded TPA remains
53 KiB plus one byte. RCP allocation is unchanged from Build 008.

Model 4 evidence: `/private/tmp/whereis-model4-20261013/screens.txt`; the final
campaign passes and leaves its disk unchanged. Earlier trials exposed missing
register preservation in a filename output loop and insufficient WBOOT input
settling; the loop was fixed, the fixture strengthened, and the campaign
repeated with suitable input delays. These failures were not counted as passes.

Final cpmsim evidence: `/private/tmp/whereis-final-cpmsim-20261013/transcript.txt`,
using the final 9,814-byte DIR artifact. It covers global and explicit scopes,
SYS admission, resident guidance, conflicting-option rejection and /VER. All
four attached disk images are byte-identical before and after the commands.
