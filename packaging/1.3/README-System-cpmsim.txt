BetterCP/M 1.3 System — cpmsim
==============================

ASSEMBLY TEMPLATE — not a completed or accepted release package.
Remove this notice only after the release acceptance checks pass.

Contains the cpmsim System Disk and formatted work media. Utilities are a separate download for the same platform.

Read docs/platform/CPMSIM-INSTALLATION.md before booting. BetterCP/M requires patched cpmsim; build the runtime using the included instructions, pinned sources and patches in host/BetterCPM/. Keep the generated environment.json. Stock cpmsim is insufficient.

Mount writable image copies: A: System, B: primary Utilities and C: companion Utilities when installed, D: work. Start cpmsim with its matching srctools on PATH. BYE /Y exits.

Verify SHA256SUMS.txt before use. RELEASE.json identifies the exact source commit, included artifacts and qualification evidence. Preserve original media; use disposable copies for validation.

Retain all included license, permission, attribution and corresponding-source files. See the release notes for known limitations and the release-wide index for matching downloads.

TCAP 2.0: use the matching ADM3A, VT52 or ANSI integrated personality/renderer. RSX LOAD ANSI selects ANSI; RSX UNLOAD ANSI removes it. No separate screen backend is required. Rediscover the same-owner provider after layout changes. Existing utilities retain their documented interfaces; HELP and its topic library are included; NDR names annotate PATH output. See TCAP-Direct-ABI.md and tcap2.inc in the matching Source package.

Full manuals, developer interfaces and engineering evidence are in the separate BetterCPM-1.3-Documentation.zip and BetterCPM-1.3-Source.zip downloads from https://github.com/CPMArchives/BetterCPM/releases/tag/v1.3. The compact cpmsim host build kit and pinned emulator sources are included under host/BetterCPM/.

1.3 candidate: default HISTORY 192 bytes, MCL and VAR Off. CONFIG F changes owner capacities for the next cold boot. Matching private loaders/modules must be rebuilt together; install the complete matching System package. STAT MEM reports owner costs. This package is not accepted for release.
