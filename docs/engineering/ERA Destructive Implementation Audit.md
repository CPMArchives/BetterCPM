# ERA destructive implementation audit

Implemented and qualified 2026-10-11, following the ordinary ERA workflow in
PR #225. Qualification evidence is in [ERA Destructive Qualification](ERA%20Destructive%20Qualification.md).

## Existing interfaces and transient components

The standard BIOS vectors provide selection, track/sector/DMA positioning,
sector translation, and logical 128-byte record transfers. Positioning divides
the data-area-relative record by DPB SPT, adds OFF, and invokes SECTRAN with DE=0
before SETSEC. Vector-address calculation preserves DE, which is a BIOS input.
No BDOS code, protected-data layout or resident allocation changes are required.

`eraraw.inc` copies the selected DPB and reads rounded directory snapshots into
caller-owned memory. It rejects invalid drives, zero SPT, track overflow,
insufficient capacity and buffer wrap. Raw writes check Function 29's drive RO
vector and return failure on denied or failed transfers. Record addresses are
16 bits; `eraplan.inc` rejects geometries exceeding that bound before writes.

`eraplan.inc` performs no disk I/O. It retains per-block ownership and one marker
per directory entry. It decodes byte/word allocation pointers from DSM, reserves
actual directory blocks and AL0/AL1 blocks, rejects invalid/reserved pointers or
duplicate target allocations, and checks all live entries across every user
area. The input snapshot is immutable. Workspace overflow fails before that
file's writes. The selected file may have no allocation blocks.

## Shared ownership and transaction order

As decided by the user, preserve any target block also owned by another live
file. Zero only unshared target blocks. After all required zero writes succeed,
scrub the selected file's entries to `E5` followed by 31 zero bytes. Shared-block
outcomes report `erased; shared blocks retained` and have separate accounting
from fully destructive erasures. Only unshared blocks contribute to freed space.

`eraerase.inc` retains snapshot, ownership map, entry markers and scrub progress
through recovery. Data failure retries restart zeroing from the saved plan.
Data failure leaves directory entries untouched. Scrub retries resume at the
failed record. A failed transfer may have published some target bytes; rereading
allows original or scrubbed target bytes while requiring every unrelated byte
to match the snapshot. Neighbor changes cause failure instead of being clobbered.
Skip/Abort after scrub begins reports incomplete erasure, without restoring
metadata whose data is already zeroed.

## Protection and disk-state reconciliation

Ordinary ERA's Function 30 RO clearing is deliberately bypassed for `/D`.
Original attributes remain in the directory throughout data overwrite. File RO
authorization does not override drive RO; `/R` permits only the selected file's
operation. Permission is checked before planning and again for each write.

Completion, skip and abort after an attempted raw directory write use Function
37 to reset only the affected drive, then reselect/relog it. This refreshes the
BDOS directory cache, checksum baseline and allocation vector. Function 37 also
clears that drive's software RO state, so it must never be used to bypass an
initially protected drive. A write denied before reaching BIOS does not mark the
directory dirty or trigger reset. Final WBOOT is not the sole cache repair path.

The BIOS handles physical-sector read/modify/write for logical 128-byte writes;
ERA supplies complete logical records with unrelated directory entries intact.
