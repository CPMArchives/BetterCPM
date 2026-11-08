# Explicit in-allocation RSX cache footer

Engineering integration extension, 8 November 2026. No permanent RAM reservation
or release assignment is introduced. This extends the existing disk-cache manager;
it is not a TCAP-specific cache or recovery subsystem.

## Permission and ownership

BRSX carrier flags bit 2 (`0004h`) explicitly permits the manager to place its
ten-byte cache bookkeeping area immediately before the runtime callable records
inside the declared allocation. The low two flag bits retain their existing
reconstruction-class meaning. Bits 3 through 15 remain reserved and zero.

The builder's `cache_footer_inline=True` opt-in reserves the ten bytes when
rounding the allocation. A carrier declaring N callable services therefore needs:

`allocation >= code_bytes + 10*N + 10`

The suffix layout is unchanged: two fixed-header CRC bytes, the eight-byte cache
footer, then N ten-byte callable records. With the permission bit, that suffix is
explicitly manager-owned. The exclusive end of provider-owned storage is:

`allocation - 10*N - 10`

Payload and declared runtime pointer words must fit before that boundary. The
normalizer checks the room before publishing metadata facts. A pointer word
starting in the last owned byte is rejected; one occupying the final two owned
bytes is valid. The footer's original-bound word records this owned-prefix limit.

**Without permission, every byte of the provider's declared allocation remains
untouched by cache bookkeeping.** The existing extra 256-byte page is still added.
Ordinary and opted-in modules can coexist, move and reconstruct in one profile.
The general builder default remains the existing behavior.

## Compatibility and accounting

Older carrier validators reject the previously reserved bit. The new display
builder refuses the opt-in for a system workspace without this implementation.
Checked systems also retain exact private build admission. Use each candidate's
matching core, R3PACK.RSX, R3CACHE.RSX and providers; this does not grant arbitrary
cross-build or legacy-manager compatibility.

All ten footer bytes and all page rounding remain charged to the provider's
full display path. This is a physical allocation reduction, not an accounting
exclusion. It can save one page when code, footer and callable records fit the
same rounded allocation. It saves nothing when those bytes cross the next page.
The unchanged 1,024-byte first-RSX machinery remains a separate generic RSX cost.

The extension changes only file-backed preparation, metadata and cache workers.
There is no new resident table, counter, root allocation or reserved top of TPA.
Complete unload still retires the generic RSX region and restores the original
application boundary.

## Qualification

`tools/test_rsx_inline_cache.py` executes production manager transactions on the
independent Z80 core. It verifies exact allocation savings; provider padding;
state and runtime pointers through movement after deleting the original carrier;
mixed STATELESS/STATEFUL modules; final unload restoration; exact-fit footer and
pointer boundaries; overlapping payload/pointer rejection; reserved-bit rejection;
and create/write/close failure rollback without live-profile or context changes.

The existing disk-cache regression also passes its 29 returning-error cases,
corrupt-cache refusal, cleanup, provenance and overlapping reconstruction checks.
Native source, installation and installed cold/warm campaigns qualify the opted-in
display providers separately. Passing a worker fixture alone is not native
installation qualification.
