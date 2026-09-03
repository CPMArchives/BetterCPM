# BetterCP/M

BetterCP/M is an effort to design a compact, maintainable successor to CP/M 2.2 while preserving a rigorously defined CP/M-compatible environment.

The project has entered implementation. Its reproducibly generated TRS-80 Model 4 disks now load the resident BetterCP/M BIOS, BDOS, directory services, and CCP; expose physical floppy drives A: through D:; boot to an `A0>` drive/user prompt under `trs80gp`; accept direct `B:`, `5:`, and `C3:` navigation; provide visible-cursor CCP line editing with insert/overwrite modes, deletion, and persistent multi-command history; and store `BASIC.CPX`, `HELLO.CPX`, and `HELLO.RSX` as ordinary directory-visible files. A protected filename loader reconstructs default BASIC on cold boot and the active CPX set on WBOOT without relying on reclaimable command code. `CPX.COM` and `RSX.COM` accept module names with or without their extensions. The first protected RSX proof intercepts experimental BDOS Function 201 through the movable `0005h` gateway, survives WBOOT while CPXs and the CCP are reconstructed beneath it, and returns its allocation to the TPA on unload. BASIC provides `DIR`, `ERA`, `TYPE`, `REN`, `SAVE`, `USER`, `CLR`, and `VER`; all except inherently resident SAVE have ordinary transient counterparts, and transient-only WARM supports scripts. Optional HELLO proves multiple-module chaining and transient-command fallback. The system retains transitional core copies pending their final removal, loads transient `.COM` programs with CP/M command tails and default FCBs, and completes clean independent physical compatibility passes for `ENTRYTST /SAFE` (25 passes), `BDOSTEST /SAFE` (56 passes), `FILETEST /SAFE` (28 passes with no omissions), and the complete applicable RANDTEST catalog: 41 required passes and 7 diagnostic observations. The complete 72-item DIRTEST catalog is also accounted for: all 52 required cases pass physically, all 15 diagnostics are observed, and its 5 private-mechanism or otherwise out-of-scope cases are explicitly identified. CPUTEST closes its five-item processor catalog with 2 required passes, 1 observation, and 2 explicit exclusions. BIOSTEST now records 29 physical required passes, including write-protect recovery, controlled logical-device behavior, and all three retained-evidence BOOT/WBOOT procedures, plus 11 non-guaranteed observations; its remaining 6 catalog entries are explicitly provider-dependent, optional, or out of scope. The build also produces canonical cross-drive, multi-user, full-disk, and genuinely blank disposable fixtures for four-drive testing.

## Design direction

The current work emphasizes:

- CP/M 2.2 compatibility grounded in an explicit specification and conformance suite
- a memory footprint in the same general class as Digital Research CP/M
- a small command processor and an improved command environment
- a unified model for drives, user areas, named directories, and command search paths
- table-driven, inspectable configuration
- separation of portable system code from hardware-dependent support
- an architecture suitable for ROM-resident code
- explicit interfaces and state instead of magic addresses and undocumented dependencies

## Documents

The maintained [`Project Backlog`](TODO.md) is the comprehensive high-level
inventory of unfinished work and its recommended execution order.

The initial architecture material is in [`docs/architecture`](docs/architecture). It covers architectural principles and boundaries, memory and boot design, the command environment, system services, hardware abstraction, program execution, storage, system state, compatibility, constraints, extensions, and open questions.

The [`Utility Compatibility Ledger`](docs/compatibility/Utility%20Compatibility%20Ledger.md) inventories the standard CP/M commands and distribution utilities that BetterCP/M must replace, separates implemented prototypes from conformant replacements, and records the required evidence and planned DU extensions.

The initial [`RSX and CPX Programmer's Guide`](docs/programmers/RSX%20and%20CPX%20Programmer's%20Guide.md) records the extension model, current CPX dispatcher, and planned relocatable module lifecycle. Interfaces marked provisional in that guide are not yet promised as a stable third-party binary ABI.

The initial development target is defined in the [`Baseline Platform Specification`](docs/platform/Baseline%20Platform%20Specification.txt). The [`Architecture Readiness Review`](docs/reviews/Architecture%20Readiness%20Review.md) records the decision to begin Phase 2, and [`Engineering Specification 01`](docs/engineering/01%20Baseline%20Bring-Up%20Specification.md) defines the first diagnostic boot milestone.

TRS-80 Model 4 development uses the reproducibly generated [`Montezuma Extended 790K System Disk`](docs/platform/TRS-80%20Model%204%20Montezuma%20Extended%20790K.md) container. [`Engineering Specification 02`](docs/engineering/02%20TRS-80%20Model%204%20Boot%20Milestone.md) records the first verified boot, [`Engineering Specification 03`](docs/engineering/03%20Initial%20Hardware%20Abstraction%20Interface.md) records the first executable boundary between portable core and platform code, and [`Engineering Specification 04`](docs/engineering/04%20Console%20Input%20Milestone.md) adds verified keyboard input. [`Engineering Specification 05`](docs/engineering/05%20Initial%20BIOS%20Scaffold.md) begins the independently buildable resident-system compatibility surface, [`Engineering Specification 06`](docs/engineering/06%20BIOS%20Direct-Call%20Conformance.md) executes its raw entry contracts, [`Engineering Specification 07`](docs/engineering/07%20Shared%20Model%204%20BIOS%20Console.md) binds it to the shared Model 4 console implementation, [`Engineering Specification 08`](docs/engineering/08%20MM%20790K%20Drive%20Definition.md) adds the first DPH/DPB, and [`Engineering Specification 09`](docs/engineering/09%20Read-Only%20Logical%20Disk%20Path.md) adds physical and 128-byte logical reads.

[`Engineering Specification 10`](docs/engineering/10%20Exhaustive%20Logical%20Read%20Conformance.md) executes all 80 logical-sector mappings and verifies every 128-byte DMA quarter.
[`Engineering Specification 11`](docs/engineering/11%20Write-Through%20Logical%20Disk%20Path.md) adds verified 128-byte read-modify-write behavior and physical write/readback.
[`Engineering Specification 12`](docs/engineering/12%20Bounded%20Disk%20Errors.md) bounds every floppy-controller wait and defines verified BIOS failure behavior.
[`Engineering Specification 13`](docs/engineering/13%20First%20Directory%20Record.md) adds the first filesystem-facing System Services component and reads and classifies a CP/M directory record through the BIOS.
[`Engineering Specification 14`](docs/engineering/14%20Exact%20Directory%20Search.md) searches all 128 directory entries for an exact CP/M user-number and 8.3 filename match.
[`Engineering Specification 15`](docs/engineering/15%20DPH-DPB%20Drive%20Login.md) derives directory geometry and allocation-vector initialization from the selected drive's DPH and DPB, with explicit invalidation and re-login.
[`Engineering Specification 16`](docs/engineering/16%20Allocation%20Reconstruction.md) completes drive login by reconstructing file-owned blocks from both 8-bit and 16-bit CP/M directory extents.
[`Engineering Specification 17`](docs/engineering/17%20Read-Only%20FCB%20Open.md) adds the first exact, read-only FCB Open result with extent selection and compatible FCB activation.
[`Engineering Specification 18`](docs/engineering/18%20Grouped%20and%20Wildcard%20Open.md) adds DPB `EXM` grouping, RC adjustment, and first-match `?` wildcard activation.
[`Engineering Specification 19`](docs/engineering/19%20Initial%20BDOS%20Dispatcher.md) introduces the first CP/M-callable BDOS dispatcher and exposes function 15 through the standard C/DE register boundary.
[`Engineering Specification 20`](docs/engineering/20%20Page-Zero%20System%20Call%20Gateway.md) composes the provisional resident image, logs in the default drive, installs the conventional page-zero vectors, and executes function 15 through `CALL 0005h`.
[`Engineering Specification 21`](docs/engineering/21%20Basic%20BDOS%20State%20Functions.md) adds version, current-drive, persistent DMA-address, and modulo-32 current-user services through the public call path.
[`Engineering Specification 22`](docs/engineering/22%20Default%20Drive%20Selection.md) adds function 14 with login-before-commit default-drive selection and coherent function-25 reporting.
[`Engineering Specification 23`](docs/engineering/23%20Disk%20Reset%20and%20Login%20Vector.md) adds disk-system reset, login-vector reporting, default-DMA restoration, and current-user preservation.
[`Engineering Specification 24`](docs/engineering/24%20Software%20Write%20Protection.md) adds transient current-drive write protection, read-only-vector reporting, and reset clearing.

[`Engineering Specification 31`](docs/engineering/31%20Sequential%20Write.md) adds BDOS Write Sequential with DPB-driven mapping, protected-write rejection, and failure-safe first-block allocation.

[`Engineering Specification 32`](docs/engineering/32%20Transactional%20Allocation%20Close.md) adds journal-validated allocation-map Close commits without permitting arbitrary block claims.

[`Engineering Specification 33`](docs/engineering/33%20Automatic%20Sequential%20Extents.md) adds transactional `CR=128` Write Sequential rollover and canonical next-extent creation.

[`Engineering Specification 34`](docs/engineering/34%20Make%20File.md) adds BDOS Make File with duplicate detection, canonical empty-FCB activation, protection, and atomic failure rollback.

[`Engineering Specification 35`](docs/engineering/35%20Delete%20File.md) adds wildcard multi-extent Delete File with read-only preflight and allocation-state reconstruction.

[`Engineering Specification 36`](docs/engineering/36%20Rename%20File.md) adds exact multi-extent Rename File with duplicate-target rejection and byte-preserving attributes.

[`Engineering Specification 37`](docs/engineering/37%20Set%20File%20Attributes.md) adds wildcard multi-extent attribute updates and completes the implemented BDOS function range 12 through 32.

[`Engineering Specification 38`](docs/engineering/38%20Compute%20File%20Size.md) adds 24-bit extent-wide Compute File Size and begins random-record support.

[`Engineering Specification 39`](docs/engineering/39%20Set%20Random%20Record.md) adds sequential-to-random FCB position conversion without disk access.

[`Engineering Specification 40`](docs/engineering/40%20Random%20Read.md) adds strict CP/M 2.2 Read Random semantics, precise random-I/O status codes, and application-level verification.

[`Engineering Specification 41`](docs/engineering/41%20Random%20Write.md) adds CP/M-compatible Random Write with automatic extent/block allocation and distinct disk-full and directory-overflow results.

[`Engineering Specification 42`](docs/engineering/42%20Random%20Write%20with%20Zero%20Fill.md) adds Function 40 block initialization, giving newly allocated random-file records deterministic zero contents.

[`Engineering Specification 43`](docs/engineering/43%20Selective%20Drive%20Reset.md) adds bitmap-selected drive logoff, read/write restoration, cache invalidation, and verified re-login.

[`Engineering Specification 44`](docs/engineering/44%20Console%20Status.md) adds non-consuming CP/M console-status reporting through the portable BIOS boundary.

[`Engineering Specification 45`](docs/engineering/45%20Direct%20Console%20IO.md) adds nonblocking direct input and uncooked output through the standard BIOS console vectors.

[`Engineering Specification 46`](docs/engineering/46%20Cooked%20Console%20Input.md) adds blocking console input, cooked echo, tab expansion, flow control, abort handling, and printer echo state.

[`Engineering Specification 47`](docs/engineering/47%20Cooked%20Console%20Output.md) adds tab-aware console output, flow-control polling, and lossless one-character type-ahead preservation.

[`Engineering Specification 48`](docs/engineering/48%20Logical%20Character%20Devices.md) adds Reader Input, Punch Output, and List Output as portable pass-throughs to BIOS logical devices.

[`Engineering Specification 49`](docs/engineering/49%20Get%20IO%20Byte.md) exposes the shared conventional page-zero I/O byte without introducing private BDOS state.
[`Engineering Specification 50`](docs/engineering/50%20Set%20IO%20Byte.md) completes the paired IOBYTE interface while leaving logical-device routing at the BIOS/configuration boundary.
[`Engineering Specification 51`](docs/engineering/51%20Print%20String.md) adds dollar-terminated string output through the shared cooked-console path.
[`Engineering Specification 52`](docs/engineering/52%20Read%20Console%20Buffer.md) adds the counted-buffer line editor and completes the CP/M 2.2 console-service group.
[`Engineering Specification 53`](docs/engineering/53%20System%20Reset.md) completes the 39 defined CP/M 2.2 BDOS functions by routing program termination through BIOS WBOOT.
[`Engineering Specification 54`](docs/engineering/54%20Initial%20CCP%20and%20WBOOT.md) adds the first resident command loop, real BOOT/WBOOT reconstruction, and verified Function-0 return to the prompt.
[`Engineering Specification 55`](docs/engineering/55%20Physical%20Resident%20Boot.md) installs the composed resident image in the MM 790K system area and boots the physical TRS-80 disk to the CCP.
[`Engineering Specification 56`](docs/engineering/56%20Transient%20COM%20Loader.md) adds `.COM` loading at `0100h` and installs `HELLO.COM` as the first end-to-end transient fixture.
[`Engineering Specification 57`](docs/engineering/57%20Resident%20DIR.md) adds a resident `DIR` implemented through public BDOS Search First/Search Next calls and verifies it on the physical boot disk.
[`Engineering Specification 58`](docs/engineering/58%20Transient%20Command%20Tail.md) separates the transient name from its arguments, constructs the conventional command tail at `0080h`, and verifies it with `HELLO WORLD` on the physical disk.
[`Engineering Specification 59`](docs/engineering/59%20Default%20FCBs%20and%20First%20Compatibility%20Pass.md) adds ordinary default FCBs, general multi-extent file installation, the first independent `ENTRYTST` evidence, and a verified original `MDIR.COM` run.
[`Engineering Specification 60`](docs/engineering/60%20Model%204%20Console%20Scrolling.md) bounds the resident Model 4 console to 80 by 24 characters and adds verified line-feed and automatic-wrap scrolling.
[`Engineering Specification 61`](docs/engineering/61%20Function%2040%20Live%20FCB%20Reads.md) preserves unclosed same-extent Function 40 state for Random Read and revises the Directory Services placement to `D600h`.
[`Engineering Specification 62`](docs/engineering/62%20Delete%20of%20Unclosed%20Allocations.md) makes same-FCB Delete retire its pending allocations transactionally, enabling repeated Function 40 scratch-file lifecycles.
[`Engineering Specification 63`](docs/engineering/63%20BDOSTEST%20Introduction.md) installs the next compatibility executable, adds reliable Model 4 command automation, records its first physical baseline, and corrects unsupported-selector return semantics.
[`Engineering Specification 64`](docs/engineering/64%20Model%204%20Two-Drive%20Conformance.md) adds physical A:/B: support, explicit FCB drive selection, independent drive workspaces, paired conformance images, and a clean 56-case `BDOSTEST /SAFE` physical pass.
[`Engineering Specification 65`](docs/engineering/65%20FILETEST%20Open%20Slice.md) installs FILETEST and its canonical runtime fixtures and records a clean 26-case physical Function 15/Open pass, with only the two unavailable C: fixture cases reported as not-run.
[`Engineering Specification 66`](docs/engineering/66%20FILETEST%20Close%20and%20Sequential%20Read.md) records clean physical Function 16/Close and Function 20/Read Sequential slices, adding 24 applicable FILETEST passes without failures or errors.
[`Engineering Specification 67`](docs/engineering/67%20Four-Drive%20Binding%20and%20Sequential%20Write.md) extends the Model 4 binding to A: through D:, relocates immutable drive tables into the gateway gap, adds a canonical C: fixture image, and records a clean 16-case required FILETEST Write pass.
[`Engineering Specification 68`](docs/engineering/68%20Complete%20FILETEST%20Safe%20Profile.md) records the complete physical FILETEST safe profile with 28 passes, no failures or errors, and no unavailable cross-drive cases.
[`Engineering Specification 69`](docs/engineering/69%20RANDTEST%20Introduction.md) installs RANDTEST on the reproducible disk, records its first physical random-field passes, and adds the exact CP/M 2.2 record-65535 boundary to local BDOS regression coverage.
[`Engineering Specification 70`](docs/engineering/70%20Function%2033%20Random%20Read.md) records clean physical passes for all eight required Function 33 Random Read cases, including exact missing-extent and range-error return codes.
[`Engineering Specification 71`](docs/engineering/71%20Function%2034%20Random%20Write.md) records clean physical passes for all twelve required Function 34 Random Write cases, including persistence, sparse allocation, and exact range/full return codes.
[`Engineering Specification 72`](docs/engineering/72%20Function%2035%20Compute%20File%20Size.md) records clean physical passes for all five required Function 35 Compute File Size cases, including maximum-extent and sparse-file behavior.
[`Engineering Specification 73`](docs/engineering/73%20Returning%20Lifecycle%20and%20Full-Disk%20Fixture.md) adds the reproducible full D: fixture and records clean physical passes for all six required returning RANDTEST lifecycle cases.
[`Engineering Specification 74`](docs/engineering/74%20File%20Read-Only%20Terminal%20Path.md) adds CP/M's resident `File R/O` WBOOT path, corrects the read-only fixture attribute, and completes all 41 required RANDTEST items.
[`Engineering Specification 75`](docs/engineering/75%20RANDTEST%20Completion.md) records all seven non-guaranteed diagnostics and closes the 49-item RANDTEST catalog with only the explicitly out-of-scope private DRI seek implementation omitted.
[`Engineering Specification 76`](docs/engineering/76%20DIRTEST%20Search%20Introduction.md) installs DIRTEST, adds special all-user Search First and independent multi-user fixtures, and records a clean eleven-case Search slice.
[`Engineering Specification 77`](docs/engineering/77%20DIRTEST%20Delete.md) records clean physical passes for all nine required Delete cases plus the non-guaranteed open-FCB observation.
[`Engineering Specification 78`](docs/engineering/78%20DIRTEST%20Rename%20Required.md) records clean physical passes for all ten required Rename cases, including all-extents, data, user, and explicit-drive preservation.
[`Engineering Specification 79`](docs/engineering/79%20DIRTEST%20Rename%20Diagnostics.md) records the four non-guaranteed Rename observations and closes the group with its four explicitly out-of-scope cases identified.
[`Engineering Specification 80`](docs/engineering/80%20DIRTEST%20File%20Attributes%20Required.md) records clean physical passes for all twelve required file-attribute cases, including all-extent updates and read-only Delete and Rename protection.
[`Engineering Specification 81`](docs/engineering/81%20DIRTEST%20File%20Attribute%20Diagnostics.md) records the two non-guaranteed attribute observations and closes the File Attributes group.
[`Engineering Specification 82`](docs/engineering/82%20DIRTEST%20Search%20Continuation%20Required.md) records clean physical passes for all four required Search Continuation cases, including multi-extent enumeration and retained continuation state.
[`Engineering Specification 83`](docs/engineering/83%20DIRTEST%20Search%20Continuation%20Diagnostics.md) records the five non-guaranteed continuation observations and closes the Search Continuation group.
[`Engineering Specification 84`](docs/engineering/84%20DIRTEST%20User%20Areas%20Required.md) records clean physical passes for the seven directly executable required User Areas cases and distinguishes the remaining CCP-integration workflow.
[`Engineering Specification 85`](docs/engineering/85%20Resident%20USER%20and%20CCP-BDOS%20Integration.md) adds the resident `USER` command, relocates the CCP within resident memory, and records the successful required CCP-to-BDOS user-state workflow.
[`Engineering Specification 86`](docs/engineering/86%20DIRTEST%20Completion.md) records the final User Areas diagnostic and closes the complete 72-item DIRTEST catalog with all required, diagnostic, and out-of-scope cases accounted for.
[`Engineering Specification 87`](docs/engineering/87%20CPUTEST%20Completion.md) installs CPUTEST and closes its portable-processor catalog with both required Intel 8080-floor cases passing physically.
[`Engineering Specification 88`](docs/engineering/88%20BIOSTEST%20Safe%20Baseline.md) installs BIOSTEST and records clean physical passes for its five non-destructive returning checks without claiming its provider-dependent procedures.
[`Engineering Specification 89`](docs/engineering/89%20BIOSTEST%20Controlled%20Allocation%20and%20DPB.md) records seven controlled Allocation/DPB passes on disposable media and identifies four newly exposed disk-trace failures for focused correction.
[`Engineering Specification 90`](docs/engineering/90%20Resident%20Disk%20Structures%20Outside%20the%20TPA.md) relocates every DPH, DPB, CSV, and ALV object out of transient memory, refreshes cached geometry from the live DPB, and records the narrowed BIOSTEST follow-up.

[`Engineering Specification 91`](docs/engineering/91%20BIOSTEST%20Returning%20Baseline.md) closes the guarded BIOS-trace investigation, records 26 physical required passes including write-protect and logical-device control, and separates the 9 remaining manual/provider/profile procedures from core BIOS implementation.

[`Engineering Specification 92`](docs/engineering/92%20ERA%20System%20Utility.md) defines the completed resident and transient ERA baseline, including wildcard deletion, all-files confirmation, drive qualification, and stock cancellation/error behavior.
[`Engineering Specification 93`](docs/engineering/93%20Drive-Qualified%20Default%20FCBs.md) completes A: through P: default-FCB drive prefixes and physically verifies `MDIR B:` against a separate disk.
[`Engineering Specification 94`](docs/engineering/94%20CCP%20Wildcards%20and%20Buffer%20Relocation.md) completes `*`/`?` default-FCB wildcard handling and moves the private CCP stack into reserved resident space without shrinking the TPA.
[`Engineering Specification 95`](docs/engineering/95%20Command%20Processor%20Extensions.md) distinguishes CPXs from RSXs, adds the first chained CPX command-dispatch ABI, and replaces the CCP's exact-fit provisional slot with an explicit protected command region pending true WBOOT reload support.
[`Memory Architecture`](docs/architecture/04%20Memory%20Architecture.txt) defines the authoritative split between protected persistent DATA/RSXs and the reclaimable CPX/CCP command environment. A movable CP/M compatibility gateway advertises the true TPA ceiling through `0005h`; WBOOT preserves installed RSXs and reconstructs CPXs and the CCP. [`Engineering Specification 96`](docs/engineering/96%20Quantitative%20Memory%20Model.md) records the earlier fixed-`C000h` implementation milestone.
[`Engineering Specification 97`](docs/engineering/97%20Relocatable%20CCP%20and%20WBOOT%20Restoration.md) records the CCP-only reconstruction milestone and its then-current fixed `C000h` transient ceiling.
[`Engineering Specification 98`](docs/engineering/98%20Calculated%20Command%20Environment.md) removes the temporary CCP-size slot, establishes the movable `BFFDh` compatibility gateway, calculates the current CCP at `BAFDh`, and reconstructs an ordered persistent CPX profile before the CCP on every cold or warm boot.
[`Engineering Specification 99`](docs/engineering/99%20BASIC%20CPX%20and%20Keyboard%20Rollover.md) installs the first production `BASIC.CPX` with `DIR`, `ERA`, `TYPE`, and `REN`, verifies native/cross relocation parity and WBOOT reconstruction, and replaces the Model 4 whole-matrix key-release wait with a rollover-safe pending-key queue.
[`Engineering Specification 100`](docs/engineering/100%20Runtime%20CPX%20Manager.md) adds `CPX.COM`, provisional fixed-core profile control, and a physical runtime proof that BASIC.CPX can be listed, unloaded, and reloaded through safe WBOOT reconstruction.
[`Engineering Specification 101`](docs/engineering/101%20CPX%20Inventory%20and%20TPA%20Report.md) expands `CPX LIST` with the active module's command inventory and a live TPA calculation, verifying that reclaimable CPXs do not reduce the 47K transient area.
[`Engineering Specification 102`](docs/engineering/102%20Multiple%20CPXs%20and%20HELLO%20CPX.md) adds `HELLO.CPX`, generalizes runtime profile control to two independently selectable modules, and physically verifies concurrent chaining, selective unload, transient fallback, and unchanged TPA.
[`Engineering Specification 103`](docs/engineering/103%20Directory%20Buffer%20and%20Warm-Boot%20Write%20Integrity.md) removes a directory-buffer/BIOS overlap exposed by runtime CPX reconstruction and verifies that physical directory writes remain sound after WBOOT.
[`Engineering Specification 104`](docs/engineering/104%20Runtime%20RSX%20Proof.md) implements the first protected RSX lifecycle: a relocatable HELLO.RSX, movable gateway interception, runtime load/unload manager, visible TPA-boundary movement, WBOOT persistence, and a physical application-level proof through Function 201.
[`Engineering Specification 105`](docs/engineering/105%20Directory-Visible%20Extension%20Files.md) replaces fixed CPX/RSX system slots with ordinary directory-visible files, adds the protected filename reader used by cold boot and WBOOT, and stores filename stems in the active reconstruction table.
[`Engineering Specification 106`](docs/engineering/106%20Drive-User%20Navigation%20and%20Prompt.md) adds direct `B:`, `5:`, and `C3:` navigation, derives the `A0>` prompt from authoritative BDOS state, and verifies automatic downward CCP relocation after its next page of growth.
[`Engineering Specification 107`](docs/engineering/107%20CCP%20Command-Line%20Editor.md) adds CCP-only cursor editing, insert/overwrite modes, deletion, one-command history, and the portable logical-key/Model-4 matrix boundary without changing CP/M Function 10.
[`Engineering Specification 108`](docs/engineering/108%20Reverse-Video%20Cursor.md) adds the optional platform cursor-character service and Model 4 reverse-video cursor presentation.
[`Engineering Specification 109`](docs/engineering/109%20WordStar%20Editing%20and%20Persistent%20History.md) adds non-conflicting WordStar editing commands and a packed warm-boot-persistent command history.
[`Engineering Specification 110`](docs/engineering/110%20CCP%20Control-Key%20Compatibility.md) restores the documented CP/M control-key meanings, moves history to physical Up/Down, shares printer echo with cooked BDOS output, and resumes `Ctrl-S` pauses on any key.
[`Engineering Specification 111`](docs/engineering/111%20Stock-Compatible%20DIR.md) replaces the diagnostic one-name-per-line listing with CP/M's four-column DIR-status presentation, DPB-aware extent suppression, wildcard selection, and verified drive/DU qualification.
[`Engineering Specification 113`](docs/engineering/113%20Stock-Compatible%20REN.md) completes resident and transient REN behavior, exact-name and same-drive validation, stock diagnostics, native build parity, and the Model 4 equals-key correction required to enter its standard syntax.
[`Engineering Specification 114`](docs/engineering/114%20Stock-Compatible%20TYPE.md) completes resident and transient TYPE behavior, literal text and CP/M EOF handling, control-key integration, drive qualification, and the BetterCP/M `/P` page-at-a-time extension.
[`Engineering Specification 115`](docs/engineering/115%20Stock-Compatible%20SAVE.md) adds stock-compatible resident SAVE with decimal page counts, replacement, DU-qualified targets, and deterministic storage-error handling while documenting why a transient fallback cannot preserve TPA contents.
[`Engineering Specification 116`](docs/engineering/116%20CLR%20Command.md) adds the BASIC.CPX `CLR` command and records its provisional Model 4 console binding pending a portable terminal-capability interface.
[`Engineering Specification 117`](docs/engineering/117%20CP-M%202.2%20Utility%20Inventory.md) fixes the stock CP/M 2.2 transient baseline at eleven executables and separates portable utilities, installation tools, source artifacts, and OEM additions.
[`Engineering Specification 118`](docs/engineering/118%20Completed%20BASIC%20Command%20Set.md) completes BASIC.CPX with stock USER and BetterCP/M VER, adds matching DIR/USER/CLR/VER transient files, and verifies all new resident and transient paths.
[`Engineering Specification 119`](docs/engineering/119%20BCPX%20Version%201%20Module%20Format.md) supersedes the BCX1 proof carrier with the documented, versioned BCPX format and its filename-driven loader contract.
[`Engineering Specification 25`](docs/engineering/25%20Allocation%20and%20DPB%20Pointers.md) exposes the current drive's reconstructed allocation vector and live 15-byte disk parameter block.
[`Engineering Specification 26`](docs/engineering/26%20Directory%20Search%20and%20DMA.md) adds Search First/Search Next continuation, wildcard and all-user matching, and complete directory-record transfer to the selected DMA address.
[`Engineering Specification 27`](docs/engineering/27%20Unchanged%20FCB%20Close.md) adds the non-mutating Close File boundary for unchanged activated FCBs and safely rejects dirty commits until writeback exists.
[`Engineering Specification 28`](docs/engineering/28%20Transactional%20RC%20Close.md) adds the first guarded directory mutation: write-protected, range-checked `RC` Close commit with BIOS writeback and cache invalidation.
[`Engineering Specification 29`](docs/engineering/29%20Resident%20Memory%20Layout%20Revision.md) replaces the exhausted bring-up addresses with enforced workspace, gateway, BDOS, System Services, scratch, and BIOS growth regions while preserving `CALL 0005h`.
[`Engineering Specification 30`](docs/engineering/30%20Sequential%20Read.md) adds DPB-driven Read Sequential with 128-byte DMA transfer, FCB position advancement, stable EOF, and automatic extent transition.

## First boot

```sh
python3 tools/build_bios.py
python3 tools/test_bios.py
python3 tools/build_native_bios.py
python3 tools/test_trs80_physical_read.py
python3 tools/test_trs80_physical_write.py
python3 tools/build_directory.py
python3 tools/test_directory.py
python3 tools/build_native_directory.py
python3 tools/build_bdos.py
python3 tools/test_bdos.py
python3 tools/build_native_bdos.py
python3 tools/build_ccp.py
python3 tools/build_ccpreload.py
python3 tools/test_ccpreload.py
python3 tools/build_native_ccp.py
python3 tools/build_basic_cpx.py
python3 tools/build_native_basic_cpx.py
python3 tools/build_hello_cpx.py
python3 tools/build_native_hello_cpx.py
python3 tools/build_basic_transients.py
python3 tools/build_native_basic_transients.py
python3 tools/build_warm.py
python3 tools/build_native_warm.py
python3 tools/build_cpx_utility.py
python3 tools/build_native_cpx_utility.py
python3 tools/build_hello_rsx.py
python3 tools/build_rsx_utilities.py
python3 tools/build_native_rsx.py
python3 tools/build_fileloader.py
python3 tools/build_native_fileloader.py
python3 tools/build_system.py
python3 tools/test_system.py
python3 tools/build_native_system.py
python3 tools/build_trs80_boot.py
python3 tools/build_native_trs80.py
python3 tools/test_trs80_boot.py
python3 tools/test_trs80_keyboard_overlap.py
python3 tools/test_cpx_manager.py
python3 tools/test_cpx_wboot_write.py
python3 tools/test_rsx_manager.py
python3 tools/test_basic_command_completion.py
```

The native build runs ZSM4 and Digital Research LINK under CP/M and must match the cross-assembled binaries byte for byte. The emulator test boots the generated 790K DMK through the Model 4 ROM and both loader stages, loads the composed resident image, reconstructs the system, and verifies the CCP `A0>` prompt.

These are working engineering documents. They record the present design thinking and may change as project goals and requirements are refined.

## Related work

BetterCP/M's compatibility foundation is developed separately in the [CP/M 2.2 Compatibility Suite](https://github.com/CPMArchives/cpm-2.2-compatibility-suite).
