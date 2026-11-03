# Final package checks and shipped Model 4 installation

4 November 2026. **Checks prepared and walkthrough verified. Package freeze on hold.** FDB.COM, CONFIG.COM and DISK.FDB remain open for 1.0 integration.

The [acceptance ledger and command](../releases/FINAL-PACKAGE-CHECKS.txt) use `tools/check_release_package_lock.py` to review a directory of six candidate ZIPs. The checker verifies exact archive membership and checksums, consistent source identity, license and notice presence, known Montezuma exclusions including nested sources, disk receipts, filesystems and shipped file bytes. It compares locked components and reserved System areas with #597, reports changed disk images and identifies the open integration components. A static pass is one input to the final runtime, documentation and maintainer acceptance checks.

The existing checker runs passed on all six 35c56a03 ZIPs and all six 4a47d233 manual-review ZIPs. Both sets retained the eight qualified disk image hashes. The checker’s additional reserved-area assertions were verified against 35c56a03 for this PR. The byte comparisons and source identities are retained in the [package results](evidence/2026-11-04-package-install-checks/baseline.json) and [manual-review results](evidence/2026-11-04-package-install-checks/manual-review.json).

## Model 4 operator procedure

The [walkthrough](../platform/MODEL4-SHIPPED-INSTALLATION.txt) used separate private copies of the 35c56a03 780K System DMK as source and destination. These commands established the destination geometry and installed the system using shipped tools:

```text
CONFIG /EDIT=B /OFF=4 /DSM=389
DIR B:
TYPE B:KEEP.TXT
SYSGEN A: B:INSTALL.SYS
SYSGEN B:INSTALL.SYS B:
```

After the destination confirmation, SYSGEN reported success. Independent readback verified all existing file entries and contents, including KEEP.TXT, and the new INSTALL.SYS. The target cold-booted in physical drive 0, displayed the banner, read KEEP.TXT, showed saved configuration and listed M4SCRN and ADM3A. Its displayed TPA was 50K with the default screen modules loaded. The separate unloaded 53K result remains in #597.

The alternative named binding `CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="BetterCP/M Model 4 System 780K"` was rejected by the shipped CONFIG with `Cannot apply logical binding. Nothing changed.` That attempted runner was stopped while waiting for its success message. The passing procedure used the field-edit route on a second set of private copies. This finding remains with the open CONFIG/catalogue integration workstream.

The [installation receipt](evidence/2026-11-04-package-install-checks/model4-install.json) records the baseline, emulator and working disk hashes. The [receipt bundle](evidence/2026-11-04-package-install-checks/model4-install-receipts.tar.gz) retains the runner, invocations, native screens and shipped-file audit. [Checksums](evidence/2026-11-04-package-install-checks/SHA256SUMS.txt)

After integration, confirm final placement and catalogue-save space, named bindings and file reads, rerun the walkthrough against the selected bytes, compare all locked payloads, and refresh tests affected by changed inputs. Rebuild from the final exported Source and finalize the documentation against the locked contents before requesting a package freeze.
