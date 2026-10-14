# BetterCP/M DUP.COM Engineering Specification
**BetterCP/M 1.0 — Consolidated Engineering Specification**  
**Status:** Documentation consolidation of existing implementation and qualified behavior.  
**Utility:** `DUP.COM`  
**Current implementation title:** `BetterCP/M 2.2 Disk Utility Program version 1.14`

This specification consolidates the current `DUP.COM` implementation, disk-format definition contract, Montezuma Micro DUP analysis, and backend qualification results. It does not redesign DUP or introduce new 1.0 functionality.

Where this specification labels behavior **Implemented**, it is present in the current `dup.mac`. Where it labels behavior **Qualified**, the cited backend qualification has exercised that behavior. Additional backend claims require separate qualification; observed behavior is not generalized beyond the cited evidence.

---

# 1. Purpose

`DUP.COM` is BetterCP/M's transient physical disk utility.

It provides three operations:

```text
A   Format a disk
B   Copy a disk
C   Check a disk for errors
```

DUP operates below the CP/M file level. It uses the selected logical drive's installed disk binding and BetterCP/M's public disk-control services to operate on the physical geometry and sector payloads represented by installed bindings.

DUP is deliberately not:

- a file copier;
- a disk-image file utility;
- an FDB editor;
- a disk-format catalog editor;
- a filesystem repair utility;
- a general disk-configuration utility.

`CONFIG` remains responsible for persistent drive bindings. `DISK.FDB` describes disk formats. DUP consumes those bindings and backend capabilities to perform physical operations.

---

# 2. Architectural boundary

DUP separates three concepts that must not be conflated:

1. **Disk-format description**
2. **Installed logical-drive binding**
3. **Backend physical capability**

A format's presence in `DISK.FDB` means that BetterCP/M can describe that format. It does **not** mean that every platform backend can physically format, copy, or otherwise reproduce that medium.

The format pipeline is:

```text
DISK.FDF -> FDFCOMP -> DISK.FDB -> CONFIG -> installed drive binding
                                                |
                                                v
                                              DUP
                                                |
                                                v
                                      platform/backend capability
```

The FDB supplies normalized disk-format information. The installed binding is the runtime authority. The backend determines whether a requested physical operation can actually be performed.

Accordingly:

> A structurally valid FDB definition is not a guarantee of formatter support.

A backend may support ordinary CP/M access to a binding while rejecting DUP's raw format operation for that same binding.

This distinction is already qualified on z80pack.

---

# 3. Invocation

## 3.1 Normal operation

DUP is primarily interactive.

```text
DUP
```

displays its title and main menu:

```text
BetterCP/M 2.2 Disk Utility Program version 1.14

[ A ] Format a disk
[ B ] Copy a disk
[ C ] Check a disk for errors

Select [ A - C ], or BREAK (^C) to exit.
```

There is no established BetterCP/M 1.0 command-line syntax for directly requesting FORMAT, COPY, or CHECK.

Forms such as:

```text
DUP A: B:
DUP /FORMAT B:
DUP /CHECK C:
```

are therefore **not part of this specification**.

Adding such forms would be a future feature, not documentation consolidation.

---

# 4. `/VER`

**Implemented through the common utility-version mechanism.**

`DUP /VER` is standalone and currently prints:

```text
BetterCP/M DUP 1.0 (Build 001)
```

It exits without entering the disk menu or operating on media. Combining `/VER`
with other operands is invalid. Version and build values come from the common
utility-version metadata and may advance with subsequent changes.

This identity is distinct from the retained legacy interactive title:

```text
BetterCP/M 2.2 Disk Utility Program version 1.14
```

The legacy title must not be interpreted as the BetterCP/M utility release version.

---

# 5. Runtime requirements

DUP is a transient utility and requires approximately 51 KiB of transient memory.

The current implementation refuses operation when insufficient TPA is available:

```text
DUP needs 51K of transient memory.
```

DUP keeps its physical work buffers, track-format stream, copy buffer, sector cache, and optional cached platform control image in transient memory.

This is intentional: DUP's physical-media support must not require large permanent resident buffers merely to accelerate an occasional disk utility.

On platforms advertising the private fast-format entry, DUP caches the platform control image for the duration of the utility and restores it before each format-track call. This removes the earlier repeated system-disk overlay loading without enlarging the resident disk/control allocations.

The qualified implementation retained the 53 KiB BetterCP/M TPA target.

---

# 6. Drive model

DUP operates on the currently installed BetterCP/M logical-drive bindings.

The present interface exposes:

```text
A:
B:
C:
D:
```

DUP obtains the selected logical drive's normalized disk binding through the public disk-control API without logging into the filesystem.

This is important because DUP must operate on the **entire medium**, including:

- system/reserved tracks;
- directory sectors;
- allocated file sectors;
- unallocated sectors;
- deleted-file data;
- other sectors not represented by currently live directory entries.

Filesystem-level file selection plays no role in DUP.

---

# 7. Physical-drive protection

Physical drive 0 is the protected BetterCP/M system disk for destructive DUP operations.

The current implementation refuses to FORMAT physical drive 0:

```text
Physical drive 0 is the protected system disk.
```

COPY likewise refuses physical drive 0 as the destination.

This protection is based on the physical drive associated with the selected logical binding, not merely on its logical letter.

Thus remapping a logical drive does not circumvent system-disk protection.

CHECK is read-only and may inspect a binding associated with the protected physical drive.

COPY may also use the protected/system medium as a **source**, because the source is not written.

---

# 8. FORMAT operation

## 8.1 Selection

From the main menu:

```text
A
```

selects FORMAT.

DUP prompts:

```text
Choose logical drive [ A - D ], or ^C to return.
```

The operator selects one currently configured logical drive.

`^C` returns to the main menu without modifying media.

## 8.2 Format selection

DUP does **not** present the FDB catalog and does not ask the operator to choose a disk-format name.

FORMAT uses the disk format already installed in the selected logical drive's binding.

Conceptually:

```text
CONFIG chooses/binds format
        |
        v
logical drive binding
        |
        v
DUP FORMAT
```

DUP displays the selected logical drive, physical drive, and available format identification before destructive operation.

To format a disk using another format, the binding must first be established by the normal disk-configuration mechanism.

DUP is not an alternative CONFIG interface.

---

# 9. FORMAT validation before destruction

Before asking the user to erase the disk, DUP validates what it can validate generically.

The current formatter checks, among other things:

- the selected logical binding is valid;
- the physical drive is valid;
- the target is not protected physical drive 0;
- the sector-size code is supported;
- physical-sector count is nonzero;
- the current implementation's sector-count limit is not exceeded;
- required FDF semantics can be interpreted;
- a complete write-track stream can be constructed;
- the generated stream fits within the permitted physical revolution capacity.

Current implementation limits include at most 32 physical sectors per surface and physical sector sizes represented by the supported 128/256/512/1024-byte size codes.

These are implementation/backend limits, not limits of the FDF source language itself.

The generic FDF language can describe formats which a particular BetterCP/M backend cannot use.

---

# 10. FORMAT confirmation

After generic validation and before any destructive operation, DUP displays a destructive warning:

```text
Insert target disk. ALL DATA ON THIS PHYSICAL DISK WILL BE LOST.
Ctrl-C stops between tracks.
Format this disk? [Y/N]
```

Only `Y` proceeds.

Any other answer returns without formatting.

Unlike the historical MM DUP behavior analyzed during development, BetterCP/M DUP does not depend on a successful probe of an existing sector to decide whether a disk deserves a destruction warning.

The BetterCP/M warning is unconditional for FORMAT.

---

# 11. Physical format description

DUP consumes the normalized physical geometry in the installed disk binding.

Relevant format information can include:

- number of cylinders;
- one or two sides;
- physical-sector count;
- sector IDs;
- uniform or mixed physical-sector sizes;
- FM or MFM encoding;
- inverted payload convention;
- logical-track topology;
- side ordering;
- track-ID convention;
- sector-ID convention.

The FDF specification remains authoritative for the meaning and validation of those fields.

DUP does not reinterpret the original Montezuma Micro FDF grammar directly.

---

# 12. FORMAT track construction

The current formatter constructs a complete physical write-track stream in transient memory.

It produces the appropriate:

- track gaps;
- sync fields;
- ID address marks;
- cylinder/track IDs;
- side IDs;
- physical sector IDs;
- sector-size fields;
- CRC-generation tokens;
- data address marks;
- erased sector contents;
- end-of-track padding.

FM and MFM streams use the controller conventions supported by the backend.

Newly formatted sector payloads correspond to CP/M erased data (`E5h`) after normal inversion handling.

Where an FDF definition specifies inverted data, inversion remains part of the BIOS/binding semantics rather than changing the logical erased-byte requirement.

---

# 13. Rotational layout

`SECTOR_IDS` specifies the format's logical physical-sector order for BetterCP/M's current formatter.

The broader FDF specification deliberately does not claim to reproduce every historical formatter's exact rotational layout.

A valid DUP-created disk must preserve the format's required:

- IDs;
- sizes;
- encoding;
- topology;
- inversion semantics;
- logical contents.

Exact flux or historical track-layout replication is not a DUP 1.0 requirement.

COPY therefore means physical-medium content duplication within the BetterCP/M disk-format model, not archival flux-level cloning.

---

# 14. FORMAT execution

Formatting proceeds one physical surface at a time.

For each cylinder/side:

1. DUP constructs the write-track stream.
2. The backend formats that physical surface.
3. DUP immediately rereads the resulting sectors.
4. DUP verifies that every logical 128-byte record contains the expected erased `E5h` data.
5. Only after successful verification does it advance to the next surface.

This immediate format-and-verify behavior is intentional.

BetterCP/M does **not** reproduce MM DUP's separate final reverse verification pass.

---

# 15. FORMAT verification strength

BetterCP/M's FORMAT verification is stronger than the historical MM behavior studied during development.

The historical MM checker established essentially that each sector was readable without selected controller errors.

BetterCP/M additionally compares the returned contents against the expected erased data.

Successful BetterCP/M FORMAT therefore means both:

- the formatted sectors can be read successfully; and
- the returned logical payload contains the intended erased contents.

---

# 16. FORMAT retries

The physical write-track operation uses bounded retry behavior.

The current implementation permits up to three attempts for a failed format-track request.

Write protection is not retried because retrying cannot make a protected disk writable.

There are no unbounded retry loops.

A failure reports the applicable controller/backend status.

---

# 17. FORMAT completion

DUP separately counts successfully written and verified physical surfaces.

It does not report success merely because the cylinder iterator reaches its endpoint.

On success, it reports the number of tracks/surfaces written and verified followed by:

```text
Format complete.
```

If the operation is interrupted or verification fails, it does not issue the successful completion message.

---

# 18. COPY operation

Selecting:

```text
B
```

from the main menu enters whole-disk COPY.

COPY duplicates all sector payloads represented by the source’s installed binding. It does not operate at the filesystem level.

It is not equivalent to `COPY.COM` or PIP.

---

# 19. COPY source selection

The prompt is:

```text
Source logical drive [ A - D ], ^C returns.
```

Valid source logical drives are therefore A through D.

`^C` returns to the main menu.

The source may be the protected system physical drive because COPY never writes to the source.

DUP obtains and retains the complete source binding for the operation.

---

# 20. COPY destination selection

The destination prompt is:

```text
Destination logical drive [ B - D ], ^C returns.
```

The current implementation therefore does not permit logical A as the COPY destination.

The selected destination must also:

- resolve to a valid physical drive;
- not resolve to physical drive 0;
- not refer to the same physical drive as the source.

---

# 21. Same physical drive

COPY requires two distinct physical drives.

It explicitly rejects source and destination logical bindings that alias the same physical drive:

```text
Source and destination must be different physical drives.
```

Thus DUP 1.0 does **not** implement single-drive disk swapping.

This restriction applies even if source and destination are represented by different logical letters.

No RAM-buffered whole-disk single-drive copy mode is specified.

---

# 22. Source and destination format comparison

## COPY source-binding normalization

Before comparing the source format with the destination binding, DUP normalizes the bootstrap cylinder-based source representation when necessary.

The bootstrap binding may describe one CP/M logical track as an entire physical cylinder. COPY converts that transient representation into the equivalent surface-track form used by ordinary destination bindings:

- the cylinder-track indication is converted to the corresponding surface-track topology;
- SPT is adjusted from records per cylinder to records per surface;
- OFF is adjusted from reserved cylinders to the equivalent number of reserved surface tracks.

This transformation does **not** alter source media and does not translate copied payload bytes. It produces an equivalent transient format description so that DUP can compare and install the source format using the ordinary destination-binding contract.

The normalized representation is used for COPY compatibility and temporary destination binding only. It does not rewrite the source's persistent configuration.


DUP compares the normalized source-format binding with the destination binding after preserving the destination's physical-drive identity.

Two cases result.

## 22.1 Matching format

If source and destination bindings describe the same disk format, COPY does not reformat the destination.

It copies the sector payloads directly using the existing destination format.

## 22.2 Different format

If the destination format differs, DUP reports:

```text
Destination format differs. Copy will format it to match the source.
```

DUP then temporarily constructs a destination binding using:

- the source disk-format semantics;
- the destination physical drive.

The destination backend validates this temporary binding **before destructive copy begins**.

This is where the distinction between format description and backend capability becomes critical.

A source format may be perfectly valid in the FDB yet impossible for the destination backend to format.

In that case COPY must reject the operation rather than proceed with an approximation.

---

# 23. Temporary destination binding

When COPY requires the destination to assume the source format, DUP saves the destination's original complete binding.

It then installs a temporary source-format binding for the physical destination.

This temporary change exists only to perform the COPY operation.

It is **not** a permanent CONFIG change.

The original destination binding must be restored on:

- successful copy;
- operator cancellation;
- copy error;
- interruption;
- return to the main menu;
- ordinary utility exit.

---

# 24. COPY confirmation

Before writing the destination, DUP shows the physical source and destination and warns:

```text
Copy ALL sectors from X to Y? Destination contents will be erased. [Y/N]
```

Only `Y` begins the destructive copy.

If the user declines after DUP installed a temporary destination binding, normal cleanup restores the original binding before returning to the menu.

---

# 25. Whole-disk COPY semantics

COPY does not log into the filesystem or enumerate directory entries.

It copies **all sector payloads represented by the installed source binding**, including payloads corresponding to:

- reserved/system areas;
- directory sectors;
- allocated files;
- deleted-file contents;
- unallocated filesystem space;
- other sectors represented by the binding.

COPY therefore reproduces the disk contents exposed through the BetterCP/M disk-format model rather than merely copying visible files.

It is **not** a flux-level or track-image duplication facility. COPY does not promise preservation of physical details that are not represented by the binding, including:

- arbitrary gap layout;
- exact historical rotational placement;
- deleted-data address marks;
- weak sectors;
- undocumented controller metadata;
- flux-transition timing;
- other track-level artifacts outside the BetterCP/M format model.

When destination reformatting is required, DUP constructs a valid destination representation of the source format and then copies the represented sector payloads into it.

---

# 26. COPY surface sequence

For each physical source surface, the current implementation uses the following sequence:

1. **Read the entire source surface into transient memory.**
2. If the destination must be reformatted:
   1. construct the destination format stream;
   2. format the destination surface;
   3. reread it;
   4. verify erased `E5h` contents.
3. Write the buffered source records to the destination.
4. Reread the destination records.
5. Compare the read-back bytes against the buffered source bytes.
6. Continue to the next surface.

A source surface is therefore read successfully **before** the corresponding destination surface is destroyed.

This differs intentionally from the historical MM order identified during reverse engineering.

---

# 27. COPY buffer limit

COPY buffers one source surface at a time.

The implementation requires the number of 128-byte logical records on that surface to fit the transient copy buffer.

The current check rejects a surface requiring 65 or more records; therefore the existing implementation supports up to 64 128-byte logical records per buffered surface.

A format which exceeds that current utility limit is unsupported by DUP even if it can be represented in FDF.

This is another example of:

```text
describable format != DUP-supported operation
```

---

# 28. COPY verification

COPY verification is byte-for-byte at the logical 128-byte record level.

After writing a destination surface, DUP rereads it and compares it with the source bytes retained in transient memory.

A mismatch is reported as status `FEh`:

```text
Read-back data does not match.
```

This is deliberately stronger than the historical MM DUP checker, which verified readability but did not compare the copied payload against the original copy buffer.

A successful COPY therefore requires actual destination data agreement, not merely readable sectors.

---

# 29. COPY completion

Only after all physical surfaces have been copied and verified does DUP report:

```text
Copy complete; destination verified.
```

The original logical-drive binding is restored before normal operation resumes where a temporary binding was used.

If the physical disk has been reformatted to the source format, restoration of the old logical binding does **not** change the physical disk back.

DUP therefore reports:

```text
Destination configuration restored. Use CONFIG for the copied format.
```

The operator must use CONFIG if the new physical medium is to become the persistent format associated with that logical drive.

This separation is intentional:

> DUP changes media; CONFIG changes persistent drive configuration.

---

# 30. CHECK operation

Selecting:

```text
C
```

enters CHECK.

DUP prompts for a logical drive A through D.

CHECK is non-destructive.

It uses the currently installed binding to walk the complete physical medium.

---

# 31. CHECK behavior

CHECK reads each physical sector represented by the binding.

It validates that the medium can be read through the selected geometry and reports errors with physical location information.

CHECK does not:

- modify sector contents;
- format tracks;
- repair filesystem structures;
- compare data against an external reference;
- require that unused sectors contain `E5h`.

Its purpose is physical read verification.

---

# 32. CHECK error continuation

Unlike FORMAT and COPY, CHECK is intended to continue after ordinary read failures.

On the first failing logical record belonging to a physical sector, DUP:

1. identifies the affected physical sector;
2. reports the error;
3. increments the error count;
4. skips the remaining logical records belonging to that already-failed physical sector;
5. continues with subsequent sectors.

Thus the final count corresponds to physical sectors encountered as unreadable, rather than repeatedly counting every 128-byte subrecord in one bad larger sector.

At completion:

```text
Check complete. Unreadable sectors: n
```

is displayed.

The error counter is a word value; BetterCP/M does not reproduce MM's historical one-byte wraparound behavior.

---

# 33. CHECK interruption

If the operator interrupts CHECK, DUP reports:

```text
Check stopped. No disk contents changed.
```

Because CHECK is read-only, interruption leaves the medium unchanged.

---

# 34. Error diagnostics

DUP reports useful physical context for read, write, verification, and comparison errors.

Diagnostics include, where applicable:

```text
Cylinder n, side n
sector ID n
record n
error status n
```

The current status explanations include:

| Status/bit | Meaning reported by DUP |
|---|---|
| `1` | Request failed or drive did not respond |
| `2` | Unsupported operation or disk address |
| `FEh` | Read-back data does not match |
| bit 7 | Drive not ready; check inserted disk |
| bit 6 | Disk is write protected |
| bit 4 | Sector/track not found; check disk format |
| bit 3 | CRC error; data could not be read reliably |
| bit 2 | Data transfer failed |
| otherwise | Disk I/O failed |

Status 1 remains deliberately broad because older adapters combine validation and timeout-type failures.

---

# 35. Fatal versus continuing errors

For FORMAT and COPY, a data error or verification failure stops the current destructive operation.

DUP does not continue blindly after a failed destination write or byte comparison.

CHECK behaves differently: ordinary media read failures are accumulated and checking continues.

Backend or binding errors that prevent meaningful continued operation may still terminate CHECK.

The exact distinction follows the current implementation/backend status path rather than an invented universal controller-error taxonomy.

---

# 36. Interruption

DUP recognizes BREAK / `^C`.

At menus and drive-selection prompts it returns or exits as indicated by the prompt.

During long physical operations DUP polls for interruption between bounded units of work.

It does not attempt to interrupt an already-issued physical controller/backend request in the middle of that request.

Consequences are reported explicitly.

For FORMAT:

```text
Format aborted. Disk is only partly formatted.
```

For COPY:

```text
Operation stopped. Destination may be partly written.
```

For CHECK:

```text
Check stopped. No disk contents changed.
```

No interrupted destructive operation may report successful completion.

---

# 37. Restoration after interruption or error

Temporary COPY bindings must be restored regardless of why the operation terminates.

The common cleanup path restores the saved destination binding and resets BetterCP/M's drive/alias state.

The implementation deliberately does not warm-boot away from a temporary binding.

If restoration itself fails, DUP reports:

```text
Cannot restore destination configuration. Press a key to retry.
```

It retains the saved binding and returns through a retry path.

It must not claim successful cleanup while the temporary binding remains installed.

---

# 38. Backend capability boundary

DUP's common transient code is portable at the BetterCP/M API level.

Machine-specific controller I/O does not belong in the common DUP implementation.

This is a deliberate departure from historical MM DUP, which contained a transient Model 4 controller driver using controller ports, an NMI handler, and MM-private drive records.

BetterCP/M instead uses:

- standard BIOS entry points for logical-record transfer;
- the public disk-control interface for bindings and raw format operations;
- optional advertised platform acceleration where available.

The common DUP code must not assume direct access to Model 4 FDC ports or other platform-specific hardware.

---

# 39. Model 4 qualified capability

The retained Model 4 DUP qualification covers:

- ordinary disk copies;
- matching-format copies;
- mixed-sector FDF copies;
- source CRC errors;
- destination write protection;
- interruption;
- temporary binding restoration;
- preservation of source media;
- preservation of system media;
- return to the command environment.

Successful copies are independently compared at the physical-sector payload level and followed by DUP CHECK.

The mixed-sector qualification demonstrates that the BetterCP/M Model 4 backend can perform the required raw formatting for the tested mixed-sector FDF medium.

This is **qualified behavior**.

---

# 40. z80pack qualified capability

The z80pack backend is qualified to FORMAT and verify a complete **uniform** raw image.

The mixed-sector qualification establishes a deliberate boundary:

1. the normalized MM SUPER binding can be installed;
2. ordinary access to that binding is accepted;
3. DUP requests the physical/raw formatting operation;
4. the z80pack backend returns **unsupported**;
5. no target byte is changed.

Thus:

> z80pack's ability to understand a normalized mixed-sector binding does not imply that its raw formatter can create that medium.

This is the canonical example of why FDB description and backend formatter capability remain separate.

---

# 41. Explicit supported/rejected cases

## 41.1 Implemented generic behavior

DUP supports formats within both:

- the current normalized binding/utility limits; and
- the selected backend's physical capabilities.

It supports uniform sector sizes and the currently implemented mixed-size representation.

It understands the established BetterCP/M topology and sector-mapping semantics used by the current bindings.

## 41.2 Rejected before destructive operation where possible

DUP rejects:

- invalid logical bindings;
- protected physical destination 0;
- source and destination aliases of the same physical drive;
- unsupported sector-size codes;
- zero or excessive physical-sector counts for the current formatter;
- format streams that exceed physical track capacity;
- copy surfaces too large for the transient surface buffer;
- backend-incompatible temporary destination bindings.

## 41.3 Backend rejection

Even after generic DUP validation succeeds, a backend may return unsupported for a physical operation.

That is a valid capability result, not evidence that the FDB entry is invalid.

The backend must not silently substitute a different format.

For the qualified z80pack mixed-sector case, unsupported is returned before modifying target media.

The no-modification result is established for the qualified z80pack mixed-sector
path. The cited evidence does not establish a universal guarantee that every
unsupported result from every present or future backend precedes all media
modification. Such a guarantee requires a separate backend-interface contract
and qualification.

---

# 42. FDB semantics versus DUP capability

`DISK.FDB` may contain formats exceeding a particular DUP/backend combination's capability.

Examples include:

- more sectors than the current binding/runtime arrays support;
- mixed sector sizes unsupported by a raw formatter;
- topology requiring semantics unsupported by a backend;
- physical timing requirements which the hardware/backend cannot provide.

FDB processing distinguishes:

1. malformed database;
2. structurally valid descriptor with unsupported required semantics;
3. valid supported descriptor incompatible with the selected drive/backend.

DUP operates only after a usable binding exists, but a usable binding for normal CP/M access still does not prove raw-format capability.

---

# 43. System-media preservation

DUP's destructive safeguards must protect the configured system medium.

Qualification explicitly checks preservation of system media in ordinary, error, write-protected, and interrupted operation cases.

No COPY or FORMAT path may accidentally modify the source or protected system disk while operating on another physical destination.

---

# 44. Source preservation

COPY reads but never writes its source.

The source surface is captured before the corresponding destination surface is formatted or overwritten.

Qualified error cases verify source preservation.

A CRC/read error on the source stops destructive progress for that surface rather than writing data known to be incomplete or unreliable.

---

# 45. Utility cleanup and drive reset

Returning to the main menu invokes DUP's cleanup path.

After temporary-binding restoration, DUP performs the system drive-reset operation used to discard stale logical-drive/alias state.

The purpose is to ensure subsequent CP/M disk operations use the restored current configuration.

DUP must not leave cached aliases referring to the temporary COPY binding.

---

# 46. Historical MM behavior that is not normative

The Montezuma Micro DUP analysis is supporting evidence, not BetterCP/M's behavior specification.

BetterCP/M intentionally differs in several respects.

Historical MM DUP:

- contained a Model 4-specific transient controller driver;
- used MM-private physical-drive/DPB structures;
- formatted the destination before reading the corresponding source cylinder during COPY;
- checked readability rather than performing BetterCP/M's byte-for-byte copy comparison;
- performed FORMAT's verification as a separate reverse pass;
- had a one-byte bad-sector counter;
- used a successful initial sector read as a “not blank” test.

BetterCP/M does **not** need to reproduce those details.

The retained lessons are architectural and behavioral where they have already been implemented: transient physical disk handling, bounded errors, useful diagnostics, and efficient access to physical formatter support.

---

# 47. Performance architecture

The original BetterCP/M formatting path repeatedly reloaded format-control code from system disk during the inner formatting loop.

The current implementation can instead use an advertised private platform entry to cache the necessary control image in transient memory.

On the Model 4 development path this reduced a measured full 800K format/verify run from approximately 341 seconds to approximately 51 seconds while retaining:

- immediate verification;
- all 1,600 sectors verified;
- byte-comparison policy;
- unchanged resident disk/control allocations.

z80pack advertises no such private acceleration and uses the ordinary public operation.

This optimization is optional backend capability. It must not change DUP's externally visible correctness contract.

---

# 48. Completion and error claims

DUP may report FORMAT success only after every required physical surface has been formatted and verified.

DUP may report COPY success only after every required source surface has been read, written to the destination, and byte-verified.

CHECK completion reports the number of unreadable physical sectors encountered.

An interrupted or failed operation must report the corresponding partial-operation status, not the normal completion message.

---

# 49. Qualification status for BetterCP/M 1.0

The DUP backend-capability qualification is closed for the retained automated matrix.

Current evidence includes:

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

The qualification report states that backend-capability closure is complete.

Native installation and final two-platform release qualification remain separate final release work; this specification does not convert those outstanding release tasks into DUP design changes.

---

# 50. 1.0 behavioral summary

DUP 1.0 is the existing interactive three-function physical disk utility:

```text
DUP
    A  FORMAT
    B  COPY
    C  CHECK
```

with standalone:

```text
DUP /VER
```

printing:

```text
BetterCP/M DUP 1.0 (Build 001)
```

Its principal contracts are:

- FORMAT uses the selected logical drive's installed binding.
- FORMAT constructs physical tracks according to the format geometry supported by the backend.
- FORMAT warns before destruction.
- FORMAT immediately rereads and verifies erased payload contents.
- COPY requires distinct physical source and destination drives.
- COPY protects physical system drive 0 from destination writes.
- COPY preserves the source.
- COPY normalizes the bootstrap cylinder-based binding into equivalent surface-track form before destination-format comparison where required.
- COPY copies all sector payloads represented by the installed source binding; it is not a flux-level or arbitrary track-metadata clone.
- COPY reformats the destination when its binding differs from the normalized source format and the destination backend supports that format.
- COPY reads each source surface before destroying or overwriting the corresponding destination surface.
- COPY rereads and byte-compares written payloads.
- CHECK is read-only and continues over ordinary unreadable sectors.
- `^C` interrupts operations at bounded safe points.
- interrupted destructive operations are explicitly reported as partial.
- temporary destination bindings are restored before normal operation resumes, or restoration is retried on failure.
- CONFIG remains responsible for persistent drive configuration.
- FDB format description and backend physical capability are distinct.
- a valid FDB/binding does not imply every backend can physically format that medium.
- the z80pack mixed-sector qualification specifically establishes rejection without target modification for that tested unsupported path.
- machine-specific controller operations remain behind the BetterCP/M disk/backend interface.

## Supporting references

- [DUP format and implementation analysis](DISK-FORMAT-MM-DUP-ANALYSIS.md)
- [Backend capability closure](202%20DUP%20Backend%20Capability%20Closure.md)
- [Disk format definition specification](DISK-FORMAT-DEFINITION-SPECIFICATION.md)
- [DUP implementation](../../src/utilities/dup.mac)
- [Utility versioning](../../specifications/UTILITY-VERSIONING.md)

Additional backend capability claims require their own named qualification;
FDB representability and ordinary disk access alone do not establish them.
