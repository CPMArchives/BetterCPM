# NOAH quiet reporting

Status: NOAH 1.0 revision 8, bounded `/Q` increment, 2026-10-25.
The [behavioral specification](NOAH%20Specification.md) remains normative.
This change implements the quiet switch over the existing LBR/codec commands.
It adds no archive formats, prompts, recovery commands, OS services or browser.

`/Q` is an exact, case-insensitive option accepted in any option position;
identical repeats are harmless. It does not imply `/Y`. Invalid extensions such
as `/QQ` and `/Q=Y` remain invalid. VER/HELP retain their existing forgiving
precedence and run without a companion file.

Quiet suppresses explicitly designated routine output:

- successful per-file extraction and standalone codec publication;
- successful compressed-source-to-stored-member announcements;
- ordinary-copy progress during EXPAND;
- successful ADD-source preflight names, ordinary capacity progress and the
  archive publication success line.

LIST and TEST results, archive identity headers, coverage counts and completion
summaries remain visible. The headers identify subsequent results or diagnostics;
quiet does not remove that context. Requested removal names and rebuild/recovery
loss notices remain visible. Prompts, declined/skipped/no-op work, protection
refusals, failures, cancellation, retained TMP/BAK names, unavailable timestamps
and explicit compression size increases remain visible. A quiet ADD source that
fails preflight or excludes the target prints its source identity with the
diagnostic even though successful-source progress was suppressed.

The implementation uses a reset-per-invocation flag and opt-in progress helpers.
General printing, console input, the publisher, codecs and archive libraries
are not globally muted. Quiet changes presentation only; authorization, source
selection, payload bytes, staging, verification and publication are unchanged.
This increment does not claim to complete the specification's remaining outcome
accounting or safe Retry/Skip/Abort behavior.

## Qualification

`python3 tools/test_noah_quiet.py` exercises 31 assembled-code transactions.
Normal/quiet command pairs compare final files, attributes, created files,
renames and deletions for LIST, TEST, extraction, standalone SQ/CR/EXPAND,
ordinary/compressed ADD and REMOVE. Additional checks cover actual prompt
decisions, protected skips, write failure, failed rollback recovery names,
compression growth, unavailable timestamps, query precedence and invalid options.
The existing 137-case adapter, 38-case writer and 51-case codec suites also pass.

`tools/qualify_noah_codecs.py --quiet-reporting` assembles and links the changed
resident/controller modules with unmodified ZSM4/LINK on both platforms. It
reuses codec products only after exact native/cross byte and padding checks.
The native campaign runs quiet LIST, extraction, SQ, EXPAND, compressed ADD,
TEST, REMOVE and an unsupported-stream failure. Independent output/CRC checks
verify the file outcomes; console assertions verify visible required results
and absent routine success messages. Loaded terminal providers remain active.

The resident image is 17,520 bytes. The overlay window remains 4580h, so all four
codec modules are byte-identical to the revision 7 full campaign. Controller
code is 16,782 bytes; aligned plans occupy 8780h–9F80h and transformed identities
9F80h–B980h. The maximum required end B980h remains below measured active ceilings
C501h (z80pack) and CA01h (Model 4). This is qualification of the recorded
configurations, not every possible loaded RSX combination.

See the [receipt](NOAH-Quiet-Qualification.json) and
[portable evidence](NOAH-Quiet-evidence.tar.gz). The prior full codec/write
campaign remains in [NOAH Codec and Overlay Integration](NOAH%20Codec%20and%20Overlay%20Integration.md).
Full NOAH completion, ARK, remaining failure/outcome handling, the interactive
browser and final Utilities Disk packaging remain separate work.

## Remaining failure-path issue

The focused failure-visibility check also confirmed an existing behavior shared
by normal and quiet mode: a new ADD whose selected source fails preflight can
still publish an empty LBR. This is outside the reporting-only change and is not
accepted as full specification conformance. The next failure/outcome increment
must leave the new archive absent when every proposed source fails or is skipped
and no explicit valid capacity/compaction change remains.
