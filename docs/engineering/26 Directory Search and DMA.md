# Engineering Specification 26: Directory Search and DMA

## Milestone

BetterCP/M now implements BDOS function 17 (Search First) and function 18
(Search Next). A CP/M application can enumerate matching directory entries in
physical directory order and receive each complete 128-byte directory record
at the address selected by function 26.

## Search First

Function 17 receives an FCB address in `DE`, replaces any previous search
continuation, and begins at the first entry of the referenced directory.

The current implementation supports:

- FCB drive 0, meaning the current default drive;
- explicit drive 1, meaning drive A;
- drive `?`, meaning the current drive across all user numbers;
- `?` wildcards in filename, type, and extent fields through `EX`;
- comparison with filename/type attribute bits masked; and
- five-bit comparison of a non-wildcard `EX` value.

Ordinary Search First clears FCB `S2` automatically. The special all-user
drive-`?` form preserves it. Explicit drives B through P remain unavailable
because the BIOS currently supplies only drive A.

## Search Next

Function 18 takes no new documented FCB argument. It retains the Search First
FCB, user mode, record number, and next-entry cursor, then resumes immediately
after the preceding match. Exhaustion returns `FFh` and deactivates the
continuation.

A new Search First replaces the old sequence. As in CP/M 2.2, applications
must keep the original FCB and relevant fields valid while using Search Next;
interleaved searches or later directory mutations need not preserve a prior
continuation.

## DMA presentation

On every success, all 128 bytes of the directory record containing the match
are copied to the current BDOS DMA address. The returned code 0 through 3
selects the matching entry at `DMA + code*32`.

Search Next reads the DMA address afresh from BDOS state. Changing it with
function 26 during enumeration does not restart the search, and the next
successful record is copied to the new address. DMA contents after a `FFh`
result are not promised to contain valid search data.

The complete copied record preserves the four compatibility-visible directory
entries, including user, FCB fields, attributes, extent state, record count,
and allocation bytes.

## System Services state

Two new provisional vectors provide Search First at `E81Bh` and Search Next at
`E81Eh`. System Services owns the continuation cursor and private FCB pointer;
BDOS owns the current user and DMA address supplied at each public call.

Search storage failures use carry internally and are mapped to the existing
provisional `FFh` BDOS failure. A normal no-match `FFh` has carry clear, so the
internal distinction remains available for a later disk-error policy.

Adding the continuation engine grew System Services across its former private
buffer at `EC00h`. The buffer moved intact to `ED00h`, below the BIOS physical
scratch area at `EE00h`. A dated source comment retains every provisional
buffer placement and the reason for this move.

## Verification

The executable tests verify:

- Search First starts at slot 0 and transfers all 128 bytes;
- Search Next returns the following slot in directory order;
- changing DMA between First and Next changes the transfer destination without
  restarting enumeration;
- ordinary Search First clears `S2`;
- exhaustion returns `FFh`;
- the all-user special form preserves `S2`; and
- the same public behavior works through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical components: 1,134 bytes for directory/System Services and 378
bytes for BDOS.

## Next increment

Engineering Specification 27 completes the unchanged-FCB portion of function
16 without media mutation. The next increment can add the directory writeback
and validation required for a dirty Close commit.
