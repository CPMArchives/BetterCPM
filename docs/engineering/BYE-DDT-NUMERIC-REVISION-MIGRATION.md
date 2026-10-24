# BYE and DDT numeric revision migration

This increment follows the shared formatter in PR #493. It makes the first
executable display changes under the accepted independent-revision policy:

| Utility | Previous identity | New identity |
| --- | --- | --- |
| BYE | 1.0 (Build 001) | 1.0 (002) |
| DDT | 1.0 (Build 002) | 1.0 (003) |

BYE's /HELP title changes with /VER. DDT's normal sign-on and /VER use the same
numeric title. Both retain their established identification blocks. The version
remains 1.0 because this changes identification, not their functional contract.
Legacy utility TSV projections are regenerated from the registry; other utility
identities and all subsystem identities remain unchanged. Core 1.0 stays frozen.

Reference builds use the prior legacy formatter at the existing revisions.
Candidate builds use numeric text with those same revision values. Actual bytes
differ, so the assignment tooling proposes one increment for each. Final builds
use the proposed revisions, and their selected-input fingerprints match the
reviewed candidates. Assignment checks pass without incrementing again for the
new revision digits. The machine-readable assignment records are retained in
`NUMERIC-REVISION-ASSIGNMENTS.json`.

Reports record null Git HEAD because the local working directories reconstruct
the pinned source through the GitHub connector rather than containing a Git
checkout. They retain actual selected-input and toolchain hashes; no historical
source provenance is invented. These are new build/assignment records, not
retroactive qualification of the old released executables. Reference, candidate
and final bytes/reports are in `build/numeric-revision-migration` locally.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| BYE.COM | 1069 | a319551ef804c9babb57037cddb1053d58e9e0c215d9f2829b5fcf1c9043e2ac |
| DDT.COM | 6528 | eff7f5369b9f2903e71d9cf7b3fa47d9dc2cad65714ee79a0b31e9680281e467 |

## Verification and boundaries

The 48 versioning tests pass after updating migration expectations. The assembled
BYE CPU harness passes 74 cases covering cancellation, confirmation, bypass,
query precedence, invalid tails, caller-state preservation, exit ports and
fallback. DDT passes seven /VER/page-zero purity cases, translation/combined
source parity, relocation guards and historical-reference isolation checks.
This is focused component verification, not final disk acceptance or a fresh
native/physical-emulator qualification campaign.

Automatic development suffix selection remains pending. The formatter can emit
`-dev`, but these migrated callers currently emit the assigned numeric identity;
their build reports still distinguish unknown/development/unchanged comparisons.
Do not interpret an unsuffixed title alone as proof of pristine or qualified
inputs during this staged migration. Native DDT shares the changed preparation
functions, but its native assembly/link execution must be requalified before
claiming new native binary parity. Checked compatibility hashes remain coupled
to broad metadata/tool inputs and are not certified by this increment.

Common utilities and codecs continue using their prior legacy formatting.
Their executable migration, RCP/MOVE/WARM identity resolution, remaining input
maps, development-state selection and disk manifests remain outstanding.
