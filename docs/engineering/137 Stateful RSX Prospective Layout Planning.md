# Engineering Specification 137: Stateful RSX Prospective Layout Planning

## Status

Phase 3 increment 4 is implemented and qualified outside Function 202.  It
calculates the prospective resident layout and reconstruction disposition
before any live allocation is changed.

## Inputs and output

The planner accepts the resident top, minimum permitted base, old and proposed
allocation vectors, proposed reconstruction classes, and either an old-profile
removal index or the append/no-op marker.  Profiles remain bounded at four
modules by the current persistent reconstruction table.

It emits one eight-byte record per proposed module:

- old live base, or zero when no live image will be retained;
- prospective new base;
- prospective allocation size;
- reconstruction class; and
- old profile index, or FFh for a fresh/stateless instance.

## Planning rules

- `STATELESS` entries are marked for disk reload and may change allocation.
- Fresh `STATEFUL` entries are initial loads with no old base.
- Retained `STATEFUL` entries preserve their old base and require an unchanged
  allocation size.
- `STATE_PRESERVING` remains rejected pending an export/import ABI.
- Fresh `COLD_ONLY` entries are permitted, but a retained instance may not
  change address or allocation.
- Every allocation must be nonzero, counts and operation relationships must be
  valid, output capacity must cover the proposed profile, and the final low
  boundary must remain at or above the configured minimum.

The returned record count is published only after the entire plan succeeds.
A rejected plan is therefore never eligible for commit even if its scratch
output contains intermediate bytes.

## Qualification

Focused Z80 tests cover removal of a leading module that moves a retained
stateful provider upward, stateless reconstruction after that removal, fresh
stateful append, stateless allocation change, and rejection of every unsupported
class or unsafe boundary described above.

The next increment combines profile records with carrier-derived pointer unions
and schedules all stateful moves before rebuilding stateless modules and
publishing loader-owned chain state.
