# Current Documentation edition — 6 November 2026

The Documentation ZIP is rebuilt as a reader collection: README and four clearly named manuals at the top level, with supporting publications, licenses and provenance in separate folders. It contains one Command and Utilities Reference. The old Utilities locator, individual command locators and backup guide are removed; controlled links now point directly to maintained manuals/entries.

All agreed supporting publications remain: cpmsim and Model 4 installation guides, Source Build and Reconstruction Guide, Release Notes, Distribution Manifest, the README Documentation Index, and Licensing and Attribution. API chapters, examples and technical references remain supporting material; qualification evidence remains the separate unchanged download.

Documentation source: `466d25b6cadd37d32372b874472737ee4b40fe5a`. Documentation ZIP: 516698 bytes, SHA-256 `62bde1db3b48597ea986f70f19572db649fe7928362336c757dc3ce959083e90`. Software source remains `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`; tag `v1.0` remains at qualification merge `2842d0eb0732683d9280a38d576c3dba423cb893`. All five current software packages and the Qualification Evidence ZIP retain their existing asset IDs/sizes/hashes. This is not a shared-source rebuild or new runtime qualification.

The current index/checksums identify this Documentation edition. The earlier release and packaging notes below retain their historical identities and context; their prior Documentation hashes/layouts do not describe the current reader ZIP. Known limitations, license terms and qualification boundaries remain controlling.

---

# BetterCP/M 1.0

> **Unpublished draft — documentation accepted; do not tag or publish.**
> Five software packages remain locked. The separately versioned four-manual
> Documentation ZIP passed final acceptance. Tagging, publication and tag-target
> alignment remain held.


BetterCP/M is a CP/M 2.2-compatible operating system for patched z80pack/cpmsim
and the TRS-80 Model 4. This release brings together the system, its utilities,
complete matching source and manuals in seven downloads: four System/Utilities ZIPs, consolidated Source, Documentation and optional Qualification Evidence.

## Choose your downloads

| Download | Contents |
| --- | --- |
| `BetterCPM-1.0-System-cpmsim.zip` | cpmsim System and work disks, installation guide, and pinned offline runtime reconstruction kit. |
| `BetterCPM-1.0-System-Model4.zip` | Model 4 System and work DMKs, installation and startup instructions. |
| `BetterCPM-Utilities-1.0-cpmsim.zip` | cpmsim primary Utilities disk, NOAH companion disk, manuals and required source companions. |
| `BetterCPM-Utilities-1.0-Model4.zip` | The matching Model 4 Utilities and NOAH companion DMKs, manuals and source companions. |
| `BetterCPM-1.0-Source.zip` | Complete matching sources, native build material, tools, metadata, dependency tar and patches for offline reconstruction. |
| `BetterCPM-1.0-Documentation.zip` | Four principal manuals with API chapters, original examples, installation/build guidance, licensing and technical references in Markdown/text form. |
| `BetterCPM-1.0-Qualification-Evidence.zip` | Optional historical qualification archives, engineering receipts and review records, with verified original paths and restoration instructions. |

System and Utilities are separate downloads. For a combined installation use
A: System, B: primary Utilities, C: NOAH companion, D: work. Preserve the supplied
images and run writable copies. Read the platform installation guide first.
Use the supplied Source ZIP for the tested offline rebuild; GitHub's automatic
source archives do not include the packaged dependency tar.

## Included in 1.0

- CPX and RSX extensions, persistent command history, configuration and system installation tools.
- FDB.COM 1.0 (001), with catalogue editing, display/compare and text/binary conversion; keep its matching FDBVIEW.OVL together with it.
- An editable 108-entry DISK.FDB built from BetterCP/M's native FDF v1 definitions. Individual foreign formats still depend on suitable media, controller support and correct bindings; this is not a claim that all 108 formats were tested on physical hardware.
- PIP, ED, TED, DDT, DUMP, assembler/linking and analysis tools, archive/compression tools, SEARCH, CRCKSUM, MD5SUM, PATCH and COMPARE. The NOAH companion contains NOAH, PATCH and COMPARE; keep NOAH.COM and NOAH.OVL matched.
- Both System disks carry optional P2DOS.RSX. Startup leaves clocks and P2DOS unloaded. When needed, load the platform clock provider first: ZPRTC on cpmsim or FREHDCLK on a suitably equipped Model 4, then P2DOS.
- Released first-party utility identities. M4SCRN remains 1.7 revision 002; utility/module/subsystem versions remain independent of the distribution version.

## Memory and supported environments

The default cpmsim disk reports 53K TPA. Model 4 startup loads M4SCRN followed
by ADM3A and reports 50K. Interactive FDB needs the unloaded 53K environment:
unload ADM3A, then M4SCRN; after leaving FDB use the unmodified `SUBMIT STARTUP`
to restore the supplied startup environment. FDB help and version queries work
at the normal Model 4 startup allocation. Follow the FDB manual for the full
workflow. The optional 56K fullram and checked RAM profiles are deferred beyond
this release.

cpmsim needs the pinned BetterCP/M runtime patches and helpers; stock upstream
cpmsim is insufficient. The Source and cpmsim System downloads include the
verified offline reconstruction inputs. Model 4 qualification used trs80gp.
Physical Model 4 media transfer, Model 4D/4P and additional hardware/platforms
remain outside these emulator receipts.

## Qualification and known limitations

Both platform installation and cold-boot workflows passed with file preservation.
The final Source ZIP reproduces all eight disk images, the runtime, guest tools
and ROM/overlay artifacts. The standalone cpmsim System host kit also rebuilds
offline. Native query checks passed: 129 transient plus nine resident cases on
cpmsim, and 126 cases on Model 4. The Model 4 FDB memory/viewer/startup-restoration
workflow passed. The refreshed protected-XIP ROM separately passed the stock
driver and all seven guard controls; this does not change the default RAM downloads.
See the [qualification and exact-hash freeze record](https://github.com/CPMArchives/BetterCPM/blob/2842d0eb0732683d9280a38d576c3dba423cb893/docs/engineering/Release-Identity-Promotion-1.0.md) for scope and evidence.

Existing compatibility dispositions remain: command tails preserve case, some
extension lookup uses fixed A0, and runtime carriers such as BATCHIO for XSUB
must be available in A0. Earlier conformance observations and excluded cases
have not been recast as new passing tests.

The recorded host Caps Lock and pending-input/CONST observations remain bounded
by their original tests. A pre-corrupted history object with valid signature
but unsafe lengths/counts can damage memory (BCPM-AUD-003); no supported command
sequence producing that malformed state was established. Its hardening and
general historical-oracle cleanup (BCPM-AUD-007) remain deferred. The 104/105
clock adapters T104C3/T104Z8 are also deferred. The documentation publication format is Markdown/text; older PDF/DOCX editions are excluded. New programmer/porting examples have their own evidence ledger and do not add software release requirements.

## Licenses and format data

Original BetterCP/M software and reusable code examples use GPL-2.0-or-later;
original manual prose and illustrations use CC BY 4.0. Third-party works retain
their own terms. Every package carries the applicable licenses, provenance and
THIRD-PARTY-NOTICES.txt. Montezuma Micro utilities, disassemblies and the original
DISK.FDF are excluded, including from nested source archives. Historical format
parameters retain the provenance and distribution-rights-undetermined notice
in the supplied records; the project licenses do not grant rights over those data.

## Exact files and retained build-time wording

The five Source/System/Utilities downloads are byte-for-byte copies of the frozen archives from source
`30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`. Their outer download names omit `-candidate`; their ZIP contents,
internal checksums and internal `-candidate` directory names are unchanged.
Some embedded README/status fields and release notes therefore still say
candidate, not accepted, or freeze on hold. Those are pre-qualification build
records, superseded for these exact files by the final freeze accepted through
PR #609 and the release-wide index supplied alongside the downloads. Dated
engineering history remains historical evidence. This paragraph does not
supersede usage instructions, license terms or known limitations.

`BetterCPM-1.0-SHA256SUMS.txt` lists the five unchanged locked hashes and the accepted Documentation hash under their final download names. `BetterCPM-1.0-RELEASE.json` records software source, qualification merge and the actual documentation commit separately. Earlier publication/preflight records are historical snapshots.

The draft retains its existing proposed target `2842d0eb0732683d9280a38d576c3dba423cb893`. This update does not align the target to the documentation merge, create a tag or publish the release. A draft tag-name field is not an existing Git tag.


## Revised documentation provenance

The new Documentation ZIP records its actual documentation commit separately from locked software source `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`. It does not claim all six downloads were rebuilt together. Source and embedded manuals in the five archives stay unchanged; the dedicated updated collection explains obsolete status/navigation without overriding license terms or known limitations. [Four-manual index](https://github.com/CPMArchives/BetterCPM/blob/549378120a8220cf546deb9c7602cfb3f73b6b0e/docs/README.md), [publication plan](https://github.com/CPMArchives/BetterCPM/blob/549378120a8220cf546deb9c7602cfb3f73b6b0e/docs/releases/DOCUMENTATION-PUBLICATION.json) and [format/verification procedure](https://github.com/CPMArchives/BetterCPM/blob/549378120a8220cf546deb9c7602cfb3f73b6b0e/docs/releases/DOCUMENTATION-PUBLICATION.md).

The accepted Documentation commit is `549378120a8220cf546deb9c7602cfb3f73b6b0e`, separate from software source `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8` and qualification merge `2842d0eb0732683d9280a38d576c3dba423cb893`. The accepted ZIP is 553,662 bytes with SHA-256 `8c184db835c90a2c60372b4f5a2bb93029fa4e772d849c6cdf1c44835e781fa9`. Its internal pre-acceptance candidate status remains unchanged; the companion acceptance receipt accepts these exact built bytes. The new archive uses root `BetterCPM-1.0-Documentation/`; the five locked roots remain unchanged.

Final checks passed: five actual archive sizes/hashes, ZIP integrity, 2,835 internal member checksums and source identities; 122 Documentation files, 1,003 local links, 78 pinned repository target paths, verbatim selected legal records, nine packaging tests and identical repeat builds. All four example cross-assembly outputs and the CPX relocation comparison reproduce their recorded evidence. These checks do not repeat software runtime qualification. Native/runtime trials of new documentation examples, physical hardware, rendered editions and further programmer/porting expansion remain separate from the locked 1.0 release requirements.

The [acceptance receipt](https://github.com/CPMArchives/BetterCPM/blob/main/docs/releases/documentation-sync-1.0/ACCEPTANCE.json) and release index record final identities. The plan embedded in the accepted ZIP is explicitly a pre-build template, not a new shared-source claim. No tag-target alignment, tagging or publication was performed.


## Software ZIP root correction — 2026-11-06

All five software ZIP root directories now match their published filenames without `.zip`. Only the enclosing root path prefixes changed; every enclosed file retains identical bytes, including historical build metadata and internal checksum files. The ZIP bytes, sizes and SHA-256 hashes have changed. The release index and outer checksum file record the corrected archives and supersede earlier archive hashes/root names. Earlier statements that the distributed ZIP bytes and candidate roots remain unchanged describe the original packaging. Software source, qualification, release tag and Documentation ZIP are unchanged.


## System image-directory correction — 2026-11-06

The cpmsim System package now stores its System/work images and diskdefs under `images/cpmsim/`; the Model 4 System package uses `images/Model4/`, matching Utilities. Disk images, diskdefs, executable and source payload bytes are unchanged. The two System READMEs, platform installation guides and internal manifests were updated for the layout. Their ZIP hashes/sizes and the release index/checksums supersede the previous packaging values. The other four ZIPs and release tag are unchanged. This supersedes the earlier root-only correction statement for these two System packages.


## Utilities source-download correction — 2026-11-06

Both Utilities ZIPs now omit the duplicated `source/` directory. Download the matching [BetterCPM-1.0-Source.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-Source.zip) from this same release for complete corresponding source and build material, including all 24 unchanged companions under `source/native-companions/` (applicable GPL texts are retained under licenses). Source ZIP SHA-256: `bd4358f80e941bf8ba927a5b25df617829256a560fd45f0729820229d2e31360`. GPLv2 section 3 permits equivalent source access from the same download place; keep that source available while offering these binaries. For offline/media redistribution, include the matching Source ZIP unless using another valid compliant method. Utilities license/attribution records and disk-image bytes are preserved; package instructions, source-access notices and internal/outer manifests are updated. Historical on-disk notices/build evidence refer to the original bundled location; exact companions are now in the matching Source ZIP. This supersedes earlier claims that Utilities source companions remain inside these ZIPs. Other ZIPs and the release tag are unchanged.


## Source consolidation — 2026-11-06

The Source ZIP now supplies one shared repository at `source/BetterCPM/`; the redundant full-repository DASM/TED tarballs were removed. All 2,514 original main-source files retain identical bytes. Both original source manifests, native TED source and native build report are preserved unchanged in that tree. `SOURCE-LAYOUT.txt` provides current instructions; `SOURCE-CONSOLIDATION.json` retains the old archive hashes, sizes and member mapping. Native companions and ZSM4 source remain available. Utilities source-access instructions and manifests now identify this consolidated Source ZIP, SHA-256 `549c99221abdfce5d32cb5e9a51b5fb7c3835b10f06dcc87f95e6ce950aa89f7`. Earlier references to bundled DASM/TED tarballs describe historical packaging and are superseded by this layout. System and Documentation ZIPs, software versions and release tag remain unchanged.


## Qualification evidence separated — 2026-11-06

Historical qualification archives, engineering receipts and review records are now in [BetterCPM-1.0-Qualification-Evidence.zip](https://github.com/CPMArchives/BetterCPM/releases/download/v1.0/BetterCPM-1.0-Qualification-Evidence.zip). All 306 moved files retain identical bytes and original Source-relative paths, recorded in `EVIDENCE-MANIFEST.json`. The Source ZIP retains build inputs and provides `EVIDENCE-ACCESS.txt`, a mapping manifest and verified `restore_evidence.py` helper to restore local references and original source-manifest coverage. ZSM4 source remains once at `source/BetterCPM/third_party/zsm4/source.tar.gz`; the identical native-companions alias was removed. Utilities source-access records identify the updated Source ZIP (SHA-256 `af180f011dcec9e79116336fe9d2c3ac2b55b393d1bc3608c51742ad32e7f8e3`). Previous six-download wording is historical: the release now offers seven ZIPs, including the optional evidence companion. This is packaging only: software versions, qualification claims, System/Documentation ZIPs and the release tag are unchanged.


## Navigation and publication-status correction — 2026-11-06

All seven ZIPs now identify published status through PACKAGE-STATUS.md and current metadata. Missing subset-manual links route to verified pinned repository files or explicitly identify omitted historical material. Original evidence files remain unchanged; edited wrapper/document originals are preserved under PACKAGING-HISTORY/. Source provides verify_historical_manifests.py for the preserved original DASM/TED manifests after optional evidence restoration. Stale current TED/DASM/ZSM4 location notices are corrected. Software and utility versions, source-code and disk-image bytes are unchanged. This does not repeat runtime qualification or extend its scope. Current archive hashes supersede previous packaging hashes, including Documentation.
