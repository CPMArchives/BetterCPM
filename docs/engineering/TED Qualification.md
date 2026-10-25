# TED qualification

Current final-payload campaigns are in progress. This page will record only
completed evidence; historical foundation results are preserved in
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
