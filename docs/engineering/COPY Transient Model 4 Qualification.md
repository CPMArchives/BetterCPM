# Transient COPY — Model 4 Qualification

Date: 2026-10-10

This campaign tests the frozen 10,303-byte COPY.COM on trs80gp with Model 4
SYSTEM source media and DATA destination media. COPY, BIOS, and BDOS remain
unchanged. The planned transient COPY functional campaign is complete on this
target. Final release-image conformance and performance work remain separate.

## Completed first case

`COPY /B /V A1:S*.DAT B3:[$RW,!$ARC]` copied eight files with every combination
of R/O, SYS, and ARC source attributes. The set includes an empty file, six
128-byte files, and a 33,280-byte file spanning three physical extents.

The saved output reports `8 FILES COPIED [46K]`, including `[0K]` for the empty
file and `[34K]` for the multi-extent file. Independent inspection of the final
images confirmed exact destination contents, R/O cleared, ARC cleared, SYS
preserved, and unchanged source contents and attributes. Reserved source tracks
and an unrelated destination sentinel remained unchanged.

- COPY SHA-256: `c0c6ee7cde8eedd32f3fb7a7ca42b67a0def6de81ff3c8ed8cee3a1d8a1e9b27`.
- Evidence bundle: `/private/tmp/copy-model4-attributes-bundle-20261010`.
- Manifest SHA-256: `3be9994dfb5baf83ff11379787f0d023306f8bf3dfb285b9fb8b7855e94ba83c`.

The first driver matched its completion text in SUBMIT's command echo and closed
before the final prompt. COPY's completion summary and final media were checked
independently; this result does not claim a successfully observed final prompt.
The revised harness uses a private FINISH.COM helper so the marker appears only
as executed output, adds settling time before exit, and allows 30 minutes per case.
It preserves old captures on retry and checks ordinary source data and attributes.

## Completed short campaign

All ten cases passed with the revised completion marker and a final A0 prompt:

| Case | Qualified behavior |
| --- | --- |
| predicates | ARC and SYS predicate conjunction, inherited metadata |
| du-sets | Nested user selections and a user-only term inheriting the caller drive |
| duplicate | Cross-DU duplicate destinations rejected before writes |
| overlap | Selected-source overlap rejected before writes |
| bad-wild | Characters following a terminal star rejected |
| bad-user | User 32 rejected |
| bad-dest | Multiple destination users rejected |
| bad-attrs | Opposite destination attribute assignments rejected |
| bad-option | Unknown global option rejected |
| no-match | No-file diagnostic, no copy summary, no destination mutation |

Every case checked source contents and attributes, reserved source tracks, and an
unrelated destination sentinel. Rejected-input cases additionally compared the
complete destination image with its initial image. Duplicate-destination rejection
also preserved the entire destination image.

- Evidence bundle: `/private/tmp/copy-model4-short-bundle-20261010`.
- Manifest SHA-256: `518205c951ecf9ebafaf3da973804befb7235f34d1ebb4f90968b42797a28a75`.
- All 207 inventoried files were verified against their recorded sizes and hashes.

## Completed mapping and interactive campaign

Thirteen further cases passed with executed completion markers and final A0
prompts. Mapping, backup, batch collision, and skip cases used the smaller
256-byte S007 fixture; the separate multi-extent case above remains the evidence
for large-file copying and verification.

| Case | Qualified behavior |
| --- | --- |
| backup | Successful verified copies clear source and destination ARC; `/BACKUP` overrides destination `[$ARC]` |
| mapping | Positional destination substitution and collapsed terminal stars |
| batch-collision | Existing writable and read-only destinations fail individually; other copies continue |
| skip | Writable collisions skip; read-only destinations fail without replacement |
| interactive-choices | Y/N, help, invalid responses, and ordinary interactive behavior under SUBMIT |
| interactive-overwrite | O applies to the current invocation and resets before the next COPY |
| interactive-skip | S applies to the current invocation and resets before the next COPY |
| collision-abort | Ctrl-C retains completed copies and preserves later destinations |
| overwrite-readonly | `/O` and destination `[$RW]` cannot override read-only protection |
| backup-skip | Skipped sources retain ARC; successful source/destination pairs clear it |
| rename-validation | Invalid names reprompt, selected-target conflicts are rejected, blank input returns to collision handling |
| rename-existing | An existing renamed destination uses ordinary collision handling |
| rename-abort | Ctrl-C at the rename prompt aborts without destination mutation |

Every case independently inspected source and destination contents and attributes,
reserved source tracks, and the unrelated destination sentinel. The harness
counts distinct collision prompts across captures, rather than counting the same
prompt again each time it appears in a saved screen.

- Evidence bundle: `/private/tmp/copy-model4-interactive-bundle-20261010`.
- Manifest SHA-256: `1abca1855046223cf43e1b9b8c13f7f34ea3e1155c2214e6c9ebfd5d4245ff72`.
- All 343 inventoried files were verified against their recorded sizes and hashes.

## Completed recovery and boundary campaign

All eighteen remaining cases passed with completion markers and final prompts:

| Cases | Qualified behavior |
| --- | --- |
| fault-read, fault-write, fault-close | Failed destination cleanup, continuation, and backup ARC changes only for successful files |
| fault-full, fault-cleanup | Stop on no space or failed cleanup; retain earlier completed files |
| verify-batch-failure | Remove unverified destinations, preserve source ARC, continue in batch mode |
| verify-skip, verify-abort, verify-retry | Help and interactive responses; retry performs the real comparison before clearing ARC |
| fault-destination-metadata, fault-source-metadata | Retain valid data, report incomplete attribute status, preserve source ARC |
| cancel-transfer, cancel-verification | Actual BREAK/ETX input removes the current incomplete/unverified destination, retains completed copies, and permits a subsequent COPY |
| caller-user31 | Qualified A0:COPY executes for an A31 caller, writes B31, and restores A31 |
| capacity-64, capacity-65 | Copy 64 empty files; reject 65 before any destination mutation |
| directory-full, allocation-full | Real media exhaustion stops copying and preserves unrelated data and raw directory entries |

Controlled-failure cases use private binary copies with narrowly placed fault
hooks, not a changed production COPY.COM. Each case saves its tested binary and
hash separately from the production identity. Verification retry runs the real
comparison; cancellation uses actual keyboard input at a private polling gate.
The media-exhaustion and capacity cases use the unmodified production binary.

The caller-user31 script explicitly qualifies COPY and FINISH as A0 commands.
An initial unqualified script could not locate its A0 test programs after
switching to A31; its captures are retained as a harness setup failure, not a
COPY failure. Successful evidence comes from the corrected script.

- Evidence bundle: `/private/tmp/copy-model4-recovery-bundle-20261010`.
- Manifest SHA-256: `b1a5e806464dbbc5cb5ac782ab31ccbe8c6332f4d953f226b825307bde5089d8`.
- All 380 inventoried files were verified against their recorded sizes and hashes.

## Input and scope

Native SUBMIT supplies bracket and exclamation characters not currently produced
by the Model 4 keyboard translation. Literal dollar signs are escaped as `$$`.
This exercises the native command-file input path without changing the keyboard
or core implementation. FINISH.COM is a test helper, not a shipped utility.

The Model 4 campaign now covers 42 cases: the initial multi-extent case, ten
short cases, thirteen mapping/interactive cases, and eighteen recovery/boundary
cases. The completed z80pack campaign remains separately documented. This closes
transient COPY implementation and its planned functional qualification; automatic
handoff, RCP selector expansion, final release conformance, and the deferred
performance investigation are separate work.

## Deferred performance investigation

The verified multi-extent case took several minutes. Destination inspection
confirmed that all 33,280 bytes had been written while the command remained
active. No stage timing was collected, so the cost cannot yet be attributed
specifically to verification, copying, or floppy timing. At the user's request,
performance work is deferred. A later first comparison should use fresh media
and the same command without `/V`; no such rerun is included in this increment.
