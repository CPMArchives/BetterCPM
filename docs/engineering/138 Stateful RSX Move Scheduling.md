# Engineering Specification 138: Stateful RSX Move Scheduling

## Status

Phase 3 increment 5 is implemented and qualified outside Function 202.  It
consumes a validated prospective layout and schedules all retained `STATEFUL`
images through the guarded live-image mover before later reconstruction and
publication steps alter loader-owned state.

## Request and inputs

The scheduler accepts the eight-byte records produced by the prospective
layout planner, one pointer-union descriptor for each record, bounded mover
request scratch, and the mover entry address.  The current implementation
retains the loader's four-module bound.

Each pointer-union descriptor identifies the sorted, validated union prepared
from a provider's static relocation words and runtime-pointer record.  The
scheduler copies that union into mover scratch together with the record's old
base, new base and allocation size; the mover remains responsible for complete
slot validation, overlap-safe copying and guarded pointer adjustment.

## Scheduling rules

- Plans are validated before the first live image is changed.
- Only retained `STATEFUL` records produce moves.
- Zero old bases and unchanged addresses require no move.
- Every actual move in one transaction must have the same direction.
- Upward moves execute in profile order.
- Downward moves execute in reverse profile order.
- Mixed-direction plans, invalid classes, wrapped ranges and inadequate scratch
  capacity are rejected without moving an image.
- The completed-move count is returned only after every requested move succeeds.

The ordering prevents one destination from overwriting the still-live source of
the adjacent provider in compact resident layouts.

## Qualification

Focused Z80 tests execute two adjacent retained providers through overlapping
upward and downward moves.  They verify image identity, repaired internal
pointers, untouched fixed words, balanced stack use and the reported move
count.  A mixed-direction plan is rejected before mutation.

Production `STATEFUL` loading still requires the final transaction layer: bind
the planner, pointer-union preparer and scheduler to Function 202, reconstruct
non-stateful entries, rebuild loader-owned chain and service metadata, and
publish the new generation atomically.
