# NOAH final outcomes and batch dispositions

Status: NOAH 1.0 revision 11, bounded reporting increment, 2026-10-26.
The [behavioral specification](NOAH%20Specification.md) remains normative.
This follows [staged failure handling](NOAH%20Staged%20Failures.md). It changes
reporting for existing LBR and codec commands, with no new archive operations,
interactive browser, OS service or distribution membership.

## Final outcome

An ordinary command that enters selection prints exactly one final outcome,
including under `/Q`:

| Text | Meaning |
| --- | --- |
| `Outcome: success.` | Useful work completed with no recorded error, warning, no-match object or declined object |
| `Outcome: warning/partial.` | Useful work completed, with errors, skips, incomplete coverage or other warnings |
| `Outcome: warning/no-work.` | Nothing useful completed and no real error occurred; includes no matches and declined/unchanged operations |
| `Outcome: failure.` | Command validation/selection failed, an unsafe stop occurred, or real errors occurred without useful completed work |
| `Outcome: cancellation.` | The user cancelled, even when earlier work completed |

Cancellation takes precedence over other outcomes. An unresolved stop takes
precedence over useful partial work. A failed extraction archive can still have
published members: those members count as useful work for the command outcome,
while that archive remains in the failed archive category. A confirmed publication
counts as useful work, including an intentional capacity-only archive change.
A skipped failed source cannot turn an unchanged ADD into a no-error no-op.
Compressed ADD carries candidate failures across subsequent codec invocations.

A successful Retry records a warning but does not count a second object or a
failed object. Earlier diagnostics remain visible. The command's internal result
is `NS_RESULT`: 1 success, 2 warning, 3 failure, 4 cancellation. This is internal
state, **not a shell exit-code interface**. `/VER` and `/HELP` retain their resident,
companion-independent behavior and do not print an ordinary-command outcome.
Resident startup failures before controller entry retain their existing diagnostics.

## Batch dispositions

The existing `Archives (hex)` / `Files (hex)` line retains selected, processed,
failed and unprocessed counts. Processed means an attempted object that reached
its final completion path, not necessarily successful work. A following
`Disposition (hex)` line adds completed, no-match and skipped counts for those
same objects. Standalone codecs count source files; LBR queue commands count
archives. Each attempted object belongs to exactly one final category:

- failed, when the object finished with its error flag set;
- completed, when error-free listing/testing found selected members, extraction
  published members, a codec published output, or an archive update published;
- no-match, when no selected member matched;
- skipped, when matching work was declined or left unchanged without an error.

Failed objects do not also increment completed, no-match or skipped. Earlier
successful subwork remains in existing member detail and affects the command
outcome. Retry records the final object disposition once. The frozen unattempted
tail remains unprocessed. Cancellation remains explicit in the final outcome;
it does not claim the remaining queue completed.

ADD still reports accepted source versions rather than pretending its source
queue is an archive queue. Its useful-work flag is set only after publication.
Existing per-archive extraction completed/skipped/failed/unprocessed counts and
ADD accepted-source diagnostics remain intact.

## Qualification and memory

`tools/test_noah_outcomes.py` exercises 20 assembled-code transactions covering
clean work, no match, all declined, useful extraction before a failure, Retry,
Abort with a remaining archive, uncertain closure, mixed valid/invalid archives,
invalid usage, failed ordinary/compressed ADD sources, successful ADD after a
skipped source, standalone codec outcomes and companion-free queries. Existing
adapter, writer, codec, quiet and failure suites pass unchanged.

`tools/qualify_noah_codecs.py --outcome-reporting` builds all six exported modules
with unmodified ZSM4/LINK on both targets and requires machine-code parity with
the host build. The runtime campaign uses loaded terminal providers and checks
ordered outcomes for TEST, no-match LIST, mixed good/bad TEST, failed TEST,
invalid usage, SQ and ADD. Published codec bytes are independently decoded;
the created LBR's CRC and member directory are checked. Disposable disk images
are filesystem-checked, and source system/toolchain images remain unchanged.
See [receipt](NOAH-Outcome-Reporting.json) and its portable evidence archive.

Resident image: 17,964 bytes. Controller window: `4780h`; codec context: `4F80h`.
Controller: 17,632 bytes. Writer plans: `8C80h–A480h`; transformed identities:
`A480h–BE80h`. The largest required boundary is `BE80h`, leaving 1,665 bytes below
`C501h` (z80pack with providers) and 2,945 below `CA01h` (Model 4 with providers).
The 512-byte private stack remains reserved. Emulator evidence qualifies these
two software configurations; physical-machine testing is not claimed.

## Remaining reporting work

This increment does not close specification section 11 in full. A subsequent
bounded accounting increment must consolidate member/file counts across archives,
add ADD candidate/declined/failed/unprocessed accounting alongside accepted
versions, and explicitly total limited coverage and retained recovery artifacts.
It must preserve the existing detailed identities and avoid double counting
retries, failed-and-skipped objects and displaced source versions. ARK support,
release packaging and the deferred interactive browser remain separate work.
