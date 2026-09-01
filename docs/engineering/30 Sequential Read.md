# Engineering Specification 30: Sequential Read

## Milestone

BetterCP/M now implements BDOS function 20 (Read Sequential). An application
can Open an FCB, read successive 128-byte records into the current DMA buffer,
observe compatible FCB position advancement, receive EOF, and cross an extent
boundary without issuing another Open.

## Call and result contract

Function 20 receives the activated FCB address in `DE` and uses the DMA address
owned by function 26.

- `A=00h` means one complete 128-byte record was transferred;
- a normal nonzero result means no data exists at the requested position; and
- an internal storage failure is carried separately and currently appears at
  the BDOS boundary as provisional `FFh`.

BetterCP/M uses `01h` for ordinary EOF, matching the familiar DRI result while
only promising the ledger-required nonzero contract. DMA contents are valid as
a new record only after a zero result.

## FCB position and EOF

The next record is selected from public FCB `EX`, `S2`, and `CR` state.
Successful reads increment `CR` exactly once. A partial final extent returns
EOF when `CR` reaches `RC`, and repeated calls at that position continue to
return EOF without fabricating records.

`CR=128` is retained as the full-extent overflow position. On the following
call, System Services increments `EX` (and `S2` when `EX` wraps), sets `CR=0`,
and invokes the existing Open engine to activate the next logical extent. A
successful first read there returns with the new extent active and `CR=1`.

If the next extent does not exist, the previous `EX`, `S2`, and `CR=128`
position is restored. This provides stable repeated exact-boundary EOF without
requiring DRI's private failed-read EX drift.

## DPB-driven record translation

The thirteenth provisional System Services vector at `D824h` performs the
translation. Drive login now retains `BSH` and `BLM` alongside `EXM`, `DSM`,
`SPT`, and `OFF`.

For each read, System Services:

1. derives the logical record within the `EXM` extent group;
2. separates allocation-entry index and record-within-block using `BSH/BLM`;
3. selects an 8-bit or 16-bit allocation entry from `DSM`;
4. rejects zero/unallocated or out-of-range blocks as no data;
5. converts the allocation block and record offset into a logical disk record;
6. divides by `SPT` and adds `OFF` to obtain BIOS track and sector; and
7. calls BIOS `SETTRK`, `SETSEC`, `SETDMA`, and `READ`.

This supports both 8-bit and 16-bit allocation-map formats and avoids compiling
the MM 790K geometry into the file-read algorithm.

## Verification

The fixture adds a two-record file whose allocation map owns block 2. A
physical-read test boundary distinguishes its data sector from directory
sectors and supplies different markers in two 128-byte quarters.

Direct and application-level `CALL 0005h` tests verify:

- Open activates the data-bearing FCB;
- the first and second records transfer exactly 128 distinct bytes;
- changing DMA before the second read changes its destination;
- `CR` progresses from 0 to 1 to 2;
- partial-final-extent and repeated EOF are nonzero and stable;
- `CR=128` automatically activates `EX=1` and reads its first record; and
- a simulated storage failure is not confused with ordinary EOF.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical components: 1,765 bytes for directory/System Services and 435
bytes for BDOS.

## Deferred work

Read Sequential currently relies on the activated FCB contract; behavior for
arbitrary unactivated or internally inconsistent FCBs is not promised. Only
drive A is available, though the translation itself is DPB-driven. Broader
multi-format conformance will require a second materially different DPB and
fixture.

## Next increment

Implement BDOS function 21 (Write Sequential) using the same record mapper.
It must enforce software and file read-only state, allocate a free block when
the target allocation entry is empty, update the ALV and FCB only around a
successful BIOS write, advance `CR`, and leave dirty extent metadata for the
transactional Close path.
