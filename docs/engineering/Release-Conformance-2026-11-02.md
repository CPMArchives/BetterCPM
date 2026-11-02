# Release conformance refresh — 2026-11-02

Current status: cpmsim accounting reconciled; eleven native Model 4 groups
and the three targeted utility error/help screens passed. Remaining release
gates include profile review, documentation and fresh-package installation.

Candidate: `6d6c103507ce8558700b3b8e412ac500de361226`.
Independent suite: `a9a878fcd2e36698c7e856654a85847a004fdd20`.
All 13 independently rebuilt suite programs match the pinned checksum manifest.

## cpmsim results

All eleven reviewed returning groups completed without failed/error rows on
private copies of the exact packaged System image. FILETEST and DISKTEST used
prepared required-group full-disk fixtures. Canonical ownership yields 273 suite
passes, 115 not-run rows and 24 observations, rather than double-counting shared
prerequisites. Supplemental fresh runs cover console I/O, read-only recovery,
resident ecology, full-TPA return, batch input, directory-full DRI comparison,
error recovery, media replacement/reset, and CCP/gateway checks. Controlled
production-instruction tests cover BIOS/BDOS, character routing, protected
mutation, Function 37, documentary I/O and 112 retry cases.

Full 627-card accounting: 273 PASS_SUITE, 98 PASS_EXTERNAL, 56 PASS_CONTROLLED,
2 PASS_PROFILE, 3 PROFILE_DIFFERENCE, 1 OBSERVED_EXTERNAL_PROFILE, 24 OBSERVED,
119 NOT_RUN_NONGUARANTEED, 50 OUTSIDE_BASELINE and 1 NOT_APPLICABLE.
No required-card accounting entries remain unresolved. This is not 627 passes,
physical-device qualification, or final release acceptance.

Card 0020's strict uppercase-tail oracle failed: the current CCP preserves
`mIxEd.TxT` in the command tail while uppercasing the default FCB. Existing CCP
case-preservation work supports host paths. The original failed transcript is
retained. An explicitly selected profile rerun completed the remaining checks
and excludes 0020 from its passing-card list. It is a compatibility difference
requiring release documentation/review. The other two profile differences are
0493/0494, the previously documented fixed-A0 lookup rules.

Harness-only corrections: private pyte dependency installation; obsolete 0.90
banner waits replaced with the product prefix while exact candidate hashes
remain checked; explicit simulator arguments; Latin-1 native-listing decoding.
Initial failures and successful reruns remain separate. No guest source or
independent-suite predicate was changed. Production images were not rebuilt.

## Model 4 reconciliation and current block

Actual current member hashes match 33 previously tested shipped COM bodies;
STAT 006, CPX 007 and RSX 008 differ and need fresh native error-path checks.
Seven prior test tools are not shipped on these disks. Matching bytes retain
only their earlier bounded assertions, not a new whole-package boot verdict.
CRCKSUM uses its successful 009 follow-up receipt; the earlier failed capture
remains historical. The maintainer's STAT 006 transcript is a displayed PASS
with unspecified platform, so it is not assigned to Model 4 by inference.

After reconnection, a read-only LaunchServices lookup still returned 1100.
The prepared runner recorded BLOCKED_OR_INCOMPLETE before starting any emulator;
no native test ran. The receipt identifies Model 4 image SHA-256
`4105ff45e411e25c0f3cd6024b970ddc231e6287086a553933e1fb577aaf2467`.
The desktop Terminal runner executes all eleven reviewed native program names
in seven jobs on private copies and preserves the baseline. It does not claim
all external/device/manual assertions. Historical reduced manual scope remains
in force; unexecuted exhaustive checks have not become passes or new demands.

## Evidence

`evidence/2026-11-02-release-conformance/` contains the 627-card matrix, summary,
exact candidate and system receipts, Model 4 member-applicability comparison,
receipts/transcripts archive and SHA256SUMS.txt. Build-local original failures
and successful reruns remain preserved. Fresh Model 4 execution, changed utility
error paths, fresh-package installation and final publication acceptance remain
pending.

## Fresh native execution — 2026-11-02 15:06 run

The maintainer's Terminal batch at `~/Downloads/model4-conformance-20261102-150614`
passed all seven jobs covering eleven reviewed suite programs. The saved
receipts and screen summaries were inspected and bind candidate
`6d6c103507ce8558700b3b8e412ac500de361226` to baseline image SHA-256
`4105ff45e411e25c0f3cd6024b970ddc231e6287086a553933e1fb577aaf2467`.
Native directory/BDOS/file/random fixture, filesystem and System-member audits
passed. Aggregate summaries are not fabricated per-card native transcripts.
Evidence is retained in `evidence/2026-11-02-release-conformance/` as
`model4-native-pass.tar.gz` and `model4-native-summary.json` (relative to the
engineering documentation directory). Earlier blocked launches remain historical.

This closes the prepared native returning-group batch only. STAT 006, CPX 007
and RSX 008 invalid-option/error paths still need their targeted native check;
the suite programs do not exercise those utilities. External/device assertions,
profile differences and fresh-package installation remain separate acceptance
items. Historical reduced-scope agreements remain unchanged.

## Targeted Model 4 invalid-option screenshots — 2026-11-02

Following the explicit Model 4 test request, the maintainer supplied three
screenshots. Visual inspection confirms:

| Command | Observed revision | Result |
| --- | --- | --- |
| STAT /BOGUS | 1.0 (006-dev) | PASS: Invalid option, current usage and option help. |
| CPX /BOGUS | 1.0 (007-dev) | PASS: Invalid usage, current usage and help options. |
| RSX /BOGUS | 1.0 (008-dev) | PASS: Invalid usage, current usage and help options. |

These close the outstanding targeted native error/help presentation checks.
The image crops do not show returned CCP prompts, so prompt return is not
independently certified by these screenshots. Displayed revisions match the
current candidate; the screenshots alone do not independently prove mounted
image hashes. Broader conformance, fresh-package installation and final release
acceptance retain their separately documented scope. Earlier pending and
blocked entries above remain historical evidence.
