# Engineering Specification 33: Automatic Sequential Extents

## Milestone

Write Sequential now crosses the 128-record extent boundary without requiring
an application Close, FCB edit, Create, Open, and retry sequence. At `CR=128`,
BetterCP/M commits the completed extent, creates the next canonical extent in a
deleted directory slot, and writes its first record through the ordinary
DPB-driven allocation path.

## Transition sequence

System Services snapshots the caller's complete 33-byte FCB and then:

1. closes the completed extent through the journal-validated transactional
   Close path;
2. increments `EX`, carrying into the six-bit `S2` field when `EX` wraps;
3. clears the new extent's `RC`, allocation map, and `CR`;
4. scans all DPB-defined directory records for the first `E5h` entry;
5. writes an empty canonical extent entry with one BIOS directory write; and
6. re-enters Write Sequential, which logs the disk in again, allocates a data
   block, writes the DMA record, and advances the new FCB to `RC=CR=1`.

The directory scanner treats only `E5h` as free. Reserved metadata entries are
not overwritten.

## Ordering and failures

The completed extent is committed before its successor is created, so a new
extent can never make the preceding 128 records unreachable. The empty new
extent is committed before its first data write; interruption can therefore
leave a harmless empty extent, but cannot leave directory metadata pointing at
an unwritten allocation block.

If no directory slot exists, function 21 returns `01h` and restores the
caller's old `EX`, `S2`, allocation map, `RC`, and `CR=128`. The completed
extent remains safely committed. A directory I/O failure returns through the
storage-error path and likewise restores caller-visible extent state; disk
login state is invalidated when media outcome is uncertain.

Software and file read-only checks still occur before any transition work.

## Verification

The executable fixture opens a canonical full extent at `EX=0`, `RC=128`, and
`CR=128`, leaves a deleted directory slot, and calls function 21. Tests verify
creation of `EX=1`, allocation of the next free 16-bit block, first-record DMA
write, `RC=CR=1`, and a subsequent Close commit to the newly created slot.

A second fixture occupies every directory entry visible through the mock
media. It verifies the normal directory-full result, byte-for-byte restoration
of the completed FCB, and no directory mutation.

Native CP/M ZSM4/Digital Research LINK and the host assembler must continue to
produce byte-identical components.

## Next increment

Implement BDOS function 22 (Make File). Automatic extent creation now contains
the core free-directory-slot and canonical-entry machinery needed for an
explicit application-level Create operation.
