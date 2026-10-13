# PIP.COM Engineering Specification — Draft

Status: received proposal, 2026-10-13; not a completed implementation contract.
Historical claims below require verification against the pinned DRI manual,
source and binary reference. The discussion-thread citation markers have been
removed because their underlying sources were not supplied. A development-only ZSM4 parser foundation is now present; the transfer engine
is not implemented and the distribution manifest remains planned.

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
- Close the INP/OUT patch-address compatibility choice. Distinguish user-visible
  device behavior from binary patch-layout compatibility.
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
- The INP/OUT patch-layout decision remains open. The development foundation
  provisionally reserves the source layout: INP 0103h, OUT 0106h, data 0109h,
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

It is not a working file/device interchange utility: operand grammar, DU
encoding, parameter semantics and transfer operations are still to be ported.
Valid framed commands explicitly report that the transfer engine is not
implemented. It is not installed on distribution disks. Initial parser/version fixtures and native ZSM4/LINK parity pass for the
1,570-byte foundation. The shared identity tests also cover its isolated
development path. These checks qualify only the foundation, not PIP transfers.

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