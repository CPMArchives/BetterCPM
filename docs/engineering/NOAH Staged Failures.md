# NOAH staged-operation failure handling

Status: NOAH 1.0 revision 10, bounded failure-handling increment, 2026-10-25.
The [behavioral specification](NOAH%20Specification.md) remains normative.
This extends the [source-preflight choices](NOAH%20Safe%20Source%20Failures.md)
to established restart boundaries after staging. It adds no archive formats,
browser, OS services or Utilities Disk membership. Complete outcome accounting
and ARK remain separate work. The subsequent
[revision 11 reporting increment](NOAH%20Outcome%20Reporting.md) adds final command
outcomes and batch dispositions; the measurements below remain revision 10 evidence.

## Restart contract

Retry is a new complete attempt at the affected file, member or archive update,
never a continuation of partially written output. It requires:

- no publication attempt or unresolved stop/cancellation state;
- confirmed source/transaction input closure where the operation reopens inputs;
- confirmed output and verification-handle closure;
- no retained candidate or live candidate stage;
- observed absence of the attempted temporary filename, across all physical
  directory extents.

The publication boundary is sticky from entry to the checked publisher, including
its final identity checks before renaming. An error after that boundary never
re-enters authorization or construction, even if rollback restored the original.
Existing verified TMP/BAK preservation and exact recovery-name reporting remain
in force. There is no in-place fallback or automatic recovery/resume command.

The shared prompt remains `Retry/Skip/Abort? R/S/A [S]:`. Enter defaults to Skip;
`/Q` retains the prompt and diagnostics; `/Y` skips without waiting when the
boundary is safe, otherwise follows the conservative abort path. Repeated Retry
requires explicit user input. Abort preserves earlier completed work and leaves
remaining work unprocessed.

## Implemented boundaries and conservative stops

| Operation | Safe Retry | Safe Skip / stop policy |
| --- | --- | --- |
| Standalone codec/copy stage | Close input, remove a disposable stage, repeat source preflight, authorization, construction and independent verification | Skip advances the frozen source queue; retained or uncertain state prevents restart |
| Compressed ADD candidate stage, before appending its encoded data | Same complete candidate restart; earlier verified aggregate rows remain unchanged | Failed/declined candidate cannot displace an earlier accepted version |
| Ordinary LBR extraction, including opaque-member staging before expansion | Require the reader to remain `AS_SELECTED`; rewind only current member position/remaining length from its validated metadata, then repeat authorization and staging | Skip advances with the existing `LBR_NEXT` contract, which abandons an unread selected member |
| Uncompressed LBR ADD/REMOVE/COMPACT stage | After confirming source and old-archive close and removing the disposable stage, reconstruct the entire transaction from frozen identities and freshly checked inputs | Skip abandons this archive update; no member or retained region is silently omitted |
| Sticky reader error, live compressed-writer aggregate, or inner expansion-spool failure | No restart is offered across those states | Abandon the affected archive/transaction through existing cleanup; do not clear `AS_FAILED` to manufacture a trustworthy boundary |
| Publication, retained recovery data or uncertain close/name state | No restart | Preserve/report recovery state; unresolved handles or unconfirmed creation stop the frozen batch |

Retries do not advance the iterator, refreeze membership or increment completed/
failed counts for each attempt. For extraction, a member ultimately skipped
after an I/O failure is counted once as failed and prints `Skipped after failure.`;
it is not counted again in the authorization-decline skipped counter. Successfully
retried members count once as completed. Source read errors remain sticky and
stop that extraction rather than being treated as ordinary output failures.

## Cleanup and ownership

Cleanup clears an open flag only after successful close. A failed output or
verification close reports `Close unconfirmed: DU:NAME.TMP`, retains ownership
state and stops the batch. Archive-reader close failure also stops the batch;
the writer's old-archive flag is no longer cleared after a failed close. A later
archive cannot reset bookkeeping over an unresolved handle.

Disposable-stage deletion is followed by an existence check. A successful BDOS
delete return alone does not prove that every directory extent disappeared.
Existence checks now use the wildcard extent selector, independent of the FCB's
current EX field, so a surviving later extent cannot be mistaken for absence.

A failed MAKE may have left a directory name without confirmed ownership.
Restart requires observed absence; if the name remains, NOAH reports it and
stops without deleting or commandeering that unconfirmed file. Closed retained
artifacts remain collision-protected by normal pair selection. No filesystem
locking or power-failure atomicity is claimed; existing input verification and
the reader's validated metadata/phase contract remain in force.

## Qualification

`python3 tools/test_noah_staged.py` covers 19 assembled-code transactions:
whole-output Retry and independent byte checks; extraction cursor rewind;
trusted Skip, quiet/default/unattended choices and Abort; whole-archive
reconstruction; compressed candidate restart; sticky source-reader errors;
delete failure and false-success deletion; unconfirmed MAKE surviving only in a
later physical extent; retained/failed-close stages; publication rollback; and
batch stop on unresolved output/archive input handles. Existing adapter (137),
writer (38), codec (51), source-failure (21) and quiet (31) suites also pass.

`tools/qualify_noah_codecs.py --staged-failures` qualifies the native build and a
real disk-full output failure on both platforms with terminal providers loaded.
The disposable image is prepared nearly full, leaving four blocks for startup/
SUBMIT. A bounded native helper fills the remainder. NOAH then attempts the first
member, encounters an output failure, accepts Retry, fails safely again, accepts
Skip and extracts a subsequent zero-length member without allocating a data
block. Console checks verify the actual choices, one failed member, no
unprocessed members and a post-exit marker. The empty output and unchanged input
files are checked independently, and filesystem checks pass. Other fault types
are assembled-code host injections, not claimed native media failures.

Changed resident/controller modules are assembled with unmodified ZSM4/LINK on
both platforms; the four unchanged codec products are reused only after exact
byte/padding parity checks. Whole reconstructed companion parity also passes.
The resident image is 17,778 bytes, window 4680h and codec context 4E80h.
Controller code is 17,289 bytes; plans occupy 8A80h–A280h and transformed
identities A280h–BC80h. The maximum required end BC80h fits recorded active
ceilings C501h (z80pack) and CA01h (Model 4), with 2,177 bytes below the lower
ceiling. These measurements qualify the recorded provider combinations.

See the [receipt](NOAH-Staged-Failures.json) and
[portable evidence](NOAH-Staged-Failures-evidence.tar.gz). Full NOAH conformance,
complete outcome reporting, ARK and release-media acceptance are not claimed.
