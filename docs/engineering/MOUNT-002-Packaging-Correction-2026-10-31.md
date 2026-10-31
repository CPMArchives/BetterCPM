# MOUNT 002 packaging correction

The maintainer had already tested MOUNT 1.0 (002-dev), but release candidate
91c7e6253eb3fd6f1e9e14d57281f639dee3a2ec still selected MOUNT 001 from its
pinned cpmsim reconstruction. The correction was not in that patch chain.

Added 0007-mount-help.patch to both runtime and qualification profiles.
It reconstructs the existing tested binary exactly, rather than changing
mount semantics or the emulator protocol. No emulator replacement is needed
for this guest help correction. System staging already copies MOUNT.COM from
the selected runtime; rebuilding that runtime now supplies the corrected file.

## Evidence

- Reconstructed runtime: build/mount002-runtime/environment.json.
- Assembled and system-image MOUNT.COM SHA-256:
  b7051dccd6bb13ade13f66f0612c64c925afef324faa1a642716da103ddb7262 (1341 bytes).
  Byte-for-byte match with the maintainer-tested Downloads/MOUNT.COM.
- Fresh System build from source commit 086e6d8e732a31b86f5dd530bd9e391ed6873e40:
  build/mount002-systems/z80pack/report.json. Boot, filesystem, file integrity,
  and configuration checks passed. MOUNT's recorded image-member hash matches.
- Real BetterCP/M integration: build/mount002-system-test/result.json and
  transcript.txt. MOUNT /VER identifies 002-dev; /HELP and /H display the revised
  usage. Explicit-selector errors, live replacement, A: cancellation, eject and
  reinsert, directory reads, and R/W transfer passed. Baseline image unchanged.
- Host service fixture: test_cpmsim_mount.py passed syntax, atomic validation,
  identity, replacement, confirmation, reset masks, and listing checks.
- The separate minimal-BDOS guest probe stalled in emulator child cleanup;
  it is not recorded as a pass. The real System integration above completed.
- Model 4 was not launched. MOUNT is cpmsim-specific.

System image SHA-256: 830d929dfc11d32d99d2fa4ca39d98d6f0585b2b03b97112c7f239aa532a3bbe

Transcript SHA-256: c931c0c337c608d49b9810f4a570e17738e0dd583c6f4752cc12067a5bd2074e

Existing candidate ZIPs have not been replaced. Rebuild candidates from the
accepted merged commit to retain consistent package/source identities.
