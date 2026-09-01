# Engineering Specification 32: Transactional Allocation Close

## Milestone

BDOS function 16 can now commit the allocation-map and record-count changes
produced by Write Sequential. The complete validated FCB metadata is merged
into one directory entry and published by one BIOS directory write.

## Why the ALV is insufficient

An allocation-vector bit proves only that a block is occupied. It does not
prove that the FCB being closed owns that block; accepting any marked block
would allow a damaged or hostile FCB to claim another file's storage.

System Services therefore maintains a small pending-allocation journal. After
a successful first write to a newly selected block, the journal records the
activated FCB address and block number. The entry is created only after the
data write succeeds, alongside publication to the FCB and ALV.

## Close validation

Close still requires filename, type, attributes, `EX`, `S1`, and `S2` to match
the canonical directory entry. `RC` must remain in the range 0 through 128.
For each 8-bit or 16-bit allocation entry:

- an existing canonical block must remain exactly unchanged;
- zero may remain zero; and
- zero may become nonzero only when the pending journal proves that this FCB
  acquired that exact block through BetterCP/M's allocator.

Removal, replacement, byte-spliced 16-bit block numbers, and unjournaled block
claims are rejected without media mutation.

## Commit and recovery

After validation, Close snapshots the original 32-byte directory entry, merges
the saved caller FCB into the private directory buffer, and issues one BIOS
directory write. Success invalidates cached login/allocation state and releases
the FCB's journal records. A physical failure restores the private buffer,
invalidates uncertain disk state, retains the journal proof for a retry, and
leaves the caller's FCB unchanged.

The journal currently has 32 resident slots and is keyed to the activated FCB
address. Normal successful Close reclaims its slots. Abandoned dirty FCBs can
temporarily consume journal capacity; lifecycle cleanup will be defined with
the later full Open/Create/Delete policy.

## Verification

Executable tests now cover the complete sequence: Open an empty canonical
extent, Write Sequential to allocate block 3, observe ALV/FCB publication, and
Close to atomically write block 3 plus `RC=1` into the directory. Existing
tests continue to reject arbitrary allocation-map mutation, protected dirty
Close, and failed directory writeback.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical System Services binaries.

## Next increment

Implement automatic extent creation when Write Sequential reaches `CR=128`.
That requires locating a free directory slot, constructing the next canonical
extent, and publishing it transactionally without losing the completed extent.
