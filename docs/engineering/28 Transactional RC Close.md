# Engineering Specification 28: Transactional RC Close

## Milestone

BetterCP/M now performs its first BDOS-driven directory mutation. Function 16
can commit a validated record-count (`RC`) change from an activated FCB to its
matching directory entry through the BIOS directory-write path.

This is intentionally narrower than the final dirty Close contract. No BDOS
write function exists yet, so BetterCP/M cannot legitimately own newly
allocated blocks. Allocation-map changes therefore remain rejected until the
allocator and write path can validate them.

## Validation and merge

System Services snapshots FCB bytes 1 through 31, locates the canonical extent
using the Open engine, and compares:

- filename, type, attributes, `EX`, `S1`, and `S2` must be unchanged;
- `RC` may change but must remain in the documented range 0 through 128; and
- all 16 allocation-map bytes must be unchanged.

An unchanged FCB retains the non-writing Close path. If only `RC` differs, the
saved FCB fields are merged into the matching 32-byte entry in the private
128-byte directory record. Other changes return `FFh`, restore the caller's
exact FCB, and leave media untouched.

This field restriction is a safety boundary, not an alternate CP/M file
model. Later sequential or random Write support must expand the accepted merge
only for blocks actually allocated by BetterCP/M.

## Protection

BDOS passes the current drive's function-28 read-only state into System
Services. Unchanged Close remains harmless and succeeds on a protected disk.
A dirty Close on protected drive A returns `FFh` without changing the FCB,
private directory record, or media.

## Writeback and failure recovery

Dirty Close writes the complete 128-byte directory record through BIOS `WRITE`
with directory-write type 1. The BIOS performs its existing physical-sector
read-modify-write operation, preserving the other three logical quarters.

Before mutation, System Services saves the original 32-byte directory entry.
After successful writeback it invalidates directory/login state so the next
filesystem operation reconstructs allocation state from media. If BIOS reports
a write failure, the private buffer entry is restored and login state is also
invalidated because the physical medium may be uncertain. The caller's dirty
FCB remains exactly as supplied in either outcome.

The current `FFh` mapping for protection, unsupported dirty state, and physical
failure remains provisional; the internal carry result still distinguishes a
storage failure.

## Verification

Executable tests verify:

- an `RC` change from 1 to 2 commits to directory slot 1;
- the caller's dirty FCB is preserved exactly;
- unchanged Close still performs no write;
- function-28 protection rejects a later dirty Close without media change;
- an allocation-map mutation is rejected without media change;
- a simulated physical-write failure preserves caller and fixture state and
  invalidates the cached login; and
- dirty Close works through application `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical components: 1,407 bytes for directory/System Services and 409
bytes for BDOS.

## Provisional memory-map pressure

The expanded System Services component crossed the private buffer's `ED00h`
placement. The buffer now resides at `E400h`, below the initialization gateway,
while the BIOS physical scratch area remains `EE00h` through `EFFFh`. The dated
source comment records all prior placements.

Only a small gap remains between growing System Services and BIOS scratch, and
BDOS is also approaching the fixed `E800h` boundary. This is now evidence that
the bring-up placements have served their purpose.

## Next increment

Engineering Specification 29 completes this increment with explicit workspace,
gateway, BDOS, System Services, scratch, and BIOS regions while preserving the
page-zero ABI. The next increment can implement Read Sequential.
