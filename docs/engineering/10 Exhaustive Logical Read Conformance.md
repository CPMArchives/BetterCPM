# Engineering Specification 10: Exhaustive Logical Read Conformance

Status: Implemented and verified
Date: 2026-09-01

## Result

The direct-call BIOS fixture now executes `READ` for every CP/M logical sector
number from 0 through 79 and verifies both physical addressing and deblocking.

For each call the fixture:

1. selects drive A, track 2, and a fixed DMA address;
2. fills the four quarters of the provisional physical buffer with distinct
   values;
3. calls the assembled BIOS `SETSEC` and `READ` entries;
4. records the cylinder, side, and sector ID passed to the physical reader;
5. requires a successful BIOS result; and
6. compares all 128 bytes copied to DMA.

The expected physical-sector order is:

```text
1, 3, 5, 7, 9, 2, 4, 6, 8, 10
```

The test crosses the side boundary at logical sector 40 and checks all four
quarters of every physical sector. It therefore covers twenty physical-sector
selections and eighty distinct DMA copies.

The physical-reader call is instrumented only in the fixture's isolated memory
image. The production BIOS binary is not modified. The separate `trs80gp`
test continues to verify actual controller seek, side selection, and sector
transfer at cylinder 2, side 1, sector 10.

## Verification

```sh
python3 tools/build_bios.py
python3 tools/test_bios.py
python3 tools/test_trs80_physical_read.py
```

Expected BIOS result:

```text
executed 17 BIOS-vector contracts from F000h binary
character transport, disk state, all 80 reads, and SECTRAN passed
```

## Subsequent increment

Engineering Specification 11 implements conservative write-through
read-modify-write behavior and extends the fixture across all 80 writes and
write types 0, 1, and 2. Caching remains deferred.
