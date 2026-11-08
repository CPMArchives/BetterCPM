BetterCP/M 1.1 System — cpmsim
==============================

ASSEMBLY TEMPLATE — not a completed or accepted release package.
Remove this notice only after the release acceptance checks pass.

Contains the cpmsim System Disk and formatted work media. Utilities are a separate download for the same platform.

Read docs/platform/CPMSIM-INSTALLATION.md before booting. BetterCP/M requires patched cpmsim; build the runtime using the included instructions, pinned sources and patches in host/BetterCPM/. Keep the generated environment.json. Stock cpmsim is insufficient.

Mount writable image copies: A: System, B: primary Utilities and C: companion Utilities when installed, D: work. Start cpmsim with its matching srctools on PATH. BYE /Y exits.

Verify SHA256SUMS.txt before use. RELEASE.json identifies the exact source commit, included artifacts and qualification evidence. Preserve original media; use disposable copies for validation.

Retain all included license, permission, attribution and corresponding-source files. See the release notes for known limitations and the release-wide index for matching downloads.

TCAP 2.0: use the matching ADM3A, VT52 or ANSI integrated personality/renderer. RSX LOAD ANSI selects ANSI; RSX UNLOAD ANSI removes it. No separate screen backend is required. Rediscover the same-owner provider after layout changes. Existing utilities retain their documented interfaces; HELP is not included. See TCAP-Direct-ABI.md and tcap2.inc in the matching Source package.

Full manuals, developer interfaces and engineering evidence are in the separate BetterCPM-1.1-Documentation.zip and BetterCPM-1.1-Source.zip downloads from https://github.com/CPMArchives/BetterCPM/releases/tag/v1.1. The compact cpmsim host build kit and pinned emulator sources are included under host/BetterCPM/.
