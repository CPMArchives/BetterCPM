# Platform-specific Utilities downloads — 29 October 2026

The maintainer requested separate Utilities downloads so a platform user does
not fetch the other platform's floppy images. The release now has six assets:
System/cpmsim, System/Model 4, Utilities/cpmsim, Utilities/Model 4, Source and
Documentation. The Utilities retain one implementation, version and manual.

The revised candidate set was assembled from
`6ee4f26eec70be3f7342c1996e107bdd50df7f11`.
[The receipt](Utilities-Platform-Packages-2026-10-29.json) records both Utilities
ZIP hashes/sizes, exact image membership and retained-source checks.

Each platform Utilities ZIP has exactly its two matching primary/companion
images. Other-platform images and image-specific JSON receipts are excluded.
Its independent inventory evidence is scoped to that platform. All shared
prepared native sources, corresponding-source archives, notices and provenance
files are retained with unchanged hashes relative to the internal Utilities
builder output. The internal paired-media build remains useful for assembly;
its combined ZIP is not a user-facing release download.

Eight packaging regression tests pass, including both platform ZIP memberships
and rejection of a Utilities set missing its primary/companion pair. Actual ZIP
membership, image hashes, matching receipt scope and complete shared-source
membership were also checked. Both formats pass the existing independent image
verifier. System images, all four Utilities images and reconstructed emulator
executables are byte-identical to candidate 021f531; earlier exact-byte runtime
evidence therefore remains applicable within its recorded scope. No guest
program, component revision, disk membership or runtime behavior changed.

This split removes unwanted media, but each ZIP is still about 195 MB because
the existing corresponding-source archives dominate size. Those companions
were preserved, not silently removed or deduplicated. Further source-package
size work requires checking the build/provenance contracts and source closure.

Archives remain candidates, not accepted or published releases. Model 4 manual
runtime/fresh-package checks and remaining documentation/source/license audits
are still pending. Earlier five-download assemblies and outcomes remain
historical evidence rather than being rewritten as six-download results.
