# Final-media qualification attempt — 3 November 2026

**Package freeze remains on hold. These candidates are not accepted.** PR 588 merged as `8921a509838e7b46dc88bb9536e36ee847e0870c`, tree `1b334c96d09e5205f0a0f22db876a655f65bfc94`. Local source tree and reconstructed Git commit identity were verified byte-for-byte before fresh builds. The upstream runtime pin remains `91fd28eb04e675c2127df88ed3f40675e15282e2`.

## Completed checks

- Fresh System builds for cpmsim and Model 4, Utilities builds, independent exact membership/allocation/file-byte inventory, and all six candidate ZIPs assembled from the merged commit.
- Every ZIP checksum, compressed member and receipt-listed member hash read back successfully. See [archive identities](evidence/2026-11-03-final-media/archive-readback.json).
- The independent format checker recovered 130 file instances across all eight packaged images, decoded DMK sector IDs/CRCs, validated the native 780K versus historical 790K distinction and passed four full-volume pattern probes. See [media results](evidence/2026-11-03-final-media/independent-media-readback.json).
- A clean cpmsim runtime was reconstructed offline using only the extracted System ZIP host kit and its bundled upstream repository. Its executable SHA-256 is `0f6b256cd6beea2ab7bf0eab8a9cc2a5241ed772408e811150c3f6e0f5cff4e8`.
- Fresh extracted cpmsim System plus both Utilities volumes and blank Work: boot, factory saved settings, directories, copy/read passed. The supplied P2DOS/provider lifecycle and ABI checks passed on private media copies using that reconstructed runtime. See the adjacent cpmsim JSON receipts.

## Verified correction: installed cpmsim geometry

The unmodified package boots and its named SYSGEN export/install succeeds, but after cold boot of the installed target CONFIG reports `Saved disk-boot IOBYTE unavailable.` and `Boot disk does not match this system. Nothing saved.` The preserved sentinel and live IOBYTE 55 still work.

SYSGEN intentionally converts the installed A: binding from surface tracks to double-sided cylinder tracks: SPT 36 becomes 72, OFF 6 becomes 3 and flags C0 become A0. Equivalent byte geometry is preserved, but CONFIG's generated validation and cold-IOBYTE records recognize only SPT 36 (plus the separate Model 4 SPT 80). This is a reproducible settings-read/save regression, not evidence of lost files.

The proposed fix explicitly supplies the matching bootstrap SPT for the supported cpmsim 36-record double-sided surface format with an even reserved-track count. CONFIG receives the same CRC/layout and IOBYTE metadata keyed by that equivalent SPT. Checked-profile selection remains separate. No guest assembly, filesystem format or SYSGEN normalization is changed.

On a **private correction probe**, only CONFIG.COM was replaced in a copy of the exact candidate. The existing install campaign, strengthened to require saved IOBYTE 85 after installed cold boot and reject the mismatch diagnostic, passed: startup save, live routes unchanged, exact named export, confirmed install, complete destination filesystem preservation, cold-boot routes, sentinel, all shipped files and read-only reboot image. See [corrected receipt](evidence/2026-11-03-final-media/corrected-cpmsim-install.json). This does not accept or re-label the original candidate.

## Other corrections

The older install runners expected an obsolete verbose VER banner; their predicates now match the current `VER 1.0 (` output. The cpmsim runner resolves paths before changing working directories. The package assembler now includes `docs/platform/FORMAT-SUPPORT-1.0.md` in each download, fixing the broken scope link in independently extracted System/Utilities user guides.

## Remaining gates

Model 4 fresh media boot, saved geometry, both Utilities directories and a complete guest copy to Work passed independent readback. The native export/install/cold-boot workflow passed with unchanged release binaries, including saved startup/routes, destination file preservation and filesystem audits. Five supplied P2DOS/FreHD ABI lifecycle cases passed with on-disk result records, unchanged supplied carriers and a clean completion-oracle exit. Earlier fixed-wait/keyboard attempts were superseded, retained and not counted as completed campaigns. The new `tools/qualify_packaged_model4_clock.py` promotes that batch/result-file method with baseline hash checks and a bounded guest completion wait. Timed keyboard trials and incomplete captures are not counted as passes. Final fresh-package installation on both platforms cannot be signed off while a required correction remains unmerged.

Review and approve the correction, then rebuild all affected candidates from the approved commit and repeat exact-image checks and installations. Retain the upstream offline-history redistribution review, documentation/generated-edition review, broader applicability accounting and separate maintainer acceptance. Existing audit and 104/105 adapter deferrals remain unchanged. This review creates no tag, freeze or release.

Raw local transcripts, invocations, images and failed attempts are retained under `final-media-qualification-20261103/` in the project workspace. [Artifact hashes](evidence/2026-11-03-final-media/artifact-identities.json) bind the original failure and correction transcripts; the original package checksums remain the candidate identity.
