# Unloadable monitor backend production integration

Status: 2026-10-16. Integration in progress. This record distinguishes production
changes from the [isolated prototype](Unloadable%20Monitor%20Backend%20Prototype.md).
It does not declare universal monitor support complete.

## Implemented: screen-service metadata admission

`SCRN` is now a reserved callable identity in the production BRSX metadata
normalizer. It is validated alongside the existing platform-bound `MCON` ABI:

- callable ABI version must be exactly 1.0;
- reconstruction class must be STATEFUL;
- capabilities must be exactly 1 for Model 4 or 2 for cpmsim, matching the
  installed BIOS character-capability query;
- other bits, unsupported versions, invalid entry offsets and malformed carrier
  metadata are rejected by the existing bounded validation path;
- failed normalization does not publish completion or change validated facts.

The new identity check reuses the existing MCON version/class/platform checks.
Other callable identities retain their opaque version/capability semantics.
No metadata record type, descriptor size or public BDOS/BIOS vector changed.
Unknown metadata records remain errors.

These rules establish admission to the callable registry, not backend selection
or screen-operation semantics. No production screen backend is yet packaged.
The prototype operation table remains a candidate pending complete personality
requirements (including reverse fill and insert/delete line handling).

The active monitor selector still accepts only its existing MCON 1.0 contract.
A hypothetical dependent MCON 1.1 frontend is rejected. It is not safe to enable
that frontend before dependency validation and commit-time rebinding exist.
The existence of SCRN in the registry does not by itself establish a dependency.

## Cost

| Component | Previous | Current | Budget |
| --- | ---: | ---: | ---: |
| Reloadable metadata normalizer | 881 | 901 | 1,024 |
| Reloadable slot preparer | 669 | 669 | 1,024 |
| Reloadable commit coordinator | 1,007 | 1,007 | 1,012 |

Values are bytes. The 20-byte increase is in a fixed-size management overlay;
its container slot count and slot sizes are unchanged. Permanent BIOS, BDOS,
resident gateway and extension-service sources/layout are unchanged.

## Qualification

After rebuilding `tools/build_rsx_runtime_overlays.py`:

- `tools/test_monitor_metadata.py`: 68 MCON/SCRN platform, version, entry and
  reconstruction cases; unrelated callable semantics remain unchanged.
- `tools/test_screen_backend_registry.py`: ten invalid SCRN LOAD attempts are
  rejected through the production manager while an existing monitor is active.
  Its binding, generation, available TPA, count and live allocation bytes remain
  unchanged. A valid synthetic SCRN provider loads alongside the monitor,
  Function 182 resolves it, its assembled callback executes, and both providers
  can be removed, restoring 53K TPA and the basic-console binding.
- `tools/test_monitor_selection.py --z80pack-build build/audit/release-090-z80pack`:
  existing monitor selection, duplicate/changed-carrier rejection, retained
  movement/state preservation, unload and TPA restoration pass.
- `tools/test_vt52_lifecycle.py --bios build/audit/release-090-z80pack`:
  existing VT52 install, parser/reply relocation, continuation, lookup and 53K
  unload pass.
- `tools/test_rsxcarrier.py`: carrier phases, bounded normalization, snapshot
  input and malformed/unknown-metadata rejection pass.

Synthetic SCRN callback tests validate registry/lifecycle plumbing, not screen
rendering. These checks do not replace live emulator or release qualification.
The existing prototype suite also passes against this normalizer: twelve
cross-platform render runs, fifteen binding cases and six allocation/removal
probes. Allocation fixtures now use the correct platform BIOS for each backend;
the new reservation correctly rejects treating an ANSI-host backend as Model 4.
This does not make the partial screen implementations production-ready.

## Remaining ordered integration

1. Define a bounded monitor-specific dependency/binding declaration. Keep the
   external backend-reference word out of ordinary internal pointer repair.
   Validate its slot, required backend ABI and operations before detach.
2. Resolve backend selection over the entire prospective profile, rejecting
   ambiguous/missing/incompatible backends and removal while still needed.
   Rebind on movement caused by unrelated members as well as either partner.
3. Carry and apply the validated reference through disk-free commit, selecting
   the basic console during reconstruction and publishing the personality only
   when both allocations and its reference are valid. Preserve failure rollback.
4. Complete the screen-operation contract and convert the settled ADM3A, VT52
   and ANSI parsers/reply queues, rather than shipping prototype subsets.
5. Add production backend builds/packaging, cold startup selection, native/cross
   parity, both platform/application tests, ROM ownership and 53K unload checks.

The target remains one portable binary per personality, hardware-specific code
in an unloadable backend, and no permanent resident growth. The remaining
commit/metadata cost is not yet proven to fit. Public subsystem/utility identity
updates should accompany completed integration, rather than advertise this
metadata-admission checkpoint as a finished monitor facility.
