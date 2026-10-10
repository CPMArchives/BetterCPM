# Transient COPY — Model 4 Qualification

Date: 2026-10-10

This campaign tests the frozen 10,303-byte COPY.COM on trs80gp with Model 4
SYSTEM source media and DATA destination media. COPY, BIOS, and BDOS remain
unchanged. This is a qualification increment, not final release conformance.

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

## Input and scope

Native SUBMIT supplies bracket and exclamation characters not currently produced
by the Model 4 keyboard translation. Literal dollar signs are escaped as `$$`.
This exercises the native command-file input path without changing the keyboard
or core implementation. FINISH.COM is a test helper, not a shipped utility.

The remaining mapping, collision, backup, interactive, cancellation, capacity,
and controlled-failure coverage must be recorded before declaring the Model 4
campaign complete. The completed z80pack campaign remains separately documented.

## Deferred performance investigation

The verified multi-extent case took several minutes. Destination inspection
confirmed that all 33,280 bytes had been written while the command remained
active. No stage timing was collected, so the cost cannot yet be attributed
specifically to verification, copying, or floppy timing. At the user's request,
performance work is deferred. A later first comparison should use fresh media
and the same command without `/V`; no such rerun is included in this increment.
