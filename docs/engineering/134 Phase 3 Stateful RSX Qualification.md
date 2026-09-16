# Engineering Specification 134: Phase 3 Stateful RSX Qualification

## Status

Phase 3 increment 1 is implemented.  It defines and builds the qualification
provider used to prove live RSX movement.  Production loading remains blocked
until the movement transaction is complete; accepting the class while the
Stage-2 disk reloader is active would silently discard mutable state.

## Qualification provider

`STATEFUL.RSX` is a BRSX-v2 provider in reconstruction class `STATEFUL`.  It
advertises service `STAT` ABI 1.0 and contains:

- a mutable counter and four-byte buffer;
- a runtime-created absolute pointer to the buffer, declared by a type-3
  metadata record;
- an ordinary linked pointer to the same buffer, present in the static
  relocation directory;
- a fixed pointer to CP/M entry 0005h;
- null and FFFFh sentinel words; and
- the loader-owned eight-byte BRSX-v2 runtime header and descriptor capacity.

The service can initialize, mutate and report this state.  A movement test can
therefore compare both values and pointer targets before and after relocation.
A counter-only preservation result is insufficient.

## Safe implementation boundary

The current reconstruction manager reloads each active carrier from disk.  It
must continue rejecting `STATEFUL` in production until reconstruction can:

1. validate the complete prospective profile;
2. identify the old and new allocation of every retained provider;
3. move complete live allocations with overlap-safe copy semantics;
4. repair the union of static relocation and declared runtime-pointer slots,
   adjusting only values inside the provider's old allocation;
5. rebuild loader-owned chain words and service descriptors; and
6. publish the new chain, limits and generation after the move succeeds.

The next increment implements that transaction for load, unload and chain
compaction, then runs `STATEFUL.RSX` through a forced address change.
