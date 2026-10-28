# Release stabilization — 28 October 2026

Status: candidate work in progress; **not accepted for publication**.
[Machine-readable evidence](Release-Stabilization-2026-10-28.json) binds the
source, suite, emulator, actual System Disk and selected results.

The reconstructed runtime and qualification emulator pass manifest checks,
poisoned-working-tree reconstruction, geometry interface version 2 and seven
ROM-guard primitives. This includes the correction for silently skipped patches
when reconstruction output is inside the BetterCP/M checkout.

A fresh cpmsim System Disk from implementation commit 2f79c31 booted and passed
the distribution builder's filesystem, file-integrity and configuration checks.
All 11 returning groups of independently rebuilt suite a9a878f completed with
no FAIL/ERROR rows. The subsequent 13075d0 commit changes only the User's Guide;
it does not alter any source/build input or the tested binary. Individual
not-run/observation rows remain such; this is not whole-system certification.

The local z80asm 2.1 tool needed its source-filename pointer restored after an
INCLUDE before printing later listing page headers. Without that host-only
correction, stage1.lst contained freed-memory bytes in the filename header and
could not be decoded. The exact external-tool patch and assembler hash accompany
the retained build evidence. This is separate from the required cpmsim runtime
patches and does not change the shipped runtime patch set.

Utilities packaging did not complete: this host's cpmtools 2.23 cpmcp aborted
with SIGABRT while reading NOAH.COM back from the 800K companion representation.
The builder therefore did not publish a new paired Utilities package. Earlier
inventory hashes in the manual checklist remain historical reference identities;
they have not been copied into a new acceptance receipt. Investigate with the
maintainer's qualified host tools and retain the failing log.

The prior workstation's paused worktree and receipts were unavailable on this
host. The earlier reported failures of ERRTEST 0408/0582 using suite 61b3639 are
not relabeled or discarded. This run uses the specified release suite a9a878f
and its own receipts. Neither result changes historical acceptance records.

Remaining release gates:

- Complete the [manual Model 4 checklist](Model%204%20Release%20Checklist.md), including actual packaged images and exact current component versions.
- Finish Utilities packaging with verified corresponding-source closure, then boot/inspect the actual platform packages and verify a fresh installation.
- Finish the manuals, release notes, licensing/attribution review and version-baseline decisions. Keep current -dev displays until the established qualification rules authorize promotion.
- Reconcile complete conformance accounting, affected regressions and candidate identity after any further implementation change.
- Obtain maintainer acceptance before tagging/publishing; the maintainer merges PRs.
