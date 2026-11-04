# BetterCP/M 1.0 release identities and replacement freeze

**Qualified replacement set frozen, 4 November 2026.** The maintainer authorized
release identity promotion, replacement reconstruction/qualification and a new
freeze. No tag, release upload, publication or automatic PR merge was performed.
The source/evidence PR remains for maintainer review and merge.

## Exact source and preservation

The six immutable archives were built from `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8` on
`release/1.0-release-identities`, based on merged PR #608 at
`5e0c2cef5b88ba6ff4df88406ebb00c79ac100ee`. Later evidence-only commits do not
relabel the source inside the archives. Review is PR #609.

The original frozen source `54c503652fa957798bf2d0d636f4172851195926` and its six
read-only archives were independently rehashed unchanged. That earlier set
retains its historical development-identity exception; this replacement closes
that gate for its own exact hashes. Candidate filenames and roots are retained
to preserve the qualified bytes. Tagging/publication is a separate decision.

[Freeze manifest](../releases/frozen-1.0-release-identities-2026-11-04/FREEZE.json),
[exact six checksums](../releases/frozen-1.0-release-identities-2026-11-04/SHA256SUMS.txt),
[qualification ledger](../releases/frozen-1.0-release-identities-2026-11-04/QUALIFICATION.json)
and [raw evidence](../releases/frozen-1.0-release-identities-2026-11-04/evidence.tar.gz)
record the source, packages, execution receipts, tools and artifact hashes.

## Identity assignment and affected scope

44 explicit registry assignments advance the applicable first-party utility
revisions once. R, W and MOUNT continue their existing development counters as
registry-owned release identities. Component versions remain independent.
[Assignment policy and table](../releases/1.0-RELEASE-IDENTITIES.md) describes the
selection. Compilation does not increment counters, and no assigned-display
override was used. Automatic selected-input comparison still marks changed or
unknown builds as development builds. The normal VER heading is BetterCP/M 1.0;
its fixed-size field and development fallback are tested.

FDB retains 1.0 (001), with the exact PR #608 qualified pair:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| FDB.COM | 20585 | `96e2cc0a6fcb79ad9fd23db1e321342077d0bcf485fe6153c8de509b85cdac45` |
| FDBVIEW.OVL | 4608 | `622452b900982936c16c0cea7bbbf6da25d0e25ba8e04b2e473f3ccfbd5fc0d9` |

NOAH and the existing subsystem/module versions are retained. M4SCRN 1.7
revision 002 is unchanged. Against the 54c50365 reference there are 82 changed
System/Utilities artifact instances, including both platform CONFIG binaries
and the newer FDB pair. Of these, 76 instances supersede hashes in the original
35c56a03 utility lock. The static successor checker accepts only their explicit
old/new hashes and assignments; every undeclared historical-lock change remains
a failure. It verifies each old hash before applying the successor expectation.
The original lock is not edited or reported as matching changed utilities.

All original utility assembly bodies remain unchanged by this promotion except
RCP's heading field. The guest generator substitutes only the two pinned
identification occurrences per command and fails on an unexpected source
layout. Source/patch integrity and the actual guest assembler are recorded.
Shipped manual identity examples and standalone offline host-kit dependencies
were aligned with these release assignments.

## Qualification

| Gate | Result and scope |
| --- | --- |
| Component/build guards | 52 component tests, 15 distribution gates, fixed-field heading/fallback checks; automatic selection retained. |
| Compiled utilities | Version/help/parser and presentation suites; CRC, MD5SUM, COMPARE, PATCH, SEARCH, PIP transfer, CONFIG/DUP command checks; 368 full-core codec query cases. Additional relinked-body regressions pass for DASM (161 campaigns), DSYM, DLINK, TED (318 frontend cases), SQ/USQ and CR/UNCR and LZH/UNLZH round trips. |
| FDB | Full-core 47 query/fall-through plus two short-syntax checks; console-only ABI, exact screens, token boundaries and bounded tails; query stack 24/512 bytes. Earlier PR #608 converter/session/editor evidence applies to the identical pair. |
| Native cpmsim | 129 transient help/version cases plus nine resident queries, normal VER heading and 53K TPA; MOUNT error/list/cancel/eject/reinsert behavior, mounted-image reads and R/W transfer. |
| Native Model 4 | 117 transient help/version cases plus nine resident queries across three bounded batches. All 126 cases pass with expected identities and no development labels. |
| Model 4 memory workflow | Default 50K and safe interactive refusal; unload ADM3A then M4SCRN to 53K; viewer pages 1/4, menu and exit; unmodified SUBMIT STARTUP restores both providers and 50K; actual keyboard file read and cold-boot refusal. All 32 original files and 20480 reserved bytes preserved. |
| Installation, both targets | Named BCPM780 read and shipped CONFIG/SYSGEN export/install; populated filesystem preservation and installed cold boot. Model 4 package-to-installed-system difference is exactly offset 7030, E0 to A0, for the expected bootstrap binding. |
| Six ZIPs | Exact IDs/source, all member checksums, image receipts, individual file bytes, filesystems, source companions, licenses/notices and nested Montezuma exclusions. |
| Release identities | Independently decoded all six nonblank images: 108 binary instances contain no numeric development identification strings. This static count is distinct from the executed query counts above. |
| Exported Source | Clean offline build reproduces all eight delivered disk images, all System components, runtime and guest hashes, plus ROM/overlay artifacts. Source ZIP SHA-256 `1975f95144998c33ba704f37da3246343dd6ecc82ae7e4b014b8d7af372e71ca`. |
| Standalone cpmsim host kit | Independent offline build from the System ZIP reproduces the same runtime and guest utilities. |
| Documentation | Manuals/licenses agree across all six archives; supplied entrypoint links resolve in Documentation or corresponding Source. Current version examples aligned; unreconciled PDF/DOCX editions remain excluded. |

Both RAM reserved system areas retain their 35c56a03 hashes:

| Target | Reserved bytes | SHA-256 |
| --- | ---: | --- |
| z80pack | 27648 | `b9da7bf1e4036b4b486a5c00b3e13f7394f69fccabdd3865febb2ea1dd4b2339` |
| trs80gp | 20480 | `ca4c6eadc6b20c14550abdeb04769b1474de50a898027a4ba33abea85d0985c3` |

Historical conformance accounting and observations/exclusions remain applicable
to the matching RAM core. This is not a new exhaustive whole-suite execution or
a claim that identity-promoted utility binaries match their old hashes.

## Fresh protected XIP

The newly built ROM contains changed identification data, so its old ROM hash
was not carried forward. The unmodified stock protected-XIP driver passes on
its matching ROM, disk, overlays and instrumented emulator. All seven guard
controls pass; CPX reconstruction and dynamic RSX load/list/unload pass.
All 18 overlay files and 812 relocations are checked. Measured stack margins
remain system 8, BDOS 12 and loader 44 bytes.

| Input | SHA-256 |
| --- | --- |
| rom-boot.bin | `5c39d1cdfbc6435aa75b53df5afdbbe7f12b704ce9378f7f21cb02a2d0cbe859` |
| rom-boot.hex | `6f4b076ed32053211ece11ee7dcf363c201bbd702bac5bf9c7b26ce1cb724ef1` |
| rom-pack.bin | `f752d3e81dace535503080670b01d18f799cb9113a14749bafc6b0dffe1df479` |
| rsx-overlays/rom-rsx-overlays.json | `3189b769744c45a2ef7599dae4905a37cfb5aa068844edea29ac63f02e71a1ec` |
| Stock fixture disk | `65ece76e9693579ae885dd7ea03c25f1d7f4079833ccd0857e2f8eaef12a50f8` |
| Instrumented cpmsim | `981a69da751fb9dc5a25bcbd2dc56ccf270943605f463e9c5882b5e7811ef443` |

The stock qualification fixture contains its required manager tools rather
than the full cached development COM inventory, which overfills 332K. That
private inventory selection changes no production source or public package
membership. The exact ROM/overlay outputs match the untouched release snapshot
and the fresh exported-Source reconstruction. The normal six downloads retain
the qualified RAM defaults; this does not select a new default ROM package.

## Retained trial dispositions and release boundary

Failed/incomplete harness attempts remain in the raw evidence and are not
counted as passes. The initial boot assertion expected the old development
heading; its corrected automatic-heading gate passes. A small CPU fixture lacked
FDB's FD instruction support; the strict full-core suite passes instead. Native
stub cleanup was bounded and corrected; full System guest tests pass. An
oversized query script exceeded SUBMIT's existing buffer; three bounded batches
pass. The completed memory campaign initially failed only while writing a hash
from the wrong build directory; independent retained-screen, media-preservation
and correct-artifact checks validate the receipt. Full development ROM-disk
packing failures are separate from the passing selected stock fixture and the
passing manifest-driven public image rebuild.

The selected profile remains 53K cpmsim and 50K Model 4 startup. 56K fullram,
physical hardware and additional machines remain outside this qualification.
The frozen files cannot be edited in place. A change requires a new source/hash
set and applicable qualification. PR review/merge remains a maintainer action;
no release tag or publication is authorized here.

## Six frozen archives

| Archive | Bytes | SHA-256 |
| --- | ---: | --- |
| BetterCPM-1.0-Documentation-candidate.zip | 7163338 | `7f67508d62269d358d749e40af69b82d6e73d71511d36a2a0449f699b03de48a` |
| BetterCPM-1.0-Source-candidate.zip | 350224651 | `1975f95144998c33ba704f37da3246343dd6ecc82ae7e4b014b8d7af372e71ca` |
| BetterCPM-1.0-System-Model4-candidate.zip | 4157094 | `5760ebcb361c80fa632e323a016a95fac477183527c7f6d661721958e8a44b97` |
| BetterCPM-1.0-System-cpmsim-candidate.zip | 4463644 | `0d6fbff549088915e85470c718b1ce05e78980e460c7429b0e0e9f7e4746c6c4` |
| BetterCPM-Utilities-1.0-Model4-candidate.zip | 232607745 | `7b92378db28281b1e05d6d4bd4f7f480c3224c848c4120b93ee2abfd217577c9` |
| BetterCPM-Utilities-1.0-cpmsim-candidate.zip | 232575318 | `37477e6b06b13337c191e3c6d78be383ff7b14143c68d65bd0814e08ef7f5b1b` |
