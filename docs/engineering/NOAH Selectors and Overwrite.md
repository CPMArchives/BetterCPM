# NOAH selectors and overwrite integration

Build 003 extends the [LBR integrity/extraction increment](NOAH%20LBR%20Integrity%20and%20Extraction.md).
This is development implementation, not full NOAH release qualification. The
[behavioral specification](NOAH%20Specification.md) remains authoritative.

## Implemented interface

```text
NOAH [/LIST] archives [member]
NOAH /TEST archives [member]
NOAH /EXTRACT archives [destination:pattern]
```

`/T` and `/X` are aliases. Operation switches may appear before or after operands;
identical repetitions are accepted, contradictory operations rejected. `/Y`, `/R`
and `/SYS` apply to extraction only. `/VER` and `/HELP` remain standalone. `/Q`,
codec/EXPAND modes and archive modification commands remain unsupported, with
usage diagnostics before archive I/O rather than partial interpretation.

Archive selection uses the existing `duselect.inc`, `filespec.inc`,
`operandqual.inc`, predicate portion of `attrselect.inc`, `rcpselect.inc` and
RCP's FCB constructor. There is one shared grammar, not a separate approximation:
compound drive/user selections, wildcards, DU-only defaults and boolean attribute
predicates are supported. As with current resident bindings, the supported drive
domain is A–D; unsupported drive requests fail before archive processing.

```text
NOAH /LIST B[0-31]:*.LBR README
NOAH /TEST [A0,B[1,3,8-10]]:*.LBR *.COM
NOAH /X B7:*.LBR[$ARC+!$SYS] C3:*.TXT
NOAH /X /Y B[-]:*.LBR A0:
```

Member filters are plain 8.3 wildcard patterns, without DU/attribute expressions.
`README` means exactly the extensionless member; it never implies `README.*`.
Extraction alone permits one destination DU before the pattern. A destination
DU without a pattern means all members, and an unqualified pattern uses the
captured caller DU. Multiple destination DUs are invalid.

## Frozen selection and identity

Before any archive open or output mutation, scan selected DUs and freeze concrete
archive identities. Logical files are deduplicated across physical extents and
overlapping DU terms; a predicate matching a later physical extent admits the
logical archive once. Sort drive, then user, then canonical filename. The queue
has 512 entries of 13 bytes each; exceeding it fails the whole selection before
any archive is processed. This is a measured bounded RAM implementation, not an
unbounded streaming promise. Sorting/insertion is quadratic; large-directory
performance remains a release qualification gate.

All members and output/recovery names are checked against the entire frozen
input set, including archives not processed yet. Newly created matching files
do not join the batch. Every archive/result/prompt/recovery identity includes
its drive and user. The captured caller DU and default DMA are restored on normal,
error and cancellation returns. Sources may be protected because they are read.

The CP/M file adapter captures its source user at OPEN. Random reads and source
close operations temporarily enter that user and restore the destination/caller
user even on failure. This matters when identically named files exist in several
user areas. Adapter workspace grows from 176 to 178 bytes; no resident storage
or BDOS/BIOS service is added.

## Member selection and audit coverage

`LBR_AUDIT` retains its all-member behavior. New `LBR_AUDIT_SELECTED` additionally
takes HL=predicate callback (zero means all). The callback receives IX=LBR context,
IY=audit workspace and current public member metadata; A=zero excludes content
checking, nonzero selects it. Preserve IX/IY, alternate bank and SP. The callback
must not mutate the reader or reenter it. `LA_NOT_SELECTED` is a separate 32-bit
count; other audit layouts and workspace size remain unchanged.

The directory and every active entry's structure, bounds, duplicate names and
overlaps are always checked. Only selected member data/CRCs are read. Thus an
unselected member's corrupt payload does not invalidate a selected-file TEST,
while unsafe container structure still blocks extraction. Reports distinguish
verified CRCs, unavailable/ambiguous CRCs and members not selected. No-match is
reported per archive; no output is created. LIST remains a metadata listing,
explicitly not a CRC test.

## Shared choices and authorization

`noahinput.inc` binds the common choice controller, event definitions and validation
hooks. Ordinary collisions offer immediate case-insensitive Yes/No/All/Cancel;
Enter means No, invalid answers retain/repaint the question, and ESC/Ctrl-C cancel
the whole operation. Ordinary All lasts for this command, including later archives.
It does not authorize protected replacements.

RO requires `/R`; SYS requires `/SYS`; both are required for both protections.
Each admitted protected object receives one separate default-No Y/N question
showing its actual RO/SYS state. No All is offered there. `/Y` authorizes ordinary
replacement without waiting for input, but always reports/skips protected objects,
even if `/R` and `/SYS` are also present. Missing override flags skip protected
objects without a question. Selected input archives cannot be replaced under
any authorization setting.

## Publication, protection and recovery

Authorization records protection across all physical extents and a first-entry
identity snapshot. Before changing an original, re-inspect and compare the
snapshot and attribute union; an unexpected target/identity change leaves the
verified temporary retained. This is bounded single-task CP/M checking, not a
concurrent filesystem lease or proof against arbitrary external media changes.

After staged data closes/reopens/byte-compares successfully:

1. If replacing, clear RO only at the authorized rename boundary, retaining the
   original's other attributes. Rename original to the reserved BAK and reapply
   its original protection there.
2. Recheck final absence and rename verified TMP to final. Restore original RO/SYS
   on the new final. The source archive is never renamed or modified.
3. Delete the original backup only after publication and required metadata succeed.
   Clear RO solely for the authorized backup cleanup; restore backup protection
   if cleanup fails and it remains. Report cleanup failure as a completed update
   with warning, without rolling back verified output.

Publication or metadata failure attempts a safe rename-back and restores original
protection. A verified replacement is retained under TMP when recoverable. If
rollback fails or a failed rename has nevertheless changed the namespace, stop
the batch, preserve both versions and identify recovery paths; never rename over
an unexpected file. Known original backups receive protection restoration where
possible. Unknown protection state is reported explicitly for manual recovery.
A temporary is reported as retained only if it is actually found; a failed
cleanup with an already absent backup is reported as absent, not fabricated as
a retained recovery file. No atomic multi-operation/power-loss guarantee exists.

The current failure path stops that archive; independent safe archives may
continue. Unsafe publication/protection recovery stops the entire batch. Interactive
Retry/Skip/Abort recovery and the remaining reporting refinements are still
pending. Batch output accounts selected/processed/failed/unprocessed archives;
member output accounts completed/skipped/failed/unprocessed selected members.
Warnings/skips/partial CRC coverage are explicitly marked.

## Qualification scope

The full Z80 harness covers sorted batches, predicates, multi-extent deduplication,
member filters, all 32 BetterCP/M user identities, cross-user reads/writes,
512-entry overflow before any open, input freezing, defaults/invalid choices/
cancellation/All, `/Y`, RO/SYS combinations, metadata failures, rename-back failure,
reported rename failure after actual movement, and cleanup failures. Inputs and
preexisting recovery files are independently checked; failures preserve originals
or retain/reveal the actual recovery files. Native stock CP/M workflow checks
and measurements are recorded separately with source/binary hashes.

Still pending: BetterCP/M platform execution (including native Model 4), native
ZSM4 expansion, historical LBR interoperability and early garbage-directory-CRC
handling, exhaustive unavailable-media/recovery behavior, timestamp services,
`/Q`, codecs, ARK, archive updates and overlays. These checks do not requalify the
core OS or declare the Utilities Disk complete.

### Build 003 results

All 123 library cases, 128 full-Z80 command/adapter cases and 17 stock CP/M
commands passed. The deterministic binary is 19,574 bytes; the observed harness
stack maximum is 32 bytes with BDOS intercepted, not a native stack bound.
The archive adapter context is 178 bytes. Both disposable emulator disks passed
independent read-only filesystem checks.

The stock template lacks STAT.COM, so the protection smoke test uses a test-only
BDOS attribute helper and requires the explicit `[RO]` prompt. This avoids treating
an unsuccessful attempt to set protection as successful qualification.

Exact source/binary hashes and scope limits are recorded in
[the Build 003 check record](NOAH-Selectors-Overwrite-Checks.json).
