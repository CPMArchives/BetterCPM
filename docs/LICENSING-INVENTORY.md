# Licensing, attribution and source-delivery inventory

This inventory reconciles existing project records with package roles. It records the supplied terms and retained distribution bases; it does not create a new rightsholder grant. Read [LICENSING](LICENSING.md), LICENSE, COPYING, NOTICE and the individual provenance records. Original inventory prose is CC BY 4.0.

| Work | Recorded basis / records | Package and source obligation |
| --- | --- | --- |
| Original BetterCP/M software/tools/tests and reusable manual examples | GPL-2.0-or-later; root LICENSE/COPYING/NOTICE; example SPDX notices | Matching software/source remains in locked Source and required independent companions. New documentation example sources travel in Documentation; no new COM program is added to media. |
| Original manual prose/illustrations | CC BY 4.0; LICENSES/CC-BY-4.0.txt | Retain credited authors, license/source attribution and identify modifications. The new documentation provenance identifies the revised collection separately from software. |
| DRI LINK 1.3 | CP/M permission/clarification and `third_party/dri-link/provenance.json`; no separate LINK-specific grant asserted | Unmodified native interface/identity. Preserve LINKCOPY.TXT, TOOLINFO and host permission/provenance in Utilities; Source retains its records. |
| DRI-derived/reference ED, PIP, DDT, DUMP and compiler/reference material | Component-specific `third_party/dri-*/` permissions/provenance and existing notices | Preserve original/reference scope separately from original BetterCP/M code grants. Do not claim blanket GPL/CC coverage for historical imports or reference fixtures. |
| ZSM4 4.7 | GPL-2.0-or-later, upstream notices and provenance | Complete ZSM4 source/manual/tests/Makefile companion remains with Utilities and matching Source material. A link to the separate Source download does not remove the independent Utilities obligation. |
| Hector Peraza TED and adaptation | GPL-2.0-or-later, credits/modification history, TED records | Keep BetterCPM-TED-SOURCE companion and notices with Utilities; retain native build/source mapping in Source. |
| Richard Conn DASM / SIG/M 91 and maintained adaptation | Historical provenance/credits and maintainer-recorded distribution basis under `third_party/dasm/` | Keep DASMCOPY and complete companion. A generic unsigned submission form is not an author-specific grant; no invented modern license. |
| z80pack / patched cpmsim and helpers | Upstream LICENSE/module COPYING, pinned source/patch/input records | cpmsim System's independent host kit and Source keep the complete selected offline tar, patches and notices. Preserve helper source/identity with runtime. |
| CPMArchives CP/M Tools snapshot | GPL records and pinned source mapping at `3e5eee55cac154e125659aadaa865b2c66e7d06a` | Seven COMs occur in full/nested source snapshots, outside selected System/Utilities disks. Keep their 66-file corresponding source/build companion wherever those binaries are conveyed. |
| Historical format data in native FDF/FDB | Provenance and “distribution rights undetermined” notice; no new grant verified | Preserve notice and exclusion policy. Native release catalogue includes 108 definitions; independent MMF017/MMI008 authorship is not an asserted third-party grant. Original Montezuma DISK.FDF, utility binaries and disassemblies remain excluded from all release packages/nested kits. |
| Quotations, scans, screenshots, evidence and third-party examples | Work-specific notices and rights | The selected Documentation package contains original manuals and legal/provenance text, not a general historical-scan/software/evidence redistribution. Omitted records can be referenced through pinned source links. |

## Delivery rules for the documentation revision

The explicit [documentation selection](../packaging/1.0/documentation-selection.json) includes the four manuals, supporting references, original example source/check records, both first-party license texts, NOTICE and selected legal/provenance text under `licenses/third_party/`. It excludes obsolete rendered editions, backup/development manuals, binaries, disk images, nested source tarballs and historical evidence archives. The five locked packages already carry their independent source/notice material and must not be repacked to synchronize this prose.

Every Documentation ZIP needs README, CONTENTS, THIRD-PARTY-NOTICES, licensing index, immutable lock reference, separate source identity, release record and complete per-member checksums. Legal records are copied verbatim; link rewriting in manual prose is not permission to alter a license or grant. Links to matching software/source do not imply another installed component.

## Audit boundary

The selection and tests can establish required notice/text presence, exact copied legal bytes, prohibited member rejection, valid links and split identities. They cannot manufacture rights for undetermined historical material or establish source completeness of a newly changed binary. This work introduces no replacement binary; fixed archives retain their recorded component/source/license audit and exact-hash evidence. Final packaging review must inspect the actual selected Documentation ZIP and verify the five archive hashes independently. License terms, permissions and frozen records are unchanged.
