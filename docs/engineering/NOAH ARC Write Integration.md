# NOAH ARC write integration

Status: production ARC command integration and both-platform qualification
complete, 2026-10-26. The exact final binaries pass native ZSM4/LINK comparison
and execution from the NOAH companion Utilities disks. PR 521 remains unmerged. The
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
512-byte allocation. Native execution confirms both loaded ceilings.

Disk costs include the original archive, full replacement stage and rollback
reservation. Compressed preparation additionally retains one current candidate
stage plus an aggregate with `ceil(selected_count/2)` metadata records and the
encoded record streams. Exact aggregate size depends on actual codec output;
explicit compression may increase size. Full-media errors never permit an
in-place update or omitted member.

## Qualification and distribution

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

The full transaction campaigns pass on z80pack and Model 4. The exact final
module bytes and companion-volume execution pass on both platforms. The full
campaigns precede two small final deltas: opaque-suffix warning reporting and a
failure outcome for rejected low-memory transactions. The final native/media
campaign covers the warning path; the final 181-case production host campaign
also covers the memory-failure outcome. The
[qualification receipt](NOAH-ARC-Write-Qualification.json) records the exact
binary/image hashes and this evidence boundary. Its
[evidence bundle](NOAH-ARC-Write-evidence.tar.gz) includes both full campaigns,
the final native/media campaigns, generated source, consoles and output files.
Unchanged native modules may be reused only after exact byte/padding comparison;
changed modules are assembled and linked again. A clean checkout after merging
main also reproduces the final NOAH.COM and overlay bytes.

The disk builder emits a separate NOAH companion Utilities volume for each
platform, containing NOAH.COM, its matching NOAH.OVL and NOAH.TXT:

- `BetterCPM-NOAH-z80pack-332K.dsk`
- `BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk`

The 332K primary was 8 KiB short with these files; no selected primary program
or license text was removed. Independent inventory, allocation, file readback
and DMK/raw checks pass for all four images. Mount the companion in B: to use
NOAH, and keep archives/sources on the writable work disk. The package retains
corresponding source and the unchanged third-party tool/license companions.
ZSM4/LINK are qualification tools, excluded from BetterCP/M-owned versioning.
NOAH component acceptance does not claim whole Utilities release acceptance.
The interactive browser, ZIP and LZH/CrLZH selectors remain deferred.
