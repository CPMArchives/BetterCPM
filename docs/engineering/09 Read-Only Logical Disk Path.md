# Engineering Specification 09: Read-Only Logical Disk Path

Status: Implemented and verified
Date: 2026-09-01

## Result

The Model 4 BIOS now has an arbitrary-cylinder, arbitrary-side 512-byte
physical reader and a read-only CP/M 128-byte logical-sector path for the MM
790K drive-A definition.

## Mapping

For a BIOS sector value from 0 through 79:

- the low two bits select one of four 128-byte quarters;
- division by four selects one of twenty physical sectors in the cylinder;
- values 0-9 select side 0 and 10-19 select side 1; and
- the on-side index maps to physical IDs `1,3,5,7,9,2,4,6,8,10`.

`READ` fetches the selected 512-byte sector into a private buffer and copies
the selected 128-byte quarter to the persistent DMA address. Invalid drive,
track, or sector state returns nonzero. `WRITE` remains an explicit failure.

## Physical reader

The Model 4 implementation selects drive 0 and MFM at port `F4h`, applies the
side-select bit, seeks through the WD179x-compatible controller, reads exactly
512 bytes by polling DRQ, waits for command completion, and returns masked
controller status.

The initial implementation uses unbounded controller waits, matching the
already recorded deferred work for timeouts, retries, and richer error codes.

## Hardware verification

A dedicated test image places a signature at cylinder 2, side 1, physical
sector 10. `diskread.mac` boots through the unchanged stage-zero loader, uses
the new physical reader, compares the signature, and displays:

```text
BIOS physical read verified
```

The test passes in `trs80gp`. Its 411-byte binary is also byte-identical
between native CP/M ZSM4/Digital Research LINK and the host assembler.

## Buffer placement finding

An initial composition placed the 512-byte buffer after a BIOS based at
`F000h`. That would extend into the Model 4 keyboard window beginning at
`F400h`. The active source instead uses provisional external scratch at
`EE00h`. Both `F000h` and `EE00h` remain bring-up placements pending the
resident-memory specification.

The production BIOS is 761 bytes and remains byte-identical across builds:

```text
25206397bdb8c3cefcc0c3cfba4109243c20e882efc1140c100b7fb282d83dc0  bios.bin
```

## Next increment

Add deterministic tests for all 80 logical-sector mappings and for the
128-byte quarter copied to DMA. Then specify and implement write-through
read-modify-write behavior, including directory and unallocated-write type
handling, before enabling `WRITE`.
