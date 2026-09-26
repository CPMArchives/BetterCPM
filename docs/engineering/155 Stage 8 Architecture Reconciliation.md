# Engineering Specification 155: Stage 8 Architecture Reconciliation

## Purpose

Stage 8 reconciled current architecture, programmer documentation, scope,
roadmap, README and backlog material with the contracts frozen through Stage 7.
It changed documentation only. Missing executable behavior remains
implementation work under the 1.0 roadmap.

Post-Stage-8 implementation update: Engineering Specification 157 records the
completed production-selector migration, 200/201 fallback and P2DOS frontend.
The source-audit findings below remain the historical Stage 8 baseline.

The governing release contract is
`docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md`. Historical engineering records
remain valid accounts of their milestones, including provisional selectors and
intermediate formats, but do not override later architecture.

## Bounded source audit

The repository audit confirmed:

- CCP dispatch is drive/user navigation, core compatibility commands, the CPX
  chain, then transient lookup.
- The production metadata normalizer handles the implemented callable-service
  and runtime-pointer records but currently skips unknown metadata-v1 types.
  The frozen contract requires rejection without publication.
- BIOS-owned physical records and normalized active logical bindings exist.
  Text FDF and FDF.RSX exist; production FDB compilation/consumption, broader
  saved-state handling and startup-command execution remain incomplete.
- Engineering Specification 139 matches the nine stable SYSBUILD inputs:
  `BOOT.BIN`, `STAGE1.BIN`, `RESIDENT.BIN`, `CCPRELOD.BIN`, `RSXSEL.BIN`,
  `CONFIG.BIN`, `RSXLOAD.BIN`, `RSXRESOL.BIN`, and `CCP.RLM`.
- Function 30, STAT support, R/O enforcement and SYS/ARC preservation are
  implemented and need final release-candidate qualification.
- TIME.COM and the FreHD and z80pack read-only providers exist. Selector
  migration, TIME.COM SET, P2DOS.RSX and the 200/201 absent fallback remain.
- cpmsim ROM write protection and guard tests exist. The integrated BetterCP/M
  ROM/RAM split and protected XIP image remain implementation work.
- DUP is partially implemented: substantial validation exists, while remaining
  backend-capability/integration behavior and final qualification remain.

These findings match Engineering Specification 154 except for no change in
architecture or retained scope.

## Reconciled authority and scope

Current documents now agree on these 1.0 invariants:

- required platforms: trs80gp/Model 4 and z80pack/cpmsim;
- default TPA: maximum 54,272-byte record-aligned COM image, exactly 53 KiB;
- PDS: fixed 192-byte HISTORY v1 object only;
- production private selectors: assigned 176-183, unassigned 184-196,
  reserved escape 197, and non-public tests 198/199;
- P2DOS clock frontend: Functions 200/201 through P2DOS.RSX;
- production RSX carrier: BRSX v2;
- service discovery: Function 182;
- native TIME: hardware-independent, with read-only 1.0 providers permitted;
- disk authority: BIOS physical records plus self-contained normalized logical
  bindings;
- FDF v1: uniform-sector core plus required mixed-sector capability;
- mixed-track formats: deferred;
- file attributes: R/O, SYS and ARC, without timestamps or enhanced SYS
  visibility; and
- ROM acceptance: actual execution in place under enforced write protection.

## Supersession map

The current controlling set consists of the 1.0 roadmap and implementation
contracts; Architecture Specifications 20, 21, 22 and 24-29; the Disk Format
Definition Specification; CONFIG startup decisions; Engineering Specification
139; and source audits 152-155.

Architecture Specifications 4, 6, 7, 14 and 18 remain conceptually useful but
are refined by the focused specifications. Architecture Specification 15 is a
historical initial-design question record. Architecture Specification 17 is
accepted future NDR design deferred from 1.0. Engineering Specification 120 is
the superseded BRSX-v1 carrier record. Provisional selector assignments in
historical engineering specifications remain historical implementation facts.

## Deferred work

Later 1.x retains HISTORY.RSX, NDR/PATH, a general PDS, terminal-capability
redesign, filesystem timestamps, broader historical clock/OS adapters,
mixed-track FDF/FDB and developer-platform facilities. The bounded single-bank
RomWBW/HBIOS port remains a 1.1 or 1.2 candidate. General bank-aware RomWBW
architecture remains 2.0 work. The final 1.0 utility and disk inventory remains
a later 1.0 decision point, not deferred post-1.0 scope.

## Implementation inventory

The implementation program remains responsible for the cold HISTORY reset,
selector migration, complete CPX/RSX behavior, unknown-metadata rejection,
FDB, saved CONFIG state and startup command, remaining DUP work, native build
and installation qualification, TIME.COM SET, P2DOS.RSX, protected ROM XIP,
packaging/provenance, utility selection and final two-platform qualification.

## Disposition

No controlling specifications conflict after reconciliation. Stage 8 is
complete. The implementation program is the current critical path.
