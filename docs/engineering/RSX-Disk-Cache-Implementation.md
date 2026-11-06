# RSX carrier caches on A0

6 November 2026. v1.0.1 follow-up to the merged RAM-capsule implementation.
The maintainer accepted an additional 256 bytes per installed RSX and requested
finished cleanup, caller integration, cpmsim/Model 4 validation and an unmerged
PR. No locked release package is replaced by this source change.

## Resident and disk cost

| BATCHIO alone | Original | RAM capsules | Disk cache |
| --- | ---: | ---: | ---: |
| Shared resident manager | 1,024 | 1,024 | 1,024 |
| Additional shared reader | 0 | 1,024 | 0 |
| Provider including loader allocation | 512 | 1,280 | 768 |
| Total resident bytes / TPA reduction | 1,536 | 3,328 | **1,792** |

The disk cache recovers 1,536 bytes compared with the merged implementation.
Its remaining increase over the original is **256 bytes**. No-RSX TPA is
unchanged (the normal cpmsim display remains 53 KB). This total includes the
shared manager; it is not an additional 1,792 bytes on top of that manager.

Every provider receives one additional 256-byte page. Its ten-byte record
holds original allocation, whole-carrier CRC16, source DU, cache slot/marker
and a separate fixed-header CRC16. Original provider padding remains entirely
provider-owned. Descriptors still occupy the top of the charged allocation;
the compact record sits immediately below them. Pointer repair uses the
original allocation bound and excludes the loader's added page.

The unique emitted manager components total **14,814 bytes**, versus 13,961
for the RAM-capsule build: **853 additional bytes of disk code/data**, including
variables/buffers. The 1,468-byte worker runs only in disposable transaction
workspace. The normal entry is 766 bytes; its 242-byte position-independent
overlay reader moved into the staged file. The fifteen-slot R3PACK remains
15,360 bytes; the raw entry remains within its existing 1 KiB slot.

R3CACHE.RSX grows from 1,024 to 2,560 disk bytes: a 512-byte relocation header,
1,536-byte worker slot and 512-byte reader slot. The caller supplies 2,560
transient bytes plus up to 255 bytes of page alignment, in addition to the
existing overlay/stack workspace. None is deducted from application TPA after
return. A BATCHIO cache uses 1,280 logical bytes (wrapper plus nine carrier
records), rounded by the filesystem to its allocation blocks.

## Separate bounded files and cleanup

Five exact A0/user-0 names, `$$RSX00.RSC` through `$$RSX04.RSC`, support at most
four installed providers and one pending candidate. They are not distributed
provider carriers and must not be loaded manually or removed while referenced
by a live chain.

Live footer IDs are authoritative. Allocation skips active IDs without even
opening their files. A candidate uses an unused slot, validates its source,
writes a signature wrapper and complete padded carrier, and successfully
closes it before any live movement. The scratch copy's allocation field is
adjusted for the extra page; the user's source file is never changed.

Before a real set change, cleanup scans these five slots, protects all live
IDs, and reclaims only unreferenced files with the exact manager signature and
matching slot ID. Foreign files and damaged ownership signatures are left
untouched. Existing files are never overwritten. The core's Make operation
also rejects an existing physical extent. Bad collisions can exhaust the
bounded namespace, in which case installation fails safely.

After successful publication, cleanup runs again from the scratch worker,
then restores the prefetched resolver. It deletes removed members' files and
otherwise leaves the newly committed chain untouched. A returning cleanup
error defers housekeeping; the operation remains committed success. The next
set change retries cleanup before preparation. This is distinct from a
preparation error, which returns failure with the old chain intact.

A failed new-file write/close attempts immediate deletion of that exact newly
created file. If both the write and its cleanup deletion fail, incomplete data
may remain. A valid ownership wrapper allows later reclamation. An empty file
or damaged signature cannot be safely distinguished from a foreign collision;
it is preserved rather than erased speculatively. Such collisions may need
operator removal after confirming ownership with no RSXs installed. Normal
successful cycles do not accumulate files; the namespace is always bounded.

Cold boot has an empty profile. First real installation reclaims verified
stale files; it never reinstalls providers from them. Idempotent operations and
QUERY/LIST remain disk-free and do not perform speculative housekeeping.

## Stream integrity and failure boundary

Each retained open compares its wrapper with the protected live record. The
first 512-byte carrier header is separately CRC-checked before it supplies
allocation/class facts to the planner, including for the member being removed.
Retained reconstruction additionally verifies the entire padded carrier CRC,
record-count completion and the existing authoritative carrier/metadata checks.
This prevents a modified removed-member header from changing move geometry
without a full body reread.

STATELESS images are rebuilt from their pristine disk template. STATEFUL
allocations retain their live code, padding and runtime data. All fallible
preparation and candidate writes precede the existing disk-free move and
publication boundary. No change is made to SUBMIT or BATCHIO source semantics.
Ordinary WBOOT preserves the chain without cache I/O. Last unload still uses
its cache during existing removal planning, then releases all resident RSX
allocations and deletes the unreferenced cache.

CRC16 protects against accidental corruption, not malicious disk modification.
Tests distinguish returning I/O statuses from ordinary EOF. They do not claim
power-loss atomicity or recovery from a fatal BDOS error path that never returns.

## Caller and build integration

The helper is relocatable into any sufficient caller-declared disposable
workspace, rather than the prototype's fixed 1000h address. Supplied RSX.COM,
XSUB.COM and provider self-retirement need no caller source changes. Legacy
version-2 A0 lookup, version-3 DU/provenance, name-based idempotence and the
four-provider limit remain unchanged.

During a transaction, the shared stream FCB's unused random-record bytes
(+33..35) hold a JP to the scratch dispatcher. The private streams use only
sequential I/O; reset clears through +32 and preserves this trampoline. Inline
vector calls preserve argument registers. This reuses existing protected bytes;
no static-memory boundary or unloaded TPA changes. QUERY/ENUM use the live
footer directly and require neither a staged helper nor cache disk access.

The post-commit continuation transfers out of CFG before housekeeping because
physical disk I/O can overwrite CFG. It discards its disposable CFG return,
cleans only unreferenced slots, then copies the prefetched disk-free resolver
prefix while preserving the manager return stack.

The checked builder binds the staged worker/reader file to its compatibility
identity and CRC before execution. The checked entry stages from caller RAM
and restores its original CFG image
after physical reads. Its 994-byte entry and scratch staging are tested with
destructive CFG reads, read failures and CRC rejection. These tests use controlled
authentication stubs to exercise staging, not to requalify the CRC algorithm.
Checked entry and overlay compilation/fit pass; shifted-layout worker builds
and external relocation closure pass.
Those checks are not new native checked-profile or ROM qualification.

Update the matched raw Function-177 selector, protected file stream, R3PACK
and R3CACHE together and cold boot. New worker files must not be mixed with the
old RAM-capsule entry/stream. Source/manifest selection includes the new builder
module; numeric release identity assignment and publication remain release
integration work, not part of this PR.

## Validation

Targeted full-Z80 execution covers 29 injected returning disk failures plus
cleanup read/close/delete failures before publication; all five staging-read
failures; post-commit delete failure/retry; damaged retained and removed-member
headers; whole-carrier corruption; foreign collisions; eight cleanup reuse
cycles; arbitrary caller workspaces; legacy idempotence; offline STATEFUL moves;
and pristine STATELESS rebuilding. Comparisons include complete live bytes,
profile, head, low bound, TPA, generation, caller DU/DMA and mutable service
state. Overlapping movement preserves original padding and fixed external
pointers numerically within the loader-owned page.

Native qualification on private copies uses the exact changed selector and
protected stream plus matched runtime files. It loads explicit B0/B3 sources,
removes original carriers, relocates STATEFUL, exercises XSUB Function 10 and
later submitted commands, explicitly unloads BATCHIO and lists an empty profile.
A development-only COM probe saves/removes STATEFUL's cache, confirms that
UNLOAD fails while its live service/state remains usable, then restores the
cache. Final filesystem audits require zero cache files and no queue, and
check both filesystems and unchanged original media. cpmsim performs six
extra reuse cycles; Model 4 performs one, avoiding a redundant long campaign.

Qualification receipts and the full emitted size map are kept in
[evidence](evidence/2026-11-06-rsx-disk-cache/). Native results are recorded only
when complete; intermediate launch/probe/time-limit failures are not passes.
