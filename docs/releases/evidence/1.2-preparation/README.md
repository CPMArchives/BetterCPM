# 1.2 focused release preparation

Feature freeze: `d7a11e2e4b5b10cc50042af5d38d7d5bec2ba825` (main after #681).
Build/package source: `dc16a08543ba7a377dd04912ece0485894e134bc`.
Subsequent evidence-only commits do not claim a new binary build identity.

The production source delta is limited to the packaged README and generated
Core OS 1.2 version text. Release-heading generation extends the existing
fixed-width rule to 1.2. Component revisions, including NOAH 1.0 (021), and
all private/public service identities remain unchanged. The source equivalence
record checks frozen production sources and existing component/layout metadata.

Three System builds and six Utilities images passed independent construction,
exact inventory, file readback and allocation checks. The Utilities source
companions were combined only after same-name content comparisons. Eight
candidate ZIPs passed archive CRC/readback, per-file ledgers, top-level hashes,
source identity and matching 1.2 Source-offer checks. The four maintained manuals
and documentation references passed the link audit. The pinned cpmsim runtime
was rebuilt from its approved local upstream source and patches.

Existing NDR/PATH/HELP/NOAH qualification is reused as listed in
`reused-qualification.json`. Old qualification is not relabelled as new
exact-media testing. No broad release qualification campaign was run.

Relevant regression results: 1.2 packaging (3), historical 1.1 packaging (4),
archive packaging (9), package licenses (3), registry (9), fixed-field release
heading (1), and the existing VER banner/query/startup check passed. Registry
projections also passed. The VER check ran against the staged built tree.

The first smoke exposed stale Core OS 1.1.1 metadata. That candidate set is
superseded. Corrected media use Core OS 1.2; cpmsim's corrected smoke observes
the 1.2 banner and 57,344-byte unloaded COM limit. Model 4's supplied startup
loads modules: expected startup limit is 52,480 bytes, while its unloaded
platform limit remains 54,272. Model II starts at the basic numeric prompt;
its expected unloaded limit is 57,344 bytes.

Artifacts are local candidates, not uploaded releases. See `archive-audit.json`,
`CANDIDATE.json` and `SHA256SUMS.txt` for the exact eight assets. The package
folder is `build/release-1.2/rc-packages/candidates/dc16a08543ba7a377dd04912ece0485894e134bc/`.
The paired cpmsim smoke includes an actual PIP topic open and exit. Its
Companion Utilities disk is mounted as C:, as required by the shipped layout.
The earlier standalone System-only fixture omitted that disk and is not HELP
acceptance. All three platform smoke checks passed. Model 4 named-DU use is retained
in `model4-named-use.json` and its capture; only private startup input/text
fixtures changed, with the release binaries unchanged. Early keyboard-paced
runs were not treated as passing evidence.
No v1.2 tag or public release has been created.


The consolidated result is `status.json`: **PASS focused release preparation**.
The candidate manifests intentionally remain review-only and retain the gates
that were pending when assembled. The hash-bound smoke and audit sidecars record
the subsequent observations; this does not retroactively rewrite those manifests.
Maintainer acceptance, final naming/tagging and publication remain separate.

Text capture projections omit trailing screen padding and blank rows; original
binary captures and raw transcripts remain in the local smoke folders.
