# BetterCP/M 1.0 documentation survey — 2026-11-01

Scope: repository documentation and release packaging inputs at main b81c255,
plus the current uncommitted Model 4 results. This is an inventory and targeted
consistency review, not a line-by-line technical or legal certification.
No manuals or release packages were changed by this survey.

## Existing documentation and remaining work

| Area | Existing material | Remaining work |
| --- | --- | --- |
| System operation | `docs/user/users_guide.md`: 17 chapters, appendices, system commands, configuration, extensions, terminals, disks and troubleshooting | Check command examples and documented help/options against current binaries; preserve the resident/transient distinction. Recent DIR footer formatting is already documented. |
| Utilities | `docs/user/utilities_manual.md`: NOAH, SEARCH, COMPARE, CRCKSUM, MD5SUM, PATCH, DUMP, DDT, TED, DASM/DSYM/DLINK, compression, ZSM4/LINK | Replace stale implementation/selection and deferred-manual-campaign introduction. Recent CRCKSUM grouping/count and NOAH overlay location are already documented. Audit against actual disk inventory and current options. |
| Individual utility entries | Separate BYE, compression, assembler/linker and checksum/patch documents | Establish which are authoritative or derived. `crc_manual_entry.md` still describes the superseded continuation-row /40 layout, whereas the integrated manual correctly describes complete two-column blocks. |
| cpmsim installation | `docs/platform/CPMSIM-INSTALLATION.md` | Patch prerequisites, pin, ordered runtime patches, offline reconstruction, helpers, mounts and MOUNT/R/W are covered. Fix guest `VER /BANNER` example to force transient `:VER /BANNER`. Verify commands from a fresh extracted package, including optional Utilities. |
| Model 4 installation | `docs/platform/MODEL4-INSTALLATION.md` | Geometry, A-D assignments, startup and CLI provided. Fix resident VER example; replace maintainer-specific launch wording with ordinary user instructions. Explain fully quitting/remounting when replacing images. Reconcile validation links to reduced completed smoke scope. Fresh-package verification remains separate. |
| Disk contents | `docs/releases/DISTRIBUTION-MANIFEST.md`, metadata/distribution.json, package inventories | Reconcile prose against generated inventories: manifest still says five downloads, CRCKSUM 006, and an obsolete startup sequence. Actual startup loads M4SCRN then ADM3A before the banner. |
| Release notes and package guidance | `RELEASE-NOTES-1.0.md`, `1.0-RELEASE-PACKAGES.md`, six README templates | Six-asset layout is documented. Replace stale full-manual-campaign and earlier packaging-failure action wording with current dated evidence. Keep remaining acceptance and historical failures distinct. |
| Documentation navigation | `packaging/1.0/DOCUMENTATION-CONTENTS.md` becomes Documentation ZIP CONTENTS.md | Contents page already exists. Update its validation entry; verify links in extracted archives, including links to source/specification material outside Documentation. |
| Build/reproduction | `DISTRIBUTION-BUILD.md`, `docs/programmers/BUILD-DISK.md`, cpmsim guide, component READMEs and native companions | Consolidate a clear fresh-source-package entry path for system and Utilities builds, prerequisites and pinned dependencies. Native build disk guide is not a complete host release reconstruction guide. Correct old WHEREIS/README status wording in distribution build guide. |
| Programmer references | RSX/CPX guide, monitor RSX development, BIOS disk configuration, CONFIG/DUP, shared input and archive library documents | Audit public entry points and current ABI/version references. Existing material is substantial; a wholesale new manual is not established as necessary for 1.0. |
| Architecture | Numbered architecture documents and existing architecture PDF/DOCX | Identify implemented 1.0 contracts versus historical proposals/post-1.0 design. Do not publish an old rendered edition as current without comparison. |
| Error reference | User's Guide chapter 12 and Appendix F, including disk/BIOS, SYSGEN, CONFIG and extension messages | Audit exact message strings, causes and recovery against source. Extend gaps; do not start a duplicate appendix. |
| Licensing/attribution | Third-party LICENSE, permission and provenance files; native/corresponding-source packaging | Produce a component-level rights/attribution/source audit tied to package membership. No top-level project LICENSE or consolidated NOTICE was found in tracked filenames; determine the intended first-party terms rather than choosing them automatically. Third-party notices alone do not establish first-party distribution terms. |
| Versioning | Utility/subsystem standards, metadata TSVs, development identity records | Check banner/manuscript/package agreement and apply established -dev rules; package version does not authorize stripping development suffixes. |
| Qualification | Historical records plus dated manual and new automated smoke evidence | Reduced Model 4 smoke checks are executed. Preserve untested original assertions and historical outcomes. New scripts/results are not yet committed, so existing candidate ZIPs cannot include them. |

## Rendered manuals

Tracked User's Guide PDF/DOCX and architecture PDF/DOCX exist. The package builder
intentionally excludes PDF/DOCX pending reconciliation with editable sources.
No Utilities PDF/DOCX is present in docs/user. Decide the release formats:
regenerate and inspect current printable editions if desired, or explicitly
ship Markdown for 1.0. A Utilities printable edition is a deliverable only if
that format is selected; it is not evidence of missing manual content.

`users_guide_backup.md` is also present. The Documentation builder currently
includes every tracked textual docs file, so this backup is included along
with engineering history. Prefer an explicit current-manual selection or clear
historical labeling to avoid competing apparent editions.

## Confirmed stale public statements

README still describes utility completion as remaining work and says the
terminal monitor implementation is pending. Both disagree with the implemented
release candidate. Utilities introduction likewise anticipates future selection
and chapters already present. These are live entry-point fixes, unlike dated
engineering records that should retain their historical wording.

## Suggested completion order

1. Correct public entry points, installation examples, disk manifest and release
   status. Preserve historical evidence and identify current authoritative sources.
2. Audit commands/options, duplicate entries and Appendix F against current source
   and binaries; check links in the actual package layout.
3. Complete first-party/third-party licensing, attribution and corresponding-source
   audit and the source-package build entry instructions.
4. Generate selected printable editions from reconciled editable sources and inspect
   contents, tables, pagination and cross-references.
5. Assemble a new candidate from the merged documentation and recorded evidence;
   verify fresh-package instructions, hashes and final conformance applicability.

The Model II port and P&T-inspired future features are separate work. Do not
expand the required 1.0 platform/manual scope merely because their media are
available in the maintainer's local collection.
