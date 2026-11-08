# BetterCP/M 1.1 — release notes (draft; not published)

**Release state: preparation only.** These notes describe the locked feature set, not a qualified binary release. The final source revision, package hashes, VER behavior and artifact acceptance must be filled in from the exact published candidates before publication. Do not attach this draft to an unverified release.

BetterCP/M 1.1 builds on the released 1.0.1 line while preserving the CP/M 2.2 programming model, the shared system architecture and separately versioned utilities and subsystems.

## New in 1.1

### Larger default transient program area

The ordinary patched z80pack cpmsim build now uses the qualified full-RAM layout, accepting up to 57,344 bytes (56 KiB) in a single `.COM` when no optional resident extensions are loaded. The documented policy is a **minimum** for ordinary flat-64K targets, not a ceiling: platforms may provide more where safe. The TRS-80 Model II also provides 57,344 bytes unloaded. The TRS-80 Model 4 retains an explicit 54,272-byte exception because its keyboard/video mapping currently reserves upper memory. Optional resident modules reduce the available TPA while loaded. Do not extrapolate cpmsim memory measurements to Model 4.

### Numeric command PATH

Unqualified transient commands search an operator-configurable ordered list of up to six drive/user locations. The default `. A0:` preserves the established behavior, while `.` follows the caller's drive and user. `PATH` shows the active list; `PATH . B0: B1: C0: A0:` replaces it; `A0:PATH /DEFAULT` restores the default even when PATH no longer searches A0. `PATH /H`, `/HELP`, and `/VER` follow the shared utility convention. Explicit DU commands and the established core/resident/CPX dispatch precedence are preserved. The list is volatile, so use the existing startup command mechanism to apply a preferred list after cold boot.

### TRS-80 Model II

BetterCP/M 1.1 adds the 64 KiB Radio Shack/Tandy TRS-80 Model II as a maintained emulated platform, tested under trs80gp 2.5.8 using the qualified BCM2SS eight-inch single-sided IMD format. The port shares the CCP, BDOS, extensions and main utility sources with the existing platforms. Emulated Model II qualification includes cold boot, transient size limits, file and disk recovery, controller retries, SYSGEN installation, DUP duplication, console modes, numeric PATH and submitted input.

## Compatibility and delivery boundaries

Use System and Utilities disks built for the **same 1.1 target and component identities**; private carriers, system packages and disk layouts are not interchangeable with 1.0.x. Current published 1.0 and 1.0.1 archives are not modified by this release.

The Model II commitment does **not** cover physical hardware, Models 12/16/16B, hard drives, double-sided formats, floppy formatting, or real serial/printer hardware. The Model 4 memory exception remains. The patched cpmsim binary is required; the stock upstream emulator is not an equivalent qualified runtime.

HELP.COM and the HELP.LBR corpus are not shipped. Named-directory search, multiple-command lines and new scripting are not 1.1 features. The separately qualified TCAP 2.0 implementation remains an **unreleased engineering candidate** unless independently assigned and requalified for a future release; no TYPE, TED or HELP TCAP migration is claimed for 1.1. Existing 1.0.1 supplemental disk-format support may remain available, but additional formats and checksum-table expansion are not new 1.1 commitments.

Three CP/M 2.2 Model II acceptance-card differences are documented: BetterCP/M retains original command-tail case (card 0020), and configured numeric PATH/explicit DU lookup differs from strict single-drive/current-user assumptions (cards 0493 and 0494). Those are known, bounded divergences rather than claims of strictly identical DRI behavior.

## Pending final-release verification

The open resident/transient VER command query discrepancy (#612) requires a final candidate check and release disposition. No fresh release-media success is claimed here for it. Final System/Utilities hashes, native install/conformance receipts, offline reconstruction, documentation reconciliation and release checksum archive still need sign-off under the [publication checklist](1.1-PUBLICATION-CHECKLIST.md).

## Packages

**Proposed:** System packages for cpmsim, Model 4 and Model II; matching Utilities packages for those three platforms (Model II primary and companion images); a matching Source package; and four-manual Documentation. Definitive download filenames, verified SHA-256 sums and source revision belong to the final release index, not this draft.
