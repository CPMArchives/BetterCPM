# Five-download candidate assembly — 28 October 2026

Five review-only archives were assembled from source commit
`021f53143292e80f2739b7c99f3e6e180816d6fd`. They are not accepted releases.
The [assembly receipt](Candidate-Assembly-2026-10-28.json) records their names,
exact hashes/sizes, platform image identities and qualification scope. Later
commits recording evidence do not silently change those archived sources.

The archives are System for cpmsim, System for Model 4, Utilities for both
platforms, Source and Documentation. Candidate names end in `-candidate.zip`;
no final tag, release asset or acceptance baseline was published. Each archive
contains README, RELEASE.json, per-file checksums and the applicable source,
manual, licensing and build companions. The release-wide candidate index and
checksums cover final ZIP bytes. Independent ZIP membership/readback checks pass.

Both System images were built in separate private source snapshots. CONFIG has
platform-specific descriptors, so a cpmsim-built CONFIG must not be selected for
the Model 4 image. The initial v2/v3 preparation did that and is withdrawn; those
unaccepted files and failure evidence remain under the local superseded output
directories. The final assembly uses the platform's own build and component
release record. Model 4 filesystem/construction checks pass, while its runtime
result remains PENDING manual execution. No trs80gp launch was attempted.

Fresh macOS Utilities assembly and the independent verifier pass exact membership,
allocation, complete record readback and DMK/raw conversion for both primary and
companion images. The original Linux cpmcp SIGABRT remains historical evidence;
this establishes successful assembly with the recorded macOS inputs/tools, not
a diagnosis or repair of the Linux tool and not native Model 4 qualification.

The cpmsim host kit and Source ZIP include the exact pinned upstream Git bundle.
A separate private ref is used for bundling without changing the user's upstream
repository. The offline restoration regression proves that an older pin can be
restored even when the source checkout is at a later commit. Extracted BetterCP/M
sources use SOURCE-IDENTITY.json rather than an unrelated enclosing Git checkout.

The actual packaged cpmsim host kit was extracted, its bundled upstream restored
offline, and its emulator rebuilt. Patched source inputs and executable hashes
match the checkout reconstruction. Actual packaged A:/B:/C:/D: copies boot and
execute directory/version queries and BYE. All 30 shipped System files and the
reserved system tracks remain unchanged. B:/C:/D: are byte-identical; A: changes
only at the deleted startup $$$.SUB entry and its freed command record, as
expected from SUBMIT STARTUP. Filesystem checks pass. Earlier test-oracle failures
are retained: DUMP/NOAH use their own existing identification builders, and a
whole-A-image immutability assertion was too strict for a pristine startup.

All 11 selected returning groups from pinned suite a9a878f were rerun on this
exact cpmsim image/emulator: 229 pass, 109 not run and 24 observations across
group output, with no FAIL/ERROR rows. This is scoped execution, not complete
release acceptance. CONFIG/DUP compiled parser/query/dispatch checks and ten
SYSGEN package-validation cases pass against both actual platform builds.
The CONFIG/DUP tests were brought into line with the already established full
identification screen; title-only assertions were stale. These are test changes,
not a new utility presentation or feature.

Six packaging/source-identity regression tests pass. Candidates refuse dirty
tracked sources, mismatched source/image receipts, unsafe member paths and output
replacement. No publishing/promotion mode is supplied. Documentation contains
current textual/editable references; PDF/DOCX editions remain withheld pending
reconciliation.

Outstanding gates remain manual Model 4 runtime checks, its fresh-package install,
complete conformance applicability/accounting, manuals/generated editions,
license/attribution/source audit and maintainer acceptance. Follow the merged
[package specification](../releases/1.0-RELEASE-PACKAGES.md) and
[Model 4 checklist](Model%204%20Release%20Checklist.md). A subsequent code or
package change requires a newly identified candidate and applicable validation.
