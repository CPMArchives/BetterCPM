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

These rules establish admission to the callable registry. The subsequent
[screen ABI and backend checkpoint](Unloadable%20Screen%20Backend%20ABI.md)
defines production primitives including reverse fill and insert/delete line.
[Portable VT52 integration](VT52%20Portable%20Backend%20Integration.md) records
conversion, lifecycle and distribution qualification; this section preserves
the admission increment’s original scope.

The manager also accepts portable MCON 1.1 under the binding contract below.
Legacy MCON 1.0 providers continue to use their existing platform-bound checks
and require no backend. Screen-operation semantics and complete personality
conversion remain separate work; no incomplete backend is packaged for users.

## Implemented: portable monitor dependency and rebinding

MCON 1.1 preserves monitor operations 0..5. Its capabilities are exactly `0004h`,
the portable-screen-backend bit. Unlike MCON 1.0 platform bits 0/1, this declares
that the frontend requires a compatible SCRN 1.0 provider. It has:

- the existing eight-byte loader-owned header and canonical BDOS dispatch at
  payload offset 8 (the service resolver depends on this convention);
- a frontend-owned, initially zero backend-reference word at payload offset 12;
- a monitor callback entry at offset 14 or later;
- STATEFUL reconstruction, with no static/runtime repair word overlapping
  offset 12, including words starting at 11 or 13.

The four-byte dispatch at offsets 8..11 must chain normally. Offset 12 is private
frontend data, not an expansion of the common BRSX header. Normalization checks
ABI/capabilities, class, payload size and initial null state; selection checks
entry/dispatch and repair-list constraints before any live mutation.

The reference is manager-owned after load. The frontend invokes its backend
without BDOS or registry lookup from a console callback. Ordinary self-relative
pointer repair must never process this cross-module reference.

Prospective-profile preparation permits at most one MCON and one SCRN role,
rejects a carrier advertising both roles, and computes final addresses from
validated carrier descriptors and plan records. A portable frontend without a
backend is rejected before detach. Thus a backend can be loaded first and kept
alone, but cannot be removed while a dependent monitor remains. Remove the
personality first, then the backend. Legacy monitors remain independent.

The durable preparation context grows from 25 to 29 bytes: monitor entry at
+23, final frontend reference-word address at +25, and final backend entry at
+27. All LOAD/UNLOAD paths initialize the full state. A retained callable table
must still match its validated carrier, and selection is repeated after changes
to unrelated modules as well as changes to the pair.

The production commit request grows from 37 to 41 bytes: +37 is the final
frontend word address (zero for no dependent monitor), +39 the final backend
entry. The finalizer verifies completeness before any detach or movement.
After movement, a fixed-store trampoline at R3MOVE offset 330h writes this
validated reference, then enters the existing publisher at 38Fh. The publisher
binds the monitor and profile before the final generation store. No callback or
disk access occurs in this publication sequence.

The trampoline uses previously unused space after the overlay-loading handoff;
the tight commit coordinator and permanent code are unchanged. Old mode-one
fixtures still enter 38Fh and do not read the extra words; mode zero is unchanged.
A failed validation or pre-commit read leaves the previous binding, generation,
profile, TPA and live allocations unchanged. The basic console remains selected
during reconstruction. No concurrent/interrupt-time console support is added.

## Cost

| Component | Previous | Current | Budget |
| --- | ---: | ---: | ---: |
| Reloadable metadata normalizer | 901 | 966 | 1,024 |
| Reloadable slot preparer | 669 | 902 | 1,024 |
| Reloadable commit coordinator | 1,007 | 1,007 | 1,012 |

Values are bytes, comparing the merged SCRN-admission checkpoint with this
binding increment. The finalizer is 966/1,012 bytes; context constructor 479,
removal coordinator 969, and handoff/trampoline 58 bytes in its 127-byte region.
The growth is reloadable code and bounded transaction scratch; container slot
count and slot sizes are unchanged. Permanent BIOS, BDOS,
resident gateway and extension-service sources/layout are unchanged.

## Qualification

After rebuilding `tools/build_rsx_runtime_overlays.py`:

- `tools/test_monitor_metadata.py`: 68 MCON/SCRN platform, version, entry and
  reconstruction cases; unrelated callable semantics remain unchanged. Portable
  MCON positive cases and new binding-specific failures are covered below.
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
`tools/test_monitor_backend_binding.py` passes with both Model 4 and cpmsim
BIOS builds, using synthetic callbacks and the real production manager:

- missing backend, duplicate backend and removal-while-needed rejection;
- invalid capabilities/minor/class, non-null reference, dual roles, wrong
  dispatch/callback offset and overlapping static/runtime repair words;
- reversible file-read failure with an installed pair;
- retained state and both references after unrelated removal/append;
- MCON 1.0-compatible Function 182 lookup of the new 1.1 entry after movement;
- execution through the real BIOS monitor binding into the backend callback;
- observing memory writes to establish that the reference and monitor are
  rebound before generation publication;
- removing monitor then backend restores the basic console and 53K TPA.

The coordinator scratch-boundary fixtures now account for the four additional
context bytes. Carrier/slot, coordinator, legacy monitor selection, publication,
container, existing VT52 lifecycle and Stage-3 allocation/state tests pass.
No live screen/backend or complete converted personality is asserted by these
synthetic lifecycle tests.

## Remaining ordered integration

1. Complete the screen-operation contract, including required reverse fill,
   insert/delete line, cursor and input behavior. The dependency mechanism is
   implemented; its screen API must now match the established personality specs.
2. Convert the settled ADM3A, VT52 and ANSI parsers/reply queues to use this
   backend boundary. Retain their complete behavior instead of shipping subsets.
3. Add production backend builds/packaging and cold startup selection, then
   qualify native/cross builds, both platforms/applications, ROM ownership,
   failures during reconstruction and 53K unloaded recovery on exact artifacts.

The target remains one portable binary per personality and hardware-specific
code in an unloadable backend. Permanent resident growth remains zero in this
increment. Public subsystem/utility identity updates should accompany completed
integration, rather than advertise these lifecycle tests as complete monitor
compatibility.
