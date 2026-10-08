# BetterCP/M Project Backlog

Status: Living project backlog  
Updated: 2026-09-27

This document records substantial unfinished work. Detailed behavioral
requirements remain authoritative in the architecture, engineering
specifications, compatibility ledger, and programmers' guides. Completed
bring-up history is kept in those documents rather than repeated here.

The authoritative ordering of design and implementation work is the
[BetterCP/M 1.0 roadmap](docs/releases/1.0-ROADMAP.md). This backlog supplies
the detailed tasks but does not replace or reorder that roadmap.


Architecture is frozen through Stage 8. The implementation program is now the
current critical path. Items below that implement a frozen contract are engineering
tasks, not unresolved architecture; historical or deferred designs do not
become 1.0 requirements by appearing in this backlog.

## Immediate priorities


- [x] Implement the frozen 176-183 production selector migration, move proof
  services to 198/199, and provide the 200/201 unhandled fallback and
  `P2DOS.RSX` frontend.
- [x] Make true cold boot initialize an empty HISTORY v1 PDS object
  unconditionally while preserving valid history across WBOOT/reconstruction.
- [x] Reject unknown metadata-v1 BRSX record types without changing the live
  profile.
- [ ] Implement the frozen startup-command lifecycle; retain DUP's remaining
  backend-capability and integration work. The production FDB compiler/reader,
  107-definition migration, native CONFIG/DUP transition, dead text-reader
  removal and release-media cleanup are complete in Engineering Specifications
  183 through 192. Engineering Specification 193 fixes the remaining Step 5
  checklist: saved/startup representation, CONFIG controls and save scopes,
  once-only cold dispatch and recovery, DUP capability closure, and clean native
  install plus two-platform qualification.
- [ ] Complete TIME.COM SET, then qualify both read-only providers and
  `P2DOS.RSX` against the migrated production selectors.
- [x] Implement and qualify the BetterCP/M ROM/RAM split and protected XIP image.
  The measured writable-object baseline, including the executable three-byte
  RAM gateway, is now machine checked by `metadata/rom-ram-ownership.tsv` and
  Engineering Specifications 159–160. Engineering Specification 161 assigns
  the initial z80pack RAM map and derives a `DF00h` protection boundary.
  Engineering Specification 162 generates and verifies its RAM initialization
  template, and Engineering Specification 163 executes the bounded cold
  initializer in isolation. Engineering Specification 164 proves the complete
  immutable packing budget without claiming executable relocation. Engineering
  Specifications 165–166 inventory and apply all resident address references,
  producing an address-complete executable artifact. Engineering Specification
  167 connects the ROM cold entry, relocated reloader and ROM-profile system
  disk and boots them through transient execution under cpmsim. Engineering
  Specification 168 relocates the reconstructed CCP's 63 external layout
  references and qualifies the complete path under locked `DF00h` CPU/DMA write
  protection. Engineering Specification 169 measures the three retained stacks
  during protected cold/warm execution and preserves at least 14 bytes of
  reserve in each. Engineering Specification 170 proves the retained workspace
  lifetimes. Engineering Specification 171 relocates all 18 file-backed RSX
  transaction artifacts, accounts for their 704 address words, and qualifies
  dynamic load/list/unload with 53 KiB TPA recovery under protection.

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

- [x] Add stock `USER` behavior to `RCP.CPX`. Engineering Specification 177
  removes the transitional core fallback after qualifying both RCP and
  transient paths.
- [x] Complete the RCP command inventory `DIR`, `ERA`, `REN`, `TYPE`, `USER`,
  plus the BetterCP/M extensions `CLS`, `VER`, `COPY`, and `MOVE`.
- [x] Supply matching transient `DIR.COM`, `ERA.COM`, `REN.COM`, `TYPE.COM`,
  `USER.COM`, `CLS.COM`, `VER.COM`, `COPY.COM`, and `MOVE.COM` fallbacks. They must reproduce the
  corresponding RCP.CPX behavior and must not acquire a divergent
  transient-only feature set.
- [x] Keep `SAVE` resident-only: a transient `SAVE.COM` would overwrite the
  TPA contents that it is supposed to save.
- [x] Remove the transitional command copies from the core CCP after verifying
  the CPX implementations and applicable transient fallbacks. Engineering
  Specifications 175 through 178 record the bounded removal increments.
- [x] Remove transitional core `VER` now that identical RCP.CPX and `VER.COM`
  implementations are verified.
- [x] Provide transient-only `WARM.COM` for scripts and testing. Interactive
  users retain canonical, disk-independent `Ctrl-C` warm boot; `WARM` does not
  belong in RCP.CPX. Engineering Specification 176 removes the transitional
  core fallback, so unqualified `WARM` now follows ordinary transient lookup.
- [x] Finalize RCP.CPX by removing SAVE after its CCP migration, renaming CLR to
  CLS, and adding COPY and MOVE with both source/destination and `dest:=source`
  syntax.

### Later 1.x named-directory and command extensions

- [ ] Implement the later-1.x canonical named-directory map in NDR.RSX-owned
  protected state. Names resolve to drive/user pairs, and all clients share one
  resolution interface with no independent authoritative maps. Define its
  bounded storage and lifecycle in that later feature; it does not occupy the
  frozen 1.0 PDS or reopen the 1.0 core boundary. Persistence across power-off
  remains a separate save/load decision.
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

The packed, multi-command history buffer in the PDS is implemented, as are
Up/Down recall and warm-boot persistence. Stage 5 freezes the existing 192-byte
region, including 182 bytes of command records, as the complete 1.0 inventory.
It requires regression coverage during the full compatibility rerun, not a
general allocator.

- [x] Freeze the versioned PDS descriptor and fixed 1.0 inventory, publish
  ownership and reset behavior, and preserve the 53 KiB TPA floor. See
  Architecture Specifications 18 and 29 and Engineering Specification 152.
- [x] Make cold boot unconditionally initialize an empty version-1 history
  object; warm boot and command-environment reconstruction continue to preserve
  a valid object. The focused lifecycle regression distinguishes the two paths.

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
- [x] Implement `STAT.COM` command families. Final qualification remains open;
  see `docs/engineering/128 STAT Utility.md` for the reconciled compatibility
  checklist. Next: current Model 4 parity and preserved two-platform release
  evidence.
- [x] Add STAT inverse device-target queries (2026-10-08). Standard targets
  report every matching logical device or `not assigned`, using the existing
  IOBYTE name tables without changing mappings. Unknown targets and extra
  operands are rejected; assignment and numeric DU syntax remain intact.
  Executed-code checks cover all 256 IOBYTE decodes and shared/unused targets;
  native cpmsim query and existing file/drive campaigns pass. STAT.COM grows
  from 5,646 to 5,912 bytes; resident OS size is unchanged. Model 4 parity is
  retained in the final qualification work.
- [x] Qualify STAT wildcard attributes on private cpmsim media (2026-10-08).
  R/O, R/W, SYS and DIR update every matching physical extent. Whole-image
  comparisons permit only the expected directory attribute-bit changes:
  ARC, payload, extent/allocation metadata, a nonmatching multi-extent file
  and the same filename in user 3 remain unchanged. Read-only disk rejection
  reports both selected files and leaves the entire image unchanged. Preserve
  binaries, images, transcripts and hashes through the test's --report output.
  No production code correction was required.
- [x] Qualify native STAT large-directory/800K reporting (2026-10-08).
  A reverse-created 100-file fixture occupies 105 physical entries on an
  MM 800K disk. Complete sorted output and exact one/two/five-entry totals
  pass through native BDOS. All DPB fields and independently counted 512K
  free space match; inspection leaves the whole image unchanged. The test
  retains binaries, private media, transcript and hashes via --report.
- [x] Qualify the STAT device interface on Model 4/trs80gp (2026-10-08).
  Default 95h selectors, multiple assignments, shared/unused inverse targets,
  invalid queries and unchanged mappings/media pass in eight captured commands.
  The harness waits for output and the returned prompt before sending the next
  command; assertions inspect only output following that command's echo.
  Actual BIOS selector routing and the remaining STAT command families still
  require their separate qualification. No production code change was needed.
- [x] Qualify Model 4 STAT file totals and numeric DU (2026-10-08).
  Native 161/513-record files report exact 22K/66K allocation and two/five
  physical entries. Reverse-created wildcard fixtures list once in ascending
  order. Both 3: and A3: locate the user-3 fixture and restore A0:; a subsequent
  unqualified lookup correctly finds no user-0 copy. All six commands return
  to the prompt and leave the entire medium unchanged. Saved report includes
  STAT, media, invocation, decoded captures and hashes. No production fix.
- [ ] Required 1.0 qualification: close the standard CP/M 2.2 IOBYTE routing
  gap on Model 4/trs80gp and z80pack/cpmsim. Audit STAT's advertised assignments
  against actual BIOS behavior; implement and test supported selector routing,
  including BAT: input through RDR: and output through LST:. Document unavailable
  devices and their behavior. Verify cold default 95h, assignment changes, and
  preservation across WBOOT and command-environment reconstruction. Fixed-console
  and unassigned-device leaves do not constitute completed routing qualification.
  This is a compatibility correction before release, not the post-1.0 extensible
  named-endpoint proposal. See roadmap Item 9.

- [x] Correct STAT multi-extent collection and summary addressing (2026-10-07).
  Search now includes all extents; full-width summary offsets prevent wrapping
  after 16 files. Exact checks cover 161-record and 513-record files, 24-file
  listings, EXM=0 two-entry aggregation, and the 64-summary boundary. Collection
  beyond 64 distinct files initially reported an error instead of silently
  truncating; the later dynamic-buffer correction removes that fixed bound.
- [x] Complete assessed STAT VAL: help gap (2026-10-08): all legal device
  selections are printed from the parser tables, with $S logical-size guidance,
  multiple-assignment syntax and BAT: routing semantics. Strict cpmsim help and
  unchanged-assignment checks pass alongside the complete utility campaign.
  Final release qualification remains.
- [x] Remove STAT's fixed 64-file collection limit (2026-10-08). Summary storage
  uses available transient memory above the utility, capped by the selected
  disk's directory capacity. Word-sized counters support directories above 255
  entries. Executed-code checks cover 384 summaries, memory/directory capacity
  bounds, explicit overflow and 257-file sorting with metadata intact; the
  cpmsim utility campaign passes. STAT shrinks from 6,550 to 5,646 bytes.
- [x] Qualify STAT USR: on disposable cpmsim media (2026-10-08). A populated
  disk reports exactly users 0, 3, 15 and 31; an empty disk reports no occupied
  users. The active user is reported correctly and invocation from B3: restores
  B3: after scanning all 32 user areas. No utility code change was required.
- [x] Qualify STAT drive status on disposable cpmsim media (2026-10-08).
  Bare STAT reports the logged drives and their R/W or R/O state; B: reports
  exactly 240K free on a fixture with independently counted allocations.
  B:=R/O sets only B's public R/O-vector bit before WBOOT, and the next
  invocation confirms WBOOT clears it. B:=R/W is rejected. Drive inspection
  from B3: restores B3:. Test-only entry/exit probes expose state within the
  invocation because warm start resets login and temporary R/O vectors.
  No utility or resident OS code change was required.
- [x] Correct STAT filespec/option parsing (2026-10-07): name/extension stars,
  exact $S/$R/O/$R/W/$SYS/$DIR options, full-width names with following options,
  and malformed/trailing operand rejection. Mixed `?*` patterns are accepted;
  consecutive stars collapse to one. Characters following a star run within
  the same field, or stars beyond a full field, produce `Invalid filespec`.
  Instruction-level parser checks and
  cpmsim wildcard/attribute/rejection checks pass; rejected attribute options
  leave the test file R/W. The separate $S reporting correction is recorded below.

- [x] Check STAT attribute-update results (2026-10-07). A returned FFh reports
  failure; valid directory-slot success values remain accepted. Preflight the
  current drive's R/O vector to report rejection before BDOS's abort path.
  Controlled-result execution and disposable cpmsim success/read-only tests pass.

- [x] Correct STAT device assignments (2026-10-07). Matching starts each legal
  value at its table boundary; values require an end/space boundary. Process
  multiple space-separated assignments, reporting malformed later operands.
  PUN: now changes bits 4–5 rather than reader bits 2–3. All 16 legal values and
  unrelated-bit preservation pass instruction-level tests; cpmsim assignment
  lists, invalid values, trailing text and DEV: output pass. Assignments apply
  sequentially: an invalid later operand does not undo earlier valid assignments.
  Actual BIOS selector routing remains the separate open 1.0 requirement.

- [x] Sort STAT file summaries alphabetically by the 7-bit filename/type
  (2026-10-07), moving the complete summary so attributes and totals stay with
  each file. Empty, single, mixed name/type and 64-entry reverse-order checks
  pass; disposable cpmsim media created in reverse order prints ascending names.

- [x] Qualify Model 4 STAT sparse and ordinary $S (2026-10-08). A native
  random-write fixture reports 513 logical records, one recorded record, 2K
  allocated and two physical entries; raw directory checks independently
  confirm recorded data and allocation. The ordinary 161-record case also
  passes. Inspection leaves the whole disk unchanged. Reports preserve the
  fixture creator, STAT, media, captures and hashes. The harness waits for
  output and the returned prompt, then allows keyboard settling before the
  next command. No production code change was required.
- [x] Qualify Model 4 STAT wildcard attributes (2026-10-08). All four options
  update exactly the requested bits in seven selected physical extents.
  Complete logical-media comparisons preserve ARC, other attributes, payload,
  allocation/extent metadata, a nonmatching five-entry file and a matching
  filename in user 3. Read-only rejection reports both files and preserves
  the complete physical DMK image. Tests retain images, captures and hashes;
  no production code correction was required.
- [x] Qualify Model 4 STAT standard drive/DPB/user reports (2026-10-08).
  Five native commands report independently counted 706K free, exact 780K
  SYSTEM DPB fields and populated users 0/3/15. Captures confirm return to A0
  and whole-media preservation. R/O lifecycle, multiple-drive reporting,
  empty-disk enumeration and nonzero-user context remain separate cases.
- [x] Qualify Model 4 STAT R/O lifecycle and multiple-drive reports
  (2026-10-08). A:/B: status and full DPBs match the 780K SYSTEM/800K DATA
  fixtures. B:=R/O yields exactly the B-only public read-only vector; the
  next command after WBOOT reports both drives R/W. B:=R/W is rejected.
  Complete physical media remain unchanged. Test-only wrappers and retained
  captures preserve evidence; no production code change was required.
- [x] Report distinct STAT $S logical size (2026-10-08) through BDOS Function
  35's full three-byte result. Native random write to record 512 reports logical
  size 513, recorded total 1, allocation 2K, and two physical entries (the empty
  Make entry plus the random-write entry). Ordinary 161-record reporting and
  24-bit formatting boundaries pass. Size lookup failure displays unavailable.
  STAT runtime assertions now fail explicitly on every missing required output;
  the complete file/parser/attribute/device/sorting campaign passes that guard.

- [x] Complete STAT DSK: reporting (2026-10-08): record/KiB capacity,
  directory and checked-directory entries, records per extent/allocation block,
  normalized records per track, reserved tracks, allocation blocks and free space.
  Unqualified DSK: snapshots logged-in drives; drive-qualified DSK: reports only
  that drive. Native 332K DPB fields, one/two logged-drive cases and return to B3:
  after inspecting A: pass. Capacity arithmetic also passes 800K and word-carry
  boundary probes. Warm start resets the login vector, so merely accessing B:
  in a previous invocation does not include it in a later all-drive report.

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
- [x] Inventory the private BDOS namespace: assign production Functions
  176-183, leave 184-196 available, reserve 197, use 198/199 for non-public
  tests, and preserve historical P2DOS 200/201 for `P2DOS.RSX` under
  `docs/architecture/25 Extended BDOS Namespace.txt`.
- [x] Migrate the registered production services from provisional Functions
  200 and 202-209 to 176-183, remove HELLO/ECHO proof selectors 201/203 from
  the released namespace, and rebuild every in-tree client. The replacement
  CPX call uses a versioned, name-based request block and enumerates active
  names without compiling module identities into `CPX.COM` or BDOS.
- [ ] Implement and qualify the frozen CPX initialization, shutdown, metadata,
  command enumeration, configured ordering, recursion, abort, and capability-
  discovery rules.
- [x] Remove BASIC/HELLO-specific knowledge from the CPX manager and support
  arbitrary valid CPX files.
- [ ] Implement and qualify the frozen RSX dispatch, chaining, bypass, initialization, shutdown,
  error, and reentrancy ABI.
- [x] Support arbitrary valid RSX files rather than only the HELLO proof,
  including ordered enumeration and removal from a multi-module chain.
- [ ] Make extension reconfiguration transactional, with validation,
  rollback, and a recovery configuration that boots without optional modules.
- [ ] Define optional state export/import without preserving stale pointers.
- [ ] Preserve explicit CPX and RSX profile order and reject duplicate callable-
  service providers before publication. Retain the former configuration after
  any failed prospective validation.
- [ ] Keep the RSX/CPX Programmer's Guide synchronized with every stabilized
  interface before promising third-party binary compatibility.
- [x] Keep the qualified CP/M-compatible SUBMIT/XSUB and `BATCHIO.RSX` path as
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
- [ ] When a concrete component requires them, design a later carrier/metadata
  revision for declarative extension relationships: dependency identifiers and
  target/version semantics, installation capability requirements, conflicts,
  relative-order declarations, graph/cycle validation, and cross-CPX/RSX
  behavior. No minor release is assigned, and none of this is a 1.0 requirement.
- [ ] Investigate the
  [unified user-facing module model](docs/engineering/POST-1.0-UNIFIED-MODULE-MODEL.md):
  a common management interface may identify a validated BCPX or BRSX carrier
  and delegate to its existing class-specific manager, while RSX/CPX remains
  the authoritative lifetime distinction. Keep functional roles, service ABIs,
  and optional filename conventions separate. Resolve the historical
  `LOAD.COM` command-name conflict and the current stem-plus-class-extension
  profile format before approving any interface or arbitrary role-oriented
  extension. This is post-1.0 investigation, not a 1.0 implementation task.
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

- [x] Implement complete CP/M file-attribute handling throughout BDOS,
  directory services, resident commands, transient utilities, and image
  tooling, including read-only, system (`$SYS`), archive, and the filename
  high-bit conventions used to encode them. Preserve and permit inspection or
  change of all three ordinary bits, enforce read-only, and treat archive as
  metadata only. Focused implementation tests pass.
- [ ] Complete final release-candidate qualification of R/O/SYS/ARC inspection,
  change, enforcement, preservation and explicitly claimed host-tool behavior.
- [ ] Complete qualification of the frozen callable `TIME` ABI as the native clock service,
  including `TIME.COM` and the read-only FreHD and z80pack providers. Registry
  lookup now uses Function 182; qualify
  provider replacement, unload, WBOOT, coherent sampling, and SET_UNSUPPORTED.
- [x] Implement and focused-qualify a separate `P2DOS.RSX` frontend which intercepts Functions
  200/201 and calls the native `TIME` service without containing hardware code.
  Verify exact P2DOS success behavior and freeze only the minimal public results
  for success, unavailable, unsupported SET, and operation failure.
- [x] Implement the frozen private BDOS namespace: migrate the registered
  services to 176-183, remove HELLO/ECHO
  proof selectors 201/203 from the released namespace, rebuild every in-tree
  client, provide the 0FFh BDOS fallback for 200/201, and route those selectors
  through the separate `P2DOS.RSX` frontend to the native `TIME` service. Pin exact
  historical success behavior and the remaining public result values before
  implementation.

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
  `E300h` as ABI. The source-derived owner inventory, initial z80pack placement,
  `DF00h` boundary, initialization artifacts, immutable packing budget and
  complete 778-word relocation accounting, retained-stack capacity and static
  workspace lifetimes are machine checked; final focused closeout remains.
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

- [ ] Conduct a measured architectural retrospective immediately after 1.0.
  Record actual byte usage, memory and overlay pressure, awkward interfaces,
  recurring implementation problems, and technical debt without changing the
  released architecture during the review. Include the fixed 1 KiB CONFIG
  control-overlay limit and any local compaction or caller-validation choices
  made to preserve it as concrete evidence.
- [ ] Before full 2.0 design, use the 1.0 retrospective and experience from
  bounded later-1.x ports to reassess memory placement, workspace lifetime and
  overlay organization, ROM execution, PDS allocation, banking, firmware and
  device services, CONFIG/FDF/installation boundaries, and platform interfaces
  as one architectural problem. Preserve the 53 KiB TPA evidence and avoid
  turning the bounded RomWBW 1.1/1.2 port into an implicit redesign.
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
