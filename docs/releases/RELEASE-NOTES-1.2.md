# BetterCP/M 1.2

Qualified release — 10 November 2026.

- Named Directory Register (NDR) provides named drive/user directories.
- PATH displays NDR annotations while preserving the established numeric and
  symbolic search contract.
- HELP supplies the integrated reader, topic library and command quick help.
- NOAH 1.0 (021) searches its invocation directory then the configured system
  PATH for its matching overlay; invalid/incompatible copies stop the search.

Use the matching 1.2 System and Utilities packages for your platform. Install
NOAH.COM and NOAH.OVL as a matching pair. Source and Documentation are separate
downloads. The 1.1.2-only NOAH update ZIP and older System disk instructions do
not apply to this release.

Validation follows [focused 1.2 acceptance](1.2-SCOPE-AND-ACCEPTANCE.md), reusing
existing engineering qualification and requiring only short manual smoke checks.
All three System builds, six Utilities image inventories, eight archive audits,
and short smoke checks on cpmsim, Model 4 and Model II passed. Exact build,
image and candidate identities are retained in
[evidence](evidence/1.2-preparation/README.md). The published RELEASE.json and
SHA256SUMS identify the final downloads. No broad qualification campaign was repeated.


For cpmsim, mount the matching Companion Utilities disk as C: so the shipped
PATH can find HELP.LBR. Model 4 and Model II include HELP.LBR on System media.
Model 4's supplied startup leaves a 52,480-byte COM limit with its modules loaded;
its unloaded limit remains 54,272 bytes. cpmsim and Model II provide a
57,344-byte unloaded COM limit. Optional modules reduce the live limit.

The release preserves the qualified disk images from build commit
`dc16a08543ba7a377dd04912ece0485894e134bc`. Final archives distinguish that
binary-build identity from the tagged source, which adds reviewed evidence
and final release metadata. Physical hardware qualification remains outside
the emulator-based support commitment.
