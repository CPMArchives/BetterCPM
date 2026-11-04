# BetterCP/M 1.0 — candidate release notes

**Release not yet accepted.** This document accompanies candidate packages and
must be reconciled with the accepted candidate before final publication.

BetterCP/M is a CP/M 2.2-compatible system with shared operating-system services
and separate cpmsim and TRS-80 Model 4 hardware bindings. The 1.0 distribution
includes system configuration/installation utilities, CPX/RSX extension support,
persistent command history, terminal providers and a separate Utilities set.

The six downloads are System for cpmsim, System for Model 4, Utilities for cpmsim,
Utilities for Model 4, complete Source, and Documentation. All carry the same candidate
source commit, with exact artifact hashes and evidence in RELEASE.json. Utility
component revisions are independent of the package version. Release identity assignments are described in
[release identities](1.0-RELEASE-IDENTITIES.md). Stable version text alone does not
indicate final acceptance.

Recent additions include CRCKSUM, MD5SUM, PATCH and COMPARE; the NOAH companion
contains NOAH, PATCH and COMPARE. CRCKSUM and MD5SUM remain on the primary
Utilities Disk. The patched-cpmsim reconstruction process now applies patches
correctly beneath a parent Git checkout and records an extracted source ZIP's
explicit source identity without requiring a BetterCP/M .git directory.

## Requirements and limitations

- cpmsim requires the pinned runtime patches and helpers. Stock upstream cpmsim is insufficient. The Source and cpmsim System packages contain a pinned cpmsim source tar for offline reconstruction; follow their dependency README and installation guide.
- Select Model 4 DMKs or cpmsim raw images as appropriate. They are different containers and system bindings. The System images use platform-specific reserved tracks and geometry.
- For the combined installation use A: System, B: primary Utilities, C: historical BetterCPM-NOAH companion, D: work. Utilities are separate downloads from the System packages.
- Keep NOAH.COM and NOAH.OVL from the same package. Check individual utility requirements before use on another CP/M implementation.
- Clock providers are optional and platform-specific. Supplied startup scripts do not automatically enable a clock. Physical Model 4 media transfer needs equipment/controller-specific validation.
- Existing PDF/DOCX manual editions have not been reconciled against all recent Markdown changes; candidate Documentation contains editable/textual documentation instead. Engineering history retains dated evidence and earlier outcomes.
- The Utilities packaging failure observed on the Linux host is historical evidence. New macOS assembly and independent inventory/readback checks pass; this does not establish Model 4 runtime acceptance.

The [35c56a03 technical lock and qualification record](../engineering/Qualification-Lock-35c56a03.md) identifies the qualified core, runtimes and unaffected utilities. FDB.COM, CONFIG.COM and DISK.FDB integration and native qualification were recorded through PR #605; PR #608 supplies the matching released FDB query/help pair. The maintainer has authorized replacement qualification and freeze after release identity promotion. The original 54c50365 frozen reference is preserved. Tagging and publication remain on hold.

## Remaining acceptance work

Fresh-package installation passed on both emulators for the six-package
candidate built at `35c56a03`. Known manual corrections and checks of the installation walkthrough can
proceed during stabilization. Complete the remaining qualification and lock the
release contents, behavior and test results first. Then finalize the manuals,
installation guides, notices and release notes against that locked baseline. Preserve results against exact hashes. The maintainer must accept
the candidate before tagging and publishing the tested final files.

## Recorded compatibility and residual-risk dispositions

The qualified default RAM environments are patched cpmsim and Model 4 under
trs80gp. Public-profile selection is still a maintainer decision; the optional
cpmsim-legacy-checked and cpmsim-fullram variants require their own current
qualification before promotion. Physical hardware, Model 4D/4P and additional
platforms are outside these emulator receipts.

The merged conformance record retains case-preserving command-tail behavior
and fixed-A0 extension lookup differences (cards 0020, 0493 and 0494).
Preserve these reported differences when interpreting stock CP/M expectations;
do not count observations or exclusions as passing tests. Extension carriers
needed at run time, including BATCHIO for XSUB, must be available in A0.

The Model 4 keyboard campaign does not establish ordinary host Caps Lock
quick-tap behavior; scripted matrix checks and the recorded manual observations
have their stated, bounded scope. The pre-existing pending-input/CONST
observation remains post-1.0 investigation unless a supported workflow fails.

BCPM-AUD-003 remains explicitly deferred: a pre-corrupted history object with
valid signature/version can contain unsafe lengths/counts and damage memory.
No supported command sequence producing the malformed state was established.
Reopen before release if supported input can produce it, or if the history
writer/PDS layout changes. This is a residual-risk disposition, not a claim of
full malformed-record validation. General BCPM-AUD-007 historical oracle cleanup
also remains deferred; failing required current gates still need disposition.

PR #583 records a passing stock protected-XIP qualification for ROM SHA-256
cc6917780ce47ab34fbed7949abdf93a17d20eb182ab9fdcd15c8d16cd864168
and its exact disk/overlay/emulator configuration. A changed candidate does not
inherit that receipt automatically. BCPM-AUD-006’s stale memory/cold-history
text was corrected in merged PR #584. Neither result accepts public packages.

Both System disks ship A0:P2DOS.RSX. Startup leaves it unloaded. Load ZPRTC
on cpmsim or FREHDCLK on a FreHD-equipped Model 4, then load P2DOS. The
35c56a03 cpmsim System disk passed the [P2DOS clock tests](../engineering/evidence/2026-11-03-candidate-cpmsim-p2dos.json).
The matching Model 4 System image passed the [six-stage trs80gp test](../engineering/evidence/2026-11-03-model4-p2dos/README.md). Both 104/105 adapters
(T104C3/T104Z8) are explicitly deferred from the 1.0 RC.

Original BetterCP/M software and reusable code examples use GPL-2.0-or-later.
Original documentation prose and illustrations use CC BY 4.0. Each package
carries both license texts and docs/LICENSING.md, with LICENSE and NOTICE
defining the split and separate-work exclusions.
BetterCP/M builds its 108-entry DISK.FDB from its own FDF v1 text definitions.
All six packages exclude Montezuma Micro’s original DISK.FDF, including nested
source archives. The historical format parameters retain their provenance. Replacement freeze requires its exact-hash acceptance ledger; tagging and publication remain on hold.
