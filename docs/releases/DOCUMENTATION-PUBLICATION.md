# Documentation publication and separate provenance

The reader collection has four canonical source manuals in [docs/manuals](../manuals/Users-Guide.md). Each is selected once and appears at the ZIP root with the same clear filename. Obsolete Utilities/standalone-command locators and the old User’s Guide backup have been removed, and controlled internal links now address the canonical manuals and command entries directly.

## Reader layout

```text
BetterCPM-1.0-Documentation/
  README.md
  Users-Guide.md
  Command-and-Utilities-Reference.md
  Programmers-Guide.md
  Practical-Porting-Guide.md
  Supporting-Reference/
  Licenses/
  Provenance/
```

README is the single starting page. Supporting-Reference contains the linked API chapters, examples, installation/build instructions, architecture contracts and other selected technical references. It contains no competing Utilities manual or individual command locator. Licenses retains selected original terms/credits verbatim. Provenance contains source identity, explicit selection, unchanged current software/evidence package identities, a member/input manifest and checksums. There are no source-tree navigation wrappers, packaged build tools or PACKAGING-HISTORY copies in this reader collection. Earlier package bytes and evidence remain in the repository/history and release audit records, rather than cluttering the manuals.

The selected format is Markdown/text and editable example sources. PDF/DOCX editions remain excluded until intentionally regenerated and visually reviewed.

## Software and documentation identities

Software source remains `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`; the published `v1.0` tag points to qualification merge `2842d0eb0732683d9280a38d576c3dba423cb893`. The five current published software packages and separate qualification-evidence ZIP retain their exact asset IDs, sizes and SHA-256 values under [software-packages-1.0.json](../../packaging/1.0/software-packages-1.0.json). That baseline distinguishes the later packaging-only correction from the original historical five-archive freeze. Do not relabel or rebuild any software package during this documentation cleanup.

The Documentation ZIP records its own actual full Git commit. It is not the software source or tag commit. Each selected source input and generated package member is hashed; legal records are copied verbatim and relative links are remapped from canonical repository paths to actual package destinations. Omitted source/history citations use explicit pinned repository revisions; verify those paths before publication. A working preview has a null final revision and cannot satisfy final verification.

## Build and verify

From the reviewed documentation checkout, with a NEW output path:

```sh
python3 tools/build_documentation.py --repository . --preview --output /path/to/layout-review.zip
python3 tools/build_documentation.py --repository . --revision DOCUMENTATION_COMMIT --output /path/to/new/BetterCPM-1.0-Documentation.zip
```

Use the real full 40-character documentation commit. Committed builds read actual Git object bytes, ignoring unrelated working-tree changes. The output must not already exist. A second build of the same commit must reproduce identical ZIP bytes.

The documentation verifier reconstructs selected input bytes and intentional link transformations from that actual commit, then compares every member, including selection, provenance and legal records. It rejects altered content even when internal checksums have been recomputed. It checks all local Markdown/text file targets and anchors, not only checksums. The package’s complete checksum list is `Provenance/SHA256SUMS.txt`; it covers every member except itself. There is no circular embedded ZIP hash.

For a combined read-only check with copies of the unchanged software/evidence ZIPs:

```sh
python3 tools/check_release_package_lock.py /path/to/published-zip-copies --repository . --documentation /path/to/BetterCPM-1.0-Documentation.zip --output /path/to/new-verification.json
```

The current baseline is selected from the independently identified Documentation ZIP and verified against its actual source commit. Original frozen lock/qualification records remain historical evidence; they are not silently rewritten to claim unchanged outer packaging after a later packaging-only correction.

## Acceptance and release update

Review the extracted reader layout as well as contents, links, licenses, source identity and deterministic reproduction. The [acceptance boundary](DOCUMENTATION-ACCEPTANCE.md) and [example/reference evidence ledger](../programmers/REFERENCE-STATUS.md) retain software scope and unexecuted-example limits. Further programmer/porting expansion does not become a 1.0 software blocker.

Only after checking the actual candidate, replace the published Documentation asset and synchronize its external index/checksum/notes. Preserve every other asset ID/hash, all software/source/media, the existing tag ref and software target. Record the new Documentation commit/hash/size separately from prior Documentation editions and original software identities. Do not rebuild the five software packages or move the tag to make the documentation revision look shared.
