# BetterCP/M 1.0 publication preflight

> **Current status correction:** The five non-documentation packages are locked.
> Documentation is incomplete and still needs synchronization. The old
> Documentation ZIP and release-note text are provisional references. Prior
> consistency checks did not establish documentation completeness. See the
> [non-documentation lock](../non-documentation-lock-1.0/README.md).
> Tagging, publication and final tag-target alignment remain on hold.

Prepared 4 November 2026, Taipei. **Draft only; tagging and publication remain
on hold.** This preflight changes no frozen archive contents or compiled code.

[GitHub release draft](https://github.com/CPMArchives/BetterCPM/releases/tag/untagged-4fe70ebb8b693d00535f) ·
[final release notes](BetterCPM-1.0-RELEASE-NOTES.md) ·
[download index](BetterCPM-1.0-RELEASE.json) ·
[six ZIP checksums](BetterCPM-1.0-SHA256SUMS.txt) ·
[verification receipt](preflight-verification.json) ·
[candidate wording inventory](candidate-wording-audit.json).

## Source and proposed tag

The frozen artifact source is
`30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`. PR #609 merged as
`2842d0eb0732683d9280a38d576c3dba423cb893`; only qualification records differ
from the compiled source. The draft records proposed tag name `v1.0` and pins
that reviewed merge as its target. This is a planned name, not a created Git
reference. Tag references were unchanged before/after draft creation and upload.
No tag was pushed and no release was published. The draft has `draft=true` and
`published_at=null`.

GitHub supports saving a draft and attaching assets before publication; see its
[draft-release workflow](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
The actual server state and tag-reference comparisons, rather than that general
workflow description alone, are recorded in the verification receipt.

## Downloads

The agreed six final filenames in metadata/release-assets.json are used.
Each is a copied, renamed frozen ZIP with the identical SHA-256 and size.
The original frozen copies remain read-only and unchanged. Three companion
assets supply final release notes, the release-wide index and six-file checksum
list: nine uploaded assets total, still six packages. All nine server-side
SHA-256 digests match. The three small companions were also downloaded and
compared byte-for-byte, and the GitHub body matches the final notes.

Changing an outer filename does not change a ZIP hash. Changing a ZIP member,
internal root, embedded README or checksum would create a new artifact set and
require updated hashes and applicable validation. This preflight performs none
of those content edits.

## Candidate wording decisions

| Location | Disposition |
| --- | --- |
| Outer download filenames | Remove `-candidate`, matching the agreed six-package names. Hashes unchanged. |
| Internal archive roots | Preserve the tested `-candidate` directories and explicitly explain them in the final notes/index. |
| README `NOT ACCEPTED`, RELEASE status/accepted_commit and SOURCE-IDENTITY candidate labels | Preserve pre-qualification build records. The final index identifies the actual qualified source and freeze accepted through merged #609. |
| Embedded pending test lists | Superseded for technical qualification by the final ledger; final authorization to tag/publish remains held. |
| `tag: null` | Still correct. The draft's proposed tag name does not create a Git tag. |
| Embedded release notes and licensing freeze-hold status | Superseded only as qualification status by the external final notes/index; license terms, usage instructions and limitations remain controlling. Current repository prose is updated. |
| Historical engineering records, source template inputs and member-index filenames | Retain dated/template provenance. A candidate word in a historical filename is not an unresolved release test. |

The detailed audit covers frozen package entrypoints, current guides and build
status metadata. It is not a blind replacement of every occurrence of the word
candidate. In particular it grants no additional third-party permissions and
removes no residual-risk or hardware qualification limitation.

## Review before any future publication

Review the draft body, asset names, checksums, wording disposition and proposed
tag target. No runtime tests were repeated for rename-only copies; qualification
continues to bind the exact frozen bytes. A source or archive-content change
requires renewed applicability review. Only an explicit later maintainer
instruction may create/push the tag and publish the draft. This preflight does
not merge its repository PR or perform either release action.
