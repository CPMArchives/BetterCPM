# RSX source selection and independence from source media

Investigation, 6 November 2026. Baseline: `16f9a479e3f24a44476018c2e94cf4b66a53408a`.
Accepted by the maintainer. The implementation and qualification record is
[RSX offline loading](RSX-Offline-Loading-Implementation.md).
FDB's exit report remains open and unreproduced.

## Required behavior

An RSX carrier is needed when that RSX is first loaded. After successful load,
its source disk may be removed. Ordinary warm boots and subsequent profile
changes must not reopen that carrier. The existing system manager runtime is
a separate system dependency; this proposal does not make the OS itself
independent of its System disk.

## Findings

`src/system/fileload.mac:FL_REOPEN` forces drive A. The adapters in
`src/system/extens.mac:AD_CALL` force user zero, preserving the caller's disk,
user and DMA afterward. Both restrictions must be addressed for explicit
drive/user selection. The shared reader also serves CPX and manager-runtime
files; changing its default globally would change unrelated behavior.

The production warm path already preserves the installed RSX chain.
`src/system/gateway.mac:SYS_WARM` retains the profile; `SINIBODY` reconnects
the existing head. The command reloaders rebuild CPXs and CCP. They do not
reopen every retained RSX. Earlier statements that every warm boot requires
RSX carriers in A0 were incorrect.

However, a later LOAD or UNLOAD does reread retained carriers:

- `r3prof.mac:PF_SCAN` and `r3drop.mac:RD_SCAN` read carrier headers for the
  prospective allocation/class vectors. The removal scan includes the module
  being removed.
- `r3keep.mac:KE_LOOP` rereads and validates retained carriers in full.
- `r3kpre.mac` uses their metadata for monitor compatibility, pointer repair,
  and STATELESS snapshots.

The persistent profile is exactly 41 bytes: count, four eight-byte names,
and four two-byte service numbers. Its region ends at the directory buffer.
There is no source-location field or spare room there. User numbers extend
through 31, so a general drive/user pair cannot fit in two four-bit nibbles.

The installed image is not sufficient input to the current preparers:
`r3snap.mac` copies the payload, materializes service descriptors, and clears
the allocation tail. It does not preserve the complete original relocation
and metadata streams. Retained STATELESS providers are reconstructed from a
fresh template; substituting their current live bytes would change behavior.

## Smallest compatible implementation direction

1. Add an explicit source-location form to Function 177 while retaining the
   existing 18-byte version-2 request and its A0 semantics. A new version can
   append drive and user bytes; validate them before I/O. Keep internal system
   runtime and CPX opens on their existing path. A location-aware stream must
   preserve its selected user for every read/reset and restore caller DU/DMA.
2. At first load, retain a manager-owned in-memory preparation record for the
   provider. Keep allocation/class, dispatch and service/monitor facts,
   relocation and runtime-pointer information, and the pristine template
   required by STATELESS semantics. Use offsets within that record so its
   bookkeeping can move safely. Remember the resolved source DU as provenance,
   not as an instruction to reopen the source later.
3. Make retained-profile preparation consume those records, including removal
   of a provider whose source disk is absent. Prepare additions/removals of
   records before commit, then publish them atomically with the profile.
   Charge their protected memory explicitly and release it on unload.
4. Preserve four-entry capacity, name-based idempotence, module/carrier formats,
   stateful pointer repair, monitor rules, and the disk-free commit boundary.
   Reject insufficient memory before changing the live profile.

Caching the complete validated carrier would require less transformation code,
but would retain redundant headers and payloads. A compact preparation record
is the recommended memory-conscious design. Its exact size, placement, overlay
fit and TPA cost require a measured implementation prototype; no byte-cost or
platform acceptance claim is made here. Existing protected regions are tightly
packed, so this is more than an XSUB filename-search patch.

## Initial discovery remains a separate policy

Support explicit `RSX LOAD B3:NAME.RSX`; resolve an unqualified name in the
current DU, then A0, and retain the chosen source. Existing version-2 callers
continue to mean A0. Preserve name-based QUERY/UNLOAD and idempotence: another
file with the same stem does not silently replace an installed provider.

XSUB needs an additional bounded decision. Its normal command tail omits the
executable token; the current public transient interface does not publish the
COM lookup location. Thus `B:XSUB` does not by itself identify B as a companion
source to XSUB. An explicit companion-DU operand avoids a new CCP interface.
Making bare `B:XSUB` discover its adjacent companion automatically requires
either an invocation-location interface or a specified fallback search.
Do not introduce an all-drive scan implicitly. Select this policy before code.

## Evidence and focused acceptance

On a disposable copy of the released cpmsim System image, the existing
implementation passed:

1. Load STATEFUL; initialize and mutate its state.
2. Delete `STATEFUL.RSX` from that copy.
3. Run its checker after normal transient returns/warm boots: PASS.
4. Attempt `RSX LOAD HELLO`: rejected with `RSX module or profile error`.
5. Run the state checker again: PASS, proving the failed change preserved it.

Transcript: `build/rsx-location-investigation/transcript.bin`. This verifies
the current dependency and warm-boot distinction, not an implemented remedy.
Previous Model 4 attempts yielded no captures; no new Model 4 pass is claimed.

Implementation acceptance should cover explicit other-drive/nonzero-user
loads, legacy A0 callers, exact DU/DMA restoration, removal of source media,
warm boot, load/unload of another provider, STATEFUL data and pointer repair,
STATELESS template semantics, source-file replacement after load, allocation
failure rollback, and unloading the last provider. Then run one focused native
campaign per supported platform, including actual XSUB Function-10 batch input
and queue cleanup. FDB and unrelated loader features remain outside this change.
