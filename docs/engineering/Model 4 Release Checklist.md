# Model 4 release-candidate validation

Status: **PENDING manual execution**. Reconciled on 2026-10-28 against
`c5f53ef2a806439eda21ceab5dcc3897bf88a7aa` and the
[deferred ledger](Deferred%20Model%204%20Validation.md). This adds a procedure;
it does not change historical blocked/deferred results into passes.

## Candidate and evidence

Record the exact tested source commit, package filename and SHA-256, System A:
image SHA-256, primary B: and companion C: image hashes, initial work D: hash,
trs80gp version/binary hash, startup configuration and date/operator. Work on
copies. Preserve original images, before/after listings, attributes, file hashes,
screens/transcripts, fixture bytes and expected-output calculations.

The latest checked-in Utilities inventory is in
[Remaining-Utility-Help-Qualification.json](Remaining-Utility-Help-Qualification.json).
Its Model 4 primary image hash is
`75bd8cfaf6c543c64a5997e178329586a9dd46b1fb03983f21cf7dc059129198`;
its companion image hash is
`f7f5ccbbf502666adbdec45377f45009901cdcbb9fbc9cc716f02d3b9a39dfcc`.
These identify recorded inventory evidence, not a newly accepted package or
Model 4 execution. Independently hash actual package images before testing.
If they differ, record the new identities and review applicability; do not
copy these hashes into a receipt without checking the bytes.

Use A: System, B: primary Utilities, C: historical BetterCPM-NOAH companion,
D: expendable work. C: must contain NOAH.COM/OVL/TXT, PATCH.COM/TXT and
COMPARE.COM/TXT. Keep the NOAH executable and overlay matched.

Manually start trs80gp using the maintainer's working launch procedure.
Do not repeat the automated LaunchServices/WindowServer path or change OS
permissions. Boot the actual packaged A: image and inspect all mounted media.

## Current component identities

The table below is generated from the latest checked-in inventory; executable
hashes are unpadded COM bodies. Preserve stored-record hashes separately when
exporting CP/M files, because record padding can change host hashes.

| Component | Version / revision | SHA-256 |
| --- | --- | --- |
| CRCKSUM.COM | 1.0 / 006 | `ce4ce0711f893b6a9e4b2491f3644424b8e6caccdc1efde24e3499d2a9c7041d` |
| MD5SUM.COM | 1.0 / 002 | `692a83f1e21911987cdabba8747463a306ac5b46e6d91b7c8bc47d00a5576022` |
| NOAH.COM | 1.0 / 019 | `6b8f0b9ab4819f721428a02fb11d27f2b179f87117e649bb8ece7e2688294e8e` |
| PATCH.COM | 1.0 / 001 | `9f4bde87442942f3bc735ac454c046abbafb26cdc7948aed609260a46a4866ba` |
| COMPARE.COM | 1.0 / 002 | `39d0dd800729c3e2cc88c5fe18f53d1d6084b046a10fe2d754725ca01f34236e` |
| DUMP.COM | 1.0 / 007 | `b9c449aad54e29f6cc718a1f2d42a75e5b4296bfeeea766b1743e8133f5070d0` |
| DASM.COM | 1.0 / 002 | `690ed903df06f7f211ef0dea0228d2f5063301f45b5e4fdd7c3cd250df33bba7` |
| DSYM.COM | 1.0 / 002 | `6b8d8229d4cee393c8d6dabafe68eb1ae98f50bbfd87688a0133284fbc14e4f1` |
| TED.COM | 1.0 / 002 | `2d13d1bc4562f97c4e65b343d0b6e580915bd08bb3ba3188ae0ebfda49377080` |
| NOAH.OVL | Matched NOAH 019 overlay | `446d6baa47bcefb1dd18fe6e2733e537c3f1d377810e49cd1b39c535fe02fcba` |

## Campaign

Prepare exact fixture files and expected bytes from the relevant utility
specification and regression cases before executing each row. Record every
actual command and key sequence, not just the campaign title. Include empty,
one-record, multi-record and greater-than-64-KiB binary files with Ctrl-Z,
high-bit bytes and nonzero final padding where applicable. Record host reference
values over complete stored 128-byte records, without text conversion.

| ID | Manual checks and required outcome | Status |
| --- | --- | --- |
| M4-01 | Boot packaged A:, inspect A:/B:/C: membership, execute each listed utility's /VER. Banners and exported bytes match the recorded candidate. | PENDING |
| M4-02 | For DUMP, DASM, DSYM, TED, COMPARE and NOAH, run /HELP, /VER and `/VER /HELP /BOGUS`. HELP wins, agrees with the current quick-reference layout and fits the screen. Return to the original drive/user; no file changes. | PENDING |
| M4-03 | Launch and exit DUMP, DASM and TED normally using disposable inputs; run DSYM on a valid matching LINK log and verify generated symbols. Confirm normal behavior after query-only invocations. | PENDING |
| M4-04 | CRCKSUM: all eight default algorithms, individual selections, explicit order and repeated switches, narrow display; values and complete record counts match independent reference calculations. | PENDING |
| M4-05 | CRCKSUM: legacy and native lists, explicit/discovered local references, master and per-user local generation/checking, missing/malformed/conflicting entries; selected failures cannot yield overall success. | PENDING |
| M4-06 | MD5SUM: exact stored-byte digests, empty and >64-KiB files, starred/two-space conventional lists, master/local generation/checking, selected/missing/malformed/conflicting entries. Compare against host digests of full stored records. | PENDING |
| M4-07 | CRCKSUM/MD5SUM: repeated `?`, Y/N/Enter/All and Ctrl-C at overwrite prompts. Help repeats context without authorizing a write; documented defaults and All scope hold. Verify inputs, unselected files, attributes and drive/user. | PENDING |
| M4-08 | NOAH 019 with matching overlay: ordinary replacement and safe-recovery prompts, repeated help and context, each choice/default, quiet and unattended modes. No action occurs solely from help; protected/destructive behavior remains as specified. | PENDING |
| M4-09 | PATCH: native assembly/link parity against the exact packaged executable; valid patch, record crossing and 64-KiB crossing. Verify the complete output and unchanged input bytes, not just displayed success. | PENDING |
| M4-10 | PATCH: mismatch, duplicate/overlap and malformed preflight reject before output; overwrite/rename/help choices, cancellation and recovery, read-only/system output protection. Preserve existing output where specified and inspect temporary/backup cleanup. | PENDING |
| M4-11 | COMPARE: native assembly/link parity; identical/different/length-mismatched files, cross-user summary and narrow unaligned ranges. Report exact expected offsets/bytes/counts. | PENDING |
| M4-12 | COMPARE: paged controls, nonpaged cancellation and return to CCP. Inputs and all mounted media remain unchanged after read-only cases. | PENDING |
| M4-13 | Re-export tested binaries and relevant fixture/output files; compare before/after media and attributes. Explain every intended write, verify unrelated bytes and filesystem integrity. | PENDING |
| M4-14 | Extract a fresh platform package and follow installation instructions without relying on development-tree images or helpers. Reconfirm package/image/component identity and boot. | PENDING |

Native parity checks require the matching prepared native sources, ZSM4 and LINK
from the same corresponding-source package. Keep assembler/linker transcripts
and compare meaningful COM bytes plus stored record padding. A stock-CP/M build
or cpmsim result is useful evidence but does not replace this Model 4 campaign.

Detailed contracts and prior fixtures:

- [CRC specification](CRC-Specification.md), [MD5SUM specification](MD5SUM-Specification.md), and [prompt-help qualification](Utility%20Prompt%20Help%20Qualification.md).
- [NOAH specification](NOAH%20Specification.md) and [latest help-layout qualification](Utility%20Help%20Layout%20Qualification.md). The prompt-help record's NOAH 018 hash is historical; the current executable/overlay are 019 above.
- [PATCH specification](PATCH-Specification.md) and [implementation](PATCH-Implementation.md).
- [COMPARE specification](COMPARE%20Specification.md) and [qualification](COMPARE%20Implementation%20Qualification.md).
- [Remaining help qualification](Remaining%20Utility%20Help%20Qualification.md) for DUMP 007, DASM 002, DSYM 002 and TED 002.

## Recording results and acceptance

Append a dated result record for each ID with candidate/package/emulator hashes,
fixture identities, commands/keys, expected and actual results, transcript and
before/after evidence paths, outcome and unresolved discrepancies. Allowed
outcomes are PASS, FAIL, BLOCKED and PENDING; give reasons for incomplete work.
A summary checkbox or the maintainer's earlier deferral is not runtime evidence.
Retain the earlier evidence and link the new record from the deferred ledger.

Do not promote until every required row has accepted evidence. For a binary or
package change, identify which prior results remain applicable by hash, rerun
affected regressions/platform checks and update candidate identity. Final tag
and published artifacts must refer to the accepted commit and exact tested bytes.
