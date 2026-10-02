# Implementation Step 5 contract audit

## Purpose

Implementation Step 5 completes the retained CONFIG, DUP, SYSBUILD, SYSGEN,
installation and two-platform work. This audit turns that heading into a fixed
set of bounded deliverables. It does not restore deferred variable PDS,
sixteen-drive, device-discovery, power-failure-atomic or third-platform work.

The acceptance authority is Section 3.6 of the 1.0 Implementation Contracts.
Architecture Specifications 24 and 28 govern configuration and disk state;
Engineering Specification 139 governs the native build and installation path.

## Current source result

Step 4 completed the production FDB transition. CONFIG and DUP consume the
compiled catalogue, CONFIG constructs normalized candidate bindings, the BIOS
owns active bindings, and release media no longer carry the transitional text
catalogue. That work is not reopened here.

CONFIG's physical-first F and G panels and checked H save path are implemented.
The save path validates the `BCSG` carrier, patches the installed resident
configuration tables, verifies every changed record and attempts rollback after
ordinary I/O failure. It currently saves active drive configuration only; it
does not provide the retained startup-command facility or a general saved-state
record with independently selectable pending/current scopes.

The command processor has one command-acquisition point, `CCP_READLN`, before
normal navigation, core-command, CPX and transient dispatch. The resident
gateway has distinct `SYS_COLD` and `SYS_WARM` entries. These are sufficient to
implement once-only startup without adding another dispatcher. No persistent
startup record exists today. The fixed gateway ends at D6BCh with only eight
unused bytes before the BDOS, while an ordinary CCP command may contain 126
characters. The startup line therefore must receive an explicit versioned
storage representation; it must not be hidden in gateway padding, history, a
temporary overlay or an unowned portion of `SYSGEN.DAT`.

DUP already performs substantial media, binding and format validation. Its
remaining retained obligation is a measured backend capability matrix and
clean pre-destructive rejection wherever the active backend cannot implement a
selected format. It is not an invitation to add every historical format or a
new device framework.

SYSBUILD already creates and verifies the frozen 161-record `SYSTEM.SYS` from
the nine retained products. SYSGEN installs either that package or an installed
source system into compatible reserved tracks while preserving the ordinary
filesystem. The remaining work is qualification from clean frozen inputs,
including a populated destination and both required 1.0 platforms.

## Fixed completion checklist

Step 5 has exactly these five deliverables:

1. **Versioned saved configuration and startup record.** Define one owned,
   validated representation for the retained saved drive state and optional
   command. Preserve the existing installed-system binding and reject wrong
   version, wrong build, malformed length and invalid complete configurations
   before the first write.
2. **CONFIG startup controls and save semantics.** Allow the command to be
   inspected, edited, cleared and tested immediately. Save pending cold-only
   changes without silently capturing unrelated session changes, or explicitly
   save all current retained settings. Display which scope is being saved.
3. **Once-only cold dispatch and recovery.** Arm startup only on true cold
   entry, set the warm-persistent executed flag before command dispatch, bypass
   it on WBOOT and reconstruction, return to the prompt without retry after
   failure, and suppress it for one boot with the documented recovery gesture.
4. **DUP capability closure.** Publish and test the supported/unsupported matrix
   for each required backend. Reject known-unsupported formatting before the
   first destructive write and qualify supported format, copy and check paths.
5. **Native install and platform closure.** From clean sources, build the nine
   frozen components and `SYSTEM.SYS`, install it on a populated compatible
   disk, prove the filesystem is unchanged, and boot the result under
   z80pack/cpmsim and trs80gp/Model 4. Preserve exact artifacts, hashes,
   commands and transcripts for release qualification.

No additional Step 5 deliverable may be inferred from older broad backlog
entries. A newly observed failure is handled by a targeted probe and the
smallest correction within one of these five items. Any requirement outside
them returns to scope review rather than silently extending Step 5.

## Increment order

Implement the checklist in dependency order: saved representation; CONFIG
editing and save scopes; gateway/CCP lifecycle; DUP capability closure; then
clean native and platform qualification. Each increment must leave focused
host tests passing and retain the 53 KiB TPA gate. Platform tests are added
when the corresponding behavior exists; they are not substitutes for
byte-level storage and lifecycle tests.

## Storage decision required by the first increment

The first increment must select the persistent record from measured existing
media and memory ownership. The representation must accommodate the ordinary
CCP line limit plus enabled state, length, version and integrity data. Runtime
state is separate: only the executed/suppressed state needs warm-boot-persistent
RAM. A disk-backed saved record may be loaded into reconstructible CCP storage
for dispatch, but neither the CCP buffer nor the fixed gateway can be the
power-off owner.

This is an implementation-layout decision inside the frozen startup lifecycle,
not a reopening of the command architecture.
