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

## Completion data drain — 2026-10-15

`ed-finish.inc` connects the buffer, source reader and work output for the data
portion of normal completion: write all remaining editing text, copy unread
source verbatim up to EOF, then finalize the output records. Global U affects
appended source but does not translate the unread tail copied by completion,
matching DRI TERMINATE. Successful repeated drain does no further disk I/O.

If output rejects a byte already fetched from the source, that byte is retained
explicitly. Raw errors are returned and EF_DONE remains clear. This stage does
not close or rename files and must not be confused with a successful E command.

- `tools/test_ed_finish.py`: integrated streams, prior A/W, unread tail, case,
  padding, repeated finish, read errors and retained pending output bytes.
- `tools/qualify_ed_finish.py`: six workflows match stock ED's **exact exported
  output records**, including padding. Evidence:
  `build/ed-development/finish/run-hwwgsgt1`.
- Existing ED regression tests pass. Native ZSM4/LINK and cross builds match
  at **4,391 bytes**.

The comparison checks data output only: stock ED performs real file setup and
publication, while the new drain runs against simulated opened streams. File
creation, close/backup/rename, quit/restart and recovery remain unimplemented.

## File setup owner — 2026-10-15

`ed-files.inc` prepares the source and work FCBs after validated invocation.
For different DUs it checks destination collision before any mutation, then
opens or creates the source. It retains NEW/RO flags for future diagnostics.
The source's RO warning takes precedence over SYS rejection as in DRI SETUP.
It removes old backups in the source/output DUs, removes stale output $$$,
creates the work file and initializes both record streams and the data drain.
Directory operations use private DMA and explicit drive/user selection.

`tools/test_ed_files.py` checks exact simulated BDOS operation order for new
and existing sources, same-DU setup, same-drive/different-user collisions,
destination collision without mutation, RO/SYS handling and source/work create
failures. Native ZSM4/LINK and cross builds match at **4,805 bytes**; existing
editing/stream tests pass. These are simulated-directory checks, not yet live
file-lifecycle qualification. The public EDDEV entry remains unchanged.

Setup returns diagnostic categories and raw status to its future command-loop
owner. It does not yet print those diagnostics, close/publish output, clean up
on quit/restart, or restore the required exit DU. Those operations and their
failure behavior remain pending, along with the S1/Close compatibility audit.

## Close and publication primitives — 2026-10-15

`ed-publish.inc` now closes finalized work output, renames the source to BAK
in its source DU, then renames $$$ to the original filename in the output DU.
Both names in each rename FCB carry an explicit drive. A live split-drive
BetterCP/M run failed its final rename with an implicit new-name drive; explicit
binding passes on both systems and avoids relying on that default resolution.

The reserved S1 byte is zeroed before Close. The unused padding count remains
in EW_PAD rather than being published as ISIS-II metadata. This produces stock
CP/M's record-aligned exported output under BetterCP/M without changing BDOS.
The general BDOS treatment of reserved S1 remains a separate validation issue.

The primitive records completed phases and refuses repeated publication after
an attempt. On a failed close or rename it returns the raw status without
attempting rollback or continuing to the next mutation. This is an internal
boundary, not yet the final user-visible recovery policy; stock DRI source
does not inspect rename return statuses, so failure compatibility still needs
explicit qualification before the lifecycle owner is finalized.

- `tools/test_ed_publish.py`: exact close/rename order, source/output DU binding,
  S1 normalization, pre-finalization rejection, repeated-attempt rejection and
  file preservation at each injected failure boundary.
- `tools/qualify_ed_lifecycle.py`: a test-only editor loop runs real new,
  existing and split-drive setup/save/publication on stock CP/M and BetterCP/M.
  It verifies exact output records and original backup text. Evidence:
  `build/ed-development/lifecycle/run-iaqj1itj` (stock),
  `build/ed-development/lifecycle/run-6tc8nlvk` (BetterCP/M).
  BetterCP/M invocation requires `--better --diskdefs PATH`.
- ED regressions pass; native ZSM4/LINK and cross builds match at **5,053 bytes**.

EDTEST.COM is generated only inside the isolated qualification directory. It
is not ED.COM and does not establish final diagnostics, exit DU, quit/restart,
recovery, protected-source behavior or Model 4 qualification. The public
development entry and System Disk planned status remain unchanged.

## Authorized lifecycle actions — 2026-10-15

`ed-lifecycle.inc` now consumes authorized E/H/O/Q requests from the console.
E drains and publishes output, then selects the output DU for its caller.
H drains/publishes, swaps the complete source/output DUs, reopens and resets
the text buffer. O reopens the original source/output pair without publishing
the abandoned edit. H/O preserve global U and verification mode. Q deletes
the current work file and selects the captured caller DU. O/Q authorization
remains in EU_READ; no extra prompt is introduced by the lifecycle routines.

The live campaign now covers eight cases: new/existing/split saves, existing
and new-file Q, O, H, and split-DU H. The file-state and output expectations
pass against pinned DRI ED on stock CP/M and the new test loop on stock CP/M
and BetterCP/M. U/-V before O/H and lowercase insertion after restarting check
that modes survive. Evidence:

- `build/ed-development/lifecycle/run-rs2o2o6h` (DRI oracle);
- `build/ed-development/lifecycle/run-9u9ew32i` (BetterCP/M);
- `build/ed-development/lifecycle/run-zp340gus` (new code on stock CP/M,
  preceding the added mode-preservation assertion).

Use `tools/qualify_ed_lifecycle.py --oracle` for pinned DRI comparison or
`--better --diskdefs PATH` for BetterCP/M. ED regressions pass; native and cross
builds match at **5,184 bytes**.

These routines select exit DU but do not implement final platform warm-return
mechanics: the stock-CP/M test loop returns to A after split E, while DRI ED
updates its saved CCP drive and returns to B. This remains an explicit open
integration item. Error diagnostics/recovery policy, protected-source cases,
full user-area lifecycle qualification and Model 4 testing remain pending.

## Exit-location integration — 2026-10-15

The lifecycle exit helper now selects the intended full BDOS DU, restores DMA
to 0080H, and updates the legacy packed CCP boot byte at 0004H. Stock CP/M
uses that byte on warm return; its user nibble represents 0..15. BetterCP/M's
full 0..31 user selection is passed separately through BDOS 32 and is not
truncated to the legacy nibble. E targets output DU; Q targets captured caller
DU. The caller still performs the actual jump to warm boot.

This closes the previously recorded stock test-loop split-E exit difference:
the new code now returns to B, as does the DRI oracle. The eight-case live
lifecycle campaign passes on both stock CP/M and BetterCP/M, including mode
preservation and split-DU H. Evidence:
`build/ed-development/lifecycle/run-gq_gj2ua` (stock),
`build/ed-development/lifecycle/run-bmyjikrr` (BetterCP/M).

`tools/test_ed_exit.py` checks all 512 drive/user combinations, full BDOS user
selection, packed-byte encoding and DMA restoration. ED regressions pass;
native ZSM4/LINK and cross builds match at **5,225 bytes**. Live nonzero-user
and Model 4 return paths, failure exits and final recovery diagnostics remain
to be qualified. The production entry is still the unshipped development
front end; these checks exercise the isolated test-only loop.

## Setup diagnostics and save-stream recovery — 2026-10-15

`ed-recovery.inc` supplies the established NEW FILE and read-only notices,
destination-collision and system-source diagnostics, and DRI's DISK OR
DIRECTORY FULL path. The storage-error path attempts Close on the work FCB,
even if Close itself fails, then selects caller DU and restores DMA for exit.
It does not delete the recovery work file or rename anything. Setup wrappers
and save-stream errors use this path; authorized O/H restarts print any new
setup notices without resetting editing modes.

Publication errors remain raw errors for later policy qualification. FQ_STAGE
distinguishes stream, publication and reopen/setup failures so a rename failure
cannot be silently classified as a confirmed DRI stream-error case.

- `tools/test_ed_recovery.py` checks exact message text, NEW/RO notices, no
  close on collision/system rejection, attempted close on disk error even when
  it returns failure, and caller DU/DMA preparation without destructive cleanup.
- The diagnostic-wrapped test loop passes all eight live lifecycle cases on
  BetterCP/M (`build/ed-development/lifecycle/run-fzcch5_u`) and stock CP/M
  (`build/ed-development/lifecycle/run-xabej4af`).
- ED regressions pass; native and cross builds match at **5,496 bytes**.

This is not complete error-path qualification. Ordinary A/W stream errors
still need routing from the console dispatcher into the storage-error owner;
disk-full/read-error behavior needs live fault injection, and rename failures
and protected-source completion still need DRI-oracle comparison. EDDEV is
unchanged as a public development front end and remains unshipped.

## Ordinary A/W stream-error routing — 2026-10-15

The command core now records a distinct raw stream-error status for A/W.
EU_READ routes those failures to the recovery owner rather than printing
BREAK and continuing. It returns carry/A=1 after the diagnostic, recovery-close
attempt and caller DU/DMA preparation; its owner must warm-return. A new command
clears the status so an unrelated command error cannot inherit it. Append also
clears its per-operation error at entry. Buffer exhaustion remains an ordinary
command error, not a disk failure.

- `tools/test_ed_stream_recovery.py`: console A/W failures, failed recovery
  close, retained unaccepted buffer text, exact diagnostic without BREAK, no
  destructive cleanup, and command-error-state reset.
- `tools/qualify_ed_faults.py --diskdefs PATH`: a test-only BDOS shim injects
  status 2 on A's source read or W's second record write while other calls use
  real BetterCP/M. The original source is preserved. Read failure leaves an
  empty recovery file; second-record write failure leaves the successfully
  written first 128 bytes in $$$, with no BAK publication. Evidence:
  `build/ed-development/faults/run-l75msol3`.

The injection establishes handling of returned error statuses, not physical
media failure or actual disk exhaustion. The shim exists only in isolated
EDTEST.COM, restores the BDOS vector before warm return, and is absent from
the development core. The ordinary live lifecycle and ED regressions pass;
native ZSM4/LINK and cross builds match at **5,517 bytes**. Protected-source,
rename-failure, real-capacity and Model 4 qualification remain open.

## Protected-source baseline and read-only save — 2026-10-15

`tools/qualify_ed_protected.py` now checks RO, SYS and RO+SYS against pinned
DRI ED. SYS-only rejects entry without removing the older BAK. RO and RO+SYS
display the read-only warning, permit editing, and Q preserves the original
while removing the work file; the older BAK is removed during setup. These
states also pass on the new BetterCP/M test loop. Evidence:
`build/ed-development/protected/run-xywzsskd` (oracle),
`build/ed-development/protected/run-e4h84yu9` (BetterCP/M).

The additional `--save-readonly` case establishes DRI's save failure: close
edited output, stop before source backup/publication with Bdos Err On A: File
R/O, accept a key and warm-return, leaving original and edited $$$ intact.
The new owner detects source RO after work close and reproduces that behavior
without letting a host BDOS reboot bypass its DU/DMA exit handling. No
attribute is cleared, no override is offered and no rename is attempted.
Non-RO publication failures remain outside this special case.

The save test verifies the complete recoverable edited text as well as source,
backup/temp states and diagnostic/acknowledgment. Evidence:
`build/ed-development/protected/run-8ni8p7c2` (oracle),
`build/ed-development/protected/run-1yvydjyj` (BetterCP/M).
The new stock-CP/M loop also passes this RO-save scenario. Publication and
recovery unit checks cover close-only preservation, one acknowledgment, no
destructive cleanup and unchanged handling of unrelated rename failures.
Normal live lifecycle and ED regressions pass; native and cross builds match
at **5,615 bytes**.

Protected split-DU saves, RO+SYS completion, attribute changes during editing,
other rename failures, actual disk exhaustion and Model 4 behavior remain
qualification work. This does not mark ED.COM complete or distributable.

## Expanded protection and live DU isolation — 2026-10-15

The protected campaign now accepts `--split`, `--readonly-system`, and
BetterCP/M-only `--users` (source A7, output user 19). Stock DRI ED passes
split-drive RO-save and RO+SYS-save recovery expectations. The new loop passes
the combined RO+SYS source in A7 with recovery output in B19 and caller-DU
return. Evidence:

- `build/ed-development/protected/run-s5nvmhlb` (oracle split RO save);
- `build/ed-development/protected/run-sa8954gy` (oracle RO+SYS save);
- `build/ed-development/protected/run-usayjfqp` (BetterCP/M A7/B19 RO+SYS).

`tools/qualify_ed_du.py --diskdefs PATH` adds four live unprotected cases:
A7 to A19 on the same drive, A7 to B19, split-DU H followed by another save,
and Q returning to caller A0. It checks output/backup contents, actual exit
prompts and preservation of same-named user-zero sentinel files on both
drives. Evidence: `build/ed-development/du/run-d5sh0i5a`. Missing-file checks
remove the prior extraction first and require a newly created result, since
cpmcp can return success for an unmatched pattern.

These qualification additions required no production-code changes. The prior
**5,615-byte** native/cross result still applies. Dynamic attribute changes,
other publication failures, actual disk exhaustion and Model 4 qualification
remain open; broader ED commands are still unimplemented.

## Literal F search — 2026-10-15

`ed-find.inc` now implements counted F/f searches in the current buffer.
Uppercase F uppercases the collected pattern; lowercase f follows global U.
Text itself is compared literally. Ctrl-Z or CR terminates the string; Ctrl-L
adds CR/LF, NUL is rejected, and the historical scratch threshold allows 99
bytes before overflow. Zero count collects without searching; negative
nonzero count is rejected.

Search scans only the suffix after the editing cursor. A successful match
moves the cursor through its final byte; repeated matches do not overlap.
A failed attempt leaves the cursor unchanged, retaining any earlier counted
matches. Misses return #, with the terminating command character retained for
the historical BREAK diagnostic. No regex, wildcard or source autoscan is
introduced by F.

- `tools/qualify_ed_find.py`: **13** pinned stock-ED workflows match text and
  marker-derived cursor position, including count failure, case, empty pattern,
  mid-buffer starts, subsequent commands and CR/LF patterns. Evidence:
  `build/ed-development/find/run-2stdqac_`.
- `tools/test_ed_find.py`: independent cursor/flag expectations, separators,
  NUL and exact scratch overflow boundaries, including expanded Ctrl-L.
- Console checks include the failed-search BREAK diagnostic. Existing ED
  regressions pass; native ZSM4/LINK and cross builds match at **5,958 bytes**.

N autoscan, S substitution, J juxtaposition and M macros remain unimplemented.
The search primitive is internal to the unshipped development editor.

## S substitution — 2026-10-15

`ed-substitute.inc` now uses the shared collector and literal search for S/s.
Pattern and replacement occupy the same scratch area with a combined 99-byte
usable limit. Case translation applies to both strings according to command
case/global U, with the same Ctrl-Z/CR terminators and Ctrl-L expansion as F.
Each match is removed and its replacement inserted; the cursor ends after the
replacement. Empty replacement deletes, and empty pattern follows the DRI
insertion behavior while there is suffix text to search.

Repeated substitutions retain prior successful changes on a later miss.
Overflow likewise retains the matched-text removal and replacement bytes that
fitted, matching the source's nontransactional editing model. Zero count only
collects the strings; negative nonzero count is rejected.

- `tools/qualify_ed_substitute.py`: **13** stock-ED text/cursor comparisons pass,
  including count failure, deletion, case, empty pattern, subsequent commands,
  CR/LF and combined scratch boundaries. Evidence:
  `build/ed-development/substitute/run-ggomvs1f`.
- `tools/test_ed_substitute.py`: independent results, partial overflow, NUL and
  scratch limits. The shared-collector refactor also passes all 13 F oracle
  cases (`build/ed-development/find/run-9fdshyr5`).
- ED regressions pass; native ZSM4/LINK and cross builds match at **6,092 bytes**.

N autoscan, J juxtaposition, M macros and auxiliary-file commands remain
pending. The public EDDEV entry remains an unshipped development front end.

## J juxtaposition and counted-command compatibility — 2026-10-15

`ed-juxtapose.inc` collects first-match, inserted-middle and end-match strings
in the shared bounded scratch region. A single J preserves both matched
delimiters, inserts the middle text and deletes the interval before the end
delimiter. Missing first match leaves text unchanged; missing end match retains
the inserted middle and cursor. Partial overflow retains bytes that fitted.

Oracle work exposed DRI's retained DIRECTION/FIRST state in counted J. Later
FIND calls can leave the cursor at a prior boundary, and subsequent pointer
restoration duplicates characters. The implementation preserves this through
explicit reverse-search movement state and an unsigned logical FIRST offset.
This is deliberately documented in source comments, the accepted engineering
spec and the user guide. It is not a new generalized search mode. A subsequent
F/S/J command resets its state through the shared collector initialization.

- `tools/qualify_ed_juxtapose.py`: **13** stock-ED text/cursor comparisons pass,
  including 2J/3J, both missing-match paths, empty strings, case, CR/LF and
  commands following J. Evidence:
  `build/ed-development/juxtapose/run-i6gmzysg`.
- `tools/test_ed_juxtapose.py`: independent normal/count-quirk expectations,
  scratch limit, rejected negative count and partial overflow.
- Shared F/S oracle suites still pass all 13 cases each. ED regressions pass;
  native ZSM4/LINK and cross builds match at **6,327 bytes**.

N autoscan, M macros, auxiliary-file commands and other previously listed
release integration/qualification work remain pending.

## N autoscan — 2026-10-15

`ed-autoscan.inc` now searches the current suffix with the shared collector
and literal matcher. On a miss it checks for interruption, writes the whole
editing buffer to work output, appends whole source lines until at least half
the buffer is occupied, returns to its beginning and searches again. Counted
searches preserve prior matches and output. Empty refill at EOF returns #.
Zero count only collects the string; negative nonzero count is rejected.

The implementation follows DRI's whole-batch algorithm: no overlap is retained
between a written batch and the next refill. It does not promise an arbitrary
streaming match across those boundaries. Source conversion follows global U;
pattern conversion follows N/n plus U. Stream failures set the shared raw I/O
status and use the console's existing fatal recovery route.

- `tools/qualify_ed_autoscan.py`: **eight** stock-ED output/cursor comparisons
  pass, including counted/missing matches, case, zero count and a command after
  N. The bounded new buffer performs multiple refills over the 1,500-byte
  prefix. Evidence: `build/ed-development/autoscan/run-x7nqeplj`.
- `tools/test_ed_autoscan.py`: multi-batch scanning, lossless completion,
  EOF/count handling, global case, read/write errors, interruption before
  mutation and the no-overlap boundary behavior. The emulator helper accepts
  an explicit larger instruction budget for these larger stream workflows;
  its existing default and other test limits are unchanged.
- ED regressions pass; native ZSM4/LINK and cross builds match at **6,443 bytes**.

M macros, R/X auxiliary-file handling, page/delay and remaining numeric-return
forms, final memory allocation/entry and prior release qualification items
remain pending. EDDEV is still unshipped.

## M macro command stream — 2026-10-15

`ed-macro.inc` captures the remainder of the command line, retaining Ctrl-Z
string separators. M uppercases the definition; m follows global U. Counts
0/1/omitted repeat until a command fails or a key interrupts. A larger count
executes that many iterations and ends with the historical # break. Empty
definition does nothing, negative nonzero counts and nested M are rejected.

Macro input is a continuous byte stream, not repeated isolated EC_RUN calls.
An unterminated insertion/search string can therefore read through an iteration
boundary. READC-equivalent polling occurs before each macro byte. A terminal
macro count or interruption restores the saved command-run stack frame, even
from inside a collector; ordinary failures also clear macro-active state before
return. Existing edits remain applied. The next console command cannot inherit
the old macro stream.

- `tools/qualify_ed_macro.py`: **13** stock-ED text/cursor comparisons pass,
  including finite/unbounded counts, command-definition case, continuous
  insertion, repeated substitution/find and nested-macro rejection. Evidence:
  `build/ed-development/macro/run-pxj93tmx`.
- `tools/test_ed_macro.py`: independent expected text/flags, empty definition,
  keyboard interruption and subsequent-command/stack cleanup.
- ED regressions and live lifecycle checks pass; native ZSM4/LINK and cross
  builds match at **6,835 bytes**.

Macro support does not implement commands still missing elsewhere (notably
R/X auxiliary files and page/delay/remaining return forms). Final memory and
production-entry integration plus earlier qualification gaps remain pending.

## Named R library input — 2026-10-15

`ed-library.inc` now reads an exact library file into the editing cursor using
an independent FCB and record buffer. R uppercases input; r follows global U.
Ctrl-Z terminates file text, while NUL and other data bytes are retained.
Numeric prefixes are rejected. Missing Open returns the historical O break;
nonzero library sequential-read statuses end input as in DRI READFILE rather
than using the primary-source fatal-read policy. Buffer exhaustion retains
inserted bytes and returns >.

Unqualified names use the current source DU. Qualified operands inherit missing
components from the captured caller, preserving the user guide's user-only
drive rule. Omitted extension means LIB; explicit extensions are preserved. A temporary
save/restore protects the main EI_FCB while the shared bounded filename parser
constructs the independent library FCB. No caller or primary source DU is
recaptured or changed. Bare R can read an existing X$$$$$$$.LIB; integration
with an active X transfer's pending bytes remains part of the X implementation.

- `tools/qualify_ed_library.py`: **eight** stock-ED text/cursor comparisons pass
  for historical basename/LIB, case, missing file, numeric-prefix rejection,
  following commands and pre-existing transfer-library input. Evidence:
  `build/ed-development/library/run-l6nlkcd3`.
- `tools/test_ed_library.py`: default/source-DU inheritance, B19 and user-only
  forms, explicit extension, main-filespec preservation, multiple records,
  controls, invalid selectors, overflow and nonzero-read termination.
- The live DU campaign now includes rB19:header.lib, r19:header.lib and rdefault
  in one A7-to-B19 save. It verifies insertion from B19, A19 and A7, ignoring
  a conflicting caller-user library and preserving the main backup/output.
  Evidence: `build/ed-development/du/run-g14syy_f`.
- ED regressions pass; native ZSM4/LINK and cross builds match at **7,434 bytes**.

X transfer output/pending-tail and lifetime handling, extended R diagnostic
boundaries, remaining page/delay/return forms and release integration remain
pending. EDDEV is still not distributed.

## X transfer foundation and bare-R tail — 2026-10-15

`ed-transfer.inc` now copies forward line ranges without moving the editing
cursor, appending to X$$$$$$$.LIB in the source DU. It creates the transfer on
first use; zero X clears it and resets pending bytes. Full 128-byte records
are deferred until the next byte arrives, as in DRI PUTXFER. Write/create
errors set the shared I/O status for fatal recovery. Transfer cleanup is
called during normal/fatal exit preparation.

Bare R closes an active transfer FCB, reads its disk records, then inserts its
pending bytes. The pending tail is copied verbatim: unlike READFILE's disk
bytes, it is not case-translated by uppercase R. This historical record-boundary
quirk is retained in code comments and tests. The shared nonmoving range
selector was factored from T; seven stock T display comparisons still pass.

- `tools/qualify_ed_transfer.py`: **11** stock-ED text/cursor workflows pass,
  including append/clear, repeated R, nonmoving ranges and disk/pending-tail
  case behavior. Evidence: `build/ed-development/transfer/run-ubnnqqy6`.
- `tools/test_ed_transfer.py`: deferred writes, raw controls in pending bytes,
  cleanup, write failure and preserved editing cursor/text.
- The live DU campaign includes X/R followed by an A7-to-B19 save and verifies
  transfer cleanup in A7. ED regressions pass; native/cross builds match at
  **8,050 bytes**.

Transfer lifetime across O/H, especially a split-DU H that changes the source
location, still requires an oracle campaign. The current active transfer keeps
its creation-DU binding; DRI's source-disk selection during subsequent transfer
operations must be audited before freezing that behavior. Existing-file and
protection/error cases also remain. This is an internal foundation, not a claim
that X's full lifecycle or ED.COM is complete.

## Transfer restart fix and numeric Enter — 2026-10-15

The pinned DRI transfer-lifetime campaign reproduced split-drive failures
twice with identical file snapshots: O inserted corrupted pending bytes and
left an orphan source-drive transfer file; H made bare R miss the transfer.
Same-DU O/H preserved data. Evidence:
`build/ed-development/transfer-lifetime/run-kq0fu2ha`, repeated at
`run-a8jhkf5f`. `tools/fixtures/ed-transfer-lifetime-dri.json` records those
observations against the already pinned ED binary and stock disk hashes.

The user approved fixing these bugs and documenting the exception. Existing
independent transfer storage and creation-DU binding provide the safe behavior:
O/H retain the file and pending bytes, bare R uses that binding, and exit
cleanup targets the bound DU. Zero X clears the active transfer before a later
new X binds to the current source. Source comments, the accepted spec and user
guide now state this deliberate exception to bug-for-bug DRI compatibility.

`tools/fixtures/ed-transfer-lifetime-safe.json` gives explicit noncorrupt output
and cleanup expectations for BetterCP/M. The same four-case campaign passes
the safe expectations on stock CP/M (`run-5d40uhxn`) and BetterCP/M
(`run-haqci0a2`). Oracle mode continues to compare the original failing states;
it does not overwrite or normalize them to the approved behavior.

Numeric Enter is also implemented. A first-command count/sign followed by CR
moves the corresponding line range and types one forward line. Blank Enter
uses the same path. CR after an earlier command does not become an additional
movement/type operation; macro stream handling remains separate.

- `tools/test_ed_return.py`: signed/count/zero/blank Enter and ignored trailing
  CR, with independent output/cursor expectations.
- `tools/qualify_ed_return.py`: **nine** stock-ED cursor/text workflows pass.
  Evidence: `build/ed-development/return/run-bvwxcm9_`.
- ED regressions pass; native ZSM4/LINK and cross builds match at **8,103 bytes**.

P paging, Z timing, extended transfer/error cases, final memory/entry and
previously listed release qualification remain pending.

## P paging and Z delay — 2026-10-15

P now moves by 23 lines in its requested direction, types 23 forward lines,
and waits after each page. Zero P types from the cursor without movement or
wait. Counted paging stops at the first/end range as in DRI PAGE. The shared
display counter now advances when a line prefix is visited, preserving DRI's
partial-line numbering behavior: a display beginning mid-line does not advance
its first later visible prefix as though it had printed the preceding one.

Z implements positive counted waits, zero-count key acknowledgment, Ctrl-Z
break and keyboard interruption. WAIT polls twenty times around TIME(250).
The pinned ED TIME routine at 1A11H uses a 12-count inner loop; the new delay
loop has identical instruction bytes apart from relocated jump addresses.
This is a CPU-timed nominal half-second unit around 2 MHz, not a wall-clock
guarantee on accelerated emulators or different CPU clocks. No clock RSX or
new BIOS/BDOS service is required.

The original FLAG variable is declared but not initialized before the first
WAIT/0Z interruption. The oracle printed AFH in this campaign. BetterCP/M
initializes its break flag to zero and thereafter retains the prior assigned
flag; it does not expose stale TPA contents. Delay qualification records both
observed flags rather than treating an uninitialized byte as a required UI.

- `tools/qualify_ed_page.py`: **11** stock-ED output/cursor cases pass, including
  current, forward/backward/count/edge pages and partial-line display.
  Evidence: `build/ed-development/page/run-7vmqjxjx`.
- `tools/qualify_ed_delay.py`: **seven** count/key/interruption/macro outcomes
  pass, with the initial undefined-flag distinction recorded explicitly.
  Evidence: `build/ed-development/delay/run-w0lmrk7z`.
- `tools/test_ed_page_delay.py`: independent page results, polling/key counts,
  negative rejection, preserved break flags and relocated delay-loop parity.
- Existing seven T oracle displays and ED regressions pass; live lifecycle
  remains qualified. Native/cross builds match at **8,358 bytes**.

All planned command groups now have initial implementations. This does not
mean ED.COM is complete: final memory allocation and production entry,
command-composition/boundary audit, remaining file/protection/failure cases,
Model 4 qualification and distribution integration remain required.


## Real editor entry and memory allocation

The development executable now enters the editor instead of printing a placeholder.
After standalone `/VER` handling and complete operand validation, ED uses the
current BDOS gateway address at 0006H as its exclusive text-buffer ceiling.
This respects a lowered gateway for loaded resident extensions. The buffer begins
at ED_STACK, immediately above the program's private downward-growing stack;
source, work and transfer record buffers are already part of the program image.
At least 1,024 text bytes must remain. Otherwise `NO MEMORY` is printed before
any source/work file is opened, created, deleted or renamed.

This allocation differs internally from DRI's separate dynamically sized disk
buffers. `0V` reports actual free/total text-buffer bytes; equal byte capacity to
DRI ED is not claimed. Existing bounded insertion/append overflow rules remain.
The 128-byte private stack is excluded from the text buffer.

- `tools/test_ed_entry.py`: below-base, empty, below-minimum, exact-minimum and
  multiple lowered ceilings; first/last byte guards; insufficient-memory and
  invalid-selector exits before any mutating BDOS call.
- `tools/test_ed_invocation.py`: standalone `/VER` remains a pure print/exit.
- `tools/qualify_ed_lifecycle.py --real-entry`: eight complete create/save,
  Q/O/H and split-DU sessions through the actual startup, rather than replacing
  it with the earlier fixed-address test loop. Stock CP/M evidence:
  `build/ed-development/lifecycle/run-u1t83ami`.

The earlier fixed-buffer fixtures remain available for repeatable command and
fault tests. This stage does not enable distribution installation. Command
composition, unresolved publication failures, remaining protection/boundary
cases, Model 4 qualification and distribution integration remain outstanding.

BetterCP/M real-entry evidence: `build/ed-development/lifecycle/run-yzbvar7x`.
Native ZSM4/LINK and cross assembly match at **8,373 bytes**. All existing
module regressions pass after entry integration.


## Composable memory reports

The initial `0V` implementation returned a private event to the console layer,
which discarded the remainder of the command line. DRI ED's V branch prints
its report and continues dispatch. ED now calls the same report formatter from
the command interpreter and continues normally, including inside an M macro.
The formatter remains shared; no new command syntax is introduced.

Five pinned-stock-ED comparisons cover `0V2C`, repeated reports and movement,
a counted macro containing a report, editing after a report and a later invalid
command. They compare saved text and cursor placement; absolute memory totals
remain allocation-dependent. `tools/qualify_ed_composition.py` records results.
Line/console tests also verify report bytes and subsequent operations. Entry,
invocation, macro and paging/delay regressions pass. Native/cross builds match
at **8,368 bytes**, five fewer than the preceding stage.


## Absolute line references and broader composition audit

The command parser had omitted DRI's numeric trailing colon (`n:`) and leading
colon (`:n` command range) forms. Both now use the existing global line state,
including EB_BASE after W, to derive relative direction/distance. Equal-line
references retain backward/zero semantics; forward leading-colon ranges include
the target line. Existing line movement/range primitives handle buffer edges.
No source reread or new disk access is introduced.

- Sixteen pinned-DRI composition cases pass, covering memory reports, absolute
  forward/backward/equal/out-of-range references, deletion, following commands
  and macros: `build/ed-development/composition/run-gv32qhjr`.
- Ten pinned-DRI T display/cursor cases pass, including leading-colon forward,
  backward and partial-current-line ranges:
  `build/ed-development/type/run-y4cen3qt`.
- Independent line tests verify global references with EB_BASE set to 10,
  representing text already written out of the buffer.

The oracle fixture now separates insertion from the tested command with a B
prompt barrier, preventing queued test input from interrupting macro/display
keyboard polls. This is test pacing, not an editor behavior change.

All 25 ED module regression scripts pass after the parser changes. Native
ZSM4/LINK and cross assembly match at **8,510 bytes**. Final publication-error,
platform and distribution qualification remain outstanding.


## Failed final work close

The lifecycle owner previously returned a raw publication error when the first
work-file close failed. The real entry then exited without the expected
recovery diagnostic or caller-DU/DMA cleanup. DRI ED.PLM FINIS explicitly checks
CLOSE for FFH and calls FERR, which attempts CLOSE again before reporting
`DISK OR DIRECTORY FULL` and rebooting. ED now routes FP_STEP=0 failures through
that existing recovery path. RO handling and later rename failures remain
separate; this change does not add rollback or repeat the rename sequence.

`tools/test_ed_recovery.py` checks the recovery close, diagnostic, captured
status and caller-DU/DMA restoration, with no delete/rename calls. The live
fault campaign now injects a one-shot FFH final-close failure on a copied
BetterCP/M disk. The recovery close succeeds: original text remains unchanged,
complete edited output remains under CASE.$$$ with ordinary record padding,
and no CASE.BAK is created. Existing read/second-record write fault cases pass.
Evidence: `build/ed-development/faults/run-cbna38p7`.

This is an injected BDOS-status test, not a claim that real disk-full and media
failures are fully qualified. Later rename failure policy remains outstanding.

Ordinary real-entry E/Q/O/H and split-DU sessions still pass on BetterCP/M:
`build/ed-development/lifecycle/run-6o3alfd3`. Native/cross builds match at
**8,521 bytes**.


## Rename return-code audit

DRI ED.PLM FINIS checks CLOSE but calls both RENAME operations without checking
return status. `tools/qualify_ed_rename.py` repeats both fault boundaries in the
pinned official binary and the real BetterCP/M development entry on stock CP/M.
The test gate occupies a reserved area above the lowered TPA ceiling, injects
FFH on one selected rename, and restores the BDOS/warmboot vectors on exit.
A no-fault control verifies byte-identical normal saved output in both editors.

| Editor / failure | Directory entries after E |
| --- | --- |
| Either / no failure | Original text in CASE.BAK; edited text in CASE.TXT |
| DRI / original-to-BAK fails | Two CASE.TXT entries: original and edited text |
| BetterCP/M / original-to-BAK fails | Original CASE.TXT and edited CASE.$$$ |
| Either / work-to-original fails | Original CASE.BAK and edited CASE.$$$ |

All six cases assert exact record bytes and directory-entry counts. Duplicate
names are extracted from disposable image copies after giving each entry a
unique name; cpmtools handles sector skew. The evidence images are unchanged.
This decoder is restricted to the one-extent IBM 3740 test fixture.
Evidence: `build/ed-development/rename/run-t3719e2a`.

BetterCP/M's existing primitive already stops at the first failed rename and
never blindly repeats the sequence. At the audit stage its lifecycle owner returned that status without a dedicated
diagnostic. The user subsequently approved the safe exit and established that
compatibility does not require reproducing confirmed DRI bugs; the correction
below supersedes the earlier pending policy.


## Model 4 initial lifecycle qualification

`tools/test_model4_ed.py` launches trs80gp through the established macOS
application wrapper and types real keyboard-matrix events. It uses private
system/data DMKs and the actual EDDEV entry, not the fixed-buffer test loop.
Four cases pass: standalone /VER, B7 save, confirmed Q discard and H save/restart
followed by a second edit/save. The completion marker is checked on screen;
physical data media are then decoded to verify exact logical text, BAK state,
absence of stale work output and preservation of a same-named user-0 sentinel.
The /VER case leaves the data DMK byte-for-byte unchanged.

Evidence: `build/ed-development/model4-entry-01/evidence.json`, with per-case
invocations, captures and copied disks. This qualifies basic Model 4 lifecycle,
not every command, protection condition or real media-full failure. Rename
policy and remaining failure/release integration work are still outstanding.


## Approved DRI defect corrections

The lifecycle owner now reports `Rename failed. Edited text retained in work
file.` on either failed rename and restores the captured caller DU/DMA before
exiting. It does not close again, rename again, roll back, or delete source,
backup or work output. Known RO errors retain their specific handling. Unit
tests cover both phases, retained status and a caller in user 31. The live
six-case fixture verifies the diagnostic only in BetterCP/M fault cases and
asserts every original/edited record remains recoverable under distinct names.
Evidence: `build/ed-development/rename/run-qn3010zs`.

The same policy supersedes the earlier decision to preserve DRI's counted-J
state bug. Each J iteration now resets forward search state. Two iterations on
`A old B A more B` produce `AXB AXB`; a requested third iteration fails with #
while retaining both completed edits. An independent test verifies equivalence
to two separate J operations. Thirteen oracle workflows qualify: eleven still
match DRI, while two explicitly assert the pinned DRI defective result and the
corrected BetterCP/M result. The oracle expectations were not erased.
Evidence: `build/ed-development/juxtapose/run-yqc5mjs_`.

Both corrections are documented in source comments, the engineering contract
and the user guide. Engineering policy 203 records the general requirement to
correct confirmed DRI defects while retaining independent evidence. Earlier
chronological entries describing deliberate J preservation are superseded.

All 25 ED module regressions pass with these corrections. Native ZSM4/LINK
and cross assembly match at **8,584 bytes**. The earlier Model 4 lifecycle
evidence predates these two fixes; exact release-artifact platform and real
media-full qualification remain part of the unfinished release checks.


## Actual disk and directory capacity exhaustion

`tools/qualify_ed_capacity.py` uses the unmodified EDDEV entry on private
BetterCP/M cpmsim disks. Unlike the earlier fault gate, these cases fill the
real CP/M directory or allocation map. Source text is in B7, the captured caller
is A0, and no backup exists before the test.

- All 64 directory entries occupied: work creation fails, the original remains,
  no work/backup appears, and the complete data image remains byte-identical.
- No data blocks free: work creation succeeds but saving cannot write its first
  record. The original remains and the empty work file is retained.
- One 2K block free: save writes exactly 2,048 bytes, then exhausts the disk.
  The complete original remains; the closed work file contains precisely the
  written prefix, with no invented completion or padding.

Each case reports `DISK OR DIRECTORY FULL` once, exits to A0, and creates no
BAK or published replacement. Host-side probes establish exhaustion before ED
runs; directory-full and allocation-full fixtures are distinguished explicitly.
Evidence: `build/ed-development/capacity/run-9zucsoip`.

The final capacity repeat additionally compares every original file record,
including padding: `build/ed-development/capacity/run-wzc0zmrm`. The expanded
rename campaign passes eight control/fault cases, including both H failure
phases exiting without a restart: `build/ed-development/rename/run-6nfscp3l`.
No editor bytes changed in this qualification stage; ED remains 8,584 bytes.
