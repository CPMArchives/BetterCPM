BetterCP/M Utilities 1.1 — Model II
==================================

ASSEMBLY TEMPLATE — not a completed or accepted release package.
Remove this notice only after the release acceptance checks pass.

Contains only the 584K BCM2SS primary and companion IMD images for Model II, with instructions, licenses and checksums. Corresponding source is available in the separate BetterCPM-1.1-Source.zip download from the same release.

Use this download with the Model II System package. Each of the other platforms has a separate Utilities download. Mount primary Utilities as B: and companion as C: beside System A: and work D:. The companion retains the BetterCPM-NOAH name and contains NOAH, PATCH, COMPARE and the optional SUPPDISK supplement. Inclusion of that supplement does not qualify its formats on Model II; use only BCM2SS on this target. CRCKSUM and MD5SUM are on the primary disk. Keep NOAH.COM and NOAH.OVL matched.

Consult the Utilities Manual for per-program requirements. These disks are not bootable replacements for the System Disk.

Verify SHA256SUMS.txt before use. RELEASE.json identifies the exact source commit, included artifacts and qualification evidence. Preserve original media; use disposable copies for validation.

Retain all included license, permission, attribution files. Obtain matching corresponding source from the Source download. See the release notes for known limitations and the release-wide index for matching downloads.

Model II is qualified only under trs80gp 2.5.8 with 64 KiB RAM and BCM2SS single-sided IMD media. Physical hardware, Models 12/16/16B and other disk formats are unverified. Utilities includes primary and companion IMDs.

TCAP 2.0: use the matching ADM3A, VT52 or ANSI integrated personality/renderer. RSX LOAD ANSI selects ANSI; RSX UNLOAD ANSI removes it. No separate screen backend is required. Rediscover the same-owner provider after layout changes. Existing utilities retain their documented interfaces; HELP is not included. See TCAP-Direct-ABI.md and tcap2.inc in the matching Source package.
