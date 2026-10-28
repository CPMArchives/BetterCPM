# BetterCP/M 1.0 — candidate release notes

**Release not yet accepted.** This document accompanies candidate packages and
must be reconciled with the accepted candidate before final publication.

BetterCP/M is a CP/M 2.2-compatible system with shared operating-system services
and separate cpmsim and TRS-80 Model 4 hardware bindings. The 1.0 distribution
includes system configuration/installation utilities, CPX/RSX extension support,
persistent command history, terminal providers and a separate Utilities set.

The five downloads are System for cpmsim, System for Model 4, Utilities for both
platforms, complete Source, and Documentation. All carry the same candidate
source commit, with exact artifact hashes and evidence in RELEASE.json. Utility
component revisions are independent of the package version. Candidate names and
existing -dev banners do not indicate final acceptance.

Recent additions include CRCKSUM, MD5SUM, PATCH and COMPARE; the NOAH companion
contains NOAH, PATCH and COMPARE. CRCKSUM and MD5SUM remain on the primary
Utilities Disk. The patched-cpmsim reconstruction process now applies patches
correctly beneath a parent Git checkout and records an extracted source ZIP's
explicit source identity without requiring a BetterCP/M .git directory.

## Requirements and limitations

- cpmsim requires the pinned runtime patches and helpers. Stock upstream cpmsim is insufficient. The Source and cpmsim System packages contain a pinned upstream Git bundle for offline reconstruction; follow their dependency README and installation guide.
- Select Model 4 DMKs or cpmsim raw images as appropriate. They are different containers and system bindings. The System images use platform-specific reserved tracks and geometry.
- For the combined installation use A: System, B: primary Utilities, C: historical BetterCPM-NOAH companion, D: work. Utilities are separate downloads from the System packages.
- Keep NOAH.COM and NOAH.OVL from the same package. Check individual utility requirements before use on another CP/M implementation.
- Clock providers are optional and platform-specific. Supplied startup scripts do not automatically enable a clock. Physical Model 4 media transfer needs equipment/controller-specific validation.
- Existing PDF/DOCX manual editions have not been reconciled against all recent Markdown changes; candidate Documentation contains editable/textual documentation instead. Engineering history retains dated evidence and earlier outcomes.
- The Utilities packaging failure observed on the Linux host is historical evidence. New macOS assembly and independent inventory/readback checks pass; this does not establish Model 4 runtime acceptance.

## Remaining acceptance work

Complete the manual Model 4 campaign for current components and matching media,
run fresh-package installation and platform checks, reconcile final conformance
applicability, finish manuals/generated editions and audit source/licensing and
attribution. Preserve results against exact hashes. The maintainer must accept
the candidate before tagging and publishing the tested final files.
