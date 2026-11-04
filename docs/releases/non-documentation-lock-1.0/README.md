# BetterCP/M 1.0 non-documentation lock

**Locked by maintainer instruction, 4 November 2026 (Taipei).** The Source,
System and Utilities packages and the software behavior they contain are fixed
for 1.0. Documentation is incomplete and is now the remaining synchronization
workstream. No documentation-completeness sign-off is inferred from earlier
link, consistency, license or reproduction checks.

[Machine-readable lock](LOCK.json) · [five package checksums](SHA256SUMS.txt) ·
[exact image/file contents](CONTENTS.json) · [preservation verification](VERIFICATION.json).

## Exact baseline

- **Software/artifact source:** `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`.
- **Qualification accepted through #609:** merge `2842d0eb0732683d9280a38d576c3dba423cb893`.
- **Reviewed repository and documentation starting reference:** `31dba474927be420796ab9e4cb3c75daddd6f0ab`, after #610.
- **Authoritative delivered contents:** the five exact ZIPs below and the eight image inventories in CONTENTS.json. The Source ZIP records the matching code, dependency pins, builders and component identities.
- **Evidence:** [qualified frozen set](../frozen-1.0-release-identities-2026-11-04/QUALIFICATION.json) and [qualification report](../../engineering/Release-Identity-Promotion-1.0.md), applied only to matching bytes. No new runtime test run is claimed by this preservation check.

The lock includes FDB.COM 1.0 revision 001 and its matching viewer, both CONFIG
binaries, the 108-entry DISK.FDB, all other shipped programs/modules, platform
bindings, startup defaults, help/version text, utilities membership, license
notices and required source companions. FDB, CONFIG and the catalogue are no
longer open for 1.0 integration.

## Fixed behavior for the manuals

| Area | Documentation baseline |
| --- | --- |
| cpmsim | Qualified patched runtime, default RAM System, 53K reported TPA with no optional modules loaded. |
| Model 4 | Startup loads M4SCRN then ADM3A; 50K reported TPA. |
| FDB | Interactive workbench requires unloaded 53K; help/version work at normal Model 4 startup. Unload ADM3A then M4SCRN; restore with unmodified SUBMIT STARTUP after exit. Keep FDB.COM and FDBVIEW.OVL matched. |
| CONFIG/catalogue | Record current commands and named BCPM780 normalization/binding behavior; do not redesign it during the documentation sync. |
| Installation | Shipped CONFIG/SYSGEN workflows and populated-file preservation/cold boot on both emulator targets. The Model 4 installed payload has the expected offset 7030 E0→A0 bootstrap-binding difference. |
| Other profiles | Current-source protected XIP has separate evidence; it does not replace default RAM downloads. 56K fullram and optional checked profiles remain deferred. |
| Limits | Preserve existing conformance observations/exclusions, AUD-003/AUD-007 dispositions, bounded Caps Lock/CONST observations, deferred 104/105 adapters and emulator-only qualification scope. |

Exact component identities, image and per-file hashes are recorded alongside
this document. Document the qualified behavior; do not change code, help text,
versions, format definitions or disk contents to fit an old manual. If an
actual software defect or behavior change is required, explicitly reopen the
affected lock and perform the applicable qualification before replacing it.

## Five preserved packages

| Final download name | Bytes | SHA-256 |
| --- | ---: | --- |
| BetterCPM-1.0-Source.zip | 350224651 | `1975f95144998c33ba704f37da3246343dd6ecc82ae7e4b014b8d7af372e71ca` |
| BetterCPM-1.0-System-Model4.zip | 4157094 | `5760ebcb361c80fa632e323a016a95fac477183527c7f6d661721958e8a44b97` |
| BetterCPM-1.0-System-cpmsim.zip | 4463644 | `0d6fbff549088915e85470c718b1ce05e78980e460c7429b0e0e9f7e4746c6c4` |
| BetterCPM-Utilities-1.0-Model4.zip | 232607745 | `7b92378db28281b1e05d6d4bd4f7f480c3224c848c4120b93ee2abfd217577c9` |
| BetterCPM-Utilities-1.0-cpmsim.zip | 232575318 | `37477e6b06b13337c191e3c6d78be383ff7b14143c68d65bd0814e08ef7f5b1b` |

The original frozen filenames/roots and renamed download copies are both
identified in LOCK.json. All five hashes/sizes match the read-only local copies
and the existing GitHub assets. No five-package asset is replaced or rebuilt.

## Documentation sync boundary

Only the dedicated **Documentation ZIP** is planned for rebuilding. Complete
and synchronize the manuals, installation guides and release notes against the
locked source, delivered files and actual interfaces. The working repository
reference above is a starting point, not an assertion that its manuals are complete.

The Source ZIP and source archives/guides nested inside the two Utilities and
two System packages stay byte-for-byte unchanged, including their embedded
documentation. They are historical snapshots. The new Documentation package
and synchronized external notes must clearly explain/correct obsolete embedded
guidance and pre-qualification status wording. License terms and third-party
notices are not overridden by that explanation.

The future Documentation ZIP needs its **actual documentation revision** and
the separate locked **software revision** in its provenance. Do not claim that
all six packages were rebuilt from a single new commit. The old six-package
checker's single-source-commit requirement must be adapted to the approved
split: five fixed hashes/source identities plus a separately identified and
verified Documentation ZIP. It must continue rejecting any undeclared change
to the locked five; do not waive identity checks or relabel old archives.

After the documentation is complete, rebuild only that ZIP, validate its
contents/links/notices/examples, and update its hash in the checksum list and
release index. Refresh the provisional documentation and notes in the draft;
preserve all five locked ZIPs. Align the proposed tag only after final review.
No tag-target change, tag creation, publication or automatic PR merge is part
of this lock. The draft remains unpublished and explicitly provisional.
