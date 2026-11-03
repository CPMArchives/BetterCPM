# BetterCP/M 1.0 technical lock at 35c56a03

**Decision, 4 November 2026.** Use the qualified core, runtimes and unaffected utilities from `35c56a03f253c10d85ccb110ca34c1f368f319a1` as the 1.0 technical baseline. **FDB.COM, CONFIG.COM and DISK.FDB remain open for integration. The package freeze remains on hold.**

| Scope | 1.0 disposition |
| --- | --- |
| cpmsim and Model 4 RAM systems | Lock the reserved boot/system areas (27,648 and 20,480 bytes respectively), including the resident core and platform bindings. Lock the shipped System programs, providers and overlays at the listed hashes, subject to the two System-file exceptions below. This includes P2DOS.RSX on both platforms. |
| Utilities and emulator runtime | Lock the existing primary Utilities and NOAH companion payloads for both platforms and the qualified cpmsim runtime and helpers. The trs80gp executable hash identifies the external test environment. |
| Protected-ROM profile | Lock the tested ROM, HEX, overlays, instrumented cpmsim and protection configuration. Record the 692K fixture disk as a test input. It contains CONFIG.COM and DISK.FDB and may change at integration. |
| FDB.COM, CONFIG.COM and DISK.FDB | FDB.COM belongs to 1.0 and was absent from this candidate. Both platform CONFIG binaries and the 108-entry catalogue have reference hashes only. Later FDB.COM work, including PRs #594 and #596, has its own evidence. |
| Packaging and documentation | The six ZIPs and eight disk images identify the reviewed candidate. Final media assembly awaits integration. Finalize documentation after the rest of the release is complete and locked. |

The [component inventory](evidence/2026-11-04-qualification-35c56a03/components.tsv) distinguishes locked bytes from open files. Repeated names identify separate platform or volume instances. The [input identities](evidence/2026-11-04-qualification-35c56a03/identities.json) include the full source and suite revisions, each platform’s disk and emulator, the XIP inputs and the candidate archive hashes.

## Qualification on the candidate

| Target | Execution and result |
| --- | --- |
| cpmsim RAM | Eleven returning programs and supplemental checks. The 627-card ledger reconciled with zero open required cases. The suite itself recorded 273 passes, 115 not run and 24 observations across 412 canonical rows. With supplemental evidence, the final accounting was 273 suite passes, 98 external passes, 56 controlled passes, two profile passes, three profile differences, 24 observations, one external-profile observation, 119 non-guaranteed cases not run, 50 outside baseline and one inapplicable. Card 0020 preserves command-tail case. Cases 0493 and 0494 use fixed-A0 lookup. |
| TRS-80 Model 4 in trs80gp | Seven jobs ran eleven selected programs and recorded **269 passes, zero failures and zero errors**. Fourteen additional runs covered full directories, disk faults, media replacement and reset, BDOS probes, full-53K TPA returns and oversize rejection, and eight read-only outcomes. The native capture records group summaries and bounded supplemental assertions. The 627-card ledger is specific to cpmsim. |
| Protected XIP in cpmsim | The stock driver passed all seven controls on the rebuilt fixture disk. The system booted with protection at DF00h, executed transient code, reconstructed CPX and loaded and unloaded RSX. The driver verified 18 overlays and 812 relocations. Observed stack margins were 8 bytes for the system, 12 for BDOS and 44 for the loader. |

The tests ran on private copies. The original RAM System disks and the XIP fixture retained their input hashes. Two unsuccessful host-side character-routing invocations are retained. The successful invocation used the correct artifact root and Latin-1 decoding for the assembler listing. Selected supplemental Model 4 runners used the current resident `VER /VER` banner as their return checkpoint. These harness changes preserved the guest binaries and behavioral checks.

## Integration before package freeze

Qualify FDB.COM with the final CONFIG and catalogue, verify placement and free space on the selected media, and test named bindings and actual file reads on both platforms. On Model 4, verify the user installation procedure on a writable 780K SYSTEM copy using the shipped tools. Compare resulting component, reserved-area and disk hashes with this inventory. Carry forward matching component evidence. Refresh the affected integration and exact-image checks, including the stock XIP run if its fixture changes. Record final package identities and obtain separate freeze approval.

## Review evidence

The [receipt bundle](evidence/2026-11-04-qualification-35c56a03/qualification-receipts.tar.gz) includes the original card ledger and its witnesses, native summaries and guest screens, supplemental receipts, and the stock ROM transcript and receipt. After extraction, paths in `summary.json` are relative to the bundle root. For original absolute cpmsim witness paths, use the part after `/lock-tests-35c56a03/` and verify the recorded SHA-256. [Evidence checksums](evidence/2026-11-04-qualification-35c56a03/SHA256SUMS.txt)
