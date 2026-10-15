# ED implementation qualification

Status: initial implementation stage, 2026-10-15. This is not a usable editor
and does not complete ED.COM. The system-disk manifest still marks ED planned.

## Implemented front end

`src/utilities/ed.mac` and `common/ed-invocation.inc` provide standalone `/VER`
and a bounded invocation parser. Valid non-version invocations report that the
editing engine is not yet available. No file is opened, created or modified.

The parser captures caller drive/user exactly once and validates one exact
8.3 source with optional simple DU plus an optional output DU. It supports
drive-only, user-only, drive/user and leading-zero forms. Unqualified source
uses the caller DU; omitted output uses the source DU. In a supplied output
operand, omitted drive/user components inherit from the caller, not the source.
All validation precedes any operational drive/user changes or disk access.
Source and output DU state and the source FCB are explicit. The parser never
uppercases the command tail in place; future command-case semantics remain
available to the editing engine. Compound selectors, attributes and wildcards
are rejected. Filename edge cases still require broader oracle qualification.

`tools/build_ed.py` emits only `build/ed-development/EDDEV.COM` and a listing.
The complete development build generates this artifact so standard version
checks can include its metadata, but no ED binary is copied to production
utilities or distribution media. EDDEV is deliberately not named ED.COM.

`tools/build_native_ed.py` runs ZSM4/LINK on copied stock CP/M media and compares
the linked output with the cross build. It accepts explicit simulator, system
disk, blank template and tool-directory arguments for other installations.
The tested front end is **1,053 byte-identical bytes**. The prospective utility
identity is ED 1.0 Build 001; the shared `/VER` implementation is reused.
No PL/M compiler or historical source image is part of this build.

## Front-end verification

`tools/test_ed_invocation.py` passes syntax cases across all 16 drive letters
and 32 users, caller/source/output inheritance, bounded names and invalid
selectors, unchanged command-tail bytes and standalone version queries. The
BDOS test fixture rejects every file operation or DU mutation. `/VER` executes
only the normal print service. The complete shared utility-version campaign
also passes (166 checks); distribution gates pass.

## Stock-binary behavior fixtures

`tools/qualify_ed_reference.py --diskdefs <host-build>/diskdefs` runs the pinned
stock ED binary on copied BetterCP/M media. Adding `--stock-cpm` uses copied
stock CP/M 2.2 IBM-3740 media instead. Original images and reference files are
not modified. `--record` is the explicit fixture-recording mode; ordinary runs
require exact equality with the committed fixture.

The stock binary hash is checked against the pinned provenance before running.
The six cases cover a new-file inline insert/E, new-file Q, existing-file E,
existing-file Q, split-output E and an alternate-output collision. Both
environments passed repeat runs. Transcripts and snapshots are retained under
`build/ed-development/oracle`; stock evidence includes `run-opzz19ie`, and
BetterCP/M evidence includes `run-hpqtiy3v`.

Verified behaviors relevant to later implementation:

- New-file E creates the edited source and an empty BAK; Q leaves an empty
  source and no work file. Opening a missing source has already created it.
- Q asks `Q-(Y/N)?`; this is historical authorization, not a new unsaved-change
  prompt. An existing source survives Q, while its older BAK was already
  deleted during setup. No additional backup generations are introduced.
- Split-output E renames the original source to BAK on its source drive,
  installs the result on the output drive, and returns on that output drive.
- A collision preserves both source and destination contents and the older
  source BAK, and prints `FILE EXISTS, ERASE IT`.

Two host differences are explicitly **not** normative ED behavior:

1. Collision exit is A0 in stock CP/M and B0 under the current BetterCP/M host.
   The port must implement the stock exit policy with explicit DU bookkeeping.
2. Stock ED output exports as a full 128-byte final record; under BetterCP/M
   the same case exports as 117 bytes (or 111 in the existing-file case). The
   logical text is identical. Inspection of the new-file directory entry shows
   reserved S1 = 0 on stock CP/M and S1 = 117 on BetterCP/M. The pinned source
   uses the unfilled-byte field for ISIS-II compatibility. BetterCP/M's Close
   path publishes that reserved byte. Audit this core compatibility difference
   before freezing file-commit behavior; do not silently adopt it as a new ED
   convention or alter the core contract without a targeted regression test.

Fixture `exported_bytes` is the length exported by cpmtools, not a claim about
physical record allocation. `text_hex` removes trailing CP/M Ctrl-Z padding
only. These fixtures do not qualify command parsing, all failure modes, RO/SYS,
H/O, library operations or high-user-area file I/O.

## Next implementation stage

Implement the text buffer, command scanner, insertion, movement and type
commands against the stock oracle. Add file streaming and completion only with
verified source/work/backup transitions, error exits and reserved-byte behavior.
Keep ED off the distribution until the complete accepted specification passes
normal and failure qualification on both supported platforms.
