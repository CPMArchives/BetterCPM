# BetterCP/M DUP.COM Engineering Specification
**BetterCP/M 1.0**
**Utility:** `DUP.COM`
**Status:** Authoritative 1.0 engineering contract

This specification consolidates the current `DUP.COM` implementation, disk-format definition contract, Montezuma Micro DUP analysis, backend capability qualification, and the committed BetterCP/M 1.0 command-line interface.

This specification documents implemented behavior. Qualification scope is
stated separately for each backend and command-line entry.

The command-line FORMAT, COPY, and CHECK entry points defined here are committed BetterCP/M 1.0 functionality. They invoke the same operation paths, validations, destructive confirmations, safeguards, and cleanup as the corresponding interactive operations.

---

## 1. Purpose

`DUP.COM` is BetterCP/M's transient physical disk utility.

It provides three operations:

```text
FORMAT   Format a disk
COPY     Copy a disk
CHECK    Check a disk for errors
```

These operations are available both:

- through DUP's interactive menu; and
- through direct command-line invocation.

DUP operates below the CP/M file level. It uses the selected logical drive's installed disk binding and BetterCP/M's public disk-control services.

DUP is not:

- a file-copy utility;
- a disk-image file utility;
- a filesystem repair utility;
- an FDB editor;
- a CONFIG replacement;
- a flux-level or archival track copier.

`CONFIG` establishes active drive bindings and separately saves startup defaults. `DISK.FDB` describes disk formats. DUP operates on installed bindings subject to the physical capabilities of the active backend.

---

# COMMAND-LINE INTERFACE

## 2. Supported invocation

BetterCP/M 1.0 supports:

```text
DUP
DUP /FORMAT drive:
DUP /COPY source: destination:
DUP /CHECK drive:
DUP /VER
```

Examples:

```text
DUP /FORMAT B:
DUP /COPY A: B:
DUP /CHECK C:
DUP /VER
```

`DUP` with no operands enters the interactive menu.

The direct forms bypass only the menu and the corresponding drive-selection prompts. They do **not** bypass:

- validation;
- physical-drive protection;
- compatibility testing;
- destructive confirmation;
- verification;
- interruption handling;
- temporary-binding restoration.

Thus command-line access is another entry path to the same operations, not a second implementation of them.

---

## 3. Command-line operation names

The operation keywords are:

```text
/FORMAT
/COPY
/CHECK
/VER
```

They are case-insensitive under normal BetterCP/M command parsing.

Only one operation may be specified in an invocation.

Examples of invalid combinations include:

```text
DUP /FORMAT B: /CHECK B:
DUP /COPY A: B: /VER
```

`/VER` remains standalone.

Unknown options or malformed operands are errors and return to the CCP without performing media operations.

---

## 4. Drive operand syntax

DUP command-line drive operands are simple logical-drive specifications:

```text
A:
B:
C:
D:
```

They are not BetterCP/M object selectors.

The following are not DUP drive operands:

```text
B7:
B[0-3]:
B:*.COM
[ A:, B: ]
```

DUP works on physical media through logical-drive bindings; CP/M user areas and file specifications are irrelevant.

---

## 5. `/FORMAT` command-line form

Syntax:

```text
DUP /FORMAT drive:
```

Example:

```text
DUP /FORMAT B:
```

The drive must be one of:

```text
A:
B:
C:
D:
```

The command-line drive replaces the interactive FORMAT drive prompt.

All normal FORMAT preflight validation is performed.

The destructive confirmation is still displayed:

```text
Insert target disk. ALL DATA ON THIS PHYSICAL DISK WILL BE LOST.
Ctrl-C stops between tracks.
Format this disk? [Y/N]
```

Only `Y` begins formatting.

There is no BetterCP/M 1.0 command-line option that suppresses this confirmation.

---

## 6. `/COPY` command-line form

Syntax:

```text
DUP /COPY source: destination:
```

Example:

```text
DUP /COPY A: B:
```

The source may be:

```text
A:
B:
C:
D:
```

The destination may be:

```text
B:
C:
D:
```

This preserves the existing interactive restrictions.

The command-line operands replace the source- and destination-drive prompts.

All normal COPY validation remains mandatory, including:

- source binding validation;
- destination binding validation;
- protected system-drive check;
- distinct-physical-drive check;
- bootstrap binding normalization;
- source/destination format comparison;
- destination backend capability validation;
- temporary-binding installation where required.

The normal destructive confirmation remains mandatory:

```text
Copy ALL sectors from X to Y? Destination contents will be erased. [Y/N]
```

Only `Y` begins the copy.

There is no BetterCP/M 1.0 force/no-confirm switch.

---

## 7. `/CHECK` command-line form

Syntax:

```text
DUP /CHECK drive:
```

Example:

```text
DUP /CHECK C:
```

The drive may be:

```text
A:
B:
C:
D:
```

The drive operand replaces the interactive CHECK drive prompt.

CHECK then enters the same read-only scan used by interactive operation C.

Because CHECK is non-destructive, no confirmation is required.

---

## 8. Command-line error behavior

A malformed command-line invocation must fail before disk work begins.

Examples include:

```text
DUP /FORMAT
DUP /FORMAT E:
DUP /COPY A:
DUP /COPY A: E:
DUP /CHECK B: C:
```

A syntax failure returns to the CCP rather than dropping into the interactive menu.

A syntactically valid operation which later fails binding or backend validation reports the same diagnostic that the corresponding interactive path would report.

Direct command-line invocation must not weaken any operation safeguard.

---

## 9. Command-line interruption and completion

Once an operation begins, command-line FORMAT, COPY, and CHECK behave identically to their interactive equivalents.

`^C` retains its existing operation-specific semantics.

At operation completion or failure, the direct command-line form returns to the CCP rather than requiring the user to navigate back through the interactive menu.

### Implementation requirement

The command-line dispatcher should enter the existing FORMAT, COPY, or CHECK operation path after supplying the already-parsed logical drive operand(s), rather than duplicating the disk-operation engine.

This minimizes code growth and prevents divergence between interactive and command-line behavior.

---

## 10. `/VER`

```text
DUP /VER
```

prints:

```text
BetterCP/M DUP 1.0 (Build 003)
```

and returns directly to the CCP.

No disk initialization or operation is performed.

This version identity is distinct from the retained legacy interactive title:

```text
BetterCP/M 2.2 Disk Utility Program version 1.14
```

The `2.2` and `1.14` in the interactive title are not the BetterCP/M utility release/build identity.

---

# INTERACTIVE INTERFACE

## 11. Interactive main menu

Running:

```text
DUP
```

displays:

```text
BetterCP/M 2.2 Disk Utility Program version 1.14

[ A ] Format a disk
[ B ] Copy a disk
[ C ] Check a disk for errors

Select [ A - C ], or BREAK (^C) to exit.
```

Selections are:

```text
A   FORMAT
B   COPY
C   CHECK
^C  Exit DUP
```

Invalid selections redisplay the menu.

Interactive operation and direct command-line operation are functionally equivalent once their required drive operands have been obtained.

---

# ARCHITECTURE

## 12. Architectural boundary

DUP distinguishes:

1. disk-format description;
2. installed logical-drive binding;
3. backend physical capability.

The format pipeline is:

```text
DISK.FDF
   |
   v
FDFCOMP
   |
   v
DISK.FDB
   |
   v
CONFIG
   |
   v
installed BIOS / drive binding
   |
   v
DUP
   |
   v
platform/backend physical capability
```

`DISK.FDB` describes a format.

The installed binding is the runtime authority.

The backend determines whether the requested physical operation can actually be performed.

Therefore:

> A valid FDB format definition does not imply that every backend can physically format or reproduce that medium.

A backend may support ordinary CP/M access to a binding while rejecting DUP's raw-format operation for that same format.

---

## 13. Runtime requirements

DUP is transient and requires approximately 51 KiB of transient memory.

If insufficient TPA is available:

```text
DUP needs 51K of transient memory.
```

DUP keeps its large working state transient, including:

- track-format stream;
- copy buffer;
- physical-sector cache;
- verification buffers;
- optional cached platform control image.

The qualified implementation preserves the BetterCP/M 53 KiB unloaded TPA target.

---

## 14. Backend access

DUP uses BetterCP/M public BIOS and disk-control interfaces.

Common DUP code must not directly depend on:

- machine-specific controller ports;
- NMI handlers;
- private hardware addresses.

Machine-specific physical operations remain behind the backend interface.

Where a backend advertises the private fast-format entry, DUP may cache the platform formatting-control image in transient memory.

Otherwise it uses the ordinary public disk-control operation.

This optimization must not change DUP's correctness semantics.

---

## 15. Logical-drive range

DUP recognizes:

```text
A:
B:
C:
D:
```

DUP obtains the installed binding without logging into the filesystem.

This allows operation on all sector payloads represented by the binding regardless of filesystem allocation state.

---

## 16. Physical system-drive protection

Physical drive 0 is protected against destructive DUP operations.

FORMAT refuses a logical binding resolving to physical drive 0:

```text
Physical drive 0 is the protected system disk.
```

COPY likewise refuses physical drive 0 as its destination.

Protection follows the physical binding rather than the logical drive letter.

The protected system medium may still be:

- a COPY source;
- a CHECK target.

---

# FORMAT

## 17. FORMAT entry

FORMAT can be entered either interactively:

```text
DUP
A
```

or directly:

```text
DUP /FORMAT B:
```

In interactive mode DUP asks:

```text
Choose logical drive [ A - D ], or ^C to return.
```

In command-line mode the supplied drive replaces that prompt.

All subsequent FORMAT semantics are identical.

---

## 18. FORMAT format selection

FORMAT uses the format already present in the selected logical drive's installed binding.

DUP does not present the FDB catalog and does not select a new persistent format.

Conceptually:

```text
CONFIG chooses active format
        |
        v
installed logical binding
        |
        v
DUP FORMAT
```

To use another format, the desired binding must first be established through the normal configuration mechanism.

---

## 19. FORMAT display

Before destructive operation, DUP identifies:

- logical drive;
- physical drive;
- current format description where available.

This applies to both interactive and command-line FORMAT.

---

## 20. FORMAT preflight validation

Before destructive confirmation DUP validates, among other things:

- logical binding exists;
- physical drive is valid;
- physical drive is not protected drive 0;
- sector-size encoding is supported;
- physical-sector count is nonzero;
- physical-sector count fits current runtime limits;
- required FDF semantics are understood;
- a complete write-track stream can be built;
- the generated stream fits supported track capacity.

Current runtime arrays permit at most 32 physical sectors per surface.

Supported sector sizes are:

```text
128
256
512
1024
```

These are DUP/backend implementation limits, not FDF language limits.

---

## 21. FORMAT confirmation

After successful validation:

```text
Insert target disk. ALL DATA ON THIS PHYSICAL DISK WILL BE LOST.
Ctrl-C stops between tracks.
Format this disk? [Y/N]
```

Only `Y` proceeds.

This confirmation is required for both:

```text
interactive FORMAT
```

and:

```text
DUP /FORMAT drive:
```

Command-line selection does not imply unattended destruction.

---

## 22. Physical geometry consumed by FORMAT

DUP uses normalized geometry from the installed binding, including as applicable:

- cylinders;
- sides;
- physical-sector count;
- sector IDs;
- uniform or mixed sector sizes;
- FM/MFM encoding;
- payload inversion;
- logical-track topology;
- side ordering;
- track-ID convention;
- sector-ID convention.

The Disk Format Definition Specification remains authoritative for those semantics.

---

## 23. FDB description versus backend capability

A format's presence in `DISK.FDB` establishes that it can be described by the BetterCP/M format model.

It does not establish that the current backend can physically generate it.

A valid binding may therefore still result in:

```text
This format is not supported by this formatter.
```

The format must not be silently approximated.

---

## 24. Track construction

DUP constructs a complete physical write-track stream in transient memory.

It emits the appropriate:

- gaps;
- synchronization fields;
- ID address marks;
- cylinder/track identifiers;
- side identifiers;
- physical sector IDs;
- size fields;
- CRC-generation tokens;
- data address marks;
- erased payload data;
- track-tail padding.

Newly formatted logical payloads correspond to CP/M erased data:

```text
E5h
```

after normal inversion handling.

---

## 25. Physical-order policy

DUP creates a compatible physical track according to the installed format definition.

It does not promise to reproduce every historical formatter's exact rotational or flux layout.

Required semantics include:

- correct sector IDs;
- correct sector sizes;
- correct encoding;
- correct topology;
- correct inversion semantics;
- correct logical contents.

Exact historical flux reproduction is outside DUP 1.0.

---

## 26. FORMAT execution order

For each physical surface:

1. build the write-track stream;
2. format the surface;
3. reread the surface;
4. compare its logical payload against expected erased `E5h`;
5. count the surface as verified;
6. proceed to the next surface.

Verification therefore occurs immediately after each surface is formatted.

---

## 27. FORMAT verification

Successful FORMAT requires:

- sectors to be readable; and
- returned payload to contain the expected erased contents.

This is stronger than the historical MM checker, which primarily verified readability.

---

## 28. FORMAT retries

The current write-track path performs bounded retry.

Up to three attempts may be made where retry is meaningful.

Write protection is not repeatedly retried.

There is no unbounded retry loop.

---

## 29. FORMAT interruption and completion

On success:

```text
Format complete.
```

DUP separately accounts for successfully formatted and verified physical surfaces.

On interruption:

```text
Format aborted. Disk is only partly formatted.
```

No interrupted FORMAT may report successful completion.

A direct `/FORMAT` invocation returns to the CCP after completion, refusal, interruption, or failure.

Interactive FORMAT returns to DUP's menu.

---

# COPY

## 30. COPY entry

COPY can be entered interactively:

```text
DUP
B
```

or directly:

```text
DUP /COPY A: B:
```

Interactive prompts are:

```text
Source logical drive [ A - D ], ^C returns.
Destination logical drive [ B - D ], ^C returns.
```

Command-line operands replace these two prompts.

The rest of COPY is identical.

---

## 31. COPY meaning

COPY duplicates:

> **all sector payloads represented by the installed source binding**

It is not file-by-file copying.

It is also not flux-level physical cloning.

---

## 32. COPY source restrictions

Source logical drives:

```text
A:
B:
C:
D:
```

The protected system disk may be a source because COPY does not write to it.

---

## 33. COPY destination restrictions

Destination logical drives:

```text
B:
C:
D:
```

The destination must:

- have a valid installed binding;
- resolve to a valid physical drive;
- not resolve to physical drive 0;
- not resolve to the same physical drive as the source.

These restrictions apply identically to interactive and `/COPY` invocation.

---

## 34. Same-physical-drive restriction

COPY requires two distinct physical drives.

If source and destination logical bindings alias the same physical drive:

```text
Source and destination must be different physical drives.
```

BetterCP/M 1.0 provides no single-drive disk-swapping COPY mode.

---

## 35. Bootstrap cylinder-binding normalization

Before comparing source and destination formats, DUP normalizes the bootstrap cylinder-based source binding when necessary.

The bootstrap binding may express one CP/M logical track as an entire physical cylinder.

DUP converts its transient COPY description to equivalent surface-track form by:

- changing the cylinder-track representation to the corresponding surface-track topology;
- halving SPT from records per cylinder to records per surface;
- doubling OFF from reserved cylinders to reserved surface tracks.

This normalization:

- does not modify source media;
- does not modify the persistent source binding;
- does not alter payload bytes.

It exists solely so COPY can compare the source with ordinary destination bindings and use the ordinary destination setter.

---

## 36. Source/destination format comparison

After normalization DUP compares source format semantics with the destination binding while preserving the destination's physical identity.

### Matching format

If they match, COPY uses the existing destination format and does not reformat each destination surface.

### Different format

If they differ:

```text
Destination format differs. Copy will format it to match the source.
```

DUP constructs a temporary destination binding combining:

- source format semantics;
- destination physical drive.

The destination backend validates this binding before destructive copying proceeds.

---

## 37. Temporary destination binding

DUP saves the original destination binding before installing a temporary source-format binding.

The temporary binding is not persistent CONFIG state.

The saved destination binding must be restored after:

- successful completion;
- declined confirmation;
- COPY failure;
- interruption;
- normal operation termination.

---

## 38. COPY confirmation

Before destructive copy:

```text
Copy ALL sectors from X to Y? Destination contents will be erased. [Y/N]
```

Only `Y` proceeds.

This confirmation is mandatory for both interactive and command-line COPY.

There is no `/FORCE`, `/YES`, or other confirmation-bypass option in BetterCP/M 1.0.

---

## 39. COPY content semantics

COPY copies all sector payloads represented by the installed source binding, including payloads corresponding to:

- reserved/system areas;
- directories;
- allocated files;
- deleted-file contents;
- unallocated space;
- other represented sectors.

DUP does not enumerate the filesystem.

---

## 40. COPY is not a flux clone

COPY does not promise preservation of physical information outside the BetterCP/M binding model, such as:

- exact historical gap placement;
- exact arbitrary rotational layout;
- deleted-data address marks;
- weak sectors;
- undocumented address marks;
- flux-transition timing;
- other controller metadata.

COPY is a whole-medium sector-payload copy within the BetterCP/M disk-format model.

---

## 41. Source-surface buffering

COPY buffers one complete source physical surface at a time.

The current buffer supports at most:

```text
64 logical 128-byte records
```

A surface requiring 65 or more records is rejected.

This limit applies even if the FDF language can validly describe the format.

---

## 42. COPY execution order

For each source surface:

1. read the complete source surface into transient memory;
2. if destination reformatting is required:
   1. build its track stream;
   2. format the destination surface;
   3. reread it;
   4. verify erased `E5h` payload;
3. write the buffered source payloads;
4. reread the destination;
5. compare destination data byte-for-byte against the buffered source;
6. proceed to the next surface.

Thus source data is safely obtained before the corresponding destination surface is destroyed.

---

## 43. COPY verification

Every written destination payload is reread and compared with source data.

A mismatch is represented by:

```text
FEh
```

and reported:

```text
Read-back data does not match.
```

Readability alone is insufficient for successful COPY.

---

## 44. COPY completion

Only after every represented source surface has been copied and byte-verified:

```text
Copy complete; destination verified.
```

If a temporary binding was used, DUP restores the destination's prior logical configuration.

If the physical media has now been reformatted to another format:

```text
Destination configuration restored. Use CONFIG for the copied format.
```

This preserves the boundary:

```text
DUP     changes media
CONFIG  applies bindings and separately saves defaults
```

A direct `/COPY` invocation returns to the CCP after cleanup.

Interactive COPY returns to DUP's menu.

---

# CHECK

## 45. CHECK entry

CHECK can be entered interactively:

```text
DUP
C
```

or directly:

```text
DUP /CHECK C:
```

Interactive mode prompts for the drive.

Command-line mode supplies it directly.

Both use the same CHECK engine.

---

## 46. CHECK is read-only

CHECK performs no writes.

It does not:

- format tracks;
- rewrite sectors;
- repair filesystem structures;
- alter directories;
- restore erased data;
- compare with a reference medium;
- require free space to contain `E5h`.

CHECK tests readability of the sector payloads represented by the installed binding.

---

## 47. CHECK behavior

CHECK traverses the complete medium represented by the selected binding.

Ordinary read failures are reported and accumulated rather than immediately terminating the scan.

---

## 48. Physical-sector error counting

When a logical-record read fails inside a larger physical sector, DUP:

1. identifies the corresponding physical sector;
2. reports the failure;
3. increments the error count once;
4. skips the remaining logical records in that failed physical sector;
5. continues with the next sector.

A failed 1024-byte sector is therefore counted once, not eight times.

The error count is a word value.

---

## 49. CHECK completion

Normal completion:

```text
Check complete. Unreadable sectors: n
```

This establishes sector readability only.

It does not establish filesystem semantic correctness.

A direct `/CHECK` invocation then returns to the CCP.

Interactive CHECK returns to DUP's menu.

---

## 50. CHECK interruption

On interruption:

```text
Check stopped. No disk contents changed.
```

CHECK is read-only.

---

# ERRORS AND INTERRUPTION

## 51. Error-location reporting

DUP reports available physical context such as:

```text
Cylinder n, side n
sector ID n
record n
error status n
```

---

## 52. Status interpretation

| Status | Meaning |
|---|---|
| `1` | Request failed or drive did not respond |
| `2` | Unsupported operation or disk address |
| `FEh` | Read-back data does not match |
| bit 7 | Drive not ready; check inserted disk |
| bit 6 | Disk is write protected |
| bit 4 | Sector/track not found; check disk format |
| bit 3 | CRC error: sector data could not be read reliably |
| bit 2 | Data transfer failed |
| otherwise | Disk I/O failed |

Status 1 remains deliberately broad because older adapters combine several failure classes.

---

## 53. Error continuation

FORMAT and COPY stop when an error makes continued destructive operation unsafe.

CHECK normally continues after ordinary unreadable-sector errors.

Backend or binding failures which make meaningful continuation impossible may terminate CHECK.

---

## 54. BREAK / `^C`

DUP recognizes BREAK / `^C`.

At interactive menus and drive prompts, it performs the indicated return or exit.

During physical operations it is polled at bounded safe points.

DUP does not attempt to cancel an already-issued backend/controller request in mid-transfer.

Command-line operations use the same interruption paths.

---

## 55. Interrupted FORMAT

```text
Format aborted. Disk is only partly formatted.
```

---

## 56. Interrupted COPY

```text
Operation stopped. Destination may be partly written.
```

The source remains unchanged.

---

## 57. Interrupted CHECK

```text
Check stopped. No disk contents changed.
```

---

# BINDING RESTORATION

## 58. Cleanup requirement

DUP must never knowingly leave a temporary COPY destination binding installed.

The common cleanup path:

1. restores the saved destination binding;
2. clears the temporary-change state;
3. resets stale drive/alias state.

This requirement applies equally to interactive and command-line COPY.

---

## 59. Restoration failure

If restoration fails:

```text
Cannot restore destination configuration. Press a key to retry.
```

DUP retains the saved binding and retries rather than claiming successful cleanup.

A command-line invocation must not simply return to the CCP while DUP knows the temporary binding remains installed.

---

## 60. Drive-state reset

After restoration, DUP performs the required system drive reset so subsequent CP/M activity observes the restored configuration.

---

# BACKEND CAPABILITY

## 61. Capability stack

An operation is supported only when all applicable layers permit it:

```text
valid FDB semantics
        +
valid installed binding
        +
DUP implementation limits
        +
backend physical capability
```

Being valid at one layer does not guarantee validity at the next.

---

## 62. Generic rejection cases

DUP may reject an operation because of:

- invalid logical binding;
- invalid physical drive;
- protected destination physical drive 0;
- source/destination physical-drive aliasing;
- unsupported required format semantics;
- unsupported sector size;
- zero physical sectors;
- excessive physical-sector count;
- track stream exceeding physical capacity;
- COPY surface exceeding transient-buffer size;
- destination backend rejecting the temporary source-format binding;
- backend lacking the requested raw-format capability.

Unsupported formats must not be silently approximated.

---

## 63. Model 4 qualified behavior

The retained Model 4 qualification covers:

- ordinary copies;
- matching-format copies;
- mixed-sector FDF copies;
- source CRC errors;
- destination write protection;
- interruption;
- temporary-binding restoration;
- source preservation;
- system-media preservation;
- return to the command environment.

Successful copies are independently compared at the physical-sector payload level and exercised through DUP CHECK.

---

## 64. z80pack qualified behavior

z80pack is qualified to FORMAT and verify a complete uniform raw image.

Its tested mixed-sector case establishes:

1. the normalized MM SUPER binding can be installed;
2. normal access to that binding is supported;
3. DUP requests raw physical formatting;
4. the backend returns unsupported;
5. the tested operation changes no target byte.

That no-modification guarantee is specifically established for the qualified z80pack mixed-sector rejection case.

This specification does not generalize it into a universal guarantee for all future backend unsupported returns.

---

## 65. FDB capability distinction

The FDB architecture distinguishes:

1. malformed format data;
2. structurally valid definitions requiring unsupported semantics;
3. supported definitions incompatible with the selected backend/hardware.

DUP preserves those distinctions.

Backend inability to format a medium does not make its FDB definition invalid.

---

# FORMAT-MODEL LIMITS

## 66. Sector payloads versus physical metadata

Throughout this specification:

> COPY means copy all sector payloads represented by the installed binding.

It does not mean:

> duplicate every physical feature present on the medium.

This distinction is normative.

---

## 67. Mixed-size sectors

BetterCP/M's normalized FDF/FDB model can represent mixed-size physical sectors.

DUP understands the current packed sector-size representation.

Backend support remains separate.

The tested Model 4 path supports the qualified mixed-sector case.

The z80pack raw formatter rejects the qualified mixed-sector case.

---

## 68. Logical-track topology

DUP uses topology from the normalized binding, including supported concepts such as:

- surface-based logical tracks;
- cylinder-based logical tracks;
- side ordering;
- side direction;
- track-ID conventions;
- sector-ID conventions.

COPY normalizes the established bootstrap cylinder representation before destination comparison.

---

# HISTORICAL MONTEZUMA MICRO RELATIONSHIP

## 69. Supporting evidence only

The Montezuma Micro DUP reverse engineering informed BetterCP/M's design but does not define BetterCP/M behavior.

---

## 70. Intentional differences

Historical MM DUP:

- contained its own Model 4 controller driver;
- used direct controller/NMI facilities;
- used MM-private physical drive structures;
- performed FORMAT verification as a later reverse pass;
- primarily checked copied-sector readability;
- formatted a destination cylinder before reading its corresponding source cylinder;
- used a one-byte bad-sector count;
- used a readable-sector probe in its destruction-warning logic.

BetterCP/M:

- puts hardware-specific operations behind a backend;
- verifies immediately after formatting;
- byte-compares copied payload;
- reads source data before destroying its corresponding destination surface;
- uses a wider error counter;
- always issues the destructive FORMAT warning.

These are deliberate BetterCP/M behaviors.

---

# PERFORMANCE

## 71. Fast-format support

A backend may advertise a private fast-format entry.

The current Model 4 implementation can cache its formatting-control image in transient storage and restore it before each write-track operation.

This removes repeated system-disk accesses from the inner formatting loop.

---

## 72. Correctness invariance

Whether DUP uses:

```text
advertised private fast-format entry
```

or:

```text
ordinary public disk-control operation
```

the visible FORMAT and verification contract remains unchanged.

---

# RELEASE QUALIFICATION

## 73. Existing automated qualification

The retained qualification includes:

```text
test_dup_operations.py copy
test_dup_operations.py same
test_dup_operations.py mixed
test_dup_operations.py bad
test_dup_operations.py protected
test_dup_operations.py abort

test_z80pack_dup_format.py
test_z80pack_dup_format.py --unsupported
```

Backend-capability closure is complete for those cases.

---

## 74. Command-line qualification required for 1.0

Release qualification must exercise direct FORMAT/COPY/CHECK entry points
as well as interactive operation. The implementation’s focused evidence is
recorded in the command-line qualification report.

At minimum:

```text
DUP /FORMAT B:
DUP /COPY A: B:
DUP /CHECK B:
DUP /VER
```

Qualification must establish that command-line entry produces the same:

- binding selection;
- validation;
- confirmation;
- media operation;
- verification;
- interruption;
- error behavior;
- temporary-binding restoration;

as the corresponding interactive operation.

Negative parser cases should include malformed/missing drives and invalid destination selection.

No duplicate disk-operation implementation should be accepted merely to provide command-line entry.

---

# BETTERCP/M 1.0 SUMMARY

## 75. Supported command forms

```text
DUP
DUP /FORMAT drive:
DUP /COPY source: destination:
DUP /CHECK drive:
DUP /VER
```

Examples:

```text
DUP /FORMAT B:
DUP /COPY A: B:
DUP /CHECK C:
DUP /VER
```

---

## 76. Interactive operations

```text
A   FORMAT
B   COPY
C   CHECK
```

Interactive and command-line forms share the same operation engine.

---

## 77. Core FORMAT contract

FORMAT:

- accepts interactive or `/FORMAT drive:` entry;
- uses the selected drive's installed binding;
- refuses protected physical drive 0;
- validates formatting capability before destruction where possible;
- always requires destructive confirmation;
- creates physical tracks according to the installed format;
- writes erased payload data;
- immediately rereads and verifies it;
- uses bounded retry;
- reports interrupted media as partly formatted.

---

## 78. Core COPY contract

COPY:

- accepts interactive or `/COPY source: destination:` entry;
- copies all sector payloads represented by the installed source binding;
- requires distinct physical source and destination drives;
- accepts A-D as source and B-D as destination;
- protects destination physical drive 0;
- preserves the source;
- normalizes the bootstrap cylinder-based binding where necessary;
- temporarily binds the destination to source format semantics when required;
- confirms before destruction;
- reads source data before overwriting the corresponding destination surface;
- rereads and byte-compares destination data;
- restores the original destination binding;
- does not persistently alter CONFIG state;
- is not a flux-level clone.

---

## 79. Core CHECK contract

CHECK:

- accepts interactive or `/CHECK drive:` entry;
- is read-only;
- scans all sector payloads represented by the binding;
- reports location and error status;
- counts failed physical sectors appropriately;
- continues after ordinary unreadable-sector failures;
- reports a final unreadable-sector count.

---

## 80. Command-line safeguard contract

Direct command-line access is a convenience and automation interface, not an unsafe shortcut.

Accordingly:

```text
DUP /FORMAT B:
```

still confirms before formatting, and:

```text
DUP /COPY A: B:
```

still confirms before erasing the destination.

BetterCP/M 1.0 defines no confirmation-bypass option.

---

## 81. Version identity

```text
DUP /VER
```

prints:

```text
BetterCP/M DUP 1.0 (Build 003)
```

The retained interactive title is:

```text
BetterCP/M 2.2 Disk Utility Program version 1.14
```

The two identities are intentionally distinct.

---

## 82. Implementation status

Interactive FORMAT/COPY/CHECK and direct `/FORMAT`, `/COPY`, and `/CHECK` are
implemented. Both interfaces share the same operation engines, validation,
confirmations and binding cleanup. Direct forms bypass selection prompts and
ordinary completion pauses, then return to the CCP. Restoration failure still
requires the existing retry interaction.

See [command-line qualification](DUP%20Command-Line%20Qualification.md) for
parser, dispatcher, media and interruption evidence. Final release
qualification remains separate.

The [2026-10-16 alignment audit](DUP%20Specification%20Alignment.md) confirms
current source alignment and records fresh focused regression evidence.

## Related utility contracts

[CONFIG](CONFIG%20Specification.md) owns binding selection and saved defaults.
[SYSGEN](SYSGEN%20Specification.md) installs the protected system while preserving
the filesystem. DUP COPY instead replaces all represented sector payloads,
including the filesystem and reserved records. Its bootstrap normalization is
only a transient COPY representation; it does not save source configuration.

## Supporting references

- [DUP format and implementation analysis](DISK-FORMAT-MM-DUP-ANALYSIS.md)
- [Backend capability closure](202%20DUP%20Backend%20Capability%20Closure.md)
- [Disk format definition specification](DISK-FORMAT-DEFINITION-SPECIFICATION.md)
- [DUP implementation](../../src/utilities/dup.mac)
- [Utility versioning](../../specifications/UTILITY-VERSIONING.md)

Additional backend capability claims require their own named qualification;
FDB representability and ordinary disk access alone do not establish them.


## Shared confirmation implementation (Build 005)

FORMAT and COPY use the shared choice-only controller through the common
one-key compatibility adapter. The original questions and operation semantics
remain unchanged: only Y/y authorizes, every other response declines. No
default, invalid-key retry, extra prompt or typeahead flush is introduced.
Menu/drive selection, cleanup, destructive-write gates and the existing 51K TPA
requirement remain unchanged. This is transient source reuse, not a new resident
service or a change to disk-control APIs.
