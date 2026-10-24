# TIME and STAT numeric revision migration

This increment follows the unpushed codec migration and uses the registry to
select numeric common-utility formatting. TIME and STAT each move from
1.0 (Build 003) to 1.0 (004). Their /VER output now contains the numeric title
and established BetterCP/M Utilities identification block. Other common utility
callers remain on their legacy path; RCP/transient coupling is not changed.

The registry owns display_format and description fields for these two entries.
Their selected-input maps include those fields by value, source/build files,
shared layout/query preparation, STAT's selected includes and actual assembler
flags. Reading one entry does not make every registry row a dependency.

`tools/component_build.py` supplies a reusable input/artifact/report wrapper.
TIME and STAT builders expose callable build functions, an isolated output
directory, target and explicit display-state options. Existing default output
paths remain available. Context-local display selection keeps nested source
preparation consistent; a failed build removes its old receipt and restores
the context. Unsupported checked capture is recorded as unknown while preserving
the existing checked assembler path. Reports make no execution-qualification
claim. Normal compilation never changes counters or baselines.

Legacy reference artifacts are newly reconstructed with actual source hashes;
they are not treated as historical qualification receipts. Same-revision numeric
candidates differ in bytes, and final revision-004 builds pass the explicit
assignment checks. Records are retained in
`COMMON-UTILITY-REVISION-ASSIGNMENTS.json`. Default cross assignments are verified;
additional target input captures label the portable path and do not imply native
or physical-emulator qualification.

The shared utility/selected-input helper changes affect review of the eight
previously mapped utilities. Assigned-mode before/after assembly confirms BYE,
DDT and all six codecs remain byte-identical. Their existing revisions are
retained with new input-equivalence records and updated baselines. Subsystem
identities, frozen core 1.0 and historical qualification records are unchanged.

## Validation and remaining work

All 61 prior versioning tests and three new common build-record tests pass.
The new tests execute five /VER tail forms per utility, compare the complete
identification blocks, check page-zero preservation, verify actual artifact
checksums, exercise development output and test failed-build cleanup/context
restoration. STAT wildcard/options parser checks and TIME error routing, SET
parsing/dispatch and GET/provider regression checks pass against rebuilt code.

These are focused component checks. Whole media, native ZSM4/LINK and checked
profile execution qualification remain separate. The RCP family, remaining
standalone utilities/modules, native input records, checked-contract dependency
refinement, core development reporting and immutable disk manifests still need
migration. The compression and TIME/STAT increments remain unpushed together.
