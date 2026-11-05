# CP/M 2.2 programming interface reference

This is the CP/M interface part of the [BetterCP/M Programmer's Guide](programmers_guide.md). It covers all standard BDOS selectors 0–40, including reserved 38/39, all 17 BIOS vectors, page zero, FCBs, DMA and disk parameter structures. The [BetterCP/M-specific reference](BETTERCPM-API.md) covers extensions separately. This is documentation of locked software source `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`, not a declaration that every historical implementation behaved identically.

Original prose is CC BY 4.0; original reusable code examples are GPL-2.0-or-later. Third-party material retains its terms. See [licensing](../LICENSING.md).

## Contents

- [Execution and calling conventions](#execution-and-calling-conventions)
- [Page zero](#page-zero)
- [FCB and record structures](#fcb-and-record-structures)
- [BDOS 0–12: console and system](#bdos-0-12)
- [BDOS 13–32: files and disk state](#bdos-13-32)
- [BDOS 33–40: random access and reset](#bdos-33-40)
- [BIOS vectors](#bios-vectors)
- [Disk parameter structures](#disk-parameter-structures)
- [Errors and compatibility boundaries](#errors-and-compatibility-boundaries)

## Execution and calling conventions

A COM program is loaded at 0100h and receives a CP/M-compatible page-zero environment. Call BDOS through `CALL 0005h`, with C holding the decimal function number. A byte argument normally goes in E; a pointer or word normally goes in DE. The per-function tables below specify the result. Do not call a historical fixed BDOS address or assume an RSX is absent.

Use A for byte results and HL for word/pointer results. Locked standard BDOS normal-return code also provides A=L and B=H aliases; this is not a universal contract for every extension or BIOS call. Treat working registers and flags as destroyed unless a particular interface preserves them. Locked standard BDOS restores its saved caller stack and IX; portable application code must not depend on undocumented preservation. Keep loop counts and pointers in owned storage or explicitly save them around calls. BIOS register rules are separate.

`JP 0000h` and Function 0 take the warm-return path. A balanced RET can use the conventional initial return frame, but it is inappropriate after changing SP without restoring that frame. The examples use an owned stack and deliberately warm boot. Query the current upper boundary through the operand of the jump at 0005h, the word at 0006h. The range from 0100h up to that address is exclusive at its top. Code, initialized data, buffers, uninitialized storage and the private stack must all fit. A loaded RSX lowers the boundary; CCP/CPX memory below it is reclaimable by the transient.

Do not enable interrupts, change the interrupt mode, patch page-zero vectors or retain system pointers unless the particular integration contract requires it. Calls are synchronous; BIOS/BDOS disk waits are bounded by their platform implementation. Standard services are not a reentrant interrupt API.

## Page zero

| Address | Length | Meaning and use |
| --- | ---: | --- |
| 0000h | 3 | JMP warm boot. Use for termination; its operand identifies WBOOT, not the BIOS base itself. |
| 0003h | 1 | IOBYTE, read/written by Functions 7/8. Device availability remains platform-specific. |
| 0004h | 1 | Conventional current/default-drive state in the CP/M entry environment; use Function 25 for the running BDOS selection. Do not mutate private state through this byte. |
| 0005h | 3 | JMP current BDOS/RSX gateway. Its operand at 0006h is the exclusive TPA ceiling. |
| 005Ch | 36 | First default FCB. The second default FCB begins at 006Ch and overlaps this storage. |
| 006Ch | 16 initially useful bytes | Second parsed filename in the conventional entry layout. Copy to a separate full 36-byte FCB before using two open files. |
| 0080h | 1 + counted data | Command-tail length followed by its characters. The same address is the initial 128-byte DMA buffer. Save the tail before directory or record I/O overwrites it. |

The command tail is counted data, not a `$`-terminated Function-9 string. The locked CCP preserves tail letter case as a recorded compatibility disposition. Do not uppercase a quoted pattern or a host filename unintentionally. Default FCB parsing is not the full command-line grammar of COPY, PIP or the extended file selectors. The application owns its parser and must reject unsupported ambiguous operands.

## FCB and record structures

| FCB offset (decimal) | Length | Field |
| --- | ---: | --- |
| 0 | 1 | Drive: 0=current drive, 1=A, 2=B, etc. This differs from Function 14's zero-based drive number. |
| 1 | 8 | Space-padded uppercase filename. |
| 9 | 3 | Space-padded type; high bits carry attributes. T1 bit 7=read-only, T2 bit 7=system, T3 bit 7=archive. Mask attribute bits when displaying names. |
| 12 | 1 | EX, logical extent low field. |
| 13 | 1 | S1, reserved/system use. |
| 14 | 1 | S2, extended extent/system state. Do not overwrite it in an active FCB. |
| 15 | 1 | RC, records represented in the current extent/subextent. |
| 16 | 16 | Allocation map; owned by file services after Open/Make. |
| 32 | 1 | CR, sequential record position. Set zero for a new initial sequential access. |
| 33 | 3 | R0/R1/R2, little-endian random record number, in units of 128 bytes. |

Construct an exact FCB by zeroing all 36 bytes, filling the drive/name/type, and space-padding both name fields. Open/Make populate disk-owned fields; preserve the live FCB until Close. Use separate FCBs for separate active files. The default FCB overlap at 005Ch/006Ch is particularly dangerous for a two-file copier.

A sequential logical extent contains 128 records (16 KiB); EXM can group several logical extents in one directory entry. Do not compute directory capacity or a file's final record count from one entry without interpreting DPB/extent semantics. Use Functions 35/36 for record-number conversion. A directory entry is 32 bytes with user/deleted status at byte 0 and name/type and extent/allocation fields following; a returned search slot selects one of four entries in a 128-byte DMA record.

Set DMA with Function 26 before reading, writing or directory searching. Reserve a complete writable 128-byte buffer with no wrap or overlap with live code, FCBs or stack. File record services do not find a text EOF character; they transfer physical logical-record bytes. Text tools can interpret 1Ah separately. After library/file activity, restore the DMA address expected by the caller, commonly 0080h for return to a conventional command environment.

### IOBYTE fields

IOBYTE has two-bit selectors for CON (bits 0–1), RDR (2–3), PUN (4–5) and LST (6–7). Conventional selector order is CON: TTY/CRT/BAT/UC1; RDR: TTY/PTR/UR1/UR2; PUN: TTY/PTP/UP1/UP2; LST: TTY/CRT/LPT/UL1. BAT uses reader input and list output. A name in this table is a convention, not an implementation promise. Use the platform capability contract and check actual device availability. Temporary routing changes must restore the original byte on ordinary return.

<a id="bdos-0-12"></a>

## BDOS 0–12: console and system

The selector is decimal; the parenthesized number is hexadecimal. Unspecified output values must not be used as success indicators.

| Function | Inputs | Result | Behavior, side effects and failure boundary |
| --- | --- | --- | --- |
| **0 (00h) System Reset** | C=0 | Does not return | Warm boot restores the command environment. It does not save application files or mean cold reset. Close output first. |
| **1 (01h) Console Input** | C=1 | A=character | Waits, echoes through cooked output. Locked cooked Ctrl-C warm boots; Ctrl-P toggles printer echo, Ctrl-S pauses. Not suitable for binary terminal-protocol input. |
| **2 (02h) Console Output** | E=character | No portable result | Cooked output handles TAB/column/flow/printer state. Use Function 6 for uninterpreted bytes, especially control sequences whose cursor movement makes cooked column state inaccurate. |
| **3 (03h) Reader Input** | C=3 | A=character | Reads the configured reader. Behavior when unavailable belongs to the BIOS/device contract; no general host EOF status is added. |
| **4 (04h) Punch Output** | E=character | No portable result | Outputs through the configured punch route. No standard disk-style error status. |
| **5 (05h) List Output** | E=character | No portable result | Outputs through the configured list route. Use BIOS LISTST where required by a hardware-specific application. |
| **6 (06h) Direct Console I/O** | E=FFh for input polling, otherwise output byte | Input: A=0 if no character, otherwise character | Bypasses cooked echo/control interpretation. Zero can also be a real NUL byte: poll status separately when that distinction matters. E=FFh selects input, so this form cannot directly emit FFh. Do not import CP/M 3 FEh/FDh operations into this 2.2 contract. |
| **7 (07h) Get I/O Byte** | C=7 | A=IOBYTE | Reads logical routing selection. It is not a device-presence query. |
| **8 (08h) Set I/O Byte** | E=new byte | No portable result | Changes routing. Keep a saved byte if a temporary caller intends to restore it. |
| **9 (09h) Print String** | DE=readable `$`-terminated bytes | No portable result | Uses cooked output until the first 24h byte. It is not length-counted and cannot print an arbitrary binary record. The caller must provide a terminator within owned memory. |
| **10 (0Ah) Read Console Buffer** | DE=buffer; byte 0=maximum | Byte 1=count, followed by accepted characters | Layout is maximum, actual count, data. Allow storage for the maximum and terminator/working margin rather than equating it to an FCB. Uses cooked line editing and context-specific Ctrl-C behavior. XSUB/BATCHIO can supply compatible submitted input; raw input callers are unaffected. |
| **11 (0Bh) Console Status** | C=11 | A=00h unavailable, FFh ready in the locked implementation | Non-consuming readiness. Pending cooked-input state can make a byte ready. Do not replace this with a blocking read or consume a terminal reply merely to answer status. |
| **12 (0Ch) Return Version** | C=12 | HL=0022h in locked BetterCP/M | Advertises the CP/M 2.2 interface baseline, not BetterCP/M's distribution or implementation version. Use Function 180 for the latter descriptor. |

Function 10's editing keys belong to that service, not the CCP history editor or the reusable input library. A normal Function-10 submission excludes the terminating Return from its count. Callers must interpret the count and may add their own delimiter in separate available storage.

<a id="bdos-13-32"></a>

## BDOS 13–32: files and disk state

For FCB operations below DE points to a complete live FCB unless stated otherwise. Normal directory success values 0–3 identify a directory slot; **test against FFh**, not only zero. File mutation may terminate through a read-only path rather than return an ordinary error; the final section explains cleanup consequences.

| Function | Inputs | Result | Behavior, side effects and failure boundary |
| --- | --- | --- | --- |
| **13 (0Dh) Reset Disk System** | C=13 | Locked normal result A=0; failures can return FFh | Selects A, resets login/software-read-only state, invalidates disk context and resets DMA to 0080h. Does not cold boot or initialize every application variable; caller user state is separate. Historical submit-detection return conventions are not a new public guarantee here. |
| **14 (0Eh) Select Disk** | E=0 for A, 1 for B, etc. | No portable success value; locked implementation returns 0 or FFh | Selects/logs in a logical disk; locked BIOS has A–D. Do not put FCB's one-based drive byte here. |
| **15 (0Fh) Open File** | DE=initialized exact FCB | A=0–3 found; FFh missing/error | Fills extent/allocation fields. Initialize CR and requested initial extent before Open. Open does not position or preserve a second overlapping default FCB for you. |
| **16 (10h) Close File** | DE=live FCB | A=0–3 normal; FFh error | Commits changed record/allocation state. Close output even after a prior transfer failure where control returns. An unsuccessful Close means success cannot be claimed for the file. |
| **17 (11h) Search First** | DE=search FCB; `?` patterns permitted | A=0–3 slot; FFh no further match/error | Copies the containing 128-byte directory record to current DMA and establishes iterator continuation. Search can return multiple extents for one logical file. |
| **18 (12h) Search Next** | Continuation from 17 | Same search result convention | Uses the existing iterator. Do not interleave unrelated directory/file operations and assume its continuation survives; copy needed entry data immediately. |
| **19 (13h) Delete File** | DE=FCB pattern | A=0–3 success; FFh not found/error | Deletes matching files/extents. Check scope before invoking; a wildcard operation is not a transactional batch or a secure overwrite. Earlier changes need not be rolled back after failure. |
| **20 (14h) Read Sequential** | DE=live FCB; current DMA | A=0 transferred, 1 EOF; other nonzero failure | Transfers one 128-byte record and advances sequential position on success. Locked mapping/I/O errors can return FFh. EOF is not a text 1Ah marker. Do not publish a record on a failed read. |
| **21 (15h) Write Sequential** | DE=live FCB; current DMA | A=0 transferred; nonzero failure | Writes one record, allocates blocks/extents and updates FCB position. Locked allocation-full is 2, directory/extent-full can be 1, general failure FFh; do not label all failures EOF. Close is still required to finish metadata publication. |
| **22 (16h) Make File** | DE=initialized exact FCB | A=0–3 created; FFh failure | Creates a new directory entry and active file state. Use a fresh name; Make is not a safe replace-existing primitive. Initialize FCB rather than reusing stale allocation bytes. |
| **23 (17h) Rename File** | DE=rename FCB: old name/type at +1, replacement at +17 | A=0–3 success; FFh failure | Replacement naming is embedded in this special FCB form, not a second pointer. No drive/user move is implied. Avoid destination conflicts; do not assume all-or-nothing wildcard rename. |
| **24 (18h) Return Login Vector** | C=24 | HL=16-bit mask, bit 0=A | Reports logged-in disks, not physical media presence or qualification. Bits can be cleared by reset. |
| **25 (19h) Return Current Disk** | C=25 | A=zero-based disk | Query current logical selection independently of the FCB's drive. |
| **26 (1Ah) Set DMA Address** | DE=128-byte buffer | No portable result | Changes subsequent record/search transfer destination/source. It does not allocate or validate actual ownership of a caller's entire memory region. |
| **27 (1Bh) Get Allocation Address** | C=27 | HL=allocation bitmap, zero on locked context failure | Inspection only. Locked drives share workspace rebuilt on disk-context changes; never retain it across selection/reconfiguration or mutate it to allocate blocks. Interpret using the active DPB. |
| **28 (1Ch) Write Protect Disk** | C=28 | No portable result | Sets the current disk's software read-only bit. It does not change hardware protection or provide a symmetric unprotect call. Use documented reset behavior to clear the software state. |
| **29 (1Dh) Return Read-Only Vector** | C=29 | HL=mask, bit 0=A | Reports software disk read-only state, not each file's R/O attribute. |
| **30 (1Eh) Set File Attributes** | DE=FCB name/pattern with desired type high bits | A=0–3 success; FFh failure | Sets CP/M attribute bits. A selector predicate in a utility is not this API. Preserve name characters while setting high bits; do not turn an attribute update into a rename. |
| **31 (1Fh) Get Disk Parameter Block** | C=31 | HL=active DPB, zero on locked context failure | Borrowed read-only pointer. Copy values you need before disk-context changes and interpret 16-bit fields little-endian. |
| **32 (20h) Set/Get User Code** | E=FFh query; otherwise user | A=current/resulting user | Locked setting masks to five bits (modulo 32); validate 0–31 yourself instead of using masking as input validation. User is global BDOS selection, not part of an FCB. Restore it when a reusable routine promises to preserve caller context. |

### Search details and wildcard boundaries

Ordinary search matches CP/M positional `?` patterns, not the user-facing shared DU/attribute selector language. The locked special drive-byte `?` search path can inspect broader raw directory entries; it is not an ordinary cross-drive file selector. Use an initialized ordinary search FCB unless implementing a deliberate directory utility. A return slot `s` selects `DMA + 32*s`. Directory data is overwritten by subsequent use of DMA; copy it before another I/O call.

A directory iterator is not an open application file handle. Do not use a saved search result as a writable allocation map. For file access, Open/Make establish the active FCB and the file services own the map. Software mutation does not acquire optional SAFEFS validation merely because the core rejects some invalid addresses or geometries.

<a id="bdos-33-40"></a>

## BDOS 33–40: random access and reset

| Function | Inputs | Result | Behavior, side effects and failure boundary |
| --- | --- | --- | --- |
| **33 (21h) Read Random** | DE=live FCB with R0/R1/R2; current DMA | A=0 transferred; nonzero missing/unwritten/seek/I/O failure | Reads the selected 128-byte record. Locked code activates an extent if needed and uses the sequential read engine; its missing/invalid paths can collapse to 1 or FFh rather than every historical detailed code. Random access positions CR without incrementing the supplied random number. |
| **34 (22h) Write Random** | DE=live FCB with random record; current DMA | A=0 transferred; nonzero failure | Writes/allocates the addressed record. Locked allocation-full=2, new directory/extent failure can be 5, general error FFh. Unwritten portions of an allocated block are not promised zero by this operation. Close to finish metadata. |
| **35 (23h) Compute File Size** | DE=exact-name FCB | R0/R1/R2=exclusive logical end in records; locked A=0 or FFh | Scans all matching extents; it is not exact host byte length or allocated disk size. Missing/error must not be mistaken for a valid zero-byte file. |
| **36 (24h) Set Random Record** | DE=FCB with sequential extent and CR | Writes R0/R1/R2 | Converts the current sequential position into a random record number. Does not read, write or find EOF. Does not advance to another random record. |
| **37 (25h) Reset Drive** | DE=16-bit drive mask, bit 0=A | Locked A=0 | Clears selected login/software-read-only bits and invalidates active disk context. Close files before media/reconfiguration operations. This does not scan or repair filesystems or supply background media-change detection. |
| **38 (26h) Reserved** | No published CP/M 2.2 operation | Locked A=0, HL=0 | Reserved. Do not use as a feature or rely on its result to identify an OS. |
| **39 (27h) Reserved** | No published CP/M 2.2 operation | Locked A=0, HL=0 | Same boundary as 38. |
| **40 (28h) Write Random with Zero Fill** | Same addressing/DMA as 34 | A=0 transferred; nonzero failure | Zeroes a newly allocated block before writing the requested record. It is not a promise to zero every hole between prior EOF and the requested record. Preserve the active FCB; the locked implementation uses its live extent/map state. |

The historical detailed random-I/O vocabulary includes 1=unwritten data, 2=allocation full, 3=close failure, 4=unwritten extent, 5=directory allocation failure and 6=out-of-range record. Those codes are useful background, not a claim that every locked BetterCP/M failure path returns that fine-grained taxonomy. Treat **any nonzero transfer result as failure**, distinguish a sequential EOF only where defined, retain the original status for diagnostics, and never silently replace failed reads with zero data.

## BIOS vectors

The standard table has 17 three-byte JMP entries. Derive the BIOS base from the target of page-zero JMP WBOOT minus 3, validating the expected environment first. Do not subtract from the address 0000h itself or use a historical BIOS base literal. A BIOS call bypasses BDOS's filesystem ownership and reset rules. Ordinary applications should use BDOS; direct disk calls require exclusive, deliberate control of buffers and disk context.

| Index / offset | Entry | Input | Output and obligations |
| --- | --- | --- | --- |
| 0 / +0 | BOOT | Platform cold-entry state | Cold initialization and entry to command environment; no normal return. A porter must initialize all required state. |
| 1 / +3 | WBOOT | Warm return | Reconstructs command environment, preserves supported protected RSXs/history; no normal return. It is not complete machine reset. |
| 2 / +6 | CONST | None | A=00h not ready, FFh ready. Must not consume a character. |
| 3 / +9 | CONIN | None | Blocking console input in A; locked public BIOS applies its 7-bit convention. |
| 4 / +12 | CONOUT | C=character | Console output; no standard result. Maintain platform/monitor state. |
| 5 / +15 | LIST | C=character | List-device output; availability is platform-specific. |
| 6 / +18 | PUNCH | C=character | Punch-device output. |
| 7 / +21 | READER | None | Reader character in A. No universal host EOF protocol. |
| 8 / +24 | HOME | None | Select track zero for subsequent I/O. Preserve consistent controller/logical selection. |
| 9 / +27 | SELDSK | C=zero-based drive; E=login hint (bit 0 distinguishes first/subsequent selection) | HL=DPH, zero if unavailable/invalid. Do not reinterpret E as a format selector. |
| 10 / +30 | SETTRK | BC=track number | Record selection for subsequent disk call; unit must match the normalized drive interpretation. |
| 11 / +33 | SETSEC | BC=translated sector | Set physical-sector selection in the adapter's documented convention. |
| 12 / +36 | SETDMA | BC=address | Set the 128-byte disk transfer address. This is separate from calling BDOS Function 26's DE convention. |
| 13 / +39 | READ | Prior select/track/sector/DMA | A=0 success; nonzero failure. Do not consume destination bytes as valid on error. |
| 14 / +42 | WRITE | Same setup; C=0 ordinary, 1 directory, 2 first write to new allocation block | A=0 success; nonzero failure. Respect directory/write-through and blocking semantics, not just the bytes. |
| 15 / +45 | LISTST | None | A=00h unavailable/not ready, FFh ready under the implemented route. |
| 16 / +48 | SECTRAN | BC=zero-based logical sector; DE=translation table or zero | HL=translated sector for SETSEC. Identity-with-no-table semantics and physical sector IDs must match the platform/format, not an assumed universal +1. |

Conventional BIOS callers save registers they need; do not infer BDOS aliases/preservation. Locked disk interfaces and monitor callbacks have their own explicit preservation rules. A BIOS adapter must restore its caller's stack and must not secretly enter a reentrant BDOS path from console callbacks or a timed disk loop.

Private vectors begin after +48 and are **not additional CP/M 2.2 vectors**. BetterCP/M uses +51 physical reads, +54 cursor support, +57 control overlays, +60 RSX manager/resolver loading, +63 character capability query, +66 MONCALL, +69 MONRAW and +72 MONBASE in the inspected implementation. These belong to the [BetterCP/M integration contract](BETTERCPM-API.md#bios-private-boundary), not a promise that another CP/M BIOS has those entries.

## Disk parameter structures

| DPH offset | Size | Meaning |
| --- | ---: | --- |
| 0 | 2 | XLT sector-translation table pointer, zero where the adapter uses identity/default translation. |
| 2, 4, 6 | 2 each | BIOS/BDOS scratch words; not application workspace. |
| 8 | 2 | Directory buffer pointer. |
| 10 | 2 | DPB pointer. |
| 12 | 2 | CSV check-vector pointer. |
| 14 | 2 | ALV allocation-vector pointer. |

The DPB is 15 bytes: SPT word at +0; BSH +2; BLM +3; EXM +4; DSM word +5; DRM word +7; AL0 +9; AL1 +10; CKS word +11; OFF word +13. Words are little-endian. DSM and DRM are last indexes, not counts. AL0/AL1 reserve directory blocks. Allocation block bytes are `128 * 2^BSH`; BLM must be consistent with BSH. EXM and allocation-map entry width depend on capacity/block geometry. CSV uses CKS bytes; ALV needs enough bits for DSM+1 blocks.

SPT/OFF are logical filesystem units, not universally physical sector counts and cylinders. For the locked runtime binding, normal formats use side-track logical units; BCPM780 catalogue cylinder units are normalized through the accepted binding path. Do not repair an apparent factor-of-two discrepancy by editing a DPB behind its owner. See the [porting disk chapter](../porting/practical_porting_guide.md#disk-integration).

Pointers returned by Functions 27/31 or a DPH are borrowed. Locked allocation/check workspaces are shared and reconstructed on context changes. Copy descriptive fields when needed; allocate through file services. Directly altering a returned bitmap/DPB bypasses validation and can corrupt other users of the disk.

## Errors and compatibility boundaries

Normal result values, console messages and nonlocal termination are different error channels. Locked read-only mutation paths can print `File R/O` or `Disk R/O` and warm boot. A normal-return cleanup sequence is then bypassed. Keep important edits in a work file, avoid modifying global routes unless necessary, and document which exceptional exits cannot restore application state.

No API here adds multi-file atomicity, power-loss durability, background media-change detection, authenticated FCB maps, named directories, PATH, filesystem timestamps or bank-aware execution. Higher-level utilities can preflight/stage operations but their guarantees must be stated separately. BCPM-AUD-003 malformed-history hardening and AUD-007 historical-oracle work retain their recorded dispositions.

Primary implementation anchors are [unified BDOS](../../src/bdos/unified.mac), [BIOS vectors](../../src/bios/bios.mac), [Program Execution Model](../architecture/09%20Program%20Execution%20Model.txt), [Compatibility Architecture](../architecture/12%20Compatibility%20Architecture.txt) and the [locked release scope](../releases/non-documentation-lock-1.0/README.md). Historical DRI Interface Guides must include the 2.2 addendum for Functions 37 and 40. The internal [service inventory](../../metadata/bdos-service-inventory.tsv) is a refactoring map, not a replacement for this complete public interface coverage.
