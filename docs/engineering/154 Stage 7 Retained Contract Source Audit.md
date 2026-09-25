# Engineering Specification 154: Stage 7 Retained Contract Source Audit

## Purpose

This document records the bounded repository audit used to publish
`docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md`. It distinguishes existing
implementation from work required later by the accepted contracts. It is not a
general source review and does not reopen architecture frozen in Stages 3–6.

## Audit results

### PDS cold initialization and TPA

`CCP_HINIT` currently preserves a history object whose descriptor appears
valid. Architecture Specifications 18 and 29 require true cold boot to create
an empty version-1 history object unconditionally. Correcting that cold path is
implementation work. Warm boot and reconstruction continue to preserve a valid
object.

The exclusive TPA ceiling remains `D501h`. Starting at `0100h`, this provides
54,273 addressable bytes and a maximum record-aligned COM image of 54,272
bytes, exactly 53 KiB.

### CPX, RSX and metadata

Engineering Specification 151 records the completed Stage 3 prepared-profile
commit and cross-platform qualification. Release acceptance must additionally
cover the complete CPX and RSX behavior published by the Stage 7 contract,
including ordering, dependencies, conflicts, cycle rejection, lifecycle,
failure recovery and arbitrary conforming module metadata.

The metadata-v1 normalizer recognizes the retained pointer and service records
but currently advances past other record types. Architecture Specification 21
requires every unknown record type to reject. A focused correction and fixture
are required; rejection must preserve the active profile.

### Command and batch behavior

Current CCP dispatch order is navigation, core compatibility commands, CPXs,
then transient lookup. `B:`, `5:` and `C3:` are retained navigation forms.
Drive-qualified directory and transient operations preserve the caller's
current drive/user unless navigation was explicitly requested.

Engineering Specification 129 records the stock-compatible SUBMIT/XSUB path.
The retained editor and bounded built-in history are implemented. These areas
need final release-candidate qualification, not architectural redesign.

### Disk formats, CONFIG, startup and DUP

The BIOS currently owns physical records and normalized active logical
bindings. Text `DISK.FDF`, the format library and `FDF.RSX` provide the current
format path. Production compilation and consumption of FDB records remain
implementation work. Saved-state provenance/fingerprint support and the
broader two-scope CONFIG design are not complete.

The startup-command behavior frozen in `CONFIG-STARTUP-SETTINGS-DECISIONS.md`
has no production implementation. DUP already performs important
binding/hardware/format validation, but remaining backend-capability behavior
and the final supported/unsupported matrix still require implementation and
qualification.

### Native build and installation

Engineering Specification 139 records the implemented native workflow. The
stable SYSBUILD input set is:

```text
BOOT.BIN
STAGE1.BIN
RESIDENT.BIN
CCPRELOD.BIN
RSXSEL.BIN
CONFIG.BIN
RSXLOAD.BIN
RSXRESOL.BIN
CCP.RLM
```

SYSBUILD creates and verifies the 161-record `SYSTEM.SYS`; SYSGEN installs it
into the reserved system area without replacing the ordinary filesystem. The
release still requires a clean native rebuild, install, boot and preservation
test using frozen artifacts.

### File attributes

BDOS Function 30, STAT inspection/change support, preservation through rename
and other applicable operations, and read-only enforcement are implemented.
Focused directory tests exist. Release-candidate qualification must cover raw
directory bits, preservation and enforcement. Enhanced SYS-file visibility and
filesystem timestamps are outside 1.0.

### TIME and historical frontends

`TIME.COM`, `FREHDCLK.RSX` and `ZPRTC.RSX` exist. The two providers implement
the same native read-only service. Current source still uses provisional
selectors, and TIME.COM does not implement SET. Migration to final Functions
182 and 177, TIME.COM SET handling, final qualification and `P2DOS.RSX` remain
implementation work. Functions 104/105 remain conditional candidates.

### ROM qualification

The cpmsim patch and focused guard tests cover CPU writes, DMA writes, guest
unlock/boundary control, reset re-protection and ordinary unprotected mode. The
BetterCP/M ROM/RAM split and integrated XIP image are not implemented. Final
workspace-lifetime proofs, stack measurements, the derived ROM boundary and
full protected execution remain implementation and qualification work.

## Documentation discrepancy

Architecture Specification 6 and current source place core compatibility
commands before CPXs. Programmer documentation that says CPXs receive first
refusal is stale and must be corrected during Stage 8.

## Disposition

No audit result changes the retained 1.0 architecture. Every missing item above
is scheduled as implementation or qualification work under the Stage 7
acceptance contract. Stage 7 is complete.
