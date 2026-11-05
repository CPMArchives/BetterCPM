# Documentation acceptance and software boundary

Acceptance identifies the actual built Documentation ZIP and its actual independent source commit. It does not reinterpret the software tag, original software source or bounded qualification evidence. The five current software packages and separate Qualification Evidence ZIP must retain their recorded asset IDs, sizes and hashes.

## Required checks

1. Audit controlled repository documentation links after removing obsolete files: no links to retired manual paths or locators, and no broken local file targets/anchors.
2. Inspect the extracted reader layout: one README and four clearly named complete manuals at the top level; supporting publications, legal records and provenance remain accessible. No obsolete command locators, old backup, development manual, rendered obsolete editions, build tools or historical packaging folders.
3. Build from an actual independently recorded documentation commit. Verify every selected source input and every generated member against that commit, including intentional relative-link remapping. Check all local package targets/anchors, pinned repository target paths, required manuals and verbatim legal records. Recomputed internal checksums must not conceal changed prose or false source identities.
4. Rebuild the same commit into a second new directory and require byte-identical ZIPs. Preserve the existing example cross-assembly evidence and explicit unexecuted native/runtime limits; no new software qualification is claimed.
5. Verify all current non-documentation asset IDs/sizes/hashes before and after the Documentation update. Update only Documentation and its external index/checksum/notes; preserve the tag ref, software target and all software/evidence assets.

## Receipt and limits

Keep the final acceptance receipt outside the ZIP to avoid a circular ZIP hash or fictitious commit. It records the documentation commit, ZIP hash/size, link/layout/license/provenance checks, repeat-build result and unchanged software/evidence identities. Provenance/MANIFEST.json records the selected input/member hashes; Provenance/SOURCE-IDENTITY.json records independent source identities.

Existing errata, licensing qualifications, compatibility observations, excluded/deferred profiles and emulator-only evidence retain their scope. Native/runtime execution of new tutorial examples, additional hardware, new rendered editions and further programmer/porting expansion remain independent work; they do not become new 1.0 software blockers.

See the [publication procedure](DOCUMENTATION-PUBLICATION.md), [reference-status ledger](../programmers/REFERENCE-STATUS.md) and [licensing inventory](../LICENSING-INVENTORY.md).
