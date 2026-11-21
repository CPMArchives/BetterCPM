BetterCP/M 1.3 System — Model II

CANDIDATE — NOT ACCEPTED FOR RELEASE.

Contains the Model II System IMD. Read docs/platform/MODEL2-INSTALLATION.md.
Use writable copies with trs80gp 2.5.8, Model II, 64 KiB RAM, BCM2SS single-sided media.
Mount A: System, B: primary Utilities, C: companion Utilities, D: work.
Physical hardware, Models 12/16/16B, hard drives and other disk formats are unverified.

TCAP 2.0 integrated personality/renderer modules: RSX LOAD ADM3A (or VT52/ANSI).
No separate screen backend is required. RSX UNLOAD ADM3A removes the provider.
Use only matching System and Utilities packages. Verify SHA256SUMS.txt and RELEASE.json.
Keep all license, attribution and source companions. Existing SCRN/SCX clients retain their documented interfaces; HELP and its topic library are included; NDR names annotate PATH output.

Full manuals, developer interfaces and engineering evidence are in the separate BetterCPM-1.3-Documentation.zip and BetterCPM-1.3-Source.zip downloads from https://github.com/CPMArchives/BetterCPM/releases/tag/v1.3.

1.3 candidate: default HISTORY 192 bytes, MCL and VAR Off. CONFIG F changes owner capacities for the next cold boot. Matching private loaders/modules must be rebuilt together; install the complete matching System package. STAT MEM reports owner costs. This package is not accepted for release.
