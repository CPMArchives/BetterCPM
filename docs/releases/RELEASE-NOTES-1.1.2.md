# BetterCP/M v1.1.2 — NOAH overlay PATH fix

This maintenance release updates NOAH to **1.0 (021)**. It is based on v1.1.1
and contains no experimental v1.2 features.

NOAH previously found NOAH.OVL only in the invocation drive/user or A0:.
Launching NOAH.COM from another directory through PATH could therefore fail.
NOAH now searches the current drive/user first, followed by the configured
system PATH in order. Dynamic PATH entries use the invocation drive/user.

A found but invalid, incompatible or unreadable overlay stops the operation
immediately; NOAH does not silently try a later copy. Missing and invalid
overlays have separate diagnostics. The caller's drive/user is preserved.
Systems without compatible numeric PATH retain the previous current-DU/A0
fallback. No established executable-load-directory interface is available.

## Downloads and installation

- **BetterCPM-1.1.2-NOAH-Update.zip** contains the same portable NOAH.COM and
  matching NOAH.OVL for cpmsim, Model 4 and Model II. Replace **both files**
  together in the directory where NOAH is installed. Keep that directory on
  PATH, or change to it before running NOAH.
- **Utilities** downloads contain the refreshed NOAH companion disk for each
  platform. The other Utilities disk and other programs are unchanged.
- **Source** contains the corresponding source, build tools and native sources.
- **System disks and core OS remain v1.1.1.** Use the v1.1.1 System download
  with this update. VER continues to report Core OS 1.1.1; NOAH /VER reports
  NOAH 1.0 (021). There is no reason to reinstall or rebuild the core OS.

Do not mix the new executable with an older overlay. Existing build-identity
checks intentionally reject mismatched pairs.

## Verification

36 focused Z80 overlay/PATH regressions, 51 existing codec/overlay cases,
38 existing LBR-write cases, and nine actual CCP/BDOS cases on disposable
v1.1.1 cpmsim media passed. The regression fails against the original loader.
The maintenance-branch build produces the exact NOAH.COM and NOAH.OVL bytes
used for those checks. Packaging verifies file readback from all three disk
formats and preserves every unrelated file. No new three-platform guest or
hardware qualification campaign is claimed.

See [the engineering record](../engineering/NOAH-Overlay-PATH-1.1.2.md).
