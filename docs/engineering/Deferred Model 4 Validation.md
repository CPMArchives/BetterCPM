# Deferred Model 4 utility validation

On 2026-10-28 the maintainer waived remaining Model 4 validation for finalization
and directed that outstanding checks be collected for a later manual campaign.
This applies to the remaining utility checks below. It is not a Model 4 PASS,
automatic release acceptance, or permission to discard the test requirements.
Earlier blocked-attempt records remain historical evidence.

| Utility | Remaining manual work |
| --- | --- |
| DUMP 007, DASM 002, DSYM 002, TED 002 | Help/version presentation, HELP precedence, query-state preservation and basic launch/exit regression checks for these new revisions. Earlier platform results remain tied to their original binaries. |
| COMPARE 002 | Native build/parity, packaged execution, cross-user summary, narrow unaligned ranges, pager controls and nonpaged cancellation, state/media preservation. |
| CRCKSUM 006 | Complete current-revision runtime campaign: historical and added algorithms, legacy/native lists, local/master generation and checking, large files, prompts and state preservation. |
| MD5SUM 002 | Native build, exact stored-byte and large-file digests, conventional lists, local/master generation/checking, display/prompts and state preservation. |
| NOAH 019 | Prompt-help/recovery regressions using its matching overlay, including repeated help, context, choices, quiet/unattended policy and unchanged protection behavior. Earlier full campaigns remain evidence for their original binaries. |
| PATCH 001 | Native build/parity; actual patched bytes and full readback; mismatch/overlap preflight rejection; overwrite/rename/help; cancellation/recovery; record and 64-KiB crossings; preservation of inputs and media. |

SEARCH already passed both platforms and is not on this outstanding list.
Use disposable system/work disks and the final matching candidate media. A later
manual procedure must identify exact executable/overlay/image hashes, commands,
expected results and observed outcomes. Never substitute a historical binary's
PASS for the current candidate. The per-utility engineering specifications and
qualification records supply the detailed assertions for that procedure.
