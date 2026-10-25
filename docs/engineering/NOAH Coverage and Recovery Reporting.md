# NOAH coverage and recovery reporting

Status: NOAH 1.0 revision 13, bounded reporting increment, 2026-10-26.
The [behavioral specification](NOAH%20Specification.md) remains normative.
This follows [member/candidate accounting](NOAH%20Member%20and%20Candidate%20Accounting.md).
It adds summary information for existing operations, with no new archive formats,
commands, prompts, disk access, recovery actions or release-disk membership.

## Observed listing and audit coverage

LIST and TEST now finish with a `Listed members (hex)` count across attempted
archives. This counts selected entries actually enumerated for display, including
entries displayed before a later archive read/close failure. It is not a claim
that all selected archives were fully enumerated; existing archive-level failed
and unprocessed counts remain authoritative for the incomplete queue.

LIST explicitly prints `LIST: contents not tested.` It does not acquire a CRC or
content-readability claim merely by listing entries. TEST and EXTRACT instead
print `Known CRC regions (hex)`, with verified and unavailable/ambiguous counts,
and an aggregate `Members not selected (hex)` count. All remain visible under `/Q`.

The shared audit counts **directory plus selected active-member CRC regions**,
not just members or logical files. CRC zero remains unavailable/ambiguous, even
when it could be the mathematical checksum zero. A region counts as verified
only after its advertised nonzero CRC passes. Excluded members count separately
in not-selected; the audit still validates their directory metadata and overlaps.
No inner codec decode is implied by an outer LBR CRC result.

The summary accumulates the audit counters even when the audit fails partway
through. For example, a valid directory and first member followed by a bad second
member CRC contribute two verified regions, while the archive remains failed.
The failing region and later unknown work are not invented as verified, missing
or zero-length members. Archives never attempted contribute no observed coverage.
The existing error diagnostics, archive dispositions and logical outcome continue
to identify incomplete work; a known-count total is not an all-pass certificate.
The reporting hook preserves the audit's original error code and carry flag.

ADD/REMOVE/COMPACT retain their existing update-preflight audit diagnostics. These
new consolidated CRC counters cover LIST/TEST/EXTRACT, not writer-preflight
attempts. Whole-update retries therefore do not inflate a reported audit total.

## Distinct recovery artifacts reported

Every command that enters ordinary selection now prints `Recovery artifacts reported (hex)`, including
zero, before its final outcome. The count covers reported temporary output names,
retained backups, expanded-member input spools and compressed-ADD aggregate
spools. Existing exact DU/name diagnostics remain visible and unchanged.

A per-name-role latch prevents repeated cleanup/reporting of the same current
artifact from incrementing the count twice. Temporary/backup latches reset when
a new output transaction begins; the expansion-spool latch resets when a new
spool takes ownership of an opaque member. The aggregate spool has one lifetime
per ADD command. Collision-safe generated temporary/backup names prevent reusing an earlier
retained artifact as a new staging name. A retained backup and
retained new temporary output count as two distinct artifacts.

This is a count of **recovery artifacts reported**, not a fresh filesystem
inventory or a recovery instruction. In particular:

- an observed temporary name after unconfirmed MAKE can be counted without
  claiming ownership or deleting it;
- a failed/uncertain handle close remains a failure even if no retained filename
  is subsequently observed; zero does not certify that recovery is unnecessary;
- a cleanup result reporting the backup already absent is a warning, not a
  retained artifact;
- output publication followed by backup cleanup failure remains useful completed
  work with a warning, rather than an unreported failure of the published output.

Counting changes no ownership flag, open/close decision, deletion, rollback,
restart boundary or cancellation behavior. It performs no additional disk reads
and never authorizes automatic cleanup. `/VER` and `/HELP` remain independent of
the companion and do not print these ordinary-command summaries.

## Qualification and memory

`tools/test_noah_coverage.py` covers 15 assembled-code transactions: untested
listing; mixed verified/missing CRC batches; member-filter exclusions; partial
CRC failure; extraction coverage; retained/de-duplicated temporary output;
unconfirmed close; failed rollback with backup and stage; successful publication
with retained backups across distinct transactions; cleanup with no retained
artifact; expansion spool and compressed-ADD aggregate retention; and resident
queries. The existing adapter, writer, codec, quiet, source/staged failure,
outcome and member/candidate suites pass unchanged.

`tools/qualify_noah_codecs.py --coverage-recovery` assembles and links all six
modules natively with unmodified ZSM4/LINK on z80pack and Model 4 and requires
machine-code parity with the host build. With terminal providers loaded, its
runtime campaign checks LIST, TEST, mixed valid/missing/bad-CRC archives, a member
filter and extraction. It checks observed partial coverage, warning outcomes,
zero-recovery summaries and exact extracted bytes. Nonzero recovery scenarios
are host-side fault injection on the assembled Z80 program, not claimed native
media failures. Disposable disks are filesystem-checked and original system/tool
images remain unchanged. See the [receipt](NOAH-Coverage-Recovery.json) and its
portable evidence archive. Physical hardware qualification is not claimed.

Resident image: 18,335 bytes; controller: 18,343 bytes. Overlay window `4900h`,
codec context `5100h`; writer plans `9100h–A900h`, transformed identities
`A900h–C300h`. Largest required boundary `C300h` leaves 513 bytes below `C501h`
(z80pack with providers) and 1,793 below `CA01h` (Model 4 with providers). The
512-byte private stack remains reserved. No TPA ceiling is raised. The audit and
listing counters reuse storage occupied by ADD's packed candidate map only in
mutually exclusive command modes; they do not overlap a live ADD map or codec.

## Status and remaining scope

The consolidated LIST/TEST/EXTRACT coverage summaries and recovery-artifact
summary gates for the currently implemented LBR/codec commands are now closed
within these observed-inventory limits. This is not full NOAH specification or
release acceptance: ARK operations, format-specific reporting/qualification and
release packaging remain. The interactive browser stays deferred. Third-party
ZSM4/LINK remain external tools and are not assigned BetterCP/M-owned revisions.
