BetterCP/M 1.2 System — Model 4
===============================

ASSEMBLY TEMPLATE — not a completed or accepted release package.
Remove this notice only after the release acceptance checks pass.

Contains the Model 4 System Disk and formatted work media. Utilities are a separate download for the same platform.

Read docs/platform/MODEL4-INSTALLATION.md before booting. Select the supplied disk geometry and work on writable image copies. Optional FreHD clock support requires appropriate hardware/emulation.

Combined layout: A: System, B: primary Utilities, C: companion Utilities, D: work. The startup script loads the integrated ADM-3A personality before displaying the banner.

Verify SHA256SUMS.txt before use. RELEASE.json identifies the exact source commit, included artifacts and qualification evidence. Preserve original media; use disposable copies for validation.

Retain all included license, permission, attribution and corresponding-source files. See the release notes for known limitations and the release-wide index for matching downloads.

TCAP 2.0: use the matching ADM3A, VT52 or ANSI integrated personality/renderer. RSX LOAD ANSI selects ANSI; RSX UNLOAD ANSI removes it. No separate screen backend is required. Rediscover the same-owner provider after layout changes. Existing utilities retain their documented interfaces; HELP and its topic library are included; NDR names annotate PATH output. See TCAP-Direct-ABI.md and tcap2.inc in the matching Source package.

Full manuals, developer interfaces and engineering evidence are in the separate BetterCPM-1.2-Documentation.zip and BetterCPM-1.2-Source.zip downloads from https://github.com/CPMArchives/BetterCPM/releases/tag/v1.2.
