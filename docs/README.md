# BetterCP/M documentation

Start with the installation guide for your platform, then use the manuals below. This collection describes the five locked 1.0 software packages. The dedicated Documentation package has separate provenance and uses a companion acceptance receipt for the exact built bytes. See the [acceptance protocol](releases/DOCUMENTATION-ACCEPTANCE.md). [Release authority and publication policy](releases/DOCUMENTATION-PUBLICATION.md).

## Four manuals

| Need | Manual |
| --- | --- |
| Perform everyday tasks and understand BetterCP/M | [User's Guide](manuals/Users-Guide.md): practical Part I, seven conceptual chapters in Part II. |
| Look up a command or utility | [Command and Utilities Reference](manuals/Command-and-Utilities-Reference.md): functional sections, alphabetized entries, separate resident/transient forms. |
| Write applications, CPXs, RSXs or service clients | [Programmer's Guide](manuals/Programmers-Guide.md), with [CP/M 2.2 API](programmers/CPM22-API.md), [BetterCP/M API](programmers/BETTERCPM-API.md), and [coverage/evidence ledger](programmers/REFERENCE-STATUS.md). |
| Adapt BetterCP/M to hardware | [Practical Porting Guide](manuals/Practical-Porting-Guide.md): staged bring-up, technical contracts, installation and qualification. |

## Supporting publications

- Installation: [patched cpmsim](platform/CPMSIM-INSTALLATION.md), [Model 4/trs80gp](platform/MODEL4-INSTALLATION.md), [named System-binding walkthrough](platform/MODEL4-SHIPPED-INSTALLATION.txt).
- Building: [Source Build and Reconstruction Guide](SOURCE-BUILD.md), [System Disk construction](releases/DISTRIBUTION-BUILD.md), [native build material](programmers/BUILD-DISK.md).
- Release: [working release notes](releases/RELEASE-NOTES-1.0.md), [locked delivered inventory](releases/DISTRIBUTION-MANIFEST.md), [six-download layout](releases/1.0-RELEASE-PACKAGES.md), [errata](releases/1.0-ERRATA.md), [format scope](platform/FORMAT-SUPPORT-1.0.md).
- Rights and attribution: [licensing boundaries](LICENSING.md), [component/package inventory](LICENSING-INVENTORY.md), and supplied notices/source companions.
- Publication: [formats, documentation selection and separate provenance](releases/DOCUMENTATION-PUBLICATION.md).

## Authority and history

The [non-documentation lock](releases/non-documentation-lock-1.0/README.md) fixes the five Source/System/Utilities archives, including embedded documentation. Updated manuals and external notes explain obsolete embedded guidance; they do not rewrite those archives or override licenses/known limitations. Source is locked at `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`, qualification through `2842d0eb0732683d9280a38d576c3dba423cb893`.

Architecture specifications remain technical contracts; dated engineering records remain evidence for their exact inputs. Historical surveys, stage-pending language and the earlier six-package preflight are not current completeness sign-off. The compact Documentation selection includes focused references; omitted source/history links lead to pinned repository records. Complete source and corresponding-source archives remain in the unchanged matching downloads.

The Command and Utilities Reference is the sole command/utility manual. Obsolete Utilities and standalone-command locators have been removed and their internal links updated. Old backup, development FDB 1.01 and PDF/DOCX editions are not current 1.0 manuals. Further programmer/porting expansion and native execution of new documentation examples remain explicitly separate from 1.0 software requirements.
