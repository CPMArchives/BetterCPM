# Automatic development identity for BYE and DDT

This increment follows the numeric-display migration in PR #494. Ordinary BYE
and DDT builds now select their visible development suffix automatically using
`metadata/component-baselines.json`. Relevant input hashes, assigned identity,
target/profile and toolchain must match a recorded per-variant baseline to emit
an unsuffixed title. Changed, absent, invalid or unsupported baselines emit
`-dev`. Git working-tree cleanliness is not used as a substitute for selected
input comparison, so committed-but-unassigned edits are detected too.

For example, unchanged assigned BYE inputs emit `BYE 1.0 (002)`. A relevant
source edit emits `BYE 1.0 (002-dev)` without advancing the counter. Unrelated
source/test files or another registry row do not affect BYE. Full input hashes
remain in the report to distinguish multiple builds sharing the visible suffix.

The initial catalog contains BYE/z80pack and DDT/z80pack and trs80gp default
cross variants. It records actual current input fingerprints, not reconstructed
historic ones. Real rebuilds with this increment produce exactly the existing
assigned numeric binaries: BYE stays at revision 002, DDT at 003. Explicit
equivalence/assignment records are retained in
`DEVELOPMENT-BASELINE-EQUIVALENCE.json`; default artifact checksums stay those in
the earlier numeric-migration record. These are input/identity baselines, not
disk releases or fresh native/checked execution qualifications.

## Avoiding display feedback

The semantic selected-input hash excludes the baseline catalog and the derived
display choice. The chosen mode/development state and matching baseline hash
are instead recorded as `display_selection`, bound to the actual artifact by
the build report. Builders compare that selection before and after assembly,
in addition to comparing selected inputs, refusing a receipt if either changes.
This avoids hashing an accepted fingerprint into itself while preserving which
display was emitted. Changing another catalog entry does not affect a consumer.

Revision proposal and acceptance require the reference/candidate/final builds
to use the same visible development state. Thus merely adding/removing `-dev`
cannot masquerade as a substantive executable change in that workflow. Both
builders expose explicit `--identity-state assigned` and
`--identity-state development` modes for controlled comparison and preparation;
the default is `auto`. Explicit assigned mode is a display override, never proof
that inputs are unchanged. Its reason is retained in the report. Publication
must still verify/accept the candidate and record the resulting baseline.

No ordinary build edits the catalog or counter. Baseline changes are explicit
reviewable metadata work. Missing Git provenance remains null, not fabricated.
Checked BYE retains its existing checked assembler validation path but now
conservatively displays development status because selected-input capture is
unsupported there. Checked DDT capture remains unsupported. Native DDT shares
the preparation functions, but native prepared-input and toolchain qualification
remain separate outstanding work; this catalog covers cross records only.

## Verification

Eight development-selection tests cover matching/missing/corrupt baselines,
relevant/unrelated edits, toolchain differences, explicit modes and unsupported
variants. Two additional assignment tests reject candidate/final display-state
mismatches. Existing formatter, registry, input and build-record tests remain
applicable. A real BYE build from a disposable copy verifies automatic `-dev`
after a source edit and restoration of identical assigned bytes after reverting.
The unchanged assigned binaries also retain the previously checked component
behavior; focused BYE/DDT harness checks are rerun for the new selection path.

Wider component mapping, shared/checked dependency refinement, native records,
remaining utility/module migration, core development reporting and immutable disk
manifests remain outstanding.
