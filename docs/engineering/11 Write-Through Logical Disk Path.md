# Engineering Specification 11: Write-Through Logical Disk Path

Status: Implemented and verified
Date: 2026-09-01

## Result

The MM 790K drive-A BIOS now supports 128-byte CP/M logical writes through a
conservative 512-byte physical read-modify-write operation.

For every `WRITE`, the BIOS:

1. validates and maps the current drive, track, and sector;
2. reads the complete containing 512-byte physical sector;
3. replaces only the selected 128-byte quarter from the current DMA address;
4. writes the complete physical sector; and
5. returns zero only after successful controller completion.

The other three quarters are preserved. A failed pre-read or physical write
returns nonzero.

## CP/M write types

Write types 0 (ordinary allocated data), 1 (directory), and 2 (first record of
a newly allocated block) all follow the same safe write-through path. Type 2
does not skip the pre-read: without a multi-record cache, doing so could destroy
the other records sharing the 512-byte sector.

This is compliant but intentionally unoptimized. A future cache may use the
type indications while preserving identical externally visible results.

## Physical writer

The Model 4 platform writer selects drive, side, and MFM mode, seeks the
requested cylinder, issues the WD179x-compatible write-sector command, sends
exactly 512 bytes while polling DRQ, waits for completion, and returns masked
controller status.

Controller waits remain unbounded pending the planned timeout, retry, and
recovery specification.

## Verification

The binary-level fixture executes all 80 logical writes. For every mapping it
verifies cylinder, side, interleaved sector ID, replacement of the selected
quarter, and preservation of the other 384 bytes. Write types 0, 1, and 2 are
distributed across the cases.

A separate disposable `trs80gp` image performs a real read, modifies a sector
at cylinder 2, side 1, sector 10, writes it, clears the memory buffer, reads the
sector again, and compares the new signature. It displays:

```text
BIOS physical write verified
```

Native CP/M and cross builds are byte-identical:

- physical-read diagnostic: 493 bytes;
- physical-write diagnostic: 348 bytes; and
- production BIOS: 942 bytes.

```text
bb1dd2911689b834441e04bf004cc171f0c418376333490a45e5928cb3d7a83b  bios.bin
```

## Next increment

Add fault-injection coverage for failed pre-read, failed physical write, and
invalid mapping state. Then specify bounded controller waits, retry policy,
error recovery, and buffer validity after failure before relying on this path
for filesystem mutation.
