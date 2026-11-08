# BetterCP/M 1.1 — release notes

Qualification, exact source identity and artifact hashes are recorded in the
release index, RELEASE.json and acceptance evidence delivered with qualified
packages. Candidate archives remain unqualified until that acceptance passes.

BetterCP/M 1.1 builds on the released 1.0.1 line while preserving the CP/M 2.2 programming model, the shared system architecture and separately versioned utilities and subsystems.

## New in 1.1

### Larger default transient program area

The ordinary patched z80pack cpmsim build now uses the qualified full-RAM layout, accepting up to 57,344 bytes (56 KiB) in a single `.COM` when no optional resident extensions are loaded. The documented policy is a **minimum** for ordinary flat-64K targets, not a ceiling: platforms may provide more where safe. The TRS-80 Model II also provides 57,344 bytes unloaded. The TRS-80 Model 4 retains an explicit 54,272-byte exception because its keyboard/video mapping currently reserves upper memory. Optional resident modules reduce the available TPA while loaded. Do not extrapolate cpmsim memory measurements to Model 4.

### Numeric command PATH

Unqualified transient commands search an operator-configurable ordered list of up to six drive/user locations. The default `. A0:` preserves the established behavior, while `.` follows the caller's drive and user. `PATH` shows the active list; `PATH . B0: B1: C0: A0:` replaces it; `A0:PATH /DEFAULT` restores the default even when PATH no longer searches A0. `PATH /H`, `/HELP`, and `/VER` follow the shared utility convention. Explicit DU commands and the established core/resident/CPX dispatch precedence are preserved. The list is volatile, so use the existing startup command mechanism to apply a preferred list after cold boot.

### Portable terminal capabilities: TCAP 2.0

BetterCP/M 1.1 includes **TCAP 2.0**, the compact direct-operation terminal-capability interface qualified in PR #664. Its integrated, unloadable ADM3A, VT52 and ANSI modules each combine a terminal personality and its platform renderer. For a matching application, load a personality with `RSX LOAD ADM3A` (or VT52/ANSI), use the application, then `RSX UNLOAD ADM3A`. The direct TCAP 2.0 interface provides bounded screen capability facts, clear/position/erase operations and strong-emphasis or readable-plain fallback. The client checks same-provider ownership and console routing; no permanent TCAP display reservation is added, and complete unload restores the exact unloaded TPA boundary. A first optional RSX still incurs general RSX manager memory overhead.

**TCAP 1.0 was abandoned before release** and superseded by the 2.0 direct ABI during engineering; TCAP 2.0 is the subsystem interface version shipped with BetterCP/M package version 1.1. The original 1.0 template/transaction design is not a supported runtime compatibility mode. The qualified built-in personalities use fixed 80×24 seven-bit protocols, not arbitrary endpoint geometry or universal terminal emulation. Existing broader SCRN/SCX interfaces remain separate; TYPE, TED and HELP have not been migrated to TCAP 2.0.

### TRS-80 Model II

BetterCP/M 1.1 adds the 64 KiB Radio Shack/Tandy TRS-80 Model II as a maintained emulated platform, tested under trs80gp 2.5.8 using the qualified BCM2SS eight-inch single-sided IMD format. The port shares the CCP, BDOS, extensions and main utility sources with the existing platforms. Emulated Model II qualification includes cold boot, transient size limits, file and disk recovery, controller retries, SYSGEN installation, DUP duplication, console modes, numeric PATH and submitted input.

## Compatibility and delivery boundaries

The utility impact audit covers the existing utility inventory; earlier TYPE,
TED and HELP examples do not define an exhaustive consumer set. Existing
SCRN/SCX clients retain their documented interfaces. TED accepts MCON 1.0
while retaining its SCRN 1.1 checks, correcting its demonstrated admission
regression with the integrated ANSI module. This is a compatibility correction,
not a new editor interface or a TCAP migration.


Use System and Utilities disks built for the **same 1.1 target and component identities**; private carriers, system packages and disk layouts are not interchangeable with 1.0.x. Current published 1.0 and 1.0.1 archives are not modified by this release.

The Model II commitment does **not** cover physical hardware, Models 12/16/16B, hard drives, double-sided formats, floppy formatting, or real serial/printer hardware. The Model 4 memory exception remains. The patched cpmsim binary is required; the stock upstream emulator is not an equivalent qualified runtime.

HELP.COM and the HELP.LBR corpus are not shipped. Named-directory search, multiple-command lines and new scripting are not 1.1 features. The shipped TCAP 2.0 direct facility does not imply TYPE, TED or HELP migration, additional personalities, arbitrary host geometry or full SCRN/SCX replacement. Existing 1.0.1 supplemental disk-format support may remain available, but additional formats and checksum-table expansion are not new 1.1 commitments.

Three CP/M 2.2 Model II acceptance-card differences are documented: BetterCP/M retains original command-tail case (card 0020), and configured numeric PATH/explicit DU lookup differs from strict single-drive/current-user assumptions (cards 0493 and 0494). Those are known, bounded divergences rather than claims of strictly identical DRI behavior.

## Qualification record and known limitation

The [exact-image VER disposition](1.1-VER-DISPOSITION.md) records all nine resident/transient queries on all three targets. Resident `/H` and `/HELP` work, but resident `/VER` remains a one-line identity rather than the shared multi-line block; issue #612 remains open as a documented UI limitation. This bounded observation does not certify the full release. The promoted TCAP 2.0 modules and every final delivered image must pass their remaining exact-artifact acceptance gates. The release acceptance ledger must identify final System/Utilities hashes, native install/conformance receipts, offline reconstruction, documentation reconciliation and archive checksums under the [publication checklist](1.1-PUBLICATION-CHECKLIST.md). Engineering evidence applies only to its recorded bytes.

## Packages

The eight independent downloads are:

- `BetterCPM-1.1-System-cpmsim.zip`
- `BetterCPM-1.1-System-Model4.zip`
- `BetterCPM-Utilities-1.1-cpmsim.zip`
- `BetterCPM-Utilities-1.1-Model4.zip`
- `BetterCPM-1.1-System-Model2.zip`
- `BetterCPM-Utilities-1.1-Model2.zip`
- `BetterCPM-1.1-Source.zip`
- `BetterCPM-1.1-Documentation.zip`

Each platform needs its matching System and Utilities packages. Utilities
packages include primary and NOAH companion images. Source includes pinned
offline runtime dependencies; Documentation contains the four maintained
Markdown manuals and supporting references. PDF and DOCX editions are not
included. Verify the release index and SHA-256 sums before use.
