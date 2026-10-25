# NOAH LBR writes — increment 3

NOAH 1.0 revision 6 implements LBR creation, ADD/replacement, REMOVE,
COMPACT and directory capacity selection. It remains a development utility;
this is not full NOAH qualification or Utilities Disk packaging. The
[behavioral specification](NOAH%20Specification.md) remains normative.
This is the historical revision 6 qualification record. The subsequent
[revision 7 codec and overlay increment](NOAH%20Codec%20and%20Overlay%20Integration.md)
implements codecs and production dispatch; its measured phase layout supersedes
the monolithic memory limits below. ARK, `/Q`, remaining recovery commands, the
browser and release packaging remain deferred.

## Commands

```text
NOAH /ADD archive sources [/Y] [/R] [/SYS] [/COMPACT] [/CAPACITY=n] [/FORMAT=LBR]
NOAH /REMOVE archives member [/Y] [/R] [/SYS] [/COMPACT] [/CAPACITY=n]
NOAH /COMPACT archives [/Y] [/R] [/SYS] [/CAPACITY=n]
```

The ADD target is exactly one resolved DU/name. Sources use the existing shared
DU, wildcard and attribute selection, frozen and sorted before updates (512
identities maximum). REMOVE/COMPACT use the existing archive batch. REMOVE
requires a member operand. `/CAPACITY` on REMOVE requires `/COMPACT`.
`/FORMAT=LBR` is valid on ADD; a new unknown extension requires it. Existing
contents must pass LBR recognition and complete audit; this is not conversion
or corruption repair. An absent new `.LBR` is created only for accepted sources.
Options may precede/follow operands; identical repeats are accepted and conflicting
operations or values fail before file activity. VER/HELP precedence is unchanged.

Member collisions use the existing Y/N/All/Cancel policy, default No. Sources
are identified by resolved DU/name. Failed preflight candidates are skipped,
leaving any previously accepted version in force. Construction, readback or
stability failures abandon the affected transaction. Protected archives retain
the separate R/SYS authorization; `/Y` always skips protected archives.
REMOVE lists matched members and asks once per archive; combined COMPACT warns
of recovery loss in that same authorization. Long interactive removal lists
pause after 20 names with a plain-console MORE prompt. `/Y` permits unattended
ordinary destructive work but still prints the warning/list. COMPACT alone
also warns and defaults No. All is not offered for these destructive questions.

No ADD matches, or self-exclusion of all sources, creates no archive or staging
file, even with COMPACT. No REMOVE match leaves the archive unchanged, including
combined COMPACT. Declined/failed additions may still leave an explicitly
requested valid compaction or capacity change; otherwise there is no rewrite.

## Format, preservation and bounds

Ordinary updates retain the original directory layout and all original payload
bytes, including holes and deleted data. Removed/displaced entries become FE;
new data append and use genuinely unused slots. Accepted intermediate versions
remain deleted during ordinary updates. Deleted slots are never reused.

Directory exhaustion uses the specification's active-result sizing formula;
layout rebuilds and explicit COMPACT copy active members only. Invalid deleted
references are never followed. Rebuilds report old/new directory record counts
and recovery loss. COMPACT retains the directory allocation unless an explicit
capacity changes it. Capacity is total ordinary entries; its unrounded limit
binds this invocation even when allocation rounds up. The format maximum is
262,139 ordinary entries (65,535 directory records). Counts and physical file
positions use checked wide arithmetic; no member or allocation is dropped to fit.

Source data preserve complete physical CP/M records, including embedded/final
Ctrl-Z and every byte value. New entries have zero padding count and unknown
zero timestamps: this adapter has no timestamp service. Retained raw timestamp
and metadata bytes are copied; relocated active offsets and CRCs are recomputed.
CRC16 covers physical stored records. Zero CRC remains ambiguous when reading
historical archives; it is not claimed as verified legacy coverage. Malformed
active metadata is rejected, not silently repaired.

## Transaction and memory contract

The writer streams through three 128-byte buffers, a 104-byte context and two
32-byte entries. It never buffers a whole LBR directory. The CLI owns an additional
12-byte accepted-source plan per frozen identity (6,144 bytes maximum). Each plan
stores status, physical length, CRC16 and an independently computed CRC32 digest.
The callback accepts 24-bit record positions and reports exactly 128 transferred
bytes or an explicit error. The archive read API remains unchanged.

The original is audited and hashed before staging. Every candidate is fully read
and closed before acceptance. Output uses the existing collision-checked TMP/BAK
pair and checked publication/rollback machinery. After constructing and closing
the stage, NOAH reopens it and regenerates intended directory/payload bytes from
the accepted plan, originals and sources, comparing every staged record. It checks
physical output length, source digests/lengths, and original size/digest again
before closing inputs and publishing. Empty sources are included in final
stability checks. This is not verification of a stage against its own checksum.
Existing recovery names and selected input identities cannot be commandeered.
Reported close failures preserve uncertain staging; publication failures retain
and identify recovery artifacts through the existing publisher.

This is single-process verification, not filesystem locking or a power-loss
atomicity guarantee. A disk full or unexpected I/O failure never triggers an
in-place fallback. Caller DU and default DMA are restored on normal/error exits.

The complete COM includes fixed workspace and a 512-byte private stack. Startup
checks its exclusive end against the active BDOS vector before using that storage.
The current image size and required ceiling are recorded in the qualification
JSON. No terminal provider is required. The earlier increments 1–2 overlay test
now explicitly retains its recorded 19,674-byte baseline reservation; it cannot
be used as proof that this larger writer and UNCR simultaneously fit. Production
codec overlays and workspace reuse remain later work.

## Qualification and reproducibility

- `python3 tools/test_lbr_write.py`: assembled reusable library on the Z80 core;
  independent Python CRC/byte oracles, preservation, malformed deleted references,
  active-only rebuilds, intermediate versions, capacity, source/stage corruption
  and callback short/error behavior.
- `python3 tools/test_noah_write.py`: bounded CLI/transaction cases, including
  binary/empty input, replacement, removal, compaction, capacity rounding/rejection,
  conflicting syntax, no-ops, protection, cancellation, low TPA and injected I/O.
- `python3 tools/test_noah.py`: existing reader/extractor/selector/publisher regression.
- `python3 tools/test_noah_proof.py`: historical isolated overlay/refusal regression;
  explicitly not current writer/codec coexistence proof.
- `python3 tools/qualify_noah_write.py --system /absolute/current/system-media --output /absolute/new/output`:
  native unmodified ZSM4/LINK assembly, exact cross/native COM parity, real filesystem
  creation/replacement/removal/compaction/capacity and TEST on both platforms.
  It rejects stale/unverified resident-core media and uses disposable disks.

Native export expands the original straight-line macros before assembly to fit
ZSM4's symbol workspace, without changing executable bytes. Long significant
identifier collisions are rejected. No changes or BetterCP/M version assignments
are made to third-party ZSM4 or LINK.

Results and precise artifact identities are in
[NOAH-LBR-Writes.json](NOAH-LBR-Writes.json), with a portable evidence bundle.
The native campaign also writes and independently checks a 20,480-byte member,
crossing the Model 4 16 KB extent boundary. Deark at the pinned compatibility
inventory revision independently extracts the binary and empty-member fixture.

These checks are bounded increment acceptance, not exhaustive media-fault,
interoperability or full-product release qualification.

The shared audit's `LBR_NEXT` error return now explicitly preserves failure carry
when the status is not normal end. This small prerequisite fix prevents a failed
directory read from being accepted as a completed write preflight. A dedicated
injected directory-read failure must produce no stage or publication.

Revision 6's qualified image is 33,101 bytes, with workspace/stack ending at
824Dh (exclusive); a CP/M-record-padded native COM loads through 8280h. Both are
below the bare D501h ceiling and the terminal-pair ceilings C501h (z80pack) and
CA01h (Model 4). Native campaigns run with terminal modules unloaded for the
build; the core CLI tests also exercise both reduced ceilings and reject a lower
ceiling before filesystem activity. Maximum measured private-stack use is 38
bytes with BDOS intercepted; the reserved 512 bytes also budget real BDOS calls.
