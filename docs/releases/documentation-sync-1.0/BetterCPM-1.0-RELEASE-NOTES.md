# BetterCP/M 1.0

> **Unpublished draft — documentation accepted; do not tag or publish.**
> Five software packages remain locked. The separately versioned four-manual
> Documentation ZIP passed final acceptance. Tagging, publication and tag-target
> alignment remain held.


BetterCP/M is a CP/M 2.2-compatible operating system for patched z80pack/cpmsim
and the TRS-80 Model 4. This release brings together the system, its utilities,
complete matching source and manuals in six downloads: five locked qualified archives plus the separately revised, accepted Documentation ZIP.

## Choose your downloads

| Download | Contents |
| --- | --- |
| `BetterCPM-1.0-System-cpmsim.zip` | cpmsim System and work disks, installation guide, and pinned offline runtime reconstruction kit. |
| `BetterCPM-1.0-System-Model4.zip` | Model 4 System and work DMKs, installation and startup instructions. |
| `BetterCPM-Utilities-1.0-cpmsim.zip` | cpmsim primary Utilities disk, NOAH companion disk, manuals and required source companions. |
| `BetterCPM-Utilities-1.0-Model4.zip` | The matching Model 4 Utilities and NOAH companion DMKs, manuals and source companions. |
| `BetterCPM-1.0-Source.zip` | Complete matching sources, native build material, tools, metadata, dependency tar and patches for offline reconstruction. |
| `BetterCPM-1.0-Documentation.zip` | Four principal manuals with API chapters, original examples, installation/build guidance, licensing and technical references in Markdown/text form. |

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
