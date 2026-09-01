# BetterCP/M

BetterCP/M is an effort to design a compact, maintainable successor to CP/M 2.2 while preserving a rigorously defined CP/M-compatible environment.

The project has entered implementation. Its reproducibly generated TRS-80 Model 4 disks now load the resident BetterCP/M BIOS, BDOS, directory services, and CCP; expose physical floppy drives A: through D:; boot to an `A>` prompt under `trs80gp`; list the physical directory with resident `DIR`; load transient `.COM` programs with CP/M command tails and default FCBs; and complete clean independent physical compatibility passes for `ENTRYTST /SAFE` (25 passes), `BDOSTEST /SAFE` (56 passes), `FILETEST /SAFE` (28 passes with no omissions), and the separate FILETEST Close, Sequential Read, and Sequential Write groups. `RANDTEST.COM` is now installed and its numbered random-I/O qualification has begun.

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

The initial architecture material is in [`docs/architecture`](docs/architecture). It covers architectural principles and boundaries, memory and boot design, the command environment, system services, hardware abstraction, program execution, storage, system state, compatibility, constraints, extensions, and open questions.

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
python3 tools/build_native_ccp.py
python3 tools/build_system.py
python3 tools/test_system.py
python3 tools/build_native_system.py
python3 tools/build_trs80_boot.py
python3 tools/build_native_trs80.py
python3 tools/test_trs80_boot.py
```

The native build runs ZSM4 and Digital Research LINK under CP/M and must match the cross-assembled binaries byte for byte. The emulator test boots the generated 790K DMK through the Model 4 ROM and both loader stages, loads the composed resident image, reconstructs the system, and verifies the CCP `A>` prompt.

These are working engineering documents. They record the present design thinking and may change as project goals and requirements are refined.

## Related work

BetterCP/M's compatibility foundation is developed separately in the [CP/M 2.2 Compatibility Suite](https://github.com/CPMArchives/cpm-2.2-compatibility-suite).
