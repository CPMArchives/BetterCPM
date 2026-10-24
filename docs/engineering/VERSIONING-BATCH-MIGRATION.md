# Version identification batch migration

This batch completes the utility identification conversion in one pass, including
the previously unpushed compression and TIME/STAT changes. Verification is limited
to compilation, metadata consistency, identification payloads and direct /VER
checks. No compression, filesystem, parser or fault-injection campaigns are added.

All 38 utility identities now use numeric revisions. Previously migrated counters
are retained; each remaining changed existing utility advances once. MOVE and
WARM begin their own 1.0 (001) sequences without inventing earlier history. MOVE's
transient identification no longer borrows RCP's counter. WARM now recognizes
/VER before requesting warm boot, using the common query preparation in both
cross and native source builders. Deferred NOAH's development foundation is
identified but is not newly added to release media.

RCP's carrier version now comes from its canonical registry identity, resolving
0.2 versus 1.0. Its revision advances to 016 for the changed package. Resident
commands keep compact one-line package-owned numeric identification; standalone
utilities use their own identities and identification blocks. The visible core
heading reports `BetterCP/M development (after core 1.0)`. Frozen core 1.0 and
subsystem implementation/API versions remain unchanged.

All eight selected loadable-module builders now read implementation versions
from the registry instead of independent numeric literals. Their carrier schemas
and callable APIs are unchanged. Subsystem/module independent revisions remain
in the registry and the artifact inventory; no carrier format is extended just
to add a revision field. Unselected diagnostic/example modules retain their
existing separate behavior, and ZSM4/LINK receive no BetterCP/M numbering.

The final inventory covers all 51 components with their assigned versions,
revisions, applicable API versions, artifact sizes and SHA-256 values:
`BATCH-COMPONENT-INVENTORY.json`. `BATCH-UTILITY-IDENTIFICATION.json` records the
38 utility identification checks and 22 direct /VER executions. The directory
is a source reconstruction, so repository HEAD provenance is explicitly null;
these files are current build inventories, not frozen disk manifests or release
qualification receipts.

## Verification

- Default cross builds pass for the utility collection, its required resident
  dependencies, all selected modules, terminal tests, the deferred NOAH
  foundation, compression tools and BYE.
- Assigned numeric titles are present in all 38 final artifacts. No legacy
  `(Build NNN)` identification remains in those artifacts.
- One /VER request passes for each of 22 common utilities, including MOVE and
  WARM, with the expected independent identity.
- All eight selected module carrier versions and RCP's carrier version match
  the registry. Registry projection checks and the existing eight registry
  consistency checks pass with the updated assignments.
- Ten previously migrated utilities rebuild byte-identically in assigned mode;
  shared helper changes therefore do not advance their revisions. Their input
  baselines are refreshed accordingly.

## Scope limits

This document records the identification migration delivered in PR #496.
The subsequent completion batch is documented in `VERSIONING-COMPLETION.md`;
it adds the remaining input maps, build records and external release manifests.
Native execution and checked-profile release qualification remain separate from
versioning implementation. Historical records remain untouched.
