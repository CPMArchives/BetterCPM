# BetterCP/M

BetterCP/M is an effort to design a compact, maintainable successor to CP/M 2.2 while preserving a rigorously defined CP/M-compatible environment.

The project has entered implementation. Its first TRS-80 Model 4 loader now boots a BetterCP/M-owned stage-one diagnostic from a reproducibly generated system disk.

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
[`Engineering Specification 25`](docs/engineering/25%20Allocation%20and%20DPB%20Pointers.md) exposes the current drive's reconstructed allocation vector and live 15-byte disk parameter block.

## First boot

```sh
python3 tools/build_trs80_boot.py
python3 tools/build_native_trs80.py
python3 tools/test_trs80_boot.py
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
python3 tools/build_system.py
python3 tools/test_system.py
python3 tools/build_native_system.py
```

The native build runs ZSM4 and Digital Research LINK under CP/M and must match the cross-assembled binaries byte for byte. The emulator test boots the generated 790K DMK, verifies the stage-one display, proves a raw-sector read, and injects and echoes a Model 4 matrix-level keypress through the platform interface.

These are working engineering documents. They record the present design thinking and may change as project goals and requirements are refined.

## Related work

BetterCP/M's compatibility foundation is developed separately in the [CP/M 2.2 Compatibility Suite](https://github.com/CPMArchives/cpm-2.2-compatibility-suite).
