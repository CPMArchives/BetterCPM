# Noah’s ARK Engineering Specification

**Program:** `NOAH.COM` with `NOAH.OVL`  
**Distribution:** BetterCP/M Utilities Disk  
**Status:** Consolidated behavioral baseline, 2026-10-23. No substantive user-policy decisions remain open; binary interfaces and measured limits must pass the
implementation gates in section 16. LBR reader/listing, integrity audit and new-file
extraction increments exist; see [current implementation scope and checks](NOAH%20LBR%20Integrity%20and%20Extraction.md).
Full specification conformance and release qualification are not claimed.

This document supersedes the chronological NOAH decision draft. Settled behavior
is normative. Editorial defaults below use existing BetterCP/M conventions;
section 17 records behavioral review closure.
See the [consolidation audit](NOAH%20Specification%20Consolidation%20Audit.md).

## 1. Scope and boundaries

Noah’s ARK manages CP/M LBR libraries and ARC-compatible archives conventionally
named `.ARK`. Both target listing, testing, extraction, creation, addition,
replacement and removal. Start implementation with readers/tests/extraction,
then add updates. ZIP and LZH/CrLZH `/LZ` are future extensions, not initial-release
requirements. No new archive format is to be invented under the ARK name.

Squeeze `/SQ` and Crunch `/CR` support both standalone files and compressed
files stored in LBR. ARK must remain compatible with existing historical CP/M
ARK archives and tools, using its native container-managed compression encodings.
For ARK, compression selectors choose compatible native methods; they must not
relabel standalone CP/M Crunch streams as native ARK data. Exact method coverage
and switch mappings must be pinned and qualified under section 16.
Encryption, automatic nested-archive traversal, undelete, writable mounting,
multivolume output and a permanent backup history are outside this baseline.
Read-only LBR mounting through an RSX is a separate post-1.0 roadmap item.

### 1.1 Container versus codec

| Representation | Normal extraction | Explicit expansion | Integrity testing |
| --- | --- | --- | --- |
| LBR member | Return its stored file, using authoritative length/padding metadata | Decode one recognized standalone codec layer; ordinary members copy unchanged | Check LBR structure/stored data and available CRCs; do not require inner decompression |
| ARK member | Decode the archive-managed method; retain the archive member name | No additional recursive decoding is implied | Decode supported methods and check their integrity fields |
| Standalone compressed file | Use `/EXPAND` | Decode one layer using a validated original filename | Codec checks are part of decoding/verification |

LBR itself does not compress members. An entire compressed LBR must first be
explicitly expanded; processing an LBR is not permission to recursively open
its contents. Unsupported methods may be preserved as opaque data only when
container boundaries and required metadata are safely understood (section 8).

## 2. Command interface

### 2.1 Forms

`archive` below is one archive selection; `member` is one optional stored-name
pattern; `sources` is one shared source-filespec expression; `destination` is one
DU. Additional operands are invalid in this initial grammar. A compound selector
is still one expression, not an unbounded list of command operands.

| Form | Meaning and defaults |
| --- | --- |
| `NOAH archive [member]` | Read-only LIST |
| `NOAH /LIST archive [member]` | List active matching members; omitted member means `*.*` |
| `NOAH /T archive [member]` | Same as `/TEST`; test all active members if omitted |
| `NOAH /X archive [destination:pattern]` | Same as `/EXTRACT`; omitted pattern means `*.*`, omitted destination means caller DU |
| `NOAH /X /EXPAND archive [destination:pattern]` | Extract, expanding recognized supported compressed LBR members |
| `NOAH /ADD archive sources` | Create if absent, otherwise update; sources mandatory |
| `NOAH /REMOVE archive member` | Member mandatory, including explicit `*.*` to remove all active members |
| `NOAH /COMPACT archive` | Explicitly reclaim LBR deleted entries/data and holes |
| `NOAH /COMPACT /ADD archive sources` | Compact and add in one staged transaction |
| `NOAH /COMPACT /REMOVE archive member` | Compact and remove in one staged transaction |
| `NOAH /EXPAND sources [destination:]` | Standalone one-layer expansion |
| `NOAH /SQ sources [destination:]` | Standalone Squeeze |
| `NOAH /CR sources [destination:]` | Standalone Crunch |
| `NOAH /VER` | Standalone metadata-owned version display |
| `NOAH /HELP` | Usage, operation/options and format capabilities |

In an extraction selector, `B3:` denotes a DU prefix, not a literal replacement
filename. Examples below make the counted command syntax concrete.

```text
NOAH /LIST B[0-15]:*.LBR README
NOAH /TEST B[0-15]:*.LBR *.COM
NOAH /EXTRACT B12:*.LBR *.?Q?
NOAH /X /EXPAND TEXTS.LBR B3:*.TQT
NOAH /EXTRACT TEXTS.LBR B3:
NOAH /X TEXTS.LBR
NOAH /ADD /SQ B:TEXTS.LBR *.TXT
NOAH /COMPACT /ADD C0:TEXTS.LBR B2:*.TXT
NOAH /REMOVE B[0-15]:*.LBR OLDFILE.TXT
NOAH /COMPACT C:*.LBR
NOAH /SQ B[1,3,8-10]:*.TXT[$ARC] C3:
NOAH /EXPAND B2:*.TQT C3:
```

Archive operations always put the archive before source/member operands.
Standalone codecs instead put sources before an optional destination DU.
`NOAH /ADD TEXTS.LBR` and `NOAH /REMOVE TEXTS.LBR` are incomplete usage;
neither inherits an implicit all-files selection. An archive-only invocation
lists it; no arguments prints concise usage and returns without file activity.
There is no implicit format conversion, rename template, `/TO=` or `LBR.COM` alias.

### 2.2 Options and parser conventions

| Option | Meaning |
| --- | --- |
| `/Y` | Unattended ordinary replacement/removal approvals; explicit COMPACT also approved; never a protection override |
| `/Q` | Suppress routine progress/success messages, not prompts, skips, warnings, failures, recovery filenames, LIST results or summary |
| `/R` | Enable a separate interactive read-only override confirmation |
| `/SYS` | Enable a separate interactive system-file override confirmation |
| `/SQ`, `/CR` with ADD | Select one supported compression method; no automatic compression without a selector |
| `/LZ` | Reserved future LZH/CrLZH codec selector; report unsupported until delivered |
| `/CAPACITY=n` | LBR total ordinary-entry capacity for creation/update; section 5 |
| `/FORMAT=LBR`, `/FORMAT=ARK` | Choose format for a new archive with an unrecognized extension; never convert an existing archive |

These capacity/format spellings close previously unspecified syntax; they do
not change agreed sizing or format-selection behavior. `/CAPACITY` is valid
with ADD or COMPACT, not with a read-only operation or standalone codec.
A smaller explicit capacity can resize the staged directory only if every
retained entry/data requirement is satisfied. This never implicitly compacts.

Use case-insensitive, exact switch tokens and documented aliases only; no
arbitrary prefix abbreviations. Identical repeated switches are idempotent;
differing codec/format/capacity settings conflict. Parse the entire counted
command tail before creating transaction files or performing mutations. Options
may appear before or after operands without changing operand order or acquiring
per-operand scope. Reject unknown switches, malformed values, extra operands
and invalid combinations with `NOAH: Invalid usage.` and concise usage guidance.

One primary operation is permitted, except the documented COMPACT+ADD,
COMPACT+REMOVE and EXTRACT+EXPAND combinations. COMPACT+ADD may also select one
compatible codec. Global approval/output/protection options retain their own
scope. `/LIST /ADD`, `/SQ /CR`, standalone EXPAND+SQ and any unlisted operation
combination are errors, not first/last-switch-wins behavior. Reject irrelevant
options instead of silently ignoring them. `/VER` and `/HELP` are standalone;
they do not require an archive or overlay. HELP may state built-in supported
capabilities without opening `NOAH.OVL`.

### 2.3 Archive recognition and creation

Recognize an existing container by validated content, not its extension. New
`.LBR` selects LBR; `.ARK` and the equivalent `.ARC` spelling select the
supported ARC-compatible format. Unknown new extensions need FORMAT. If a
FORMAT option contradicts an existing recognized container, refuse the request;
never reinterpret a file to make an update fit. Missing, unreadable and invalid
existing files are distinct; only genuine absence permits create-on-ADD.
Ambiguous or unsupported recognition produces an explicit diagnostic.

## 3. Selection, order and input preservation

LIST, TEST, EXTRACT, REMOVE and COMPACT accept wildcard archives and shared
DU/user selections. ADD requires one exact archive name resolving to one DU.
Reject a wildcard/compound target before mutation; use separate invocations or
SUBMIT for multiple ADD targets. ADD and standalone codec source selections
use BetterCP/M's shared filespec grammar, including supported DU ranges and
attribute predicates, without a divergent NOAH interpretation.

Member patterns are case-insensitive CP/M 8.3 `*`/`?` patterns. A supplied
`README` means exactly the extensionless file, never implicit `README.*`.
Use the common filename matcher. Attribute/DU selectors on disk files do not
create internal archive directories or member predicates. A member selector is
not a filesystem lookup. Expanded extraction still matches stored names first;
`*.TQT` may produce `README.TXT`. Destination checks use the final output name.

Traverse drives alphabetically, all selected users of that drive in numeric
order, then filenames alphabetically within each DU; only then change drive.
Source-file traversal follows the same rule. Use normalized padded 8.3 name
comparison. Member enumeration/listing preserves the handler's on-disk order;
it need not load/sort a whole member directory merely for display.

Capture the caller DU at entry. Unqualified destinations always use that captured
DU, not the location of the input or a temporary traversal DU. Restore caller
drive/user on every NOAH-controlled return path, including errors/cancellation.
Destination operands resolve to one DU, not multiple destinations or renames.

Freeze source/archive membership before output can expand the selection. Use a
bounded plan or demonstrably equivalent stable traversal; RAM limits do not
justify acquiring newly created output as input or losing pending input identity.
Read-only concurrent source changes must be detected where possible; abort the
affected transaction if stable input cannot be established. No power-loss or
concurrent-writer locking guarantee is implied.

ADD excludes its resolved target and active transaction files, reporting full
DU/name and reason. Same basename on another DU is not self-inclusion. Do not
exclude unrelated files merely because their extensions are TMP/BAK.
Extraction/standalone output may not overwrite any selected input file/archive,
including pending ones, even with Y/All/R/SYS. Report and count exclusions.

ADD and standalone codecs do not delete sources, change source attributes or
clear their ARC bits. Future archive-and-mark/delete behavior needs a separate
specification. This does not suppress automatic access metadata maintained by
a future host independently of NOAH.

## 4. Compression, names and binary lengths

Store unchanged source contents unless one codec is explicitly requested. Do
not auto-select a codec by filename, size or remembered settings. Explicit
compression remains selected even if output grows: report the increase; do not
silently fall back to another method or mislabeled uncompressed contents.
Unchanged retained archive members are not transcoded during an update.

For LBR/standalone Squeeze, use traditional `.?Q?` naming and an original-name
header, e.g. README.TXT → README.TQT. Crunch uses its selected historical naming
and format (`.?Z?`); future CrLZH uses its qualified variant, not an invented
container. Pin extensionless/short-extension transformations against the
reference codec fixtures. Resulting stored names drive ADD collision detection.
ARK integrated compression retains the original archive member name. Standalone
CP/M codec files are not automatically valid native ARK method streams. Shared
codec internals are permitted wherever compatible, but historical on-disk
encodings must be preserved.

Normal LBR extraction returns opaque stored files, even if squeezed/crunched.
EXTRACT+EXPAND decodes one recognized supported inner layer and copies ordinary
members unchanged. Recognized unsupported/corrupt compressed data must not be
silently copied as successful expansion. Standalone EXPAND reports `not compressed`
for genuinely ordinary inputs and copies them unchanged, retaining their names.
This is a successful copy, not a skipped file or an expansion failure; normal
destination collision, protection, staging and verification rules still apply.
If source and destination identify the same file, report `not compressed; unchanged`
and leave it untouched rather than overwrite the source.
A compressed entire LBR needs an explicit outer EXPAND first.
ARK decoding of its storage method is normal extraction, not permission to
recursively unpack its decoded member. No automatic recursion is permitted.

Future browsing mode may provide `V` to display a selected file whether compressed
or ordinary, using the same transparent-content principle. Browsing is a future
design consideration, not an initial implementation requirement.

Identify compression by header/structure, never the Q/Z/Y filename alone.
Embedded output names must be valid plain CP/M 8.3 names. Reject drive/user
prefixes, paths, wildcards, invalid/overlong/unterminated names instead of
truncating or sanitizing. The selected destination remains authoritative.
Ordinary case normalization is allowed; manufacturing a different name is not.

All I/O is binary: no Ctrl-Z EOF, CR/LF translation or trailing-byte stripping.
Separate host record count, stored representation length, decoded length and
container padding. A CP/M source exposing only full 128-byte records supplies
that length; do not invent byte precision by scanning for 1Ah. Honor valid
container/codec pad metadata. On output hosts lacking byte-precise lengths,
record padding must be deterministic and excluded from logical comparisons
where authoritative metadata permits; preserve all significant bytes.

## 5. LBR directory capacity and deleted-data preservation

Use LUDEF5 as the layout reference, retaining compatibility with older unstamped
libraries. Directories have four entries per 128-byte record; the first describes
the directory. N records therefore hold at most 4N−1 ordinary entries, including
retained deleted entries. Active count is not allocated capacity.

For F occupied entries in the proposed result (active plus retained deleted),
default spare allowance S=max(4,ceil(F/4)). Allocate ceil((F+S+1)/4) records.
Do not grow a sufficient directory just to restore 25% spare after every ADD.
When genuine unused entries run out, automatically grow the staged directory
using that formula, reporting old/new capacities and rebuilding from active
members only. Recompute F from the active result for this rebuild.

Explicit CAPACITY C can increase or reduce the default allowance. It denotes
total ordinary-entry capacity, not added spare or the directory-control slot.
Require C≥F; allocate ceil((C+1)/4) records and report actual capacity 4N−1.
Up to three rounded spare slots are unavoidable. The explicit requested limit
is binding in this invocation: incidental rounding does not authorize additional
selected entries beyond C. The unrounded request is not persisted in standard
LBR; later invocations use actual allocated capacity. Reject insufficient or
out-of-format values before publication; do not drop members to fit.

When no layout rebuild is required and COMPACT is absent, preserve deleted
entries, associated bytes and unused payload regions. Do not reuse deleted slots/data, even for a smaller incoming file.
Append new data and use genuinely unused entries. REMOVE marks an active entry
deleted; successful replacement retains its displaced version as deleted and
uses another entry for the replacement. A replacement therefore can require a
new slot. Count retained versions when sizing. Preserve accepted intermediate
versions too if later selected sources replace them. A failed/skipped replacement
retains the previously accepted data/metadata, not an incomplete candidate.

A staged safety copy that retains the directory layout preserves existing payload
before appending changes; making a safety copy alone does not require compaction.
When rebuilding the library from scratch, including directory enlargement or
another layout-changing resize, copy active members only. Do not attempt to copy
deleted entries, deleted-file data or payload holes, and do not interpret their
possibly invalid references. Report that the rebuild discards deleted recovery
material. This is an explicit exception to preservation during ordinary updates;
no additional COMPACT switch is required for a necessary directory rebuild.
Recalculate all active offsets and integrity fields. The original library remains
protected by the normal staged verification and publication rules. Preservation
in ordinary updates is not an undelete feature or a promise to recover files
already damaged by another program.

Explicit COMPACT discards deleted entries/recovery data and payload holes in the
replacement. Warn/authorize under section 7. Keep the selected directory capacity
unless explicit CAPACITY requests a valid resize; compaction alone does not
shrink it. Recalculate offsets/integrity fields correctly. A valid empty-member
library is permitted after explicit REMOVE+COMPACT; its directory still exists.
COMPACT in other containers requires an advertised, defined implementation;
do not invent an ARK deleted-entry format or silently recompress its members.

## 6. Metadata and timestamps

Expose stored name, stored/logical/original sizes with availability, storage
method, available timestamps/attributes and integrity information. Zero is a
valid size, not an unknown sentinel. Recorded checksums and verified results
are distinct. For LBR, an inner compressed file remains container-stored data;
optional codec inspection returns additional metadata separately.

Read legacy and timestamped LBRs. Preserve member timestamps on copying and
reorganization. Follow format-specific raw/effective timestamp semantics: do
not universally equate a zero field with an unknown value where the format uses
it as an inherited/default date or a valid midnight. Preserve raw metadata for
unchanged entries and expose availability accurately. Invalid optional metadata
is reported without inventing dates; it is not permission to accept unsafe
member bounds.

The CP/M adapter defines get/set timestamp operations now, returning available
fields, unsupported/unavailable, or actual error distinctly. No new BIOS/BDOS
filesystem date service is required now. ADD captures source timestamps where
available; otherwise writes format-defined unknown fields. Never use current
time as a substitute for unknown source history. Extract restores available
metadata only when the host can; otherwise completes data extraction with an
explicit not-restored warning. An actual timestamp-write failure uses normal
retry/skip/abort before publication, not silent success.

Use existing clock facilities only for metadata describing a genuinely new
archive/directory change, if a valid clock is available. Preserve original
archive creation metadata and unchanged members. If unavailable, use legal
unknown representation. The per-format implementation appendix must specify
precision/range conversions and cannot fabricate a timestamp for a format
without an agreed legal unknown encoding.

New extraction/standalone outputs default read/write, non-system. Replacing an
existing destination retains that destination's RO/SYS settings after authorized
modification. Do not copy source/member protection over those existing settings.
Source ARC is never cleared. Newly created/modified output ARC follows normal
BetterCP/M changed-file behavior, not an imported source backup history (see
COPY's [ARC convention](COPY%20Specification.md)). Failures applying required
attributes are real metadata failures and enter recovery; report actual state
if protection cannot be restored.

## 7. Collisions, protection and authorization

| Situation | Interactive behavior | Under `/Y` |
| --- | --- | --- |
| Ordinary extraction/standalone output exists | Yes, No, All, Cancel | Approve replacement |
| ADD member name exists, including an earlier accepted source | Replace, Skip, All, Cancel | Approve replacement |
| REMOVE has matching active members | Show names; confirm once per archive, default No | Approve ordinary removal |
| Explicit COMPACT, alone or combined | Warn of deleted-recovery loss; confirm once per archive, default No | Approve only because COMPACT is explicit; keep warning |
| Archive/output is RO or SYS without required selectors | Report skip/refusal | Same |
| Protected modification with R/SYS selectors | Separate confirmation per object, default No, no All | Skip, do not prompt |

R enables requesting an RO override; SYS enables a SYS override; both are needed
for both attributes. These are not source-selection broadening or approval by
themselves. Ordinary All/Y never approves protected operations. Confirm each
protected archive transaction or extracted/standalone destination once, showing
resolved DU/name and attributes. Preserve or restore original protection after
publication/failure; do not clear it just to start staging. Read-only LIST/TEST/
EXTRACT input access is allowed on protected archives.

Ordinary All spans matching ordinary collisions in this operation only and
includes later source/member/output collisions; no state leaks to another
invocation. Show the currently accepted origin and incoming source where names
collide. No unconditional first-source-wins rule exists: a larger replacement
is safe because it is built separately, not over the old allocated region.

Use the [shared input/UI library](Shared%20Input%20and%20UI%20Specification.md).
Single-character answers are case-insensitive/immediate; invalid answers retain
the question. Enter chooses displayed No defaults; ordinary collision prompts
also default to No/Skip, never destructive Yes. Retry/Skip/Abort has no automatic
retry default. ESC cancels the current decision with operation-cancel semantics;
Ctrl-C requests the controlled stop in section 10. Do not treat a No as Cancel.
Page long preflight lists using established utility paging; show the final
question only after its required list. Q suppresses no required prompt/list.
Combined REMOVE+COMPACT may use one explicit question naming both actions and
the recovery loss; it must authorize both. Decline leaves that archive unchanged,
not an implicit update without requested compaction.

## 8. Construction and verification

Every new archive, update, extraction and standalone codec output is staged in a
separate file on its target DU. Never overwrite original contents in place or
fall back to in-place updates when space is short. Allocate capacity/counts with
retained deleted data, candidate outputs and rollback needs included. Do not
promise a specific scratch maximum before the memory/disk prototype.

After completing and closing staged output, reopen it for verification. Check
container structure, non-overlapping bounds, lengths, expected accepted change
set and metadata. Compare retained member stored bytes to original bytes; when
preserving the LBR layout, also compare preserved deleted/unused regions and required
reference adjustments. The verification plan includes failed/skipped replacements
and must not mistakenly require a change the user explicitly skipped.

For new/changed content, compare readback to source or an independently retained
construction digest, and validate available format integrity fields. A staged
file's checksum compared only against its own recomputed checksum is insufficient
proof that it contains the intended source. Compressed output must be decoded
and checked against intended input; unchanged retained LBR files do not require
inner decompression. Specify digest coverage and source-stability checks before
implementation. No user option disables mandatory publication verification.

ARK members with safely understood boundaries but unsupported codecs may be
retained byte-for-byte, reporting `preserved; contents not tested`. This permits
an update with limited content coverage, not a full verification pass. Such a
member may be removed/replaced without decoding its old contents. Unknown unsafe
boundaries or required semantics forbid the update. TEST/EXTRACT must not report
unsupported decoding as passed.

Older LBR CRC absence/garbage conventions need explicit compatibility fixtures;
a missing CRC is not a passed checksum. A mathematically valid zero CRC must not
be confused with an absent-field convention. Follow format-specific handling
and report coverage. Verification failure blocks publication and preserves the
original. Malformed input is never repaired as a side effect of unrelated work.

## 9. Publication and recovery files

Derive a pair from the first six basename characters (or the full shorter name)
plus two digits, extensions TMP/BAK. Search 00–99 for a pair unused in that DU
and distinct from all protected input/target/reserved identities. Examples:
BETTRCPM.LBR → BETTRC01.TMP / BETTRC01.BAK; TEXTS.LBR → TEXTS01.TMP / TEXTS01.BAK.
Extraction uses the final output basename, including expanded names. Do not
commandeer earlier recovery files or unrelated TMP/BAK files. New creation has
no old file to back up but uses the same collision-safe pair-selection rule.
If no safe pair/space is available, fail before changing originals. No automatic
alternate scratch DU or destructive cleanup is permitted.

| Stage | Required result |
| --- | --- |
| Build/close/verify TMP | Original unchanged; clean disposable failures, retain required recoverable data |
| Rename original to BAK | If it fails, do not publish TMP or assume original moved; report actual names/state |
| Rename verified TMP to requested name | Recheck target identity/absence; never overwrite an unexpected file |
| Publication fails after backup rename | Restore original name; preserve TMP until safe cleanup/recovery decision |
| Restoration also fails | Stop batch; retain/report original backup and verified replacement with exact DU/names |
| Publication and required metadata succeed | Delete original backup |
| Backup deletion fails | Keep new published output; report `Update completed; backup cleanup failed` (appropriate extraction wording), warning outcome |

New output publishes without an original backup. These are separate CP/M file
operations, not a power-failure-proof atomic transaction. Retain authoritative
original/protection state through rollback. Clearing RO solely for an authorized
backup cleanup must not expose an incorrectly unprotected published file.
If names/state cannot be established after an I/O failure, stop; don't guess.
On any failure/cleanup issue report which file contains the original versus
verified or incomplete output. No automatic resume/recovery command is promised.

## 10. Failure handling, cancellation and no-ops

Offer Retry/Skip/Abort only where safe. Retry must return to an established state
without duplicated output or lost original data; Skip requires a trustworthy next
member/boundary. Abort preserves originals and necessary recovery files.
Under Y, skip when safe, otherwise abort; never wait for these prompts or retry
indefinitely. Failed restoration/unsafe publication stops the whole batch.

| Case | Behavior |
| --- | --- |
| New ADD source fails and is skipped | Omit that requested addition; report it |
| Replacement source fails and is skipped | Keep previously accepted version, including one from earlier in this invocation |
| Existing member/deleted region that must be retained cannot be copied | Abandon affected archive update; don't silently omit it |
| Member extraction/codec failure | Preserve old destination; clean/retain incomplete staged output appropriately; continue only safely |
| One selected archive unreadable/corrupt | Report failed archive and continue if safe; no implicit rewrite/repair |
| Invalid invocation | Reject before mutation, with usage diagnostic |
| No ADD sources match, or all selected sources are excluded | Report no match/exclusions; no new empty archive, rewrite, timestamps, compaction or leftover transaction files |
| REMOVE matches no active members | `No members matched` with archive identity; unchanged, continue; no staging even with combined COMPACT |
| LIST/TEST/EXTRACT member filter matches nothing | Report per-archive no match; no output or update |
| No archive/standalone source matches | Report selection no match; no output or staging |

If all proposed changes are declined/skipped and no explicit valid compaction or
capacity change remains, leave the archive unchanged rather than publishing a
meaningless rebuild. A no-match REMOVE remains unchanged even with COMPACT;
this preserves its explicitly agreed no-match rule. Invalid capacity or required
capability errors are not silently downgraded to no-match success.

Poll Ctrl-C at bounded safe points through long reads/codec work. Before
publication, stop without publishing an incomplete result, preserving originals.
Defer cancellation during the rename sequence until it finishes or restores the
original; report if publication completed before cancellation took effect.
Previously completed extraction files/archives remain completed. Stop before
further members; account for completed/skipped/failed/unprocessed work. Cleanup
failure never licenses deleting the only recoverable original. Restore caller DU.

## 11. Reporting and completion

Use 7-bit ASCII, CR/LF and the finalized [visual identity](../../specifications/VISUAL-IDENTITY.md).
No startup banner on ordinary commands. VER uses metadata-owned version/build
and the compact implied-corner format in [utility versioning](../../specifications/UTILITY-VERSIONING.md).
CLI operation needs no loaded monitor provider. Standard prompts use the shared
library; optional paging must have a plain-console fallback and must not introduce
a full-screen monitor prerequisite.

LIST identifies each archive by DU and displays active member name and sizes;
show codec, timestamps and availability where meaningful with bounded-width
continuation/detail lines. Do not display invented zero dates or claim an LBR
member's inner codec was decoded merely to enumerate it. Deleted entries are
not active LIST/EXTRACT/TEST matches. Q never removes requested LIST results.

Report every exclusion, skip, failure, protection refusal, unsupported/untested
representation and retained recovery file with enough archive/member/source/
destination identity to distinguish duplicate names. Default Q suppresses routine
progress/success per-file lines only. Size increases from explicit compression
are reportable, not silently hidden by Q. Removal preflight names remain visible.

Summarize archives selected/completed/no-match/skipped/failed/unprocessed and
members/files completed, skipped, failed and unprocessed as applicable. Include
changes declined, limited test coverage, recovery artifacts and cancellation.
Counts must describe accepted changes separately from candidate inputs and must
not double-count an object merely because it has several diagnostic reasons.

Logical completion outcomes are success, warning/partial, failure and cancellation.
Cancelled is explicit even when earlier work succeeded. Fatal validation/unsafe
recovery or zero completed work with actual errors is failure; useful completed
work with skips, some failures or incomplete coverage is warning/partial, with
all component failures retained. No matches is a reported no-op, not fabricated
work; classify as warning/no-work. Backup cleanup failure is a warning after
successful publication. Clean success excludes skipped/untested required work.

Do not promise a numeric shell exit API: none was established by the source/spec
review. Keep an internal logical result and textual summary; bind numeric return
status only to an audited existing BetterCP/M mechanism. Adding resident status
services is outside this utility's scope.

## 12. Reusable libraries and I/O contract

Keep separate callable ZASM4 LBR and ARK libraries; future ZIP uses the same
architecture. Macros may simplify calls but must not replicate substantial
handler code per invocation. Libraries own container recognition, directories,
member positions, metadata and format checks. Applications ask for members/data;
they never need to parse container directories. Libraries do no prompting or
screen output. NOAH owns CLI, selection, authorization, reporting and transactions.

The standard CP/M adapter supplies ordinary-file open/close/seek/read/write and
timestamp capabilities. A simple open/first/next/read/close wrapper binds it for
normal callers without callback wiring. Advanced callers can supply a versioned
callback vector and opaque context for other byte sources. This permits reuse,
not a promise of automatic nested archives or a mounted filesystem now.

| Interface | Required contract |
| --- | --- |
| Stream callback | Caller context, direction, absolute byte offset/position and bounded buffer; actual transfer count and explicit result |
| Container context | Caller-owned initialized state and workspace; no hidden resident allocation |
| Capabilities | Implemented read/write/test/compact operations, format versions, method compatibility and required workspace |
| Iterator | Open, first/next, close; one caller-buffered member record, no whole-directory RAM prerequisite |
| Member record | Normalized stored name; stable identifier; stored/logical/decoded lengths with validity; method; available attributes/timestamps/checksum and separate verification status |
| Member reader | Sequential bounded reads; stop at member boundary; optional advertised random access |
| Codec | Init/step/final/close; bounded input/output, consumed/produced counts, explicit need-input/need-output/done/error |
| Timestamp adapter | Available fields, unavailable/unsupported and actual errors distinguished |

Use 32-bit checked byte offsets/lengths at the shared stream boundary, 16-bit
per-call buffer counts and 16-bit memory pointers on Z80. Reject arithmetic
wrap, unaddressable CP/M FCB records and format-specific overflow. Handlers impose
their narrower format bounds. EOF/end-of-member/end-of-directory, unsupported,
invalid structure, checksum failure, ordinary I/O error, cancellation and insufficient
resources are distinct logical results. A short read is not automatically EOF.
Zero-capacity reads perform no I/O; empty members reach normal end without data.

Buffers/workspaces/records belong to the caller. Define overwrite/lifetime rules
explicitly; returned metadata cannot be a pointer into an overlay that gets
replaced. One active callback/prompt context must not recursively reenter itself.
Codec step loops must make progress or return a defined wait/error condition.
A codec may need a fixed window/dictionary or two passes/rewind (e.g. static
Huffman construction); streaming does not require an impossible single-pass
encoder or whole-file RAM. Optional seekability must be checked before starting.

Before coding, produce one common include defining actual register conventions,
request/record offsets, error values, preserved registers, stack use and version.
Cross/native expansions and reusable examples must consume that same include.
The logical contract here is not a claim that a measured binary ABI exists yet.

## 13. Overlay loader and memory

One `NOAH.OVL` contains format and codec modules. Load only needed code; direct
linking of shared routines remains available to other applications. Lookup uses
the captured invocation DU, then A0: as the standard fallback, with clear missing/
mismatch diagnostics; do not scan arbitrary drives/users or overwrite modules.
Document this search and test launching NOAH from a different DU than its files.

Validate signature, file-format/ABI version, matching build ID, index/module bounds,
entry addresses and CRC-32/ISO-HDLC coverage before executing code. Cover index
and lengths as well as module bodies; arithmetic checks precede reads. A changed
companion must be revalidated before additional modules execute. Checks detect
accidental corruption/mismatch, not hostile replacement of executable and overlay.

Determine required modules/capabilities before mutations. Missing/invalid modules
cannot silently change requested representation or bypass verification. Validate
later-loaded modules before use; if loading fails mid-operation, preserve original
and recovery states. Loader/adapter dispatch and transaction cleanup must remain
available when a handler or codec window is replaced.

Allocate separate non-overlapping live code/state regions for controller/adapter,
container handler and active codec, or prove an equivalent safe reload model.
Keep live records/state outside overwritten windows. No codec can invalidate a
handler callback still on the stack. Budget code, buffers, dictionary, iterator,
selection plan, verification digests, recovery state and worst-case stack together.
Inspect current TPA before work; fail honestly if the required combination cannot
fit, including with optional RSXs loaded. Do not lower existing OS TPA contracts
or add BIOS/BDOS resident code to make this utility fit. Exact load addresses,
minimum TPA and codec-specific limits are measured prototype gates, not guessed
user commitments.

## 14. Compatibility references and unresolved coverage

References were inspected on 2026-10-23. Pin copies/hashes/versions and fixtures
before using them as implementation or qualification baselines; a live URL is
not a frozen artifact. Published source is not automatic permission to copy it;
record license/attribution and choose a compatible implementation path.

- [LUDEF5](https://www.seasip.info/Cpm/ludef5.html): canonical LBR layout,
  directory control entry, CRC/padding and timestamp compatibility. In particular,
  deleted-entry fields are undefined, affecting preservation during relocation.
- [SEA ARC packing source](https://github.com/hyc/arc/blob/master/arcpack.c):
  native stored, squeezed and crunched representations are selected by archive
  method identifiers; standalone CP/M files cannot simply be inserted as those
  native streams. Its smallest-method fallback is **not** NOAH behavior when a
  user explicitly selects compression.
- [Deark ARC decoder](https://github.com/jsummers/deark/blob/master/modules/arc.c):
  independent method dispatch/structural oracle; distinguishes old/new stored,
  packing, several crunched variants and later extensions. Not a substitute for
  historical interoperability fixtures or a license audit.
- [Frank Prindle's UNCR231 source](https://www.tuhs.org/Usenet/comp.sources.unix/1986-December/003288.html):
  CRUNCH 2.x decoding explicitly differs from 1.x. Existing conformance-toolkit
  CRUNCH 2.4/UNCR binaries and hashes are a candidate oracle, not NOAH-linked code.
- [Archived CP/M codec/source inventory](https://dflund.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/squsq/):
  candidate CRUNCH/CrLZH artifacts to retrieve and pin. An inventory entry alone
  does not prove source completeness or reuse permission.

The compatibility matrix must state, separately, which container methods can be
recognized/preserved, decoded/tested and encoded; standalone codec versions; and
whether later format extensions are read-only or rejected. Initial target names
are not a promise to implement every historical ARC dialect.

## 15. Qualification plan

Qualification is required before adding NOAH to release media as implemented.
Retain revision, program/overlay/source hashes, native/cross build tools, fixture
provenance, platform and explicit pass/fail/blocked/not-applicable results.

| Area | Required evidence |
| --- | --- |
| CLI | Every command/combination/default; malformed/conflicting/duplicate options; no mutation on invalid input; VER purity, aliases, counted-tail bounds |
| Selection | Shared DU/attribute grammar; exact README vs README.*; drive→user→name order; no newly generated inputs; selected-input exclusions |
| Container | Old/extended/empty LBR; spare/full/deleted entries; growth/rounding/explicit limits; exact lengths/pad/CRC; active overlaps; ARK approved variants, unknown codecs/headers/trailers and corruption |
| Codecs | Independent golden fixtures, zero/record-boundary/binary/all-byte inputs, incompressible growth, max dictionary, truncated headers/trees/codes, checksums, malformed filenames, one-layer/mixed expansion |
| Preservation | Layout-preserving deleted entries/data/holes; active-only directory rebuilds; larger replacements and duplicate selected names; skipped replacement retention; active/deleted timestamps and metadata |
| Transactions | Fault each read/write/close/verify/rename/delete/attribute boundary; disk/directory full, read-only media, missing media, preexisting TMP/BAK, suffix exhaustion, unexpected target; compare originals independently |
| Authorization | R/SYS/both; separate default-No decisions; ordinary All; REMOVE/COMPACT/Y/Q combinations; protected skips and restored attributes |
| Batch/cancel | Earlier successes plus later failure; no-match; unsafe-recovery stop; long codec cancel and each publication boundary; caller DU restored |
| API/loader | Alternate byte-source consumer, iterator EOF vs failure, callback clobbers, stack canaries, offset/count overflows, zero buffers, code/state overlap, low TPA/RSXs, swapped/truncated/mismatched module/index checks |
| Platforms/media | Native ZSM4/cross parity; cpmsim and Model 4 screens, keys and disposable media; independent filesystem checks, arbitrary binary byte comparisons, compatible historical tools; Utilities Disk integration |

Mandatory verification/recovery/capability checks are not waived for a small
memory target. No test skip counts as passed. This is separate Utilities Disk
qualification; earlier core/System Disk acceptance does not qualify new NOAH code.

## 16. Implementation gates, not additional user-policy questions

Before implementation is considered reviewable, engineering must:

1. Pin the source/format/codec matrix, exact native ARK selector mappings and permitted source provenance;
   retain independent historical fixtures and checksum/codec test oracles.
2. Implement layout-preserving updates and active-only rebuilds, including malformed
   deleted references, with preservation and discard fixtures.
3. Publish the common include/API, overlay index/build manifest and checksum
   coverage; prove bounded selection, simultaneous handler/codec safety and stack.
4. Measure per-module code/workspace, realistic minimum TPA, physical file limits,
   scratch/directory costs and performance before claiming any numeric guarantee.
5. Audit the actual available command-status path; otherwise retain logical/text
   outcomes without introducing a new resident ABI. Test plain-console operation.
6. Verify exact timestamp/attribute/padding conversions, source-stability checks,
   publication/rollback stages and command-table coverage using the plan above.

These are engineering deliverables, not reasons to ask the user to choose register
assignments, every error string or another sequence of routine syntax defaults.
Initial reader work does not close these gates; full implementation remains
in progress until the applicable deliverables are satisfied.

## 17. Behavioral review closure

All substantive user-policy decisions identified by consolidation are settled.
Historical ARK encodings are required; standalone EXPAND copies ordinary files
unchanged with notice; from-scratch LBR rebuilds copy active members only.
Implementation and qualification gates in section 16 remain outstanding.
