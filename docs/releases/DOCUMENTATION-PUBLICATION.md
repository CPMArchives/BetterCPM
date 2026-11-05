# Documentation publication and provenance

The dedicated Documentation ZIP is the only 1.0 package open for rebuilding. The five Source/System/Utilities ZIPs and their embedded manuals, licenses, roots, checksums and source identities remain unchanged under the [lock](non-documentation-lock-1.0/README.md). This procedure prepares reviewable documentation; it does not authorize tag changes, draft uploads or publication.

## Publication formats

The selected 1.0 format is Markdown plus plain-text supporting material and editable example sources. The four principal entry points are [User's Guide](../user/users_guide.md), [Command Reference](../user/command_reference.md), [Programmer's Guide](../programmers/programmers_guide.md) and [Practical Porting Guide](../porting/practical_porting_guide.md). Linked API chapters and detailed technical records support them. [Documentation index](../README.md).

Old User/Architecture PDF/DOCX files are withheld. They do not track the reconciled editable sources. No new printable edition is claimed in this step; any later PDF/DOCX/HTML publication must be generated from the selected revision, carry the same attribution/example boundaries, and have its contents, tables, pagination and links visually reviewed. Adding printable editions is a deliberate format decision, not an automatic missing-content blocker.

The explicit [selection manifest](../../packaging/1.0/documentation-selection.json) replaces indiscriminate collection of all textual docs. It excludes the old backup, FDB 1.01 development guide, binary/media fixtures, source archives and historical evidence bundles. Original engineering history remains in the matching repository/Source context. A selected manual's link to an omitted source/history path is rewritten in the ZIP to the pinned software-source URL, not left as a broken relative path. Local selected paths stay local.

## Separate identities

| Field | Meaning |
| --- | --- |
| `software_source_revision` | Fixed `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`. |
| `qualification_merge_revision` | Fixed `2842d0eb0732683d9280a38d576c3dba423cb893`. |
| `documentation_revision` | Actual reviewed documentation commit for a committed build; never reuse the software revision to disguise new prose. |
| `documentation_source` | Commit identity and selected input manifest, or an explicitly labelled working-tree review snapshot with null final revision. |
| `locked_packages` | Five unchanged filenames, sizes and SHA-256 values copied from LOCK.json. |
| Documentation ZIP hash | Computed from its own final bytes, separate from the five pinned hashes. |

An uncommitted authoring preview is named distinctly and records its base commit, selected input hashes and snapshot digest. It is not the final-named accepted Documentation ZIP, cannot satisfy a final review, and never invents a final revision. A committed build reads the selected files from the specified actual commit, not mixed working-tree files. The documentation revision must be distinct from the locked software revision for this new collection.

## Build a documentation-only review

Use the new documentation tools from the reviewed documentation checkout, not the older tools embedded in the frozen Source ZIP. They use Python's standard library and touch only an explicitly new documentation output. The legacy six-candidate assembler is not the documentation-sync route.

```sh
python3 tools/build_documentation.py --repository . \
  --preview --output /path/to/new-documentation-review.zip
```

Preview output must have a distinct review filename. For a committed candidate, after recording/reviewing the actual documentation commit:

```sh
python3 tools/build_documentation.py --repository . \
  --revision DOCUMENTATION_COMMIT \
  --output /path/to/new-candidate/BetterCPM-1.0-Documentation.zip
```

Replace DOCUMENTATION_COMMIT with the full real 40-character commit. The builder rejects the software commit as a substitute. The output path must not exist. Generated RELEASE.json/SOURCE-IDENTITY.json describe only the documentation revision and locked software baseline. SHA256SUMS covers every other member including both records; it does not hash itself. Legal/provenance text remains verbatim. Publication-tool copies in the ZIP allow read-only verification without pretending the frozen Source kit includes them.

## Verify the split collection

Place copies or read-only paths to the five exact locked downloads alongside the new Documentation ZIP; do not rename internal archive roots or rebuild them. Run:

```sh
python3 tools/check_release_package_lock.py /path/to/six-downloads \
  --repository . --output /path/to/new-verification.json
```

The checker verifies the declared committed documentation inputs against their actual Git object bytes and streams hashes/sizes of the five files against the canonical lock, verifies documentation ZIP names/member checksums/licenses/selection and separate provenance, and reports static identity checks. A mutation to one locked archive is a failure even if a new checksum list claims it is valid. It does not demand one new source commit for all six, and does not reinterpret old candidate labels as changed behavior. Missing packages fail; no test waiver is inferred. `--allow-preview` is for explicitly labelled authoring checks and cannot yield final acceptance.

After final documentation review, use the new ZIP's actual hash/size and documentation commit in the release index and checksum list. Preserve the five locked rows exactly. Existing draft index/hash/receipt files under `publication-1.0/` describe the earlier preflight and provisional old Documentation ZIP; they are historical snapshots, not the new build's provenance. The [publication plan](DOCUMENTATION-PUBLICATION.json) leaves the new final revision/hash unset until actual build/verification. Do not claim that six packages were rebuilt from one new commit.

## Final review and companion receipt

Step 4 reconciles support documents, selection, formats and tooling. Step 5 performs final content/example/link/license checks on the actual assembled ZIP under the [acceptance protocol](DOCUMENTATION-ACCEPTANCE.md). Its external receipt identifies the accepted bytes without rewriting the ZIP’s pre-acceptance build status or creating a self-referential hash. New programmer/porting writing and unexecuted native examples retain the [coverage/evidence boundary](../programmers/REFERENCE-STATUS.md), without becoming extra software blockers. Existing qualification applies only to matching locked bytes; these static checks do not rerun emulator or physical-hardware trials. Tag-target alignment, tagging and publication remain held until separately authorized after review.
