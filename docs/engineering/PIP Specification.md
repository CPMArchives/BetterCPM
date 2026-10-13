# PIP.COM Engineering Specification — Draft

Status: received proposal, 2026-10-13; not a completed implementation contract.
Historical claims below require verification against the pinned DRI manual,
source and binary reference. The discussion-thread citation markers have been
removed because their underlying sources were not supplied. A development-only ZSM4 implementation now provides operand parsing and the
disk-copy, concatenation and wildcard paths. Full DRI compatibility remains incomplete, and the
distribution manifest remains planned.

## Work review: remaining closure

- Source and reference binary are pinned below; pin the corresponding manual
  edition and complete behavioral comparison before freezing compatibility.
  Source reference: [DRI PIP PL/M source](https://github.com/ivop/cpm22-from-source/blob/master/src/pip.plm).
- Build policy: Z80 assembly with ZSM4, consistent with ED; no production PL/M
  compiler dependency. Native/cross parity is established for the first foundation.
- Audit actual temporary-file, verification, replacement and abort sequencing;
  define existing .$$$ collisions, source/destination identity, and close/delete/
  rename failures. Do not infer power-loss atomicity from use of a temporary.
- Freeze PIP wildcard behavior against the DRI reference. Do not silently impose
  the newer COPY wildcard restrictions on valid historical PIP invocations.
- ARC policy is settled: retain DRI behavior for now. Audit and port the pinned
  source's actual attribute operations without adding modernized ARC behavior.
- Retain the original INP/OUT patch-page layout as the implementation
  compatibility default; qualify actual driver calls when device transfers are
  implemented. This default can be revised by the maintainer before closure.
- Audit physical aliases and IOBYTE routing on both platforms. The roadmap
  already identifies IOBYTE compatibility as an unfinished 1.0 requirement.
  A documented unavailable device may fail; an implemented alias must route
  correctly and restore temporary assignments.
- Specify captured DU inheritance across concatenated operands and interactive
  commands, normal/error return cleanup, and explicit fatal-WBOOT exceptions.
- Qualify SUBMIT cancellation against BetterCP/M's actual queue conventions;
  do not assume the historical transient cancellation mechanism is sufficient.

## Implementation decisions and first increment — 2026-10-13

- Retain historical destination-first assignment and comma-separated sources;
  the proposed `PIP SOURCE DEST` shorthand was withdrawn by the maintainer.
- Use Z80 assembly with native ZSM4/LINK parity. The PL/M source is a behavioral
  reference and introduces no production PL/M compiler dependency.
- Maintainer decision: retain DRI attribute behavior for now. Do not introduce
  automatic ARC marking, preservation enhancements, or backup switches beyond
  what the pinned reference actually does.
- Pinned source and binary identity: DRI PIP 1.5, with exact hashes and repository
  revisions in `third_party/dri-pip/provenance.json`. The source already accepts
  G0 through G31; BetterCP/M makes all those users available rather than changing
  this source check. The matching binary/manual qualification remains explicit.
- Preserve historical `_` left-arrow assignment as an alias for `=`, as found
  in this source. This is not the withdrawn source-first syntax.
- Source verification happens per written group before final destination
  installation; final close/delete/rename sequencing follows CLOSEDEST.
  SETUPDEST removes a prior same-stem .$$$ file before creating a new one.
  Source compatibility tests and explicit failure-safety rules must cover these
  operations rather than assuming temporary-file use is globally atomic.
- The implementation keeps the original INP/OUT patch layout as a conservative
  compatibility default (the maintainer has not yet answered that separate
  preference question). The development foundation reserves the source layout: INP 0103h, OUT 0106h, data 0109h,
  reserved space through 01FFh. No device transfer is implemented yet.
- ERROR cancels a historical .SUB queue in the captured user; the BetterCP/M
  port must implement the equivalent against its authoritative A0 submit queue,
  not accidentally remove a same-named unrelated source-user file.

`tools/build_pip.py` writes only `build/pip-development/PIP.COM`. It provides
standalone /VER, a nonmutating interactive `*` loop, and assignment/source-span
framing that respects bracket parameters and S/Q strings delimited by 1Ah.
/VER recognition ignores occurrences inside parameter strings. The framing
scanner can represent the full 127-byte command-tail limit, including 64
minimal operand spans, and leaves input unchanged on success and failure.

Build 003 supports the exact disk-copy subset described below. Unsupported
transfer forms still report an explicit development-only diagnostic. It is not
installed on distribution disks. The initial 1,570-byte foundation qualified
only framing and identity; later increments have separate qualification below.

The received draft follows; remaining historical/provenance details are not
closed merely by implementing command framing.


## 1. Purpose

`PIP.COM` is BetterCP/M's implementation of the Digital Research **Peripheral Interchange Program**.

Its primary compatibility target is **DRI CP/M 2.2 PIP**.

BetterCP/M PIP shall reproduce DRI PIP's documented behavior, including:

- disk-to-disk file copying;
- wildcard multiple-file copying;
- file renaming while copying;
- concatenation of multiple sources;
- console, reader, punch, list, and supported physical-device transfers;
- PIP's special pseudo-devices;
- text-transfer transformations;
- Intel HEX handling;
- verification;
- SYS-file access;
- RO overwrite behavior;
- interactive multi-command mode.

BetterCP/M adds:

- native `DU:` addressing;
- user areas `0..31`;
- `/VER`.

Additional PPIP-derived features may be adopted only after explicit review.

---

## 2. Compatibility Principle

The baseline rule is:

> A valid DRI CP/M 2.2 PIP command should have the same meaning under BetterCP/M PIP unless BetterCP/M documentation explicitly identifies an extension.

DRI syntax shall not be replaced by a more modern syntax merely because another BetterCP/M utility uses one.

In particular, historical PIP bracket parameters remain supported.

---

## 3. Invocation Modes

DRI's two invocation styles are retained.

### 3.1 Interactive mode

```text
PIP
```

PIP enters its command interpreter and prompts:

```text
*
```

Each entered transfer command is executed independently.

An empty line exits PIP.

This behavior is part of historical PIP and must remain available.

### 3.2 Single-command mode

```text
PIP destination=source
```

The supplied operation executes and PIP returns to the CCP.

---

## 4. Core Assignment Syntax

Historical form:

```text
destination=source1,source2,...,sourceN
```

Examples:

```text
PIP B:=A:*.COM
PIP B:NEW.ASM=A:OLD.ASM
PIP BIG.TXT=PART1.TXT,PART2.TXT,PART3.TXT
PIP LST:=REPORT.TXT
```

Concatenation proceeds from left to right.

DRI PIP supports both files and devices in the source list.

---

# 5. BetterCP/M DU: Extension

Any **disk-file operand** may carry a BetterCP/M DU.

Examples:

```text
PIP B3:FOO.COM=A7:FOO.COM
PIP C0:=B12:*.COM
PIP A5:BIG.TXT=B2:ONE.TXT,C7:TWO.TXT
```

A DU selects exactly one drive/user location.

PIP does **not** acquire the multi-DU object-selector semantics of DIR/COPY. Forms such as:

```text
B[-]:
[A0,B3,C7]:
```

are not part of PIP 1.0 unless separately specified.

This keeps PIP's historical one-source-location-per-filespec model intact.

---

## 5.1 User-Only DU

If BetterCP/M's ordinary DU grammar permits user-only notation:

```text
5:FOO.TXT
```

PIP should accept it for disk files, meaning current drive/user 5.

---

## 5.2 Device Names Take Precedence

Names ending in `:` that match PIP device names remain devices, not DUs.

For example:

```text
CON:
RDR:
PUN:
LST:
PRN:
NUL:
EOF:
INP:
OUT:
```

retain their PIP meanings.

There is no ambiguity with ordinary `B3:`-style DU syntax.

---

# 6. Historical `[Gn]` Compatibility

DRI's `[Gn]` user-area parameter shall remain supported for compatibility.

Historically, CP/M 2.x PIP used `Gn` to obtain a source from another user area; later PIP variants expanded user-number handling further.

BetterCP/M shall extend valid user numbers to:

```text
0..31
```

Where both an explicit DU and `[Gn]` attempt to specify the same operand's user area, the invocation should be rejected as contradictory rather than silently choosing one.

Example:

```text
PIP B3:FOO.COM=A7:FOO.COM[G2]
```

→ invalid: source user specified twice.

Native DU notation is the preferred BetterCP/M form; `[Gn]` remains for PIP compatibility.

---

# 7. Wildcard Copy

Historical wildcard operation is retained:

```text
PIP B:=A:*.COM
```

Each matching logical file is copied under its existing filename.

PIP shall retain the DRI restrictions concerning inappropriate wildcard destination forms and source/destination identity.

SYS files remain excluded unless the historical `R` parameter is specified.

---

# 8. Destination Safety and Temporary File

Disk-file output shall preserve the DRI transactional model.

PIP writes a temporary destination using type:

```text
$$$
```

and only installs the final destination after successful completion.

The historical documentation describes the temporary file as protection against losing an existing destination if the copy fails.

Where an existing destination must be replaced:

1. construct the new `.$$$` file;
2. complete the transfer successfully;
3. perform verification if requested;
4. remove/replace the old destination according to PIP rules;
5. rename the temporary file to the final name.

An aborted or failed transfer must not leave a partially copied file under the intended destination name.

---

# 9. Attributes

PIP shall reproduce DRI handling of:

- `RO/RW`;
- `SYS/DIR`.

When SYS files are copied under the `R` parameter, their attributes are preserved as DRI specifies.

BetterCP/M's `$RO/$SYS/...` selector language is **not** added to PIP merely because other BetterCP/M utilities support it. PIP retains its own historical option model.

---

# 10. Read-Only Destination

Without `W`, attempting to replace an RO destination shall reproduce the DRI confirmation behavior.

Historical prompt:

```text
DESTINATION FILE IS R/O, DELETE (Y/N)?
```

A negative response skips replacement.

`W` permits overwrite without that exchange.

Exact wording should follow the selected DRI PIP reference unless BetterCP/M has a project-wide compatibility reason to normalize diagnostics.

---

# 11. Devices

PIP shall retain the historical CP/M logical devices where the BetterCP/M BIOS supports them:

```text
CON:
RDR:
PUN:
LST:
```

and physical names supported through the historical CP/M device mapping where applicable, including such names as:

```text
TTY:
CRT:
UC1:
PTR:
UR1:
UR2:
PTP:
UP1:
UP2:
LPT:
UL1:
```

The precise availability of physical device aliases depends on BetterCP/M's BIOS/device implementation.

Unsupported physical devices shall fail cleanly; PIP shall not fake devices that the BIOS cannot supply.

The DRI manual explicitly treats device interchange as part of PIP's purpose.

---

# 12. PIP Pseudo-Devices

Historical PIP pseudo-devices shall be reproduced where applicable.

### `NUL:`

Outputs 40 NUL bytes.

### `EOF:`

Outputs CP/M text EOF (`1Ah`).

### `PRN:`

Equivalent to list output with the historical default formatting options:

```text
N T8 P60
```

### `INP:` / `OUT:`

DRI PIP exposed patchable hooks at fixed addresses for custom character devices.

Whether BetterCP/M reproduces the **exact historical patch addresses** needs an implementation review. If binary compatibility with patched PIP installations is part of the requirement, those addresses become normative; otherwise the user-visible device semantics can be preserved without promising identical internal patch layout.

I would flag this for Work rather than guess.

---

# 13. ASCII vs. Object Transfers

PIP retains DRI's distinction between character and object transfers.

COM files are treated as non-ASCII/object data automatically.

For normal ASCII transfers, `1Ah` is the CP/M EOF convention and PIP appends appropriate EOF output.

The `O` parameter forces object transfer and prevents `1Ah` from terminating the data stream.

---

# 14. Historical PIP Parameters

BetterCP/M shall reproduce the CP/M 2.2 parameter set.

| Parameter | Meaning |
|---|---|
| `B` | Block-mode input buffering |
| `Dn` | Delete characters beyond column n |
| `E` | Echo transfer to console |
| `F` | Filter form feeds |
| `Gn` | Get from user n |
| `H` | Validate/process Intel HEX |
| `I` | Ignore `:00` HEX records; implies H |
| `L` | Uppercase → lowercase |
| `N` / `N2` | Add line numbers |
| `O` | Object/non-ASCII transfer |
| `Pn` | Insert page ejects |
| `Qs` | Quit at string s |
| `R` | Read SYS files |
| `Ss` | Start at string s |
| `Tn` | Expand tabs |
| `U` | Lowercase → uppercase |
| `V` | Verify destination |
| `W` | Overwrite RO destination without interrogation |
| `Z` | Clear parity/high bit on ASCII input |

These meanings come from the DRI CP/M 2.2 PIP table.

---

# 15. Option Placement

Historical PIP parameters remain attached to the affected source or device:

```text
PIP X.ASM=B:X.ASM[V]
PIP LST:=X.ASM[NT8U]
PIP ED.COM=B:ED.COM[R]
```

Multiple parameters may be placed within the brackets according to DRI syntax.

BetterCP/M slash switches shall **not** replace these parameters.

---

# 16. `S` and `Q` Extraction

Historical start/quit-string extraction remains supported.

Conceptually:

```text
PIP OUT.TXT=SOURCE.TXT[Sstart-string^ZQend-string^Z]
```

The start and quit strings themselves are included in the output, matching DRI behavior.

This is one area where a direct implementation from DRI source, if available, would be preferable to reinterpreting the manual.

---

# 17. Intel HEX Handling

`H` shall reproduce DRI Intel HEX validation/transfer behavior.

`I` implies `H` and ignores termination `:00` records as documented.

PIP's special behavior when receiving HEX from peripheral input should be preserved to the extent the corresponding BetterCP/M input device exists.

Do not silently simplify this into ordinary text copying while still claiming DRI PIP compatibility.

---

# 18. Verification

Historical:

```text
[V]
```

verifies a disk destination by rereading data after writing.

This must remain DRI-compatible.

A BetterCP/M implementation may optimize internally, but `[V]` must not silently change meaning into a CRC-only comparison.

---

# 19. Abort Behavior

DRI PIP allows an active operation to be aborted from the keyboard and reports:

```text
ABORTED
```

It also cancels pending SUBMIT commands after an aborted/error operation.

BetterCP/M should reproduce that behavior unless the project's current SUBMIT architecture requires a documented equivalent mechanism.

The exact abort key semantics should be taken from the selected DRI implementation rather than generalized from modern utility conventions.

---

# 20. Interactive PIP Command Loop

When invoked without a command tail:

```text
PIP
*
```

PIP repeatedly accepts transfer commands.

An empty command returns to CCP.

Errors in one interactive command should return to the `*` prompt where DRI does so rather than terminate PIP unnecessarily.

This interactive personality is an important part of PIP compatibility and shall not be omitted just because BetterCP/M users can execute separate command lines.

---

# 21. `/VER`

BetterCP/M extension:

```text
PIP /VER
```

prints:

```text
BetterCP/M PIP 1.0 (Build nnn)
```

and exits.

`/VER` is standalone-only.

It is not a PIP transfer parameter and is invalid when combined with a transfer command.

For example:

```text
PIP /VER
```

valid.

```text
PIP B:=A:*.COM /VER
```

invalid usage.

---

# 22. DU Preservation

PIP shall capture the caller's DU before execution.

Temporary switching required to access source/destination user areas must not accidentally change the caller's user/drive context unless historical PIP explicitly defines a final drive change for that operation.

For ordinary BetterCP/M DU-enhanced copying, the caller's DU should be restored after completion.

If DRI PIP has documented exceptions, those should be preserved and called out individually.

---

# 23. Error Compatibility

Where practical, DRI PIP diagnostics should be retained, particularly for behavioral conditions that scripts or experienced users may recognize.

Examples historically include:

```text
INVALID USER NUMBER
START NOT FOUND
SOURCE FILE INCOMPLETE
UNEXPECTED END OF HEX FILE
DESTINATION FILE IS R/O, DELETE (Y/N)?
ABORTED
```

The selected DRI reference version should be recorded in the engineering provenance, just as we decided for ED.

---

# 24. Provenance Requirement

Before implementation is frozen, the engineering specification shall identify:

- exact DRI PIP version/release used as baseline;
- corresponding CP/M release;
- primary manual edition;
- source code revision if DRI source is available;
- original `PIP.COM` binary used for behavioral comparison;
- known differences among PIP revisions.

We should avoid accidentally combining CP/M 2.2 behavior with later CP/M 3 or Concurrent CP/M additions.

---

# 25. Review of PPIP and Replacement Utilities

PPIP is particularly relevant because it was designed as a practical PIP replacement and remained close enough to PIP syntax to substitute for it in existing workflows. The surviving v1.8 lineage adds cross-user convenience, verification, move, and overwrite controls.

Its modern reimplementation documents these useful ideas:

```text
/V   CRC-16 verify
/C   display CRC after verification
/E   overwrite existing RW destination without asking
/W   overwrite even RO destination
/M   move: copy, verify, then delete source
```


But we should **not simply adopt those letters**, because several collide conceptually or syntactically with historical PIP.

For example, DRI PIP already has:

```text
[E]  echo
[V]  verify
[W]  overwrite RO
```

So PPIP's slash switches can coexist syntactically, but using the same letters for subtly different meanings creates cognitive traps.

---

# 26. Candidate BetterCP/M Extensions from PPIP

I see three PPIP ideas worth serious consideration.

### 26.1 Move

PPIP's move operation:

> copy successfully, verify, then delete source

is useful.

However, BetterCP/M already has/will have explicit `MOVE` semantics through the COPY family, so adding move to PIP may duplicate functionality rather than fill a gap.

**Recommendation: do not add for PIP 1.0.**

Keep PIP focused on DRI interchange semantics.

---

### 26.2 CRC reporting

PPIP can calculate and display a CRC after verification.

That could be useful for removable media and serial/peripheral transfers.

But it is not DRI PIP behavior, and BetterCP/M `[V]` must retain DRI reread/compare semantics.

Potential future extension:

```text
/CRC
```

rather than stealing or redefining `[V]`.

**Recommendation: potentially useful, but defer unless we identify a concrete workflow requiring it.**

---

### 26.3 Explicit overwrite policy

PPIP distinguishes:

- overwrite ordinary existing destination;
- overwrite RO destination.

DRI PIP already has a well-established RO policy through `[W]`, and its ordinary destination replacement behavior is part of the compatibility contract.

Adding another overwrite model risks complicating a utility whose syntax is already dense.

**Recommendation: retain DRI behavior for 1.0.**

---

# 27. Other PPIP Ideas Not Suitable for Core PIP

Modern CPPIP variants add special namespaces such as:

```text
IA:
SD:
NX:
```

for particular hardware/network storage systems.

Those are excellent examples of what an extensible PIP-like utility can do, but they should **not** enter BetterCP/M's generic PIP specification.

If BetterCP/M later gains pluggable storage namespaces, that deserves an architectural design rather than hard-coded special cases in PIP.

---

# 28. Recommended BetterCP/M 1.0 Scope

My recommendation is deliberately conservative:

### Required

- complete DRI CP/M 2.2 PIP behavioral clone;
- interactive `*` mode;
- disk/device transfers;
- concatenation;
- all documented PIP parameters;
- SYS/RO handling;
- temporary-file safety;
- Intel HEX semantics;
- DRI verification;
- native BetterCP/M `DU:` addressing;
- users 0–31;
- `/VER`.

### Do not add yet

- `/M` move;
- CRC options;
- new overwrite modes;
- hardware-specific pseudo-drives;
- selector sets/ranges;
- BetterCP/M attribute-expression syntax;
- COPY-style collision UI.

That gives PIP a very clear identity:

> **DRI PIP, but it understands BetterCP/M's drive/user namespace.**

That is probably the strongest 1.0 design. PPIP should inform our implementation and later enhancements, but I don't yet see a PPIP extension compelling enough to justify muddying the compatibility clone.

## Operand-parser increment — Build 002

The development build now parses each disk/file/device operand and retains a
bounded array of 80-byte descriptors before any transfer work. There are up to
64 descriptors, the maximum possible number of minimal operands in a 127-byte
command tail; this is not a new command-length restriction. Each descriptor
contains operand kind, device code, drive/user, wildcard and explicit-user
flags, a 36-byte FCB, the historical 26-byte parameter array, and S/Q extraction
string spans. It contains no live disk pointers or resident private addresses.

Disk qualifiers support A–P plus conventional one/two-digit users 0–31, including
leading zeros and user-only notation. Unspecified drive/user independently
inherit the captured caller DU. A bare drive retains caller user. Actual
configured-drive execution checks belong to the later transfer engine. Device
names take precedence over DU interpretation; the pinned 21-name PIP 1.5 table
is retained. Recognition does not claim physical availability or emulate the
IRD hardware reader on unsupported machines.

Native users must be in range and no more than two digits. [G] is accepted
through 31, defaults to 1 without digits like the source, and rejects an explicit
DU-user conflict even when the values agree. Repeated historical [G] parameters
without a DU user retain last-value behavior. Other numeric parameter values
use the reference's byte arithmetic. S/Q spans can contain spaces, commas,
equals signs and brackets; their 1Ah terminators are required. Parameter
execution/transformation remains unimplemented.

PIP wildcard fields follow the reference scanner: star fills the remainder
of a field with question marks; characters after a filled field are invalid.
This deliberately does not import COPY's repeated-star normalization or its
selector/predicate grammar. File names and device keywords are case folded
without modifying the caller's input buffer.

Command-plan checks reject wildcard file destinations, file-destination
parameters, invalid source/sink device directions, wildcard sources outside
the single-source destination-drive form, and concatenation to a bare drive.
DEST=DRIVE: inherits DEST's exact name for the source, retaining the source DU
and parameters. File identity, temporary-name collisions, attributes and other
I/O safety checks remain prerequisites for the transfer engine.

The 7,758-byte Build 002 development artifact is byte-identical under native
ZSM4/LINK. Operand, framing, extraction, interactive and pure-version fixtures
pass; shared identity checks pass. No file I/O is implemented or invoked, and
the system-disk manifest still marks PIP planned. A validated command continues
to print the explicit development-only message. The next increment is the
transactional disk transfer path and its failure/cleanup qualification.


## Exact disk-copy increment — Build 003

The development implementation copies one exact disk source to one named file
or a single destination DU, using source parameters G, O, R, V and W. Devices,
concatenation, wildcard expansion and other transformations remain unsupported;
they are rejected before file I/O. Execution currently uses configured A–D
drives. This is a staged implementation, not release-ready PIP.

The DRI fast path copies complete 128-byte records, including bytes after 1Ah,
and preserves the source FCB unused-byte field in the destination. Source
attributes remain unchanged; newly created destinations are writable ordinary
files with ARC clear, matching the reference for this path. SYS sources require
R. V rereads and compares copied records. W authorizes replacement of a
read-only destination; otherwise the DRI Y/N prompt is used.

Copies use a .$$$ staging file. The old destination survives transfer,
verification and successful staging close. Self-copy and staging-name conflicts
are rejected before file I/O. A protected preexisting staging file is retained
and reported as an error. This guard is deliberately stricter than DRI's
unconditional staging deletion.

Replacement deletes the old destination before renaming the staging file, as
in DRI PIP; this is not an atomic replacement or power-loss guarantee. If rename
fails, the completed staging file is retained. Recoverable transfer failures
attempt staging cleanup and restore the caller DU and default DMA. Fatal BDOS
errors and interrupted cleanup remain to be qualified. Later increments below
add staging-deletion reporting and SUBMIT cancellation.

Fixtures cover multi-extent data, verification, RO authorization, staging
protection, DU restoration and injected read/write/verify/make/close/delete/
rename failures. A real cpmsim campaign compared a multi-extent SYS source
copied with RV against the pinned DRI PIP 1.5 binary: extracted source and both
outputs match byte for byte, including the partial final record and trailing
data after 1Ah. Model 4 transfer qualification remains pending.


## Cleanup-reporting increment — Build 004

If removal of a staging file fails during recoverable error cleanup, PIP emits
`CLEANUP FAILED: temporary file remains.` after the original error. It still
restores the caller DU and default DMA. The staging file is available for
inspection or manual removal; its presence does not imply a complete copy.
A fixture injects both a source read failure and a staging deletion failure,
checking that the old destination and source survive and both errors appear.
This increment closes staging-deletion reporting only; Build 005 below adds
SUBMIT cancellation. Fatal BDOS errors remain pending.

## Error/SUBMIT increment — Build 005

Following DRI PIP's error policy, ordinary parser errors, unsupported transfer
forms, preflight failures and recoverable transfer errors cancel the pending
SUBMIT stream. BetterCP/M's queue is specifically `A0:$$$.SUB`; PIP does not
delete same-named files in the caller's or source/destination user areas.
Operand/preflight failures still perform no transfer-file mutation, but may
inspect and remove the command queue. Successful transfers and standalone
`/VER` leave the queue intact; `/VER` remains pure console output.

Cancellation preserves the operation's current DU before its ordinary cleanup
restores the invocation's caller DU and DMA. An absent queue requires no delete.
A read-only queue, read-only A drive or reported deletion failure produces
`CANNOT CANCEL SUBMIT QUEUE`. PIP does not clear queue protection or claim that
the batch stopped if deletion failed. Fatal directory/media errors remain
subject to the existing BDOS paths, not this recoverable-error policy.

Fixtures cover parser/preflight/transfer cancellation, success and `/VER`,
protected queues, drive protection, failed deletion and DU restoration.
`tools/test_pip_submit_media.py` qualifies the real cpmsim SUBMIT path: a batch
switches to A7, invokes invalid PIP syntax, and never reaches its next copy.
The A0 queue is removed, an unrelated A7 same-named file is unchanged, and the
prompt remains A7. Native ZSM4/LINK matches the 9,596-byte development artifact.


## Exact disk concatenation — Build 006

The development port now accepts a named destination and two or more exact disk
sources, each with independent DU inheritance and G/O/R/V/W parameters. All
source operand kinds, supported parameters, configured-drive bounds and
destination/staging aliases are checked before transfer I/O. Wildcards, devices
and transformations remain unsupported. Later source-open/read failures clean
up the staging file and leave the old destination intact.

Concatenation follows DRI's character path: text sources stop at the first 1Ah;
.COM sources and sources with O contribute complete disk records, including
1Ah and physical padding. High-bit data bytes are retained. A partial output
record is padded with 1Ah, with DRI's unused-byte field set on close. Empty
sources, exact record boundaries and multiple extents are supported. The
standalone single-source fast path remains unchanged.

The shared writer verifies each emitted record when the current source has V.
A record crossing a source boundary uses the source active when that record is
written. Final RO replacement authorization uses W from the last source, as
in the reference close path. The 128-byte output buffer is intentionally small;
matching DRI's larger-buffer verification cadence and character-path console
interruption handling remain qualification/implementation work. No new ARC
policy is introduced.

Fixtures cover mixed DUs, text/object sources, empty inputs, binary bytes,
partial/full records, multi-extents, SYS admission, late missing sources,
staging conflicts, unsupported late options, verification failures and RO
replacement. The real cpmsim campaign in `tools/test_pip_concat_media.py`
compares mixed-user multi-extent text concatenation and COM/text concatenation
with the pinned DRI binary. Both ordinary cpmtools extraction and complete
physical record data match. For the latter inspection only, S1 is cleared on a
separate image copy because cpmtools treats it as used bytes whereas the DRI
character path stores unused bytes; the executed disk is not changed by this
normalization. Native ZSM4/LINK matches the 10,244-byte development artifact.
Model 4 transfer qualification and full PIP completion remain pending.


## Wildcard disk copying — Build 007

A single wildcard disk source now copies matching logical files to a destination
DU, using G/O/R/V/W. Same-DU wildcard copies are rejected before enumeration,
as in DRI PIP. Unsupported transformations are rejected before transfer I/O.
The directory search restarts after each transaction and skips the previously
visited entries, avoiding dependence on search state surviving file operations.
The scan is bounded by the configured directory; no list proportional to the
number of matched files is retained.

The scan uses an all-extent pattern and the selected disk's DPB extent mask to
choose each logical file's first extent group. This is necessary on BetterCP/M
media with EXM nonzero: a literal extent-zero Search First currently omits
files whose first grouped directory entry has EX=1. The pinned DRI PIP binary
exhibits that omission on the same media. This implementation avoids the
omission locally; the underlying BDOS Search First extent-group compatibility
issue remains a separate qualification finding. No BDOS code or allocation
changes are included in this increment.

SYS sources require R; RO sources may be read. Matching names are printed under
`COPYING -`; no admitted match reports `NOT FOUND` and cancels SUBMIT. A
recoverable file-copy failure stops the wildcard invocation. The current development wildcard path preserves ARC and clears RO/SYS.
This attribute handling is not yet a qualified DRI compatibility result: the
original DRI BDOS rename routine copies the complete new name/type bytes,
including their attribute bits, whereas BetterCP/M rename retains the old
directory attribute bits. PIP must account for that difference before this
increment is considered complete.

Fixtures cover restarted scans, SYS/RO/ARC selection, multi-extent data, no
matches, same-DU rejection, verification and replacement failures. Native
ZSM4/LINK matches the 10,974-byte development artifact. The real cpmsim wildcard campaign passes for complete record data,
SYS/RO admission, ARC preservation and a larger file whose first grouped
extent has EX=1. These attribute expectations follow the pinned DRI source.
The optional `--reference` campaign currently times out after the stock DRI
binary reports its final small file; no successful live wildcard binary
equivalence claim is made. That separate BetterCP/M/reference compatibility
finding still needs diagnosis. This staged increment is not a distribution
utility.


### Wildcard compatibility investigation — 2026-10-13

The reference timeout reproduces on an independently rebuilt current system
disk, with RCP loaded and unloaded. A saved cpmsim core places execution in the
command-environment reloader's hard-failure loop after the last copy; it is not
an active PIP copy loop. The loader workspace still contains the final record
of PIPREF.COM when reconstruction fails. This observation does not establish
the underlying corruption or failed-I/O cause.

Changing DMA and exhausting a directory search in small transient probes both
return normally, including from A6. The reference wildcard campaign returns
normally when ARC is cleared on the seeded sources while RO/SYS are retained.
Retaining ARC while clearing RO/SYS reproduces the failure. The repeatable
control is `tools/test_pip_wildcard_media.py --reference --clear-source-arc`;
without the latter option the ARC-dependent reload failure remains unresolved.

The original DRI BDOS source at the same pinned upstream revision,
`src/bdos.ASM`, implements rename through `copy$dir` with the twelve-byte new
user/name/type portion. BetterCP/M's `UB_RNCOPY` retains each existing attribute
bit and masks the incoming name byte. Consequently, confirming the intended
DRI PIP wildcard attributes requires accounting for this ABI behavior rather
than inferring the final attributes solely from temporary-file creation. No
BDOS, BIOS or reloader production changes were made during this investigation.
The wildcard increment remains in development pending attribute closure and
diagnosis of the reference's ARC-dependent warm-return failure.
