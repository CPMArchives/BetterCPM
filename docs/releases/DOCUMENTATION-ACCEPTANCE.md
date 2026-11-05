# Documentation acceptance and release boundary

Acceptance is a local documentation decision. It does not authorize uploading assets, aligning a tag target, tagging or publishing. The five-package [lock](non-documentation-lock-1.0/LOCK.json) and its historical status fields remain unchanged.

## Required acceptance record

Keep a companion acceptance record outside the Documentation ZIP. It identifies the actual documentation commit, the built ZIP's SHA-256 and size, all five fixed package identities, the checks performed, their results and the limits below. Keeping the final receipt outside avoids a self-referential archive hash or a fictitious commit identity.

The ZIP's `DOCUMENTATION_CANDIDATE_NOT_ACCEPTED` build status records its state when assembled. Acceptance of those exact bytes is conveyed by the companion receipt; do not repack the accepted ZIP to change that field. Likewise the publication-plan JSON is a pre-build template, not the final asset index. Produce a separate accepted six-download index and checksum list after verification; retain earlier preflight records as history.

## Checks

1. Verify the five actual Source/System/Utilities ZIP sizes and SHA-256 hashes against the unchanged canonical lock. Check ZIP integrity, existing internal member checksum lists and software-source records without writing the archives.
2. Review all four manual entry points, task/concept organization, command reference structure, API coverage, installation/build instructions, licensing boundaries and release identities. Distinguish historical technical records from current contracts.
3. Build Documentation from a real, separately identified local commit. Check selected membership, local links/anchors, pinned external target paths, notices copied verbatim, and absence of withheld formats, development FDB, binaries/media and nested archives. Verify packaged source-derived bytes against that actual commit, including intentional link rewriting.
4. Reproduce the recorded cross-assembly checks for the four example sources and the CPX two-origin relocation comparison. Preserve the explicit absence of native/runtime qualification; do not silently turn unexecuted expansion examples into release software gates.
5. Run the split-provenance checker with the five real ZIPs and the committed Documentation ZIP. Rebuild the same Documentation commit into a separate new directory and compare output bytes. Record the final hashes/sizes and publication hold.

## Acceptance limits

Acceptance covers the reconciled Markdown/plain-text collection and editable examples at the recorded evidence level. It does not certify a new PDF/DOCX/HTML edition, perform physical-hardware qualification, rerun software emulator campaigns, resolve undetermined historical rights, or promote broader programmer/porting expansion to a 1.0 blocker. Existing errata and bounded observations remain visible. A genuine binary/content change requires explicitly reopening the affected software lock and applicable qualification.

The [publication procedure](DOCUMENTATION-PUBLICATION.md), [reference-status ledger](../programmers/REFERENCE-STATUS.md) and [licensing inventory](../LICENSING-INVENTORY.md) supply the detailed boundaries. A content or verification failure must be corrected and rebuilt before acceptance; a missing check must be reported as missing.
