# TED.COM Adoption and WordStar Editing Engineering Specification

Status: adopted implementation direction, 2026-10-25; detailed behavioral
contract proposed for implementation review. TED is the selected Utilities
Disk full-screen editor. No implementation, platform qualification or release
acceptance is claimed by this specification. New behavioral choices below are
explicit requirements for the adaptation, not claims about unmodified TED.

## 1. Purpose, scope and authority

Adopt Hector Peraza's Z80 TED as a source-maintained adaptation providing
WordStar-compatible non-document editing and file commands, recoverable file
publication, correct transient-memory ownership and preservation of source
text on BetterCP/M. Qualify the same portable editor on z80pack/cpmsim and
trs80gp/TRS-80 Model 4, with physical Model 4 hardware a separately reported
qualification scope.

This is an adaptation, not a clean-room replacement or a claim of complete
WordStar compatibility. Retain TED's disk-backed document engine where it
satisfies this contract. Correct or replace upstream behavior where it does
not. Do not reproduce confirmed data-loss defects for historical fidelity.

The [distribution manifest](../releases/DISTRIBUTION-MANIFEST.md) determines
membership; this document determines editor behavior. The
[shared input specification](Shared%20Input%20and%20UI%20Specification.md)
governs ordinary filename/search fields and choices where applicable. Its
single-line editing profile does not replace this document's editing engine
or WordStar command language. Existing ED.COM and the CCP retain their own
contracts. No BIOS/BDOS ABI, permanent resident allocation, extension ABI or
system-wide key-binding change is authorized by this adaptation.

### 1.1 Initial release scope

- One document at a time, with a disk-backed workspace and character blocks.
- Source/non-document editing; no automatic word wrap or paragraph formatting.
- The movement, editing, search, block and file commands in section 3.
- 80-column, 24-row operation on both platforms, using explicit terminal
  personality/backend dependencies. Larger host windows may contain this fixed
  logical viewport; they do not increase document limits implicitly.
- Simple exact DU-qualified file access, standard /VER and /HELP queries,
  safe saving, explicit recovery diagnostics and reproducible native builds.

Document-mode soft returns, WordStar high-bit formatting, printing/mail merge,
spell checking, multiple simultaneous documents, shell escapes, syntax
highlighting, background saving and multilevel undo are outside this release.
Unsupported commands must be identified; they must never invoke a conflicting
TED operation or silently transform document bytes.

## 2. Upstream, licensing and reference evidence

Pin upstream [hperaza/TED](https://github.com/hperaza/TED) at
`7da2e1e39ae4cb57b45d84cf715b88fabbeadd17`. Preserve the complete source,
GPL-2.0-or-later notices, build scripts and documentation. Record the fetched
archive SHA-256 and hashes of every imported file before implementation.
The upstream snapshot is reference material; maintained adaptation sources
must be separately identifiable. Do not change files under this project's
synced `sources/` directory.

Relevant upstream evidence:

- [main.mac](https://github.com/hperaza/TED/blob/7da2e1e39ae4cb57b45d84cf715b88fabbeadd17/main.mac):
  startup, private stack and minimum 2048-byte free-memory check.
- [cpmio.mac](https://github.com/hperaza/TED/blob/7da2e1e39ae4cb57b45d84cf715b88fabbeadd17/cpmio.mac):
  GETTOP reads the BDOS pointer; output creation erases first; workspace name
  is fixed as EDITOR.TMP. These paths require the audits and corrections below.
- [termdef.mac](https://github.com/hperaza/TED/blob/7da2e1e39ae4cb57b45d84cf715b88fabbeadd17/termdef.mac):
  80x24 VT100/VT52 definitions, not evidence of BetterCP/M application success.
- [docs/ted.txt](https://github.com/hperaza/TED/blob/7da2e1e39ae4cb57b45d84cf715b88fabbeadd17/docs/ted.txt)
  and [docs/vmem.txt](https://github.com/hperaza/TED/blob/7da2e1e39ae4cb57b45d84cf715b88fabbeadd17/docs/vmem.txt):
  162-character lines, trailing-space removal, 516-byte cache buffers and a
  bounded disk workspace. Those original limits are not the new promises.

Use MicroPro WordStar 3.3 for CP/M, non-document mode, as the compatibility
reference. Record the exact manual edition and independently sourced reference
binary hashes in a TED reference-baseline document. The
[1983 reference manual](http://www.bitsavers.org/pdf/microPro/Wordstar_3.3/Wordstar_3.3_Reference_Manual_1983.pdf)
is a reference, not a license to redistribute WordStar. Do not import its code,
manual prose, screens or binaries into TED's distributable package.

For the supported subset, compare observable cursor, text, block, search and
file-command behavior with the pinned oracle. This specification's explicit
safety/text-preservation rules take precedence over historical destructive or
formatting behavior. Record each deliberate difference. Unresolved oracle
details block the affected compatibility claim; they do not justify guessing
and calling the result compatible.

## 3. WordStar-compatible interaction

`^K S` means Ctrl-K followed by S. In prefix state accept upper/lowercase letters
and the corresponding Ctrl-letter byte. Commands execute without Enter unless
they open a text field. Every recognized key is consumed exactly once.

### 3.1 Command matrix

| Keys | Required action |
| --- | --- |
| ^S / ^D | Previous/next character boundary. |
| ^E / ^X | Previous/next logical line, retaining preferred display column. |
| ^A / ^F | Previous/next word; freeze exact delimiter behavior with oracle fixtures. |
| ^R / ^C | Page up/down by the visible text height, preserving screen-relative position where possible. |
| ^W / ^Z | Scroll viewport one line up/down without changing text. |
| ^Q S / ^Q D | Beginning/end of current logical line. |
| ^Q R / ^Q C | Beginning/end of document. |
| ^Q B / ^Q K | Move to beginning/end block marker. |
| ^H / DEL | Delete preceding character; at line start join with previous line. |
| ^G | Delete following character; at line end join with next line. |
| ^T | Delete next word according to the pinned WordStar word-deletion fixtures. |
| ^Y | Delete current logical line, including its terminator when present. |
| ^Q Y | Delete from cursor to line end; preserve the terminator. |
| ^V | Toggle insert/overwrite; show the active state. |
| ^M | Insert a line break at cursor and move to the new line. |
| ^N | Insert a line break at cursor without moving the cursor. |
| ^I | Insert one literal TAB byte. |
| ^Q F | Find text using section 3.4. |
| ^Q A | Replace text using section 3.4. |
| ^L | Repeat the last committed search/replace operation. |
| ^K B / ^K K | Mark beginning/end of a character block. |
| ^K H | Toggle marked-block display; retain the marks. |
| ^K C / ^K V / ^K Y | Copy/move/delete marked block. |
| ^K R | Read another file at cursor; current filename remains unchanged. |
| ^K W | Write marked block to a prompted file through safe publication. |
| ^K S | Save current document and continue at the same cursor/viewport. |
| ^K D | Save and close document, then return to TED opening screen. |
| ^K X | Save and exit to the CP/M command prompt. |
| ^K Q | Abandon current document, default-No confirmation if modified, then return to opening screen. |
| ^J | Context help; return without changing text or document position. |

The distinction between ^K D and ^K X corrects the earlier conversational
outline, which treated both as exit-to-CP/M. TED has no requirement to reproduce
WordStar's complete opening menu. Its opening screen shall offer Open/New,
Help and Exit; closing a document must not unexpectedly select another file.
Exit from the opening screen performs normal workspace cleanup.

### 3.2 Editing semantics

Start in insert mode. Overwrite replaces the next ordinary byte, never consumes
a logical line terminator, and extends the line at its end. Preserve a preferred
visual column during consecutive vertical moves; horizontal motion establishes
a new preferred column. Tabs occupy the next eight-column stop for display,
but cursor positions and blocks refer to byte boundaries. Moving into a tab's
display span selects a documented adjacent byte boundary; never split a stored
tab into spaces just to position the cursor. Freeze this boundary behavior in
fixtures before enabling physical navigation aliases.

Clamp motion at document boundaries. Do not insert spaces merely by moving
beyond a short line. Horizontal scrolling must permit editing logical lines
longer than 80 columns. Moving/scrolling/help/redraw must not mark text modified.
No automatic indentation, tabification, case folding, word wrap or trailing-
space trimming occurs in the initial source-editing profile.

### 3.3 Prefixes, prompts and terminal keys

Represent normal editing, ^K prefix, ^Q prefix, text prompt, choice prompt,
opening screen and busy operation as separate states. Show pending prefixes.
ESC cancels a prefix with no document change. Invalid suffixes report an
unsupported command and return to normal state without inserting the suffix.
No prefix may remain active across help, save completion or cancelled prompts.

In ordinary document editing ^C means Page Down, not warm boot or entry to
TED's legacy prompt. In text fields ESC/^C cancels locally; in long operations
they request interruption at safe boundaries. Literal Q is text in editing
state. Confirmation Enter means No; invalid choices retain the question.
Default-No abandonment is required even if the historical oracle differs.

Use the shared field/choice controllers where their defined behavior fits.
Filename fields preserve typed case/spaces until semantic validation; normalize
only the parsed CP/M filename. Cancelling a field restores the previous search,
filename, document, cursor and viewport, as applicable.

Portable code shall consume logical actions and never read Model 4 keyboard
matrix/video memory directly. Bind physical arrows, Home/End, Page Up/Down,
Backspace and Delete where the existing platform path can distinguish them.
Model 4 CLEAR/Shift-CLEAR map to ESC and Ctrl-CLEAR to DEL under the established
input contract. Controls conflicting with an arrow representation must remain
distinguishable. Document actual physical aliases separately for each platform.
WordStar control keys must work even without optional host escape-key decoding.
Do not probe with terminal queries that BetterCP/M does not answer, or consume
ordinary user input while waiting indefinitely for an ESC sequence suffix.

Retain legacy TED command mode only through a visible Advanced command on the
opening/help UI, outside the WordStar editing bindings. Its destructive writes
must use the same safe publisher; it is not a bypass. It is not required for
any supported WordStar workflow.

### 3.4 Find and replace

Support forward/backward literal search, ASCII case-sensitive/insensitive
matching, single occurrence, repeat, and global replace. Prompt separately for
search text, replacement text and options; default to forward/case-sensitive,
with confirmation for replacements. Preserve accepted settings for ^L. Empty
replacement means deletion; an empty search is invalid. Cancelling either
field leaves the last committed search unchanged. Do not interpret filename
query switches inside literal search/replacement text.

Initial prompts may present named choices instead of reproducing WordStar's
entire option-letter grammar. Mark that difference in help and compatibility
fixtures. Confirm replacements with Yes/No/All/Cancel; Enter means No, All lasts
for this operation only. Cancellation keeps completed replacements and reports
their count, with the document still modified. Search never wraps silently.
Report end/not-found; a subsequent explicit repeat may start a newly requested
search, not an undocumented wrapped scan. Search must cross cache boundaries;
matching must not force the entire document into RAM.

### 3.5 Blocks

Represent a block as a half-open byte range [begin,end) in logical document
order, including any selected TABs and line terminators. Reject reversed,
missing or empty ranges for operations needing nonempty text. Marks track
insert/delete operations deterministically; record position-affinity fixtures.
Block hide changes display only. Copy/move insertion inside the source range
is rejected without mutation. Move to its own boundary is a no-op. After a
successful copy/move, mark the inserted range; after deletion clear the marks.

Before changing text, verify capacity for a block operation or stage its result
in workspace so allocation/disk failure leaves the original document intact.
File insertion must likewise be complete or leave text unchanged. Operations
work when source/destination lie in swapped-out blocks. Block-file output does
not change the document filename or its dirty state and uses section 5.

## 4. Invocation, filespecs and queries

Initial syntax: `TED [simple-DU:]filename` or `TED` for the opening screen.
Open/New and file prompts accept the same exact 8.3 filespec grammar, with
simple drive/user qualifiers and all 32 BetterCP/M user areas. Capture caller
DU once. Unqualified invocation uses caller DU; subsequent unqualified file
prompts use the current document DU, or caller DU before a document is named.
Reject wildcards, attribute predicates and compound selectors before file I/O.
Use the shared exact-filespec implementation where practical.

An absent file becomes a new, initially empty document only after filename
validation; opening it does not create a disk file. Directories with the same
name in different users are independent objects. Status and destructive/recovery
prompts show the complete canonical drive, user and filename.

Use the current [utility query](../../specifications/UTILITY-VERSIONING.md)
and [help](../../specifications/UTILITY-HELP.md) contracts: exact case-insensitive
/VER and /HELP tokens, /HELP precedence, handled before ordinary file parsing,
provider lookup, workspace creation or DU mutation. Queries require no monitor.
Follow current component revision policy, not obsolete hard-coded Build text.
Preserve upstream identity/license alongside a distinct BetterCP/M adaptation
identity. Register the adaptation only when implementation starts; documentation
alone does not invent a binary revision. ZSM4/LINK retain third-party identities.

## 5. File-safety contract

### 5.1 Invariants and assumptions

The original document and every unrelated existing file remain recoverable
until a complete replacement has been written, closed and independently
read back. No failed operation may mark an uncommitted save successful, clear
the dirty flag, close the document or exit after a requested Save-and-Exit.

Assume single-task CP/M; no exclusive-create, atomic multi-file transaction or
power-loss guarantee exists. Reinspect names and metadata at publication
boundaries. Media replacement or an ambiguous mutation invalidates prior
checks. Stop and expose recovery files rather than overwrite an unexpected
object. Never claim full durability merely because BDOS CLOSE returned success.

### 5.2 Workspaces and name reservation

Allocate workspace in an explicitly selected writable DU, defaulting to document
DU (caller DU for an unnamed document). Permit selecting another DU when space
or protection prevents this. Never assume Utilities B: is writable.

Use a bounded candidate search for exact 8.3 names, for example TEW00000.$$$
(workspace), TET00000.$$$ (staged output), TEB00000.BAK (backup). Every candidate
must be absent across all physical extents before creation. Exhaustion is a
clean failure, never authority to reuse an existing file. Distinguish files
created by this session with an owned-name record and format/version signature;
a signature alone never authorizes deletion of a pre-existing file.

Output TMP and BAK reside on the destination DU so publication uses same-DU
rename. Workspace may be elsewhere. Reject aliases among source, selected
input, workspace, destination and recovery objects. No startup wildcard cleanup
is allowed. Discoverable abandoned workspaces require explicit recovery or
deletion choice, defaulting to preservation, after validating their structure.

### 5.3 Save state machine

| State | Required operation | Failure disposition |
| --- | --- | --- |
| S0 Validate | Parse exact target; inspect existence, extent attributes and media state; obtain authorization. | No namespace/data mutation. |
| S1 Stage | Reserve absent TMP on target DU; serialize complete intended output; check every write. | Original untouched; remove only owned incomplete TMP if safe, otherwise report it. |
| S2 Close | Close TMP and check result. | Original untouched; retain/reveal TMP if cleanup cannot be established. |
| S3 Verify | Reopen TMP; compare all intended records and defined padding against document serialization; check read/close results. | Never publish mismatching/unreadable output. Original untouched. |
| S4 Reinspect | Recheck destination identity, attributes, TMP and reserved BAK absence. | Preserve verified TMP; require a new explicit decision after unexpected change. |
| S5 Back up | If replacing, rename original to absent BAK; verify resulting names and original metadata. | Stop; inspect actual namespace even when rename reports failure. |
| S6 Publish | Confirm final absence; rename verified TMP to final; inspect names and readback/metadata. | Attempt bounded rollback under section 5.4; keep edited data recoverable. |
| S7 Commit | Required final metadata and verification succeed; mark document clean. | Metadata failure is an incomplete save with recovery paths, not a clean document. |
| S8 Retain | Keep the original BAK and report its exact name; cleanup owned workspace only on successful close/exit. | Cleanup failure reports a warning and actual retained paths. |

For new targets skip S5. A failed save must never delete an existing final
object to make publication succeed. Save As changes the current document
identity only after S7. Save-and-Continue preserves cursor, marks and viewport.
Repeated saves reserve new backups rather than silently replacing an unrelated
.BAK file. Backup pruning is a later explicit operation, outside initial scope.
Warn about required free space and accumulating backups; do not present a
capacity estimate as a promise that writes will succeed.

### 5.4 Rollback and recovery

If original-to-BAK succeeded but publication fails, restore original only when
final is absent and BAK still matches the captured original. If final exists,
do not rename over it. If a failed BDOS rename nevertheless moved an entry,
base recovery on observed namespace and record content, not its return byte.
No blind retry of the whole publication sequence is permitted.

On rollback failure retain original BAK, edited TMP and any unexpected final,
stop namespace mutation, and print complete recovery identities. Never say a
file was retained unless it can actually be located. If media becomes unreadable,
state that the name was last known and that verification is unavailable.

Cancellation before S5 leaves original untouched. Once namespace publication
begins, latch cancellation and finish a bounded publish/rollback decision before
returning. Fatal BDOS warm boot, media removal or power loss can interrupt this
sequence; user documentation shall explain recovery from retained exact names.
Do not automatically recover/delete by wildcard on the next launch.

### 5.5 Attributes and protected files

Inspect the union of RO/SYS attributes across physical extents. Read-only
documents may be opened for inspection. Saving over any RO/SYS target requires
a separate default-No confirmation naming the actual attributes; ordinary
overwrite authorization never implies protected-file authorization. After No,
keep the document editable and permit Save As to another target.

Preserve original RO/SYS on the backup and replacement. Clear RO only at a
specifically authorized mutation boundary, restore it on failed paths, and
verify restoration. Mark successfully changed output ARC according to current
BetterCP/M file-attribute semantics; preserve original backup ARC. New outputs
are ordinary writable non-SYS files with the appropriate changed-file ARC state.
Do not invent filesystem timestamps or a new timestamp API. Unknown supported
attribute bits must not be silently cleared; record the chosen preservation
policy against the current filesystem contract before release.

## 6. Text preservation and limits

The editor is an ASCII source editor, not a byte-exact binary editor. Preserve
every supported text byte except an explicitly requested edit. Preserve literal
TABs, trailing spaces, blank lines, case, leading whitespace and missing final
newline. Never trim, expand or compress output whitespace automatically.
Internal space compression is allowed only if exact original bytes can be
reconstructed. Display control notation is never written to the document.

Recognize CRLF, LF and CR line endings and retain the terminator of each
existing line, including mixed files. A new document uses CRLF. New breaks in
an existing document use its first observed terminator, or CRLF if none exists.
Joining removes only the selected terminator. An explicit future conversion
command is not implied by Save. Store logical byte positions independently
from the display width of a TAB or a two-byte CRLF terminator.

### 6.1 CP/M record length and EOF

Portable CP/M files are sequences of 128-byte records; exact host byte length
cannot generally be recovered. In default text mode, accept the first 1Ah as
logical EOF only when the rest of the recorded file consists entirely of 1Ah.
Retain that recognized suffix on a no-edit round trip. If non-padding data
follows 1Ah, reject the text load with an explicit diagnostic; do not silently
discard the suffix. A full-record file without 1Ah is complete text to its
record boundary. Do not infer a shorter length from trailing spaces or zeros.

For changed/new text, preserve supported logical bytes and append 1Ah only as
needed to pad the final physical record; do not add an extra record solely for
an EOF marker when data ends on a record boundary. Empty new files are zero
records. Do not rely on nonportable reserved FCB bytes for exact length.
Verification compares the defined logical output and its physical padding.

NUL, unsupported C0 bytes and bytes >=80h require a diagnostic before exposing
a partially loaded document as editable. Refuse the load, preserve the prior
document and explain the unsupported byte/offset. This is deliberate scope;
do not strip high bits, substitute '?' or silently treat a WordStar document
file as plain source text. Binary/high-bit editing may be specified later.

### 6.2 Long lines and disk-backed capacity

Replace the upstream 162-character assumption with a required initial maximum
of **4095 text bytes per logical line**, excluding terminator. Longer lines
are refused with filename/line/offset evidence, without replacing the current
document or changing disk files. This is a product limit, not a claim that
WordStar used this limit. Audit all 8-bit counters and fixed 164-byte buffers.
Do not allocate a 4096-byte permanent buffer for every line or every cache page;
use bounded streaming/chunked operations and explicit overflow checks.

Expose the workspace's measured record/address limits rather than advertising
an unconditional 1 MiB text capacity. Linked-record, line-number and file-offset
arithmetic must be wide enough or reject overflow before mutation. A document
larger than available RAM must remain editable by paging. Staging a load or
block operation may require additional disk capacity; check safely and retain
the original document if staging fails. Bound repeated operations and allow
cancellation during long scans at cache/record boundaries.

## 7. Memory ownership and runtime boundary

The current BetterCP/M contract uses the active BDOS gateway address obtained
from the word at 0006h as the exclusive upper boundary for application-owned
memory; loaded RSXs reduce it. Existing ED_MEMORY in
[ed.mac](../../src/utilities/ed.mac) uses this contract. The
[full-TPA loader record](FULL-TPA-COM-LOADING.md) distinguishes this active bound
from fixed unloaded-memory measurements. Upstream TED's GETTOP is therefore
not automatically a defect; its use and all dependent allocations require
qualification. Never replace it with a hard-coded D500h/53K assumption.

After establishing a private stack, capture the active ceiling and validate
code/data end, initialization overlays, stack bounds, block map, cache buffers,
line fragments and prompt workspace against it using checked arithmetic.
Application intervals shall be disjoint and lie in [0100h, ceiling). No byte at
or above ceiling may be used as scratch. Reserve stack and call-frame space
explicitly; do not let the cache allocate through it.

No private ECB/PDS access is needed. If a later platform profile changes the
public boundary contract, introduce a documented adapter then; do not invent
a function number or extrapolate from the current gateway implementation.
Use normal entry/exit conventions. Queries return without an interactive
startup or warm boot; interactive exit may use the documented warm-boot path.
Preserve caller DU and restore normal DMA before normal interactive return.

Retain at least upstream's 2048-byte post-static-workspace startup requirement
only if measured cache/map/stack needs prove it sufficient. Derive and publish
the actual minimum from the final map and worst-case live state. Fail before
workspace creation if insufficient. Report available bytes and required bytes.
No extension loading/unloading is performed during editing, which would change
the captured ceiling. Reject/avoid paths that can invalidate document pointers.

Measure stack high-water marks under actual BDOS/BIOS calls, nested prompts,
cache eviction, replacement, save failure and cancellation, plus a stated
engineering reserve. Intercepted-BDOS unit-test measurements are not native
stack bounds. Use canaries and protected-memory guards in qualification.
No permanent OS growth or reduced unloaded TPA is permitted for TED.

## 8. Screen and platform integration

Use existing portable personality/backend facilities: M4SCRN plus ANSI on
Model 4; ANSISCRN plus ANSI on cpmsim. Startup currently may select another
personality; document explicit switching with the existing manager commands.
Do not silently replace/load/unload providers or alter saved startup profiles.
If a required capability is missing, explain it before creating workspace.
Keep query/help text usable on the basic console.

Restrict screen output to the qualified bounded ANSI subset. No DSR/device
query, alternate-screen assumption, full xterm behavior, 132-column switching,
hardware-specific memory access or function-key dependency is required.
All actions must be available through the specified control keys. Reserve
header/status rows and compute Page Up/Down from the actual text viewport.
Keep the cursor and markers visible, including the final screen column and
last logical line. Restore attributes/cursor visibility on exit. Do not promise
restoration of an arbitrary prior screen image. Require a native Model 4
keyboard/video campaign in addition to host terminal-model tests.

## 9. Implementation structure and build outputs

Suggested maintained source layout (paths are prospective until implementation):

- `third_party/ted/`: immutable upstream snapshot, license and provenance.
- `src/utilities/ted/`: adapted engine, dispatcher, file lifecycle, publisher,
  memory and terminal adapters, with traceable upstream origins.
- `tools/build_ted.py`, `tools/build_native_ted.py`: canonical cross/native
  build entry points; publish `build/utilities/TED.COM` only after gates.
- `tools/test_ted_*.py` and `tools/qualify_ted_*.py`: layered harnesses.
- `docs/user/TED.md`: actual supported keys, limits, module setup and recovery.
- `docs/engineering/TED Reference Baseline.md` and
  `TED Qualification.md`: exact provenance and cumulative bounded evidence.

Keep engine, logical key dispatcher, prompt controller, renderer, file adapter
and publication state machine independently testable. Reuse the shared prompt
library where semantics match; do not fork a second generic input framework.
All non-query write paths, including legacy command mode, go through one
publisher. Record adaptation patches and upstream license headers.

Native ZSM4/LINK must assemble actual maintained instructions and macros.
Record deterministic source preparation if needed; host preparation must not
preassemble instruction bytes or silently repair linked output. Native and
cross executables must match byte for byte over the exact executable length,
excluding only verified CP/M final-record padding. No date/path-dependent
identity. Use current component metadata and independent adaptation revisions.

## 10. Qualification and acceptance matrix

Every row requires independent expected text/namespace results, not merely a
success banner. Keep all tests on disposable images. Do not modify source
reference disks or the user's mounted working media.

| ID | Campaign | Required evidence |
| --- | --- | --- |
| T01 | Provenance/build | Pinned source/archive/license hashes; reproducible cross and native builds; exact COM parity and size. |
| T02 | WordStar subset | Oracle fixtures for every supported command, prefix/control-letter variants, movement boundaries, word delimiters, page behavior, blocks and search. Record deliberate differences. |
| T03 | Text round trips | TABs, trailing spaces, mixed CR/LF/CRLF, no final newline, empty and full-record files, 127/128/129-byte cases, valid padding suffixes and rejected embedded 1Ah/high-bit/NUL data. |
| T04 | Long lines | 161/162/163 and 4094/4095/4096-byte lines, TAB display widths, horizontal scrolling, split/join/replace/block crossings; refusal never truncates. |
| T05 | Virtual workspace | File exceeds available RAM by at least 2x, repeated eviction, cache-edge matches, block moves/copies, full map/address limits, wrap/overflow rejection and interruption. |
| T06 | Namespace/attributes | Drives/users 0,7,15,16,31; same names across DUs; multi-extent RO/SYS unions; ordinary/protected refusal; Save As and block-output aliases; unrelated file preservation. |
| T07 | Publisher fault injection | Every S0-S8 boundary, first/later write, close/reopen/readback, attribute operations, both renames, cleanup and rollback; failed rename with actual movement; unexpected final/BAK appearance. |
| T08 | Real capacity faults | Directory full; no blocks; one/few blocks; workspace-full during edit/load/replace; output-stage capacity exhaustion; distinguish real exhaustion from injected status. |
| T09 | Memory/stack | Reduced ceilings with loaded modules, exact minimum and one-byte-below, 16-bit wrap, cache/map collision, stack canaries/high-water, untouched protected core and terminal modules. |
| T10 | cpmsim live | Installed editor from Utilities B: beside normal System A:, private work DU, all command groups, large document, safe save/exit/relaunch, filesystem and source audits. |
| T11 | Model 4 live | Same scope through trs80gp, physical keyboard matrix actions and native 80x24 screen captures/VRAM checks, no lost prefixes or last-row corruption. |
| T12 | Final package | Exact membership/user placement/readback, artifact/image hashes, notices/source/build companions, both final paired System/Utilities image runs. |

Additional requirements:

- Run T07 with media/read/write/rename/protection failures before and after
  actual mutation. Independently inspect raw directory entries, extent maps,
  all original/edited file records and owned recovery names. Check for duplicate
  names, cross-linked allocation and accidental deletion of sentinels.
- Read-only input/Utilities media must remain unchanged. Filesystem inspection
  must not depend exclusively on the same library that prepared the images.
- Abort tests cover pending key prefixes, text prompts, search, swap I/O,
  serialization, verification and publication. No cancelled Save-and-Exit may
  exit with unsaved changes. Successful Save-and-Exit must reopen to exact text.
- Run native keyboard workflows on the Model 4's real 24-row viewport, including
  Ctrl-C paging, CLEAR cancellation, Control-key distinction, long key sequences
  and repeated return to CP/M. Host keyboard injection alone is insufficient.
- Run applicable legacy and checked cpmsim RAM profiles separately where
  supported by the selected release. Protected-ROM/XIP application acceptance
  is a separate required receipt if TED is advertised for that profile; ordinary
  RAM success does not transfer to ROM. No Model 4 ROM claim is implied.
- Physical-hardware results are PASS/FAIL/NOT RUN separately from trs80gp.
  Passing emulator evidence supports emulator qualification only.
- Retain initial failures and corrected reruns with their dispositions. Distinguish
  guest bugs, harness preparation errors, terminal limitations and unsupported
  cases. No silent skips, substituted binaries or hand-edited outputs.

Each receipt records source commit plus actual input hashes, profile/config,
assembler/linker/emulator identities, COM size/hash, loaded module identities,
System/Utilities/work image hashes, command/key transcript, screen oracle,
pre/post filesystem audit, expected/actual results and limitations. A changed
COM, module, System core or image requires affected reacceptance; old PASS
records retain only their original scope. Document-only edits do not invent a
new executable revision or force unrelated campaigns.

## 11. Ordered implementation and release gates

1. **Reference and design:** import/pin upstream; freeze WordStar fixtures and
   differences, simple-DU grammar, text representation, marker affinity and
   limits; audit all destructive writes, counters and memory allocation.
2. **Safe foundation:** implement owned workspace, measured memory layout,
   staged publisher and recovery diagnostics. Prove faults/capacity invariants
   before interactive file replacement is enabled.
3. **Text engine:** remove trimming/tab conversion and fixed 162-byte paths;
   implement terminator/padding preservation, long lines and transactional
   document operations across cache boundaries.
4. **Interaction:** implement prefix dispatcher, WordStar editing/file commands,
   opening screen, prompts/help and portable terminal adapter. Retain no
   conflicting legacy binding under a supported WordStar key.
5. **Platform qualification:** complete T01-T11, record native/cross parity,
   measured minimum TPA, stack reserve, response times and known limits.
6. **Distribution:** add the qualified adaptation to the Utilities builder,
   component metadata and manuals, keep GPL corresponding-source companions,
   then complete T12 on both exact final paired image generations.

Selection of TED does not add an unqualified binary to daily media, change the
System Disk's ED membership, settle the standalone disassembler selection or
declare the full Utilities release complete. Implementation may proceed under
this adopted direction; any change to these explicit compatibility, safety or
text-preservation requirements must be documented and reviewed as a contract
change rather than silently weakened to fit the original engine.
