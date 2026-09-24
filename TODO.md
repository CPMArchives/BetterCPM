# BetterCP/M Project Backlog

Status: Living project backlog  
Updated: 2026-09-21

This document records substantial unfinished work. Detailed behavioral
requirements remain authoritative in the architecture, engineering
specifications, compatibility ledger, and programmers' guides. Completed
bring-up history is kept in those documents rather than repeated here.

The authoritative ordering of design and implementation work is the
[BetterCP/M 1.0 roadmap](docs/releases/1.0-ROADMAP.md). This backlog supplies
the detailed tasks but does not replace or reorder that roadmap.

## Immediate priorities

- [ ] Enforce at least 53 KiB usable TPA in the default 1.0 configuration as a
  continuous build and qualification gate. Apply it after each remaining PDS,
  disk-state, CONFIG, clock, RSX, CPX and CCP integration;
  do not defer aggregate memory accounting until release qualification.
- [ ] When resuming CONFIG.COM, implement the agreed active/startup settings
  separation, configurable cold-boot drive capacity, and two H save scopes.
  See [CONFIG startup decisions](docs/engineering/CONFIG-STARTUP-SETTINGS-DECISIONS.md).

The first release milestone is engineering and compatibility qualification of
BIOS, BDOS and their accompanying structures. Freeze that core baseline before
finalizing the CCP and later distribution milestones. See
[1.0 milestone scope](docs/releases/1.0-SCOPE-DRAFT.md#milestone-1-qualify-and-finalize-the-system-core).
The older task inventory below is not a requirement to finish every higher-level
feature before qualifying the core.

- [ ] Resume BIOSTEST where physical testing stopped and reconcile every
  catalog entry against the current system image.
- [ ] Rerun ENTRYTST, BDOSTEST, FILETEST, RANDTEST, DIRTEST, CPUTEST, and
  BIOSTEST after the later memory, CCP, CPX, RSX, and command changes.
- [ ] Record every result as pass, failure, observation, provider-dependent,
  optional, or out of scope; leave no silent omissions.
- [ ] Audit and compact the resident system so the production TPA returns to
  the same general size class as stock CP/M, beyond the current 51K + 765-byte TPA.
  Packing recovered 4,608 bytes; reaching 56K still requires 4,355 bytes of
  additional resident reduction, not more gap removal.
- [x] Inventory functions 13 through 40 against a single set of universal
  drive, FCB, directory, extent, allocation, transfer, and recovery services.
- [x] Replace the separate dispatcher/filesystem implementation with the
  unified BDOS specified by Engineering Specification 123; require no more
  than 3.5K for functions 0 through 40 before switching the system build.
  Integrated at 3,373 bytes with 211 bytes free; extension and BIOS support
  are separately accounted in Engineering Specification 125. Full physical
  compliance regression remains the separate task above.
- [x] Pack the protected layout and verify that transients can overwrite the
  recovered memory without losing BDOS, RSXs, or WBOOT reconstruction.
- [x] Measure and publish the memory cost of the core, buffers, persistent
  DATA, installed RSXs, CPXs, and CCP.

## Command environment and RCP.CPX

Agreed 1.0 boundary: the stock CCP contains only GET, JUMP, PEEK/P, POKE, GO and
SAVE as built-in commands. RCP.CPX supplies DIR, ERA, TYPE, REN, USER, CLS, VER,
COPY and MOVE. The contracts are fixed in `docs/architecture/16 Resident Command
Set.txt`; the first implementation and focused command tests are complete.
Full SUBMIT/XSUB compatibility is required; further flow-control functionality
is supplied through loadable CPXs rather than added to the core CCP.

- [x] Move SAVE from RCP.CPX into the stock CCP and qualify memory-image
  preservation; it must work without loading RCP.CPX or a transient.
- [x] Specify and qualify the six core commands and remove transitional
  standard-command copies after RCP.CPX qualification.
- [x] Qualify full SUBMIT/XSUB compatibility with original command files and
  submitted-input workflows, including error/abort and warm-boot behavior.

- [x] Add stock `USER` behavior to `RCP.CPX`.
- [x] Complete the RCP command inventory `DIR`, `ERA`, `REN`, `TYPE`, `USER`,
  plus the BetterCP/M extensions `CLS`, `VER`, `COPY`, and `MOVE`.
- [x] Supply matching transient `DIR.COM`, `ERA.COM`, `REN.COM`, `TYPE.COM`,
  `USER.COM`, `CLS.COM`, `VER.COM`, `COPY.COM`, and `MOVE.COM` fallbacks. They must reproduce the
  corresponding RCP.CPX behavior and must not acquire a divergent
  transient-only feature set.
- [x] Keep `SAVE` resident-only: a transient `SAVE.COM` would overwrite the
  TPA contents that it is supposed to save.
- [ ] Remove the transitional command copies from the core CCP only after the
  CPX implementations and applicable transient fallbacks are verified.
- [ ] Remove transitional core `VER` now that identical RCP.CPX and `VER.COM`
  implementations are verified.
- [x] Provide transient-only `WARM.COM` for scripts and testing. Interactive
  users retain canonical, disk-independent `Ctrl-C` warm boot; `WARM` does not
  belong in RCP.CPX.
- [x] Finalize RCP.CPX by removing SAVE after its CCP migration, renaming CLR to
  CLS, and adding COPY and MOVE with both source/destination and `dest:=source`
  syntax.

### Later 1.x named-directory and command extensions

- [ ] Implement the canonical named-directory map in protected, persistent OS
  DATA, as confirmed by the user. Names resolve to drive/user pairs. The map
  survives transient execution and CCP reconstruction/warm boot; the CCP and
  utilities share one resolution interface and no independent authoritative maps.
  Specify its bounded storage, initialization and interface as part of the core
  boundary; implement higher-level navigation and utility syntax in their own
  milestones. Persistence across power-off is a separate save/load decision.
- [ ] Add transient `NDR.COM` to manage the live map and load/save disk-backed
  sets such as `DEVLPMNT.NDR` and `GAMES.NDR`. A future optional `NDR.CPX` may
  expose the same `ND` command forms. Both must call the common protected
  resolver; these files are backing sets, not the live lookup database. Follow
  `docs/architecture/17 Named Directory Register.txt`.
- [ ] Finish common named-DU resolution and use it consistently for command
  lookup, RCP commands, transient utilities, and module loading.
- [ ] Implement a system `PATH` facility for command lookup across canonical
  `DU:` locations, with documented search order, failure behavior, and CPX
  command precedence. Accept named-directory references as input conveniences,
  but resolve them immediately to canonical `DU:` entries for storage and
  runtime use (for example, `ROOT:,UTILS:,C3:,GAMES:` might resolve to
  `A0:,A1:,C3:,B0:`).
- [ ] Add a low-priority customizable prompt facility. Supported prompt fields
  should include the current drive/user (`DU:`), named directory, and current
  date/time while preserving a compact CP/M-style default.

### 1.0 bounded history and PDS

The packed, multi-command history buffer in the PDS is already
implemented, as are Up/Down recall and warm-boot persistence.  The current
53K layout reserves 192 bytes (182 bytes of command records).  This is the
temporary size accepted while the resident-memory trade-offs are reviewed;
do not reduce it again.  It requires regression coverage during the full
compatibility rerun, not a new implementation.

- [ ] Finish the versioned PDS descriptor and fixed 1.0 inventory; measure every
  retained 1.0 owner using `docs/engineering/130 Protected Memory Audit.md`,
  publish ownership and reset behavior, and preserve the 53 KiB TPA floor.

### Later 1.x PDS generalization

- [ ] Make the cold-boot PDS size configurable while preserving 53 KiB in the
  default profile. Saving this setting must be independent of saving drive
  formats. Runtime contraction always waits for cold boot.
- [ ] Generalize resident-layout reconstruction and module-state contracts for
  RSX load/unload, compaction, and controlled runtime PDS expansion. Keep
  complex preparation in transient code, preserve only
  declared state, enforce the minimum-TPA policy, and never shrink the physical
  high-water boundary before cold boot.

## Candidate CP/M transient utility inventory

This list is input to the final 1.0 utility-selection decision, not the release
contract. A selected requirement may be satisfied by a suitably licensed,
redistributable existing utility; an unchecked item does not by itself block
1.0.

- [ ] Implement `PIP.COM`.
- [ ] Implement `STAT.COM`.
- [ ] Implement `DUMP.COM`.
- [x] Implement `SUBMIT.COM`.
- [x] Implement `XSUB.COM`.
- [ ] Implement `ED.COM`.
- [ ] Implement `ASM.COM`.
- [ ] Implement `LOAD.COM`.
- [ ] Implement `DDT.COM`.
- [ ] Implement a BetterCP/M `MOVCPM.COM` equivalent for supported memory and
  resident-system configurations.
- [x] Implement `SYSGEN.COM` installation of the running A: system on a
  compatible prepared target, with record-by-record readback, file-area
  preservation and a cold-boot acceptance test. Image retrieval remains a
  possible later extension rather than an alpha installation requirement.
- [ ] Specify and compare each replacement against reference CP/M behavior;
  matching names alone do not establish compatibility.

Existing freely redistributable community utilities may be included in the
distribution when useful. BetterCP/M need not create another enhanced
directory utility unless it provides genuine additional value.

## CPX and RSX production interfaces

- [x] Replace the proof `BCX1` CPX carrier with the versioned, documented
  `BCPX` v1 format while retaining native CP/M ZSM4 assembly of module code.
- [x] Replace the proof `BRX1` RSX carrier with a versioned, documented module
  format practical to build under native CP/M with ZSM4.
- [x] Inventory the private BDOS namespace and adopt Functions 176-199 under
  `docs/architecture/25 Extended BDOS Namespace.txt`.
- [ ] Migrate the registered production services from provisional Functions
  200 and 202-209 to 176-183, remove HELLO/ECHO proof selectors 201/203 from
  the released namespace, and rebuild every in-tree client. The replacement
  CPX call uses a versioned, name-based request block and enumerates module
  metadata without compiling module identities into `CPX.COM` or BDOS.
- [ ] Finalize CPX initialization, shutdown, metadata, command enumeration,
  ordering, dependency, recursion, abort, and capability-discovery rules.
- [ ] Remove BASIC/HELLO-specific knowledge from the CPX manager and support
  arbitrary valid CPX files.
- [ ] Finalize the RSX dispatch, chaining, bypass, initialization, shutdown,
  error, and reentrancy ABI.
- [x] Support arbitrary valid RSX files rather than only the HELLO proof,
  including ordered enumeration and removal from a multi-module chain.
- [ ] Make extension reconfiguration transactional, with validation,
  rollback, and a recovery configuration that boots without optional modules.
- [ ] Define optional state export/import without preserving stale pointers.
- [ ] Preserve explicit extension ordering and reject missing dependencies,
  conflicts, and cycles.
- [ ] Keep the RSX/CPX Programmer's Guide synchronized with every stabilized
  interface before promising third-party binary compatibility.
- [ ] Keep the qualified CP/M-compatible SUBMIT/XSUB and `BATCHIO.RSX` path as
  the 1.0 batch facility. Treat `SUBMIT.CPX`, `FLOW.CPX`, and the extended
  language in `specifications/BATCH-FLOW-CONTROL.md` as later 1.x work.
- [ ] After 1.0, implement the persistent command-input system specified in
  `specifications/COMMAND-INPUT-SYSTEM.md`: expand the one-byte output-time
  pending key into a BDOS type-ahead ring, add a completed-command queue, and
  integrate multiple commands, history, batch sources, and scripted input
  without conflating their distinct state.
- [ ] Maybe: on platforms with bank-switched memory, provide a `BANKMEM.RSX`
  exposing portable extended-BDOS query, allocation, and inter-bank transfer
  services over a small hardware-specific BIOS/HAL interface. This is an
  optional-module possibility, not a requirement for ordinary 64K targets.

## Post-1.0 Developer Platform

- [ ] Apply `docs/architecture/26 Developer Platform Direction.txt` as a
  future-compatibility review when freezing the remaining 1.0 interfaces;
  preserve inexpensive ABI headroom without adding speculative 1.0 machinery.
- [ ] Define a collision-resistant allocation policy for stable,
  experimental, project-local and third-party CPX, RSX and service identities.
- [ ] Investigate supported introspection, demonstrated optional hooks,
  removable tracing/diagnostics, an extension SDK, minimal ABI examples,
  native development tools, and native build/test integration as independent
  later-1.x increments.
- [ ] Before distributing Digital Research LINK 1.3, record the exact binary
  hash, z80pack and compatibility-suite provenance, and applicable
  redistribution permission in the BetterCP/M third-party inventory.

## Configuration, installation, and disk formats

### DUP development order

Complete these stages in order:

1. [x] Finish reliable disk formatting (option A), including validation,
   failure reporting, and verification of the resulting disk images.
2. [x] Implement disk copying (option B) and checking disks for errors (option C),
   sharing the formatter's verification path and restoring temporary destination
   configuration. Continue broader media/platform qualification with formatting.
3. [x] Stabilize CONFIG/DUP, implement CONFIG H to save current A: defaults,
   and provide standalone SYSGEN to install a verified bootable system.
4. [ ] After DUP and CONFIG H are complete, discuss which remaining settings
   belong in a modern CP/M implementation before implementing more CONFIG
   menus. Review MM's settings as a reference: retain useful portable settings,
   identify hardware/driver-specific settings, and consider retiring obsolete
   ones. MM parity means the agreed useful capabilities, not blindly cloning
   every historical setting. Verify implemented behavior against that scope.
5. [ ] Reconsider a disk editor only after that parity work. Physical-sector
   and logical-record views, hex/ASCII display, and explicit edit/write actions
   remain possible later enhancements.

Command-line configuration is a design consideration for scripted setups.
Use the same parameter validation and application routines as the menus, with
unambiguous errors and completion status. Define command syntax, runtime versus
saved settings, and explicit authorization of system-disk writes before treating
the scripting interface as stable; no syntax is committed yet.

Format selection within DUP and the division of format-editing functions
between CONFIG and DUP remain design considerations for the formatting work.

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
- [x] Select the existing California Computer Systems 40T DS DD 332K format as
  the initial default floppy distribution format. The decision and migration
  gates are specified in `docs/architecture/23 Default Floppy Format.txt`.
  Implementation remains part of the generalized host-image builder and DUP
  formatter work; no private BetterCP/M floppy format was introduced.
- [ ] Decide whether later BetterCP/M-native disk formats need compatible
  timestamp or attribute extensions; the MM 790K format remains a development
  carrier rather than an architectural filesystem commitment.

## File metadata, attributes, and native clock

- [ ] Implement complete CP/M file-attribute handling throughout BDOS,
  directory services, resident commands, transient utilities, and image
  tooling, including read-only, system (`$SYS`), archive, and the filename
  high-bit conventions used to encode them. Preserve and permit inspection or
  change of all three ordinary bits, enforce read-only, and treat archive as
  metadata only.
- [ ] Finish and qualify the Functions 200/201 clock-provider ABI, `TIME.COM`,
  and the read-only FreHD and z80pack providers. Verify exact P2DOS success
  behavior, freeze the minimal status values, and qualify provider replacement,
  unload and WBOOT. With no provider installed, both calls must return 0FFh
  rather than a fabricated clock value.
- [ ] Adapt `TIME.COM` to use Functions 200/201 for display and SET requests,
  and ship `P2DOS.MAC` as the standard provider source with a stable
  `CLKHW.INC` contract plus `CLKFREHD.INC` and `CLKZ80PK.INC` library modules.
- [ ] Before the 1.0 ABI freeze, implement the adopted 176-199 private BDOS
  namespace: migrate the registered services to 176-183, remove HELLO/ECHO
  proof selectors 201/203 from the released namespace, rebuild every in-tree
  client, provide the 0FFh BDOS fallback for 200/201, and adapt each clock RSX
  to intercept their P2DOS-compatible meanings. Pin exact historical success
  behavior and the remaining status values before implementation.

### Later 1.x date/time and timestamp work

- [ ] Qualify unmodified date/time utilities for the five-family candidate set:
  DateStamper, ZSDOS/ZDDOS, P2DOS, CP/M Plus, and DOS+/Z80DOS. Start with
  DateStamper and ZSDOS/ZDDOS. Cover detection, call/entry conventions, return
  behavior and applicable file timestamp layouts, not only clock reads.
- [ ] Add and qualify a writable clock provider only with defined error,
  validity, rollover, and persistence behavior. Function 201 and TIME.COM's SET
  request already belong to the 1.0 interface; this later task supplies working
  writable hardware/provider support rather than adding the public operation.
- [ ] Scope filesystem timestamps separately from the clock service, including
  persistent/on-disk representation and behavior without a real-time clock.
- [ ] Extend the native directory/filesystem design to store file timestamps
  while retaining the chosen level of cpmtools compatibility and defining
  behavior for legacy disks without timestamp metadata.
- [ ] Propagate date/time and timestamp support through BDOS calls, directory
  operations, file creation/update semantics, CONFIG, disk-image tools,
  cpmtools definitions or extensions, and relevant utilities.
- [ ] Extend `TIME.COM` to inspect or modify file timestamps only when those
  later capabilities have defined on-disk contracts.

## ROMability

- [ ] Inventory every writable resident object by owner, lifetime, cold/warm
  behavior and RAM class (bounded PDS, fixed subsystem state, stack or shared
  workspace). Prove static overlay lifetimes before sharing storage and derive
  the final protected boundary from the completed inventory; do not freeze
  `E300h` as ABI.
- [ ] Qualify actual execution in place of BetterCP/M immutable code under
  enforced ROM write protection. Locate every stack, variable, live
  configuration, disk-state object and reconstruction record in RAM, exercise
  cold/warm boot and representative runtime paths, and fail on any attempted ROM
  write. A ROM-to-RAM bootstrap does not satisfy this 1.0 acceptance test.
- [ ] Extend and pin the z80pack/cpmsim qualification runtime so the configured
  BetterCP/M ROM region is genuinely read-only and any attempted write is a
  deterministic test failure. Retain that emulator change with the ROM-profile
  evidence rather than relying on an unprotected memory-map convention.
- [ ] For 1.0 ROMability, consolidate mutable drive definitions and disk
  workspaces into the fixed persistent RAM layout, separate from ROM-resident
  defaults and routines. Preserve DPH pointer interfaces, define cold/warm/reset
  rules, and budget history/named-directory space explicitly. Moving tables
  alone does not reduce their RAM cost.

## Devices and portability

- [ ] Qualify trs80gp/Model 4 and z80pack/cpmsim as the two 1.0 platform
  targets. RomWBW support is staged after 1.0 as described below; it is not a
  1.0 release gate.

- [ ] Complete configurable `CON:`, `RDR:`, `PUN:`, and `LST:` routing and
  `IOBYTE` behavior, including absent-device and timeout rules.
- [ ] Add and test the z80pack/cpmsim platform port.
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
  PDS, CPX ABI, and RSX ABI.
- [ ] Define release versioning, compatibility promises, upgrade rules, and
  automated release acceptance tests.

## Recommended execution order

The former task-oriented list in this section predated the accepted staged
architecture process and is superseded by the
[canonical 1.0 roadmap](docs/releases/1.0-ROADMAP.md). In particular, Stage 3,
the final scope freeze, Stages 4 through 7, and the Stage 8 architecture
reconciliation gate precede the corresponding implementation program.

## Post-1.0 considerations

- [ ] Replace provisional Model 4-only terminal operations with a portable
  terminal-capability interface while retaining `CLR` behavior.
- [ ] Give `$SYS` files enhanced system-wide visibility across user areas only
  after defining isolation, lookup and duplicate-result behavior.
- [ ] Target a bounded, single-bank RomWBW/HBIOS port for the first suitable
  post-1.0 minor release (1.1 or 1.2). Pin one RomWBW/HBIOS version and one
  repeatable hardware or emulator configuration; implement console, block-device,
  boot, and clock-provider integration; and qualify the applicable BetterCP/M
  core tests. Keep BetterCP/M within its existing 64 KiB execution model and do
  not expose RomWBW banks to the core, PDS, RSXs, or transient programs. Broader
  RomWBW configurations and devices may follow in a later minor release.
- [ ] Reserve full RomWBW integration for 2.0. Design and qualify explicit bank
  ownership and allocation, bank-qualified references, inter-bank call and copy
  services, bank-aware PDS/RSX/transient lifecycles, reconstruction across bank
  changes, and a generalized firmware/device architecture. Treat this as an
  architectural version boundary rather than an expansion of the basic HBIOS
  adapter.
- [ ] After 1.0, evaluate a conventional third 64 KiB platform without making
  it a retroactive 1.0 release gate. Prefer z80pack Cromemco for disk/controller
  and removable-media evidence; retain Altair/Tarbell as the lower-cost
  demonstration option and IMSAI/FIF as the controller-diversity option. Assign
  a release only after deciding whether this is a demonstration or a continuing
  qualification target. See the
  [post-1.0 third-platform assessment](docs/engineering/POST-1.0-THIRD-PLATFORM-ASSESSMENT.md).
- [ ] Preserve the demonstrated Cromemco hybrid-density requirement for a
  future required FDF/FDB extension that can describe track ranges with
  different encoding, sector counts and sector sizes. Do not design or add that
  extension during 1.0 unless a required 1.0 format proves FDF/FDB v1
  insufficient; uniform and already-supported formats remain the 1.0 path.
- [ ] Evaluate a common BIOS core with separately loadable device/controller
  drivers, selected by machine configuration, rather than one monolithic
  machine-specific extension. Investigate a BIOS driver interface, bootstrap
  requirements, dependencies, safe unloading, and RAM costs. This is deferred
  research, not a 1.0 requirement or an instruction to implement now. See
  [loadable BIOS device-driver proposal](docs/engineering/BIOS-DRIVERS-FUTURE.md).

## Deferred disk-change enhancement

- [ ] Automatic relogging after media-change detection. Consult available
  ZSDOS/ZDDOS and ZRDOS source and documentation before implementation.
  Define safe treatment of open FCBs, dirty buffers, and interrupted writes;
  start by considering relogging at the idle command prompt. Current work
  implements the CP/M 2.2 read-only response, not automatic relogging.
