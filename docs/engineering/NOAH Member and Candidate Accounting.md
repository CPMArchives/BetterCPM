# NOAH member and candidate accounting

Status: NOAH 1.0 revision 12, bounded reporting increment, 2026-10-26.
The [behavioral specification](NOAH%20Specification.md) remains normative.
This extends [final command outcomes](NOAH%20Outcome%20Reporting.md) with extraction
batch totals and ADD candidate accounting. It adds no archive operations, formats,
prompts, disk access, browser or release-disk membership.

## Extraction totals and their limits

After each validated extraction archive reaches its existing summary, NOAH folds
its completed, skipped, failed and unprocessed member counts into one batch total.
The final `Known members (hex)` line reports completed, skipped and failed members;
the following `Unprocessed (hex)` line reports the remaining inventoried members.
These lines remain visible under `/Q` and precede the final logical outcome.
Per-archive member summaries and archive selected/processed/failed/unprocessed
counts remain visible.

The totals describe **inventoried, selected extraction members**, not an invented inventory
of archives that were never opened or failed the required pre-extraction audit.
An unattempted archive remains in the archive queue's unprocessed count; its
unknown members are not reported as zero members of work. Similarly, an archive
that fails pre-extraction validation is a failed archive without a fabricated
member count. LIST/TEST retain their existing per-archive listing/audit reporting;
these new member totals apply to extraction.

A successful member Retry contributes once to completed. A member ultimately
skipped after an I/O failure contributes once to failed, rather than both failed
and skipped. Declined/protected output contributes to skipped. Cancellation
preserves prior completed members and leaves the rest of the current validated
inventory unprocessed, with later archives still unprocessed at archive level.
No further archive or member reads are performed to manufacture totals.

## ADD candidates versus accepted and published changes

The frozen source queue has one final two-bit state per candidate. The 512-entry
limit uses 128 bytes of state, independent of source-file length. State survives
codec overlay loads and the compressed-ADD preparation/writer boundary. Reporting
never changes frozen identities, writer plans, archive contents or recovery state.

The final `ADD candidates (hex)` line and following `Unprocessed (hex)` line
partition that queue:

| Candidate category | Meaning |
| --- | --- |
| Completed | Its accepted version is an active member of the successfully published archive |
| Skipped | Declined, protected/excluded, or superseded by a later accepted version; also prepared work declined before publication |
| Failed | Its source preparation/read/close ultimately failed |
| Unprocessed | Not reached, or prepared/accepted work left unpublished because the transaction failed or was cancelled |

`Accepted candidates (hex)` counts accepted source versions in the successfully
published plan, including versions subsequently superseded in that plan. It is
not added to the partition. It remains zero if publication did not succeed; a
verified compressed candidate is only preparation, not yet an accepted change. For example, two same-name sources
accepted in order and successfully published produce accepted=2, completed=1,
skipped=1. This remains true when normal LBR update policy retains the superseded
version's deleted payload. A compacted archive may discard that payload; it does
not turn a superseded candidate into another active completed member.

An archive-output failure is still a failed archive transaction. Its prepared/accepted
sources remain unpublished/unprocessed candidates, rather than being relabelled
as source-read failures. A complete transaction Retry resets the ordinary ADD
candidate attempt state and counts only the final attempt. Compressed ADD retains
preparation failures through the writer phase, which cannot relabel them as simple
skips. A recovered source Retry ultimately contributes one accepted/completed
candidate. Failed source plus Abort counts that source once as failed and later
sources as unprocessed. No ordinary source failure can displace an earlier
accepted version.

The existing `Accepted source versions` publication diagnostic remains unchanged.
The new candidate report distinguishes those versions from active published
members. Skipped/superseded final candidates produce warning/partial when useful
work completed, rather than a clean-success outcome. Counts use eight hexadecimal
digits for candidate/member categories and four for the bounded accepted count.
The new summary lines fit within 80 columns.

## Qualification and memory

`tools/test_noah_accounting.py` covers 18 assembled-code transactions: successful
ADD; source and whole-transaction Retry; source failure versus unpublished output;
declined replacement; protected-target refusal after compressed preparation;
Abort with a remaining source; compressed SQ/CR preparation
failures; same-name supersession in ordinary and compressed ADD; packed-state
byte boundaries; all 512 failed candidate identities; multi-archive extraction;
quiet output; member Retry; and cancellation with a remaining archive. File bytes,
active member counts and existing harness memory/stack guards remain checked.
Existing adapter, writer, codec, quiet, source/staged failure and final-outcome
suites pass unchanged.

`tools/qualify_noah_codecs.py --member-accounting` qualifies all six modules with
unmodified ZSM4/LINK on both platforms and checks machine-code parity against the
host build. The final resident/controller are rebuilt; the four codec products
are reused from the preceding native campaign only after exact machine-code
comparison. Their original build logs and products are retained in the evidence. With terminal providers loaded, the runtime campaign
extracts three members from two libraries in one batch, adds two ordinary sources,
and adds two squeezed sources. It checks exact extraction bytes, both created
LBR directories and CRCs, and independently decodes the compressed payloads.
Disposable disks are filesystem-checked and the original system/toolchain images
remain unchanged. See [receipt](NOAH-Member-Accounting.json) and its portable
qualification evidence archive. Physical hardware testing is not claimed.

Resident image: 18,207 bytes; controller: 18,095 bytes. The overlay window is
`4880h`, codec context `5080h`; writer plans occupy `8F80h–A780h`, transformed
identities `A780h–C180h`. The largest required boundary is `C180h`, below loaded
provider ceilings `C501h` (z80pack, 897 bytes spare) and `CA01h` (Model 4, 2,177
bytes spare). The private stack remains 512 bytes. No TPA ceiling is raised.

## Remaining work

This increment closes extraction batch totals and ADD candidate accounting within
the stated inventory limits. Specification section 11 is not closed in full:
consolidated LIST/TEST coverage reporting and explicit retained recovery-artifact
totals remain. Existing detailed CRC limitations and recovery filenames remain
visible. ARK, release qualification/packaging and the deferred interactive browser
are separate work; NOAH is not yet a complete release-disk utility.
