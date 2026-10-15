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
The initial front end was **1,053 byte-identical bytes**; the expanded buffer
core below is 1,649 byte-identical bytes. The prospective utility
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

## In-memory buffer and first commands — 2026-10-15

`common/ed-buffer.inc` now implements a caller-sized gap buffer. The prefix is
text before the cursor and the suffix is text after it; moving the gap
preserves logical text. Insertion/deletion operate at the cursor. Initialization
rejects empty/reversed bounds without replacing an existing valid context.
No fixed text-buffer size or final ED memory-capacity promise is introduced.
The final integration must reserve command workspace, stacks and I/O buffers
below the actual transient ceiling before supplying the editable region.

`common/ed-command.inc` executes the initial inline command subset: I/i, B, C,
D and U, with negative/count/# forms where applicable. Counts wrap at 16 bits
as in the reference; movement/deletion saturate at the buffer boundary.
Uppercase I translates inserted text, lowercase i follows global U state,
un-terminated inline text gains CR/LF, and Ctrl-L inserts CR/LF. Completed
commands remain applied on subsequent error or overflow, as required by ED.

These are internal routines, not an interactive editor yet. Standalone I/i
returns a private “enter interactive insertion” result to its future caller;
it must not be mistaken for an automatic empty-line insertion. The console,
line-number verification, line/type commands and source/work file streams
remain unimplemented. The public EDDEV entry continues to report that editing
is unavailable and never opens files. No partial editor is distributed.

The following checks pass:

- `tools/test_ed_buffer.py`: 5,000 deterministic operations against an independent
  text/cursor model, memory canaries, full-gap movement, partial insertion
  overflow, invalid initialization, signed/count/case commands and insert handoff.
- `tools/qualify_ed_commands.py`: ten command sequences against the pinned stock
  ED binary on copied stock CP/M media. A final inserted marker exposes the
  oracle's cursor position; saved text and marker position match the new core.
  Evidence: `build/ed-development/commands/run-s0_lof4i`.
- Native ZSM4/LINK versus cross build: **1,649 identical bytes**. Prior invocation
  and standalone-version checks continue to pass.

The command campaign does not validate final ED file commits: the stock binary
performs the disk save, while the new implementation is checked in memory.
Next comes interactive insertion, line movement/deletion/type and streaming,
followed by full commit/recovery behavior and the remaining accepted commands.

## Line ranges and text display — 2026-10-15

The internal command core now includes L, K, T, V and -V. Forward line ranges
end after the requested LF; zero/backward ranges reach the current or prior
line starts. K removes that range and leaves the cursor at its surviving
boundary. T selects the same range but restores the cursor before output.
It reads across the gap without allocating or flattening a second text buffer.

Verification starts enabled. T prints right-aligned five-column line numbers
and the original prefix spacing at line starts. -V suppresses those prefixes.
Tabs expand to eight-column stops, other C0 characters use caret notation, and
CR/LF retain their historical behavior. T polls keyboard status at line starts;
an available key is consumed and returns the historical `#` interruption flag
without altering text or cursor. Standalone 0V currently returns a private
request for the future console caller to format the memory report; it is not
falsely treated as -V.

Updated checks pass:

- `tools/qualify_ed_commands.py`: **19** stock-ED text/cursor workflows, now
  including L/K, zero/backward ranges and whole-buffer saturation. Evidence:
  `build/ed-development/commands/run-pawmka3h`.
- `tools/qualify_ed_type.py`: **seven** stock-ED displays and cursor positions,
  including verification, signed T ranges, partial lines, tabs/control bytes
  and a final LF. Evidence: `build/ed-development/type/run-aotipcnh`.
- `tools/test_ed_lines.py`: independent output expectations plus output
  interruption, cursor preservation and the pending 0V handoff.
- Existing buffer, invocation and shared version tests continue to pass. Native
  ZSM4/LINK and cross builds now match at **2,301 bytes**.

The stock display campaign deliberately synchronizes through a separate B
command after setup. Inline Ctrl-L insertion can print intermediate asterisks;
using the first one as the final prompt queues a new key during T and causes
a legitimate interruption. This was a harness timing issue, not an ED parser
change. No sleeps or reduced interruption behavior are used to hide it.

The interactive console, insert-mode editing controls, 0V report, file streaming
and the remaining accepted commands still require implementation. EDDEV's
public entry remains an explicit development front end, with no file writes.

## Interactive insertion and console turns — 2026-10-15

`ed-input.inc` now implements interactive insertion, including CR/LF, case
translation, NUL, tab/control bytes, Ctrl-L, Ctrl-U, Ctrl-X, Ctrl-R,
backspace and rubout. Partial insertion survives buffer exhaustion, and the
error identifies the actual failing byte. `ed-console.inc` owns one console
turn: numbered prompts, buffered command entry, interactive insertion,
blank-line movement/type, errors and 0V memory reporting. Standalone E/H
return file-action requests; O/Q first require the historical Y/N response.
These requests do not perform file operations. The caller must eventually
own the streams, commits and command loop.

Qualification:

- `tools/qualify_ed_input.py`: **16** saved-text workflows match the pinned
  stock ED on stock CP/M. Evidence: `build/ed-development/input/run-6to4ayir`.
  Retype/backspace input is paced against observed output so later keystrokes
  do not spuriously interrupt the reference's internal T operation.
- `tools/test_ed_input.py`: insertion controls, boundary backspace, partial
  overflow, uppercase mode and control-byte preservation.
- `tools/test_ed_console.py`: prompts, action requests, confirmations,
  memory-report formatting, blank-line behavior and lowercase overflow
  diagnostics. Only console BDOS calls are permitted by the test stub.
- Existing invocation, buffer and line/display checks pass. Native ZSM4/LINK
  and cross builds produce **3,333 identical bytes**.

This qualifies the in-memory routines and console turns, not complete file
editing. The final buffer allocation and exact 0V capacity still depend on the
file engine. Rubout at an empty buffer and other boundary diagnostics need
broader reference coverage. Source/work-file streaming, remaining commands,
commit/recovery and the previously recorded S1/Close compatibility issue remain
open. EDDEV remains unshipped and its public entry does not open files.

## Source record stream foundation — 2026-10-15

`ed-source.inc` reads an already opened, caller-owned source FCB one record at
a time. It selects the source user and private DMA before each sequential read.
The owner remains responsible for opening/closing the stream and restoring DU
and DMA. As in DRI GETSOURCE, bytes are preserved without case conversion and
Ctrl-Z terminates text. Physical EOF also becomes sticky; later calls do not
read more records. Other BDOS statuses remain distinct errors and leave the
private record buffer empty. No automatic retry or FCB rollback is promised.

`tools/test_ed_source.py` verifies record crossings, NUL/high-bit preservation,
text/physical EOF, error propagation, a simulated subsequent successful read,
and reinitialization. This is a BDOS-stub test; live file integration is still
pending. Existing buffer, console, input and line tests pass. Native ZSM4/LINK
and cross builds match at **3,571 bytes**. This foundation is not yet connected
to A, file setup or completion, and does not create or alter files.

## Append command — 2026-10-15

A/a now connects the source reader to the gap buffer. It reads the requested
number of LF-terminated lines at the buffer's end, then restores the original
editing cursor. A final unterminated line is retained. Global U controls case
conversion, matching DRI READLINE; the command letter's case alone does not
uppercase source text. Zero count appends whole lines until at least half the
buffer is occupied. Negative nonzero counts are rejected.

Space is checked before consuming each source byte. Overflow retains inserted
bytes and leaves the cursor at the buffer end; a byte that could not fit stays
unread. Other read errors remain available in EA_ERROR and currently return
the generic command error pending integration with the file-error owner.

- `tools/qualify_ed_append.py`: six workflows match stock ED saved text and
  marker-derived cursor placement. The comparison includes unread source, which
  stock E copies through at completion. Evidence:
  `build/ed-development/append/run-th2ky023`.
- `tools/test_ed_append.py`: counts, EOF, cursor preservation, global uppercase,
  half-buffer append, rejected negative counts and overflow without byte loss.
- Native ZSM4/LINK and cross builds match at **3,763 bytes**.

The source owner must still open the FCB and initialize the stream. EDDEV's
public entry remains unchanged; work-file writing and completion are next.

## Work-file record output foundation — 2026-10-15

`ed-output.inc` accepts bytes for an already opened caller-owned work FCB,
selecting its user and private DMA for sequential writes. Finish pads only a
partial record with Ctrl-Z; empty and exact-record output add no extra record,
matching DRI FINIS's alignment rule. EW_PAD exposes the unused-byte count for
the future close owner; this does not settle the open S1 publication issue.
Repeated successful finish performs no disk I/O, and subsequent insertion is
rejected. The file owner still handles create, close, rename and final DU/DMA.

Any nonzero write status is latched with the pending record intact. Later put
or finish calls return the same error without another disk operation. There is
no automatic retry of a potentially advanced sequential FCB. In particular,
when a full record fails to flush, the next proposed byte is not accepted.

`tools/test_ed_output.py` covers 0/1/127/128/129/255/256/257/1,024 bytes,
byte preservation, padding counts, finish idempotence, sealed-stream rejection,
and statuses 1/2/255 during full-record and final-partial writes. These use a
BDOS stub; actual work-file lifecycle and live write-failure qualification
remain pending. Editing/source regressions pass, and native ZSM4/LINK matches
the cross build at **4,070 bytes**. This stage is not yet connected to W/E.

## W output command — 2026-10-15

W/w now sends counted lines from the buffer's beginning to the initialized
work-file stream and removes accepted bytes. The surviving part of the original
editing cursor is restored on success. Zero count writes whole lines until at
most half the buffer remains; negative nonzero counts are rejected. An explicit
buffer line base advances for each removed LF and is used by display/input
line numbering. Source input is unaffected.

On write failure, already accepted output stays in the output stream, the
first unaccepted byte remains in the editing buffer, and the cursor stays at
that boundary. EX_ERROR retains the raw status; the command currently reports
a generic error pending file-owner integration. A subsequent command cannot
silently retry the latched output failure.

- `tools/qualify_ed_write.py`: six stock-ED output/cursor workflows pass.
  Evidence: `build/ed-development/write/run-65m32h07`.
- `tools/test_ed_write.py`: counts, partial final lines, surviving cursor,
  half-buffer writes, line base and failure retention.
- Output, source, append, buffer, console, insertion, line and invocation tests
  pass. Native ZSM4/LINK and cross builds match at **4,283 bytes**.

The output foundation and W implementation remain development-only. File
creation, close/publication, E/H/O/Q lifecycle and the remaining commands still
need integration and live qualification before ED.COM can be distributed.
