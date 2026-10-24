# Explicit component revision assignment

Status: assignment tooling increment, 2026-10-24. Based on merged PR #491 at
`92f49404dcc4540f1d4b583a42060c6184ebc03d`. No production revision changes.

`tools/component_revision.py` compares actual artifact bytes with their selected
input/build records, produces a revision proposal, and verifies a final rebuild
against that proposal. Ordinary builders never increment counters. The tool
does not edit the component registry or declare execution qualification.

## Two-stage workflow

1. Preserve the reference executable and its original build report. Build the
   candidate with the same revision value, retaining its own report and bytes.
2. Run `plan` with both reports and artifacts. Changed bytes propose the next
   revision exactly once. Identical bytes retain the revision, even if selected
   inputs changed. A version change does not reset the numeric sequence.
3. Review the proposal. Update the authoritative registry to its proposed
   identity, regenerate legacy TSV projections if needed, and rebuild the final
   artifact. This is explicit publication preparation, not a compilation side
   effect. Do not increment again because the new embedded revision changes
   final bytes.
4. Run `accept` with the proposal, original reference/candidate evidence, and
   final report/artifact. Preserve the resulting assignment record together with
   that evidence. The record includes the final selected input record, checksum,
   identity and available provenance. It never rewrites older evidence.

Example proposal command:

```sh
python3 tools/component_revision.py plan \
  --reference-report reference/build-report.json \
  --reference-artifact reference/BYE.COM \
  --candidate-report candidate/build-report.json \
  --candidate-artifact candidate/BYE.COM \
  --output proposal.json
```

For acceptance, use the same four reference/candidate arguments with operation
`accept`, add `--proposal proposal.json --final-report final/build-report.json
--final-artifact final/BYE.COM`, and choose a new `--output` pathname. Both
operations refuse to overwrite an existing output. No repository baseline file
or assignment record is installed implicitly.

## Guards and scope

The command verifies selected-input fingerprints, report/component identity,
artifact size and artifact SHA-256. Reference/candidate components and variants
must match, and planning requires the same revision. Acceptance recomputes the
proposal from supplied evidence; the final identity must match its assignment
and the final selected-input fingerprint must match the reviewed candidate.
When retaining the revision, final artifact bytes must remain identical too.

Because revisions are excluded from their own selected-input fingerprints, a
final rebuild can embed its proposed revision without creating a feedback loop.
When executable bytes change, final bytes may differ from the candidate because
of the revision itself; the matching selected-input fingerprint, final identity
and bound output checksum establish the assignment record. The tool relies on
the supplied builder's input-map coverage and truthful build receipts. It is
not a binary semantic analyzer or a signature/authenticity system.

Only current cross-build receipts with valid selected-input records are usable.
That currently covers the BYE/DDT maps. Unsupported checked captures, native
records, missing input records and artifact mismatches are refused. Global
variant sequence reconciliation is not automatic: a retained older variant's
artifact cannot be used to silently restart the latest component sequence.
The operator must select the correct current sequence/reference or retain the
old artifact with its original identity and provenance.

This records identity assignment, not release acceptance, subsystem API approval
or execution qualification. Historical artifacts without these records remain
historical; do not fabricate retroactive selected-input provenance for them.
No `-dev` display change or frozen release alteration is introduced here.

## Verification

Twelve focused tests cover one-step advancement, identical rebuilds, byte-equal
input changes, continuing revisions across version changes, 999-to-1000,
planning at the old revision, artifact tampering, unsupported records, variant
mismatch, modified proposals, changed final inputs/identity and refusal to
change bytes while retaining a revision. Existing registry/input tests and
legacy projection checks also pass.

A disposable checkout additionally exercises real BYE assembly end to end:
a comment changes inputs while preserving binary bytes and revision 001; a
changed prompt changes bytes and proposes 002; the rebuilt 002 artifact passes
final acceptance with matching candidate input fingerprint. The public CLI
writes the acceptance record and refuses a second write to the same path.
The disposable checkout is removed afterward. Production counters remain
unchanged; no simulator execution or release qualification is claimed.

```sh
python3 tools/test_component_revision.py
python3 tools/test_component_inputs.py
python3 tools/test_component_registry.py
python3 tools/component_registry.py --check
```
