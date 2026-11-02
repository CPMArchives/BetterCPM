# Utility finalization — 2026-11-02

Status: implementation, focused host/cpmsim checks and all 45 bounded Model 4
checks pass. Updated release packaging and final acceptance remain pending. This record does
not transfer historical runtime passes onto new executables.

## Corrections

CPX and RSX now normalize a private command-tail copy, folding ASCII lowercase,
converting TAB separators to spaces and trimming trailing whitespace. LIST,
LOAD and UNLOAD retain their exact keyword and operand rules. Original command
tails are preserved. Explicit zero-filled scratch storage makes native and
cross assembly identical. Bare invocation remains usage; /LIST is not a new alias.

STAT gains a standard quick-reference screen with /HELP and /H. The revision
does not introduce the proposed post-1.0 STAT MEM redesign. Existing operational
interfaces are retained.

The owned transient utilities now recognize exact /H and /HELP as equivalent
case-insensitive help queries, before /VER and operations. New help screens
cover utilities that previously had version queries only. Existing specialized
help screens retain their operational options. PIP bracketed S/Q string data
and SEARCH quoted patterns stay literal; interactive H commands are untouched.
The common help recognizer uses one matcher, without an additional query-call
stack level. DDT's enlarged startup text fits an explicitly enlarged bootstrap
area; original debugger core adaptation and relocation guards pass.

CONFIG, NOAH, MOUNT and R/W already support /H and are unchanged here.
Unmodified ZSM4 and LINK retain their historical syntax. RCP resident commands
are not changed by the transient help rollout: use :DIR /H or :COPY /HELP to
select the full transient interface. No /V-as-version rollout is introduced.

## Revision assignments

Each changed executable advances once. These assignments are development
identities, not platform or release acceptance. Exact artifact hashes and
selected input dependencies accompany the receipts.

| Utility | Revision |
| --- | --- |
| STAT | 004 → 005 |
| CPX | 005 → 006 |
| RSX | 006 → 007 |
| DIR | 011 → 012 |
| USER | 007 → 008 |
| CLS | 008 → 009 |
| VER | 009 → 010 |
| COPY | 009 → 010 |
| MOVE | 001 → 002 |
| ERA | 006 → 007 |
| REN | 010 → 011 |
| TYPE | 008 → 009 |
| TIME | 004 → 005 |
| DUP | 008 → 009 |
| SYSGEN | 009 → 010 |
| ED | 004 → 005 |
| SUBMIT | 004 → 005 |
| XSUB | 004 → 005 |
| PIP | 030 → 031 |
| DLINK | 001 → 002 |
| DUMP | 007 → 008 |
| DASM | 002 → 003 |
| DSYM | 002 → 003 |
| TED | 002 → 003 |
| ADMTST | 005 → 006 |
| VT52TST | 005 → 006 |
| ANSITST | 004 → 005 |
| SYSBUILD | 004 → 005 |
| RESPACK | 004 → 005 |
| RLMBUILD | 004 → 005 |
| WARM | 001 → 002 |
| DDT | 003 → 004 |
| COMPARE | 003 → 004 |
| CRCKSUM | 008 → 009 |
| MD5SUM | 002 → 003 |
| PATCH | 001 → 002 |
| SEARCH | 001 → 002 |
| SQ | 005 → 006 |
| USQ | 005 → 006 |
| CR | 005 → 006 |
| UNCR | 005 → 006 |
| LZH | 005 → 006 |
| UNLZH | 005 → 006 |
| BYE | 002 → 003 |

## Validation

- PASS: 37 compiled help screens and 316 alias/precedence/manager parser cases,
  current revision prefixes, 23-line/79-column bounds and preserved command tails.
- PASS: four existing DUMP/DASM/DSYM/TED help paths, 24 compiled cases.
- PASS: COMPARE 94 cases; CRCKSUM 135 fixtures; MD5SUM 88 fixtures; PATCH 88 scenarios.
  Consult saved logs for exact counts rather than assuming unchanged test totals.
- PASS: SEARCH regression, PIP parser/literal handling, 368 full-Z80 codec cases,
  DDT core/input checks, STAT parser/devices/capacity checks, BYE's 74 cases,
  registry projections and 12 input-isolation tests.
- PASS: native ZSM4/LINK parity for current CPX (1498 bytes) and RSX (1570 bytes).
- PASS: actual cpmsim boots and help/alias precedence for all 44 changed utilities;
  CPX/RSX lowercase, trailing-space LIST executed. Each case uses private media;
  read-only utility media and the original system image are preserved.
- Primary Utilities allocation remains 328 KiB, within its current 332-KiB format.

The initial native comparison found different assembler DS padding, fixed with
explicit initialized bytes. The initial cpmsim run caught stale ED build output
at revision 004; ED was rebuilt as 005 and passed in the continuation. Earlier
passed cases were reused only after checking their exact artifact hashes.
One input-isolation test used the newly assigned revision as its supposedly
changed fixture; it now increments the actual baseline revision and passes.
Legacy tools/test_utility_versions.py predates several current query/rendering
interfaces and is not a passing suite claimed by this record; applicable query
paths are checked by the focused and utility-specific suites above.

## Evidence and remaining work

[Receipts and logs](evidence/2026-11-02-utility-finalization/receipts-and-logs.tar.gz)
include input/output hashes, native transcripts, both cpmsim run receipts and
per-case transcripts. The adjacent SHA256SUMS.txt binds the archive.
No full disk images are checked into this evidence bundle.

`tools/run_utility_finalization_smoke.py` prepares private Model 4 media from
current binaries. Its prepare-only run and filesystem check pass. At that preparation stage,
Terminal-launched execution was PENDING; the completed runs are recorded below.
The runner checks 43 help paths and two
manager LIST cases, records component/image/emulator hashes and captures screens.
Do not repeat the blocked agent GUI launch path.

Release candidate archives and the maintainer's stable image collection have
not been refreshed. Changed binaries need accepted affected-platform evidence,
matching updated packages and regression applicability review before release.

## First Model 4 run — 44 PASS, CRCKSUM help height FAIL

Run `/Users/nathanael/Downloads/model4-utility-finalization-20261102-093709`
executed all 45 cases. Forty-four passed the automated text/identity/media checks,
including both lowercase, trailing-space manager LIST commands. The final
original-image preservation check passed. CPX lists RCP.CPX; RSX lists M4SCRN
and ADM3A; both report 50K TPA. These captures were visually inspected.
The raster captures can have the previously recorded display dropouts; automated
text checks alone are not a blanket visual certification of every help screen.

CRCKSUM 009-dev printed its 23-line help, but subsequent newline/prompt output
scrolled the title off the 24-row display. This is a help-height defect, not
evidence that a different executable ran. Its failed identity assertion and
original capture are preserved unchanged. The layout now groups SUM8/SUM16 and
KERM6/KERM12 on paired option rows, retaining all algorithm names/descriptions
while reducing help to 21 lines. A build-time height/width guard enforces the
limit. No additional revision is assigned within this uncommitted change set.

All other tested component hashes still match current binaries; only CRCKSUM's
hash changed. Its new COM SHA-256 is
`fdad82f035da2d8611279adb1161bd81afd4c527ad58d6d01d9bd91dba61d3c0`.
Retest only CRCKSUM with the runner's `--only crcksum` selector. Its prepare-only
filesystem check passes; actual changed-binary Model 4 execution remains PENDING.
Initial receipts and captures are preserved in
[evidence/2026-11-02-utility-finalization/model4-initial-receipts-and-captures.tar.gz](evidence/2026-11-02-utility-finalization/model4-initial-receipts-and-captures.tar.gz).

The shortened CRCKSUM help also passes a fresh cpmsim execution and all 135
compiled CRCKSUM fixtures. Follow-up receipt/transcript/log are in
[evidence/2026-11-02-utility-finalization/crc-help-height-followup.tar.gz](evidence/2026-11-02-utility-finalization/crc-help-height-followup.tar.gz).

## CRCKSUM Model 4 retest — PASS

Run `/Users/nathanael/Downloads/model4-crcksum-help-20261102-115107`
passes the shortened CRCKSUM 009-dev help check. The agent inspected both
screen memory and the final raster capture: identification, all algorithm
options, /H /HELP, /VER and returned A0> remain visible on one screen.
The receipt matches current COM SHA-256
`fdad82f035da2d8611279adb1161bd81afd4c527ad58d6d01d9bd91dba61d3c0`.
All other component hashes were rechecked against the initial run and remain
unchanged. Combined evidence therefore closes all 45 bounded Model 4 checks
(43 help/query checks plus two manager LIST checks). The initial CRCKSUM failure
remains historical evidence; it is not relabeled PASS.

[Retest receipt and captures](evidence/2026-11-02-utility-finalization/model4-crc-help-height-pass.tar.gz)
are preserved with checksums. This closes the affected smoke scope only, not
full per-utility operational qualification or final packaged release acceptance.

## Invalid-command help follow-up

The maintainer observed CPX 006-dev `/BOGUS` printing the obsolete one-line
usage string. RSX had the same fallback. CPX 007-dev and RSX 008-dev now
print `Invalid usage.` followed by their full current help on malformed or
missing commands. Explicit `/H` and `/HELP` retain their existing precedence.

Cross-builds passed. The compiled-COM regression suite passed 37 help screens
and 324 alias, precedence and manager parser checks, including `/BOGUS`,
`LISTX`, `LIST BAD`, missing LOAD/UNLOAD operands and an empty command tail.
These rejection paths issue no manager control requests and preserve the
command tail. The Function 177 v2 workspace contract and registry checks passed.

Exact new binaries:

- CPX.COM: `09132ee1178ab46a68ee5159697d489ca280f589ac835c9784d018234b40c24f`
- RSX.COM: `2dd217cc3c07a4d281713e322603c730413da551e51cfbcff749b4c070acdf87`

These are host Z80 execution results. The previous Model 4 results apply to
the earlier revisions; Model 4 validation of these changed error paths and
incorporation into a new release candidate remain pending. Existing candidate
packages and the image collection have not been replaced by this follow-up.
