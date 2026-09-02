# BetterCP/M Project Backlog

Status: Living project backlog  
Updated: 2026-09-03

This document records substantial unfinished work. Detailed behavioral
requirements remain authoritative in the architecture, engineering
specifications, compatibility ledger, and programmers' guides. Completed
bring-up history is kept in those documents rather than repeated here.

## Immediate priorities

- [ ] Resume BIOSTEST where physical testing stopped and reconcile every
  catalog entry against the current system image.
- [ ] Rerun ENTRYTST, BDOSTEST, FILETEST, RANDTEST, DIRTEST, CPUTEST, and
  BIOSTEST after the later memory, CCP, CPX, RSX, and command changes.
- [ ] Record every result as pass, failure, observation, provider-dependent,
  optional, or out of scope; leave no silent omissions.
- [ ] Audit and compact the resident system so the production TPA returns to
  the same general size class as stock CP/M, rather than the current 47K
  development layout.
- [ ] Measure and publish the memory cost of the core, buffers, persistent
  DATA, installed RSXs, CPXs, and CCP.

## Command environment and BASIC.CPX

- [ ] Add stock `USER` behavior to `BASIC.CPX`.
- [ ] Make the intended BASIC command inventory `DIR`, `ERA`, `REN`, `SAVE`,
  `TYPE`, `USER`, plus the BetterCP/M extensions `CLR` and `VER`.
- [ ] Supply matching transient `DIR.COM`, `ERA.COM`, `REN.COM`, `TYPE.COM`,
  `USER.COM`, `CLR.COM`, and `VER.COM` fallbacks. They must reproduce the
  corresponding BASIC.CPX behavior and must not acquire a divergent
  transient-only feature set.
- [ ] Keep `SAVE` resident-only: a transient `SAVE.COM` would overwrite the
  TPA contents that it is supposed to save.
- [ ] Remove the transitional command copies from the core CCP only after the
  CPX implementations and applicable transient fallbacks are verified.
- [ ] Remove transitional core `VER` after identical BASIC.CPX and `VER.COM`
  implementations are verified.
- [ ] Provide transient-only `WARM.COM` for scripts and testing. Interactive
  users retain canonical, disk-independent `Ctrl-C` warm boot; `WARM` does not
  belong in BASIC.CPX.
- [ ] Finish common named-DU resolution and use it consistently for command
  lookup, BASIC commands, transient utilities, and module loading.

The 512-byte packed, multi-command history buffer in persistent DATA is
already implemented, as are Up/Down recall and warm-boot persistence. It
requires regression coverage during the full compatibility rerun, not a new
implementation.

## Stock CP/M transient utilities

- [ ] Implement `PIP.COM`.
- [ ] Implement `STAT.COM`.
- [ ] Implement `DUMP.COM`.
- [ ] Implement `SUBMIT.COM`.
- [ ] Implement `XSUB.COM`.
- [ ] Implement `ED.COM`.
- [ ] Implement `ASM.COM`.
- [ ] Implement `LOAD.COM`.
- [ ] Implement `DDT.COM`.
- [ ] Implement a BetterCP/M `MOVCPM.COM` equivalent for supported memory and
  resident-system configurations.
- [ ] Implement a platform-aware BetterCP/M `SYSGEN.COM` equivalent for
  installing, retrieving, and verifying bootable system images.
- [ ] Specify and compare each replacement against reference CP/M behavior;
  matching names alone do not establish compatibility.

Existing freely redistributable community utilities may be included in the
distribution when useful. BetterCP/M need not create another enhanced
directory utility unless it provides genuine additional value.

## CPX and RSX production interfaces

- [ ] Replace the proof `BCX1` and `BRX1` carriers with versioned, documented
  module formats practical to build under native CP/M with ZSM4.
- [ ] Finalize CPX initialization, shutdown, metadata, command enumeration,
  ordering, dependency, recursion, abort, and capability-discovery rules.
- [ ] Remove BASIC/HELLO-specific knowledge from the CPX manager and support
  arbitrary valid CPX files.
- [ ] Finalize the RSX dispatch, chaining, bypass, initialization, shutdown,
  error, and reentrancy ABI.
- [ ] Support arbitrary valid RSX files rather than only the HELLO proof.
- [ ] Make extension reconfiguration transactional, with validation,
  rollback, and a recovery configuration that boots without optional modules.
- [ ] Define optional state export/import without preserving stale pointers.
- [ ] Preserve explicit extension ordering and reject missing dependencies,
  conflicts, and cycles.
- [ ] Keep the RSX/CPX Programmer's Guide synchronized with every stabilized
  interface before promising third-party binary compatibility.
- [ ] Eventually supply useful optional modules, including an extended
  SUBMIT/ZEX-like CPX, without delaying the core system.

## Configuration, installation, and disk formats

- [ ] Implement BetterCP/M `CONFIG` with saved RSX and CPX profiles, default
  drive/user state, logical-device assignments, disk-format presets, and
  field-level drive-parameter editing.
- [ ] Persist cold-boot defaults separately from the active runtime RSX chain
  and active CPX reconstruction table.
- [ ] Generalize the table-driven BIOS from the current Montezuma Micro 790K
  development carrier to multiple formats and mixed configured drives.
- [ ] Provide system-disk, data-disk, DSDD, DSHD, 80-track, and other useful
  native presets where supported by the platform.
- [ ] Define a semi-automatic or automatic conversion path from cpmtools
  `diskdefs`, filtering definitions by each platform's controller abilities.
- [ ] Convert useful Montezuma Micro definitions missing from cpmtools back
  into cpmtools-compatible definitions where possible.
- [ ] Implement platform-aware formatting, verification, and error reporting.
- [ ] Revisit automatic disk-change detection without requiring `Ctrl-C`,
  using safe checks appropriate to each controller.
- [ ] Complete bounded retry, timeout, recovery, and crash-consistency policy
  for physical and filesystem writes.
- [ ] Decide and specify BetterCP/M native disk formats and any compatible
  timestamp or attribute extensions; the MM 790K format is a carrier, not an
  architectural filesystem commitment.

## Devices and portability

- [ ] Complete configurable `CON:`, `RDR:`, `PUN:`, and `LST:` routing and
  `IOBYTE` behavior, including absent-device and timeout rules.
- [ ] Replace provisional Model 4-only terminal operations with a portable
  terminal-capability interface while retaining `CLR` behavior.
- [ ] Add and test the z80pack/cpmsim platform port.
- [ ] Prove the hardware-abstraction boundary on at least one substantially
  different additional machine or emulator.
- [ ] Build per-platform boot loaders, BIOS modules, disk-image builders, and
  installation tests while sharing portable system components where possible.
- [ ] Run compatibility tests on physical hardware when practical.

## Build, distribution, and release readiness

- [ ] Preserve native CP/M assembly/link builds for all system code and
  require byte-identical cross builds where practical.
- [ ] Produce reproducible source, binary, system, data, test, and recovery
  disk images.
- [ ] Record the license, authorship, version, and redistribution basis of
  every bundled third-party utility.
- [ ] Finish user documentation for installation, commands, configuration,
  disk handling, extensions, recovery, and upgrades.
- [ ] Finish programmer documentation for the BIOS, BDOS, system gateway,
  persistent DATA, CPX ABI, and RSX ABI.
- [ ] Define release versioning, compatibility promises, upgrade rules, and
  automated release acceptance tests.

## Recommended execution order

1. Close and rerun compatibility testing.
2. Recover a stock-class TPA through a measured resident-memory audit.
3. Add USER to BASIC.CPX and complete the resident/transient command split.
4. Stabilize configuration storage sufficiently to begin CONFIG.
5. Implement PIP, STAT, and BetterCP/M's MOVCPM/SYSGEN workflows.
6. Generalize disk formats and add z80pack as the second platform.
7. Stabilize the public CPX and RSX formats and ABIs.
8. Complete the remaining utilities, documentation, packaging, and physical
   platform validation.
