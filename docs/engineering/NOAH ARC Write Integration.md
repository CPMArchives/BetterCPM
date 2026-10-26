# NOAH ARC write integration

Status: implementation and host fault qualification complete; current native
z80pack campaign passes. Current Model 4 and packaged-media qualification remain
in progress, 2026-10-26. PR 521 remains unmerged. The
[NOAH specification](NOAH%20Specification.md) defines behavior; this record
explains its implementation and evidence without changing that scope.

## Commands and representation

Existing containers are recognized by validated content. New `.LBR` selects LBR;
`.ARK`/`.ARC` select ARC; unknown extensions need FORMAT. Contradictory FORMAT
options and LBR-only CAPACITY on ARC fail before archive staging. Identical
FORMAT repeats are accepted; conflicting repeats are rejected.

ARC ADD creates missing archives, retains unchanged members in original order,
replaces only accepted name collisions and appends the accepted source versions.
A failed/skipped source never displaces an earlier accepted version. REMOVE
omits matched members; no-match REMOVE is unchanged, including combined COMPACT.
COMPACT preserves every retained header/payload exactly and trims only excess
00h/1Ah end padding. Opaque suffix bytes forbid COMPACT before archive staging.
Ordinary updates preserve the entire suffix after the original terminator.

ADD selects stored method 2, SQ selects native method 4 and CR selects native
method 8. Native compression preserves member names and exact encoded byte
counts, excluding scratch-file record padding. Original input is the complete
CP/M physical-record stream, including 00h/1Ah/high-bit bytes. Available source
precision cannot be invented; a source with no logical EOF metadata contributes
its full record length. Retained members retain their raw DOS date/time words;
new members have unavailable timestamps represented as zero.

## Construction, verification and recovery

Before preparing compressed sources, recognize/authorize the archive and check
the active source-plan memory bound. Each compressed candidate is encoded to a
private temporary, replayed/compared and gathered into a target-DU aggregate.
Each 64-byte private metadata row holds frozen identity, original CRC-32, encoded
record count/pad/base, encoded physical-record CRC-32, exact original byte length,
original CRC-16/ARC, exact encoded byte length and a metadata-row checksum.
Failed candidates remain failed/skipped; zero prepared candidates cannot cause
an uncompressed fallback. ARC keeps original identities; LBR keeps its existing
marked-extension naming.

The archive writer streams a distinct archive temporary. CP/M FCB extent,
allocation and record state is cleared before every temporary MAKE. Output is
packed into 128-byte records, with final 1Ah padding only after the terminator
and any required preserved suffix. A construction CRC-32 covers every emitted
physical record and the expected physical size is retained separately.

Final checks rehash all selected accepted source streams and the entire original
archive. Compressed ADD also rehashes the original uncompressed sources against
their independently retained preflight digests. Then the staged archive is opened
through the production ARC reader: duplicate names, structure, bounded extents,
decoded lengths and available CRCs are checked. Its full physical-record digest
and size must match construction. A staged file's own valid member checksums do
not replace the independently retained construction/input evidence.

Only verified output enters the shared TMP/BAK publication transaction. The
original remains authoritative until publication/attribute restoration succeeds.
Failed publication attempts restoration; uncertain rollback stops the batch and
reports actual original/backup/new/temporary paths. Verified or necessary recovery
files survive; disposable failures are removed only after confirmed cleanup.
No power-loss atomicity or automatic resume is promised.

The compressed aggregate's prefix metadata and encoded data share a file. On
EXM>0 media, lower logical-extent updates can otherwise reduce the shared
physical extent's recorded high-water mark. Standard CP/M Get DPB supplies the
target drive's EXM; the metadata transaction saves/restores the allocated FCB
for the appropriate physical extent before CLOSE. Read-only aggregate source
handles select the final committed record before CLOSE. This keeps metadata
updates and earlier-source reads from truncating later encoded data, without
changing BDOS or the disk format.

## Memory and disk costs

`tools/noah_overlays.py` emits a checked resident program and matching overlay.
The loader requires the actual controller extent rather than maximum selection
workspace. Before planning, the transaction checks `12 * selected_count` bytes
against the current BDOS vector at 0006h. ARC plans follow the record-rounded
NHARK phase. LBR transformed identities additionally require 13 bytes per selected
source in their separate arena. The frozen selection limit remains 512; it is
not a promise that every 512-source operation fits every RSX configuration.

The final methods-5–9 decoder owns a 24 KiB dictionary and can replace the now-dead
plans. All source-plan-dependent stability checks finish first. A resident
64-byte active-disposition bitmap preserves ADD accounting across that final
phase; transaction contexts, digests and callbacks also remain resident. No
handler callback can return into overwritten code: the resident bridge restores
the matching controller and ARC phase before returning.

The current z80pack receipt records resident bytes, rounded window, every phase
requirement and plan base. Its largest fixed phase ends at BB80h, below the loaded
C501h z80pack and CA01h Model 4 ceilings. Per-operation plan memory is checked
separately. Host tests measure a 56-byte maximum stack within the existing
512-byte allocation. Native Model 4 claims await the current campaign.

Disk costs include the original archive, full replacement stage and rollback
reservation. Compressed preparation additionally retains one current candidate
stage plus an aggregate with `ceil(selected_count/2)` metadata records and the
encoded record streams. Exact aggregate size depends on actual codec output;
explicit compression may increase size. Full-media errors never permit an
in-place update or omitted member.

## Qualification and remaining acceptance

`tools/test_noah.py` covers production creation, retained-copy buffers, REMOVE,
COMPACT, native SQ/CR creation/replacement, empty/binary inputs, TPA bounds,
physical-size corruption and write/publication failures. Existing LBR, codec,
source-decision, accounting, outcome, coverage and quiet suites remain regression
gates. Low-level ARC reader/writer and independent encoder suites retain their
own focused error/format coverage.

`tools/qualify_noah_codecs.py` assembles and links nine production modules with
unchanged third-party ZSM4/LINK and compares every executable byte. Separate
bounded runtime batches cover existing codecs/LBR operations, ARC creation/
replacement/REMOVE/COMPACT and 20 KiB compressed ARC/LBR extent transitions.
Original ARC and Deark independently decode the generated method-2/4/8 archives;
Deark also checks the larger SQ/CR outputs. Every disposable native filesystem is
checked and the source System/Utilities images must remain unchanged.

Current z80pack passes. The current Model 4 campaign is running. The disk builder now emits a separate NOAH companion Utilities volume for each
platform. The 332K primary was 8 KiB short with NOAH.COM, NOAH.OVL and NOAH.TXT;
no selected primary program or license text was removed. Independent inventory,
allocation, file readback and DMK/raw checks pass for all four images. Native
companion-volume execution remains to be qualified. No whole Utilities Disk
release acceptance or interactive browser completion is claimed here.
