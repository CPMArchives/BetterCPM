BetterCP/M 1.0 qualified archive snapshot — FROZEN

Source: 54c503652fa957798bf2d0d636f4172851195926
Qualification: PR #605, merge d95b30bfa91cbc3cace53c861d8964375a7afe70

FREEZE.json and SHA256SUMS.txt record the exact six qualified ZIPs. This
repository directory contains records only; no archive payloads are uploaded.
The local project working area holds read-only copies under:
release-freeze-20261104/qualified-1.0-frozen/packages/
Their filenames, candidate suffixes and contents are unchanged.

Release-identity exception: OPEN. Ordinary first-party utility identification
still contains -dev. This freeze preserves the qualified baseline; it does not
promote development identities to released component assignments. The static
inventory finds such strings in 41 distinct shipped files, including embedded
helper identities and diagnostics; it is not 41 newly executed /VER queries.

The component revision policy defines -dev as relevant inputs differing from
the recorded inputs of an assigned revision. Review the qualified first-party
component assignments and baselines, retaining independent component versions.
Do not force every tool to version 1.0 or blindly strip labels from diagnostics
and third-party tools. Do not force assigned display mode as a substitute for
proper assignment and qualification.

No tag or release publication has been authorized or performed. Promote the
appropriate identities, regenerate and check affected outputs before final
release. Any replacement set needs a new source/hash/evidence and freeze record.
Preserve these qualified bytes unchanged.
