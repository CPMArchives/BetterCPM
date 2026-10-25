# TED qualification

TED 1.0 revision 001 passes component acceptance on the exact normal RAM
z80pack and trs80gp System/Utilities pairs recorded in
[TED-Qualification.json](TED-Qualification.json). The agreed command subset,
text preservation, safe publication/recovery and memory bounds are covered by
the layers below. Historical foundation results remain in
[TED Foundation Qualification](TED%20Foundation%20Qualification.md).

The implementation is TED 1.0 revision 001, with a 30,380-byte COM payload,
SHA-256 `272c31a168d63d4b5a5f2c5517d0c614a00fccf746dc966e8a180f16cc9f959c`.
The initial version reference is an input-comparison baseline, not execution
acceptance. External ZSM4 4.7 and LINK 1.3 keep their own version numbers.

The compiled tests execute the maintained assembly with register-clobbering
BDOS and a separate Z80 CPU implementation. Native emulator campaigns are
separate: API storage probes, native COM parity, and actual installed-editor
keyboard/screen/file workflows have different receipts and scopes.

Current console limitations must not be hidden by simulated nonexistent keys.
The Model 4 raw arrows collide with control codes. Primary control navigation
is the qualified route. Its current MCON also offers no populated physical
Ctrl-underscore chord; logical ASCII US redraw is retained and tested via the
independent CPU and z80pack terminal. The Model 4 application does not inspect
the keyboard matrix or alter the console ABI to distinguish these bytes.

Physical hardware and ROM/XIP or checked-profile application acceptance are
not claimed. The whole Utilities release remains provisional, independently
of TED-specific component acceptance on exact paired images.

## Measured native results

| Platform | Active exclusive word6 ceiling | Free bytes above static image | Editor stack high-water | API-probe stack high-water |
| --- | --- | --- | --- | --- |
| z80pack | C501h / 50,433 | 19,797 | 54 / 2,048 | 36 / 2,048 |
| Model 4 / trs80gp | C601h / 50,689 | 20,053 | 54 / 2,048 | 36 / 2,048 |

All completed editor workflows preserve the 32-byte low-stack and 32-byte
line-buffer guards. Both platforms independently build the same logical COM
with ZSM4/LINK; the collector compares every payload byte and checks native
record padding. Installed execution reads B:TED from the exact candidate
Utilities image. All expected saved files and retained backups compare exactly,
final work filesystems pass their checks, original paired media remain unchanged,
and Model 4 captures preserve the unused video tail.

## Verification layers

The maintained editor is deliberately different from upstream in its byte
representation and failure handling. Upstream erase-before-create, fixed temp
name, lossy line codec and unsafe modified-flag resets are not preserved.
Its screen/browse/command modes and existing operation semantics are retained.
The adopted WordStar subset adds command sequences and the three approved
line-local word operations, without persistent block marks or undo.

The final compiled suite currently passes 140 text cases, 179 publisher cases,
42 workspace cases, 105 command cases and 21 complete frontend cases (487
in total). Workspace bounds include a complete 8,191-record input and refusal
of 8,192 records while preserving the old document. That large test runs one
continuous CPU invocation across bounded instruction-budget slices; it does
not restart the operation or replace guest results with host output.

The full-image maximum is not a claim that a one-MiB document plus work files
fits an 800-KiB floppy. Disk space must accommodate the input, immutable
checkpoints, pending stage and retained backups. The real emulator campaigns
exercise the capacities of their actual disposable floppy formats.

The private stack reserves 2,048 bytes below the static end. Exact-minimum and
one-byte-below ceilings, protected core sentinels, no dynamic allocations, and
a 32-byte stack guard plus 32-byte line-buffer guard are exercised separately.
The application bound for this COM is exclusive word6 >= 77ACh (30,636).
This is a static application admission bound, not a claim about arbitrary
third-party BDOS/BIOS stack requirements. Qualified native configurations are
identified by exact System, module-containing disk and emulator hashes.

## Acceptance coverage

The machine-readable [receipt](TED-Qualification.json) and
[retained evidence](TED-Qualification-Evidence.tar.gz) bind acceptance to the
exact executable and paired media. Compiled tests execute guest instructions;
host expectations are separate fixture data. Real capacity probes run the
maintained storage/publisher implementation in a guest probe, while installed
editor scenarios execute B:TED from the candidate Utilities image.

| Gate | Evidence and scope |
| --- | --- |
| T01 | Pinned upstream/archive checks, cross build and native ZSM4/LINK logical-payload parity on each platform. Native record padding is checked separately. |
| T02 | 105 command and 21 frontend cases, plus installed prompted block/file workflows and navigation/search interaction. No unapproved WordStar features are implied. |
| T03 | 140 text cases and independent exact-byte installed output/backup oracles; mixed separators, tabs, trailing spaces and missing final newline survive. |
| T04 | Boundary cases through 4095 bytes, refused 4096-byte input and edit overflow, split/join/word deletion and line-buffer guards. |
| T05 | 42 workspace cases including 8191 records and refused 8192; installed 45,952-byte document exceeds twice available editor RAM on each qualified configuration. |
| T06 | Publisher/workspace/command tests cover DU namespaces, attributes, ranges, aliases and unrelated-file preservation; native campaigns audit original media and extracted inputs/outputs. |
| T07 | 179 publisher cases cover staged publication, failure-after-move rename ambiguity, rollback, readback and input callbacks changing DU/DMA. Fault-injected cases are distinct from real disk exhaustion. |
| T08 | Guest API probes exhaust actual data allocation and directory entries, leave one block, and verify edit/save refusal without losing the document or existing destination. |
| T09 | Independent exact-minimum/one-below and protected-memory cases; native post-editor stack/line guards, stack high-water and loaded-module ceilings. Hardware and alternate profiles are excluded. |
| T10 | z80pack: installed groups, interaction, large document and real-capacity API session; separate native product build/parity gate. |
| T11 | trs80gp: separate native product build/parity and installed groups, interaction, large document and real-capacity API session. Physical matrix input and 2048-byte screen captures are retained; unused video tail must stay unchanged. |
| T12 | Package builder requires both exact image hashes from the receipt, checks membership/readback/filesystem/DMK round trip, and includes deterministic GPL corresponding source, licenses and native build input. |

The installed large-file test is larger than available editor RAM, not larger
than the complete TPA. The maximum-size compiled workspace test supplies the
separate one-MiB address-bound proof. Real-capacity probes are not a claim
that an entire editor session fits on a completely full work disk.

## Initial failures and dispositions

- Early adaptations had zero-count LDIR and input-during-disk-I/O defects.
  The bounded RAM-line adapter and input queue replace per-key checkpoints;
  the current tests include the previously failing paths.
- Early interactive fixtures lacked CP/M record padding. The input validator
  correctly refused the resulting zero bytes. Corrected fixtures are padded
  explicitly; the failed run is not counted as acceptance.
- One post-exit harness incorrectly removed 256 bytes from an already absolute
  COM. It was corrected to remove a zero prefix only when actually present.
- A forward-search workflow wrongly expected implicit wrap. It now explicitly
  issues P 1, retaining TED's forward-only search behavior.
- Model 4 preparation initially lacked shifted-parenthesis matrix encoding.
  The test driver now presses actual shifted 8/9 for TED R syntax. Its missing
  Ctrl-underscore encoding instead exposed an unavailable physical chord;
  that chord is not fabricated or reported as a Model 4 PASS.
- The user-requested pause interrupted a disposable API campaign. Superseded
  probes were stopped when expanded final-source campaigns replaced them.
  Neither interrupted nor superseded runs supply final acceptance.

Two final-payload Model 4 attempts were stopped on faulty harness readiness
predicates: an inverse-video command cursor was treated as plain text, and a
word-deletion marker also matched the pre-edit line. The corrected driver waits
for the complete resulting line and allows settling time. It reuses only the
independently verified native build and completed group workflow on identical
payload and original paired media, with the reused receipt hash recorded.
The remaining interaction, large-document and capacity checks run separately.

The retained native receipt checks payload, record padding, native source,
completed group outputs/backups and memory guards. Its stopped mid-SUBMIT
snapshot is explicitly not a final filesystem acceptance result. The remaining
installed session must finish with its own output and filesystem checks. A
host-monitor extension and the executed helper version remain with the stopped
run. The helper's wall-budget variable is now separate from its per-key tuple.

A host performance sample of a superseded Model 4 run found most sampled
main-thread time inside macOS sound-effect playback. Final headless execution
uses the emulator's documented `-sx -sfmute` options; only host audio output is
suppressed. The sample and exact invocation are retained. Earlier unmuted
wall times must not be presented as TED hardware performance measurements.

## Application and loader bounds

The direct-entry CPU tests exercise TED's static write/stack admission bound.
A real CP/M loader reads complete 128-byte records: this 30,380-byte payload
occupies 30,464 bytes on disk, so its record-rounded load end is 7800h even
though its last static application byte is below 77ACh. Normal native runs
have ample space above both bounds. No claim is made that a CCP can load the
file at the unrounded static bound. The native measured configurations and
application-only boundary tests are separate evidence.

Numeric line-command operands are bounded to 16 bits. Larger physical input
and 24-bit byte positions do not imply an unlimited line-number language.
Overflow is refused; full-file byte preservation and publication have their
own independently tested limits. Large-file checkpoint and publication work
streams the whole document and can be slow on a Z80. Ordinary typing buffers
one line; it does not checkpoint the disk on every character. Physical
hardware performance has not been measured.

The adaptation now queues input at render rows and random-read boundaries.
Critical publication has a separate non-cancelling input observer; it cannot
turn a late ESC/Ctrl-C into an abandoned rename. A 200-key test crosses
multiple redraw pages and a save, while a publisher observer deliberately
changes DU/DMA. The file APIs rebind their descriptors after those callbacks.
The queue remains bounded at 128 bytes and does not add editing capabilities.

For the current Model 4 console, raw arrows are control bytes: up is ^K,
down ^J, left ^\, right ^]. Those bytes retain their TED meanings, which can
include insertion or deletion. Use ^E/^X/^S/^D for navigation. TED cannot
infer the originating physical key from an ambiguous ASCII byte.

## Reproduction and evidence layout

Build the maintained binary with `python3 tools/build_ted.py --output
build/utilities`. Run the five `test_ted_{text,publisher,workspace,commands,frontend}.py`
programs for the compiled layers. The installed-session driver is
`tools/qualify_ted_session.py --system <paired-system-root> --utilities
<utilities-image-directory> --output <new-disposable-directory> --platform
z80pack` (or `trs80gp`). It refuses an existing output directory. The z80pack
native product build uses `qualify_ted_editor.py --platforms z80pack --scenario
groups` without `--installed` or `--cross-smoke`;
the Model 4 native build is retained separately. Its final installed session
uses `--skip-native-build --reuse-groups <retained-native-and-groups-receipt>`
to avoid repeating independently verified work. Fresh qualification can run
without these flags; reuse requires the identical payload and paired media.

The retained archive includes original paired media, disposable work media,
input/output fixtures, physical key invocation, screen/console captures,
filesystem checks, compiled reports, test tools and exact native source/build
records. `EVIDENCE-MANIFEST.json` hashes every other archived member. Private
WordStar reference material is excluded; only the already tracked derived
compatibility fixtures travel with the corresponding source.
