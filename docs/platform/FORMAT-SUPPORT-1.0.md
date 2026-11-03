# Disk-format support for 1.0

Package freeze is on hold. This document defines the qualification target; it does not accept final packages.

| Release-media layout | Catalogue ID | Independent basis | Use |
|---|---|---|---|
| CCS 332K | MMF017 | CCS System 300 CP/M Supplementary Manual rev B, appendices B-D | cpmsim System, Work, Utilities and NOAH |
| 800K data | MMI008 | Published TRSN geometry and sector order | Model 4 Work, Utilities and NOAH |
| BetterCP/M 780K System | BCPM780 | BetterCP/M BIOS cylinder-based layout | Model 4 System |

The production builder compiles BetterCP/M FDF v1 text from `metadata/DISK.FDF` and `metadata/release-formats.fdf`. It replaces MMF017 and MMI008 with independently authored, field-identical definitions, preserving their IDs, positions and public CONFIG display names. It appends BCPM780, giving 108 descriptors: all 107 historical compatibility entries plus the native System layout. Cold-boot defaults and guest assembly are unchanged. The migrated historical source remains reproducible and retains its provenance and undetermined-rights notice.

The independent CCS parameters come from [the vendor manual](https://bitsavers.org/pdf/ccs/CCS_System_300_CPM_Supplimentary_Manual_Sep81.pdf). The 800K parameters use [published TRSN tables](https://www.trs-80.com/sub-reference-dos-cpm.htm); their ancestry is not established. The native System parameters follow [the installed BIOS defaults](DEFAULT-TEST-DISKS.md). See the [bounded independent trial](../engineering/evidence/2026-11-03-release-formats/README.md) for derivation, CRC/full-file/full-volume checks and guest transfers. Independent authorship is a provenance improvement, not a claim of a newly discovered third-party rights grant.

## Supported release media and compatibility catalogue

The three layouts above are the release-media qualification scope for 1.0. Recorded trials cover emulator images, not physical controllers or universal disk interchange. The [Model 4 P2DOS trial](../engineering/evidence/2026-11-03-model4-p2dos/README.md) qualifies the clock lifecycle for the System image identified there. Final candidates still require matching image hashes and fresh-package installation checks.

The full historical compatibility catalogue remains available. Catalogue admission means a structurally valid descriptor, not successful runtime testing of each format on every controller. Five previously rejected historical records remain excluded for their recorded validity errors; this change removes no admitted format.

MMI012 remains an optional 790K historical compatibility format with its existing name and parameters. It is distinct from BCPM780: its directory starts at 10 KiB, while the release System directory starts at 20 KiB. Do not use MMI012 to identify the release boot disk. The other compatibility formats are retained without a blanket runtime qualification claim; additional physical/media qualification is post-1.0 work unless a failure affects release media.

All six packages and nested source kits exclude the original Montezuma DISK.FDF, utility binaries and disassemblies. Historical format data remain under the maintainer's accepted “distribution rights undetermined” notice. No format is silently relicensed by the project software/documentation split.
