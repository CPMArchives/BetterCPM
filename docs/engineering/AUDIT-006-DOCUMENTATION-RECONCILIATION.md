# Audit 006 documentation reconciliation

Date: 3 November 2026. Review base: `04f0e610fdb0c53a325dabfbb560dee6d3b82f46`.

The approved audit triage routes BCPM-AUD-006 to documentation finalization.
This change corrects the current default RAM examples in Architecture 04 to
LY_SYS=D5C4h, LY_BDOS=D6BCh, LY_PDSD=D644h and the unloaded gateway D501h.
The diagram and dispatch description use layout symbols rather than the old
system-base-plus-100h assumption. These are private build addresses, not new
ABI promises; other profiles retain their own emitted layouts.

Architecture 18 now describes the implemented SYS_COLD signature invalidation
and CCP_HINIT empty-object reconstruction, with SYS_WARM preserving valid
history. It explicitly distinguishes header validation from record validation.
No production source, allocation, component identity or artifact changes.

## Retained dispositions

- **BCPM-AUD-003:** comprehensive corrupt-history validation remains deferred
  post-1.0. Seeded malformed records are unsafe. No supported producer was
  established. Reopen before release if supported input produces malformed
  history or the writer/PDS layout changes. This is a residual-risk disposition,
  not a claim that the retained invalid-object contract is fully implemented.
- **BCPM-AUD-007:** broad historical oracle/fixture cleanup remains post-1.0;
  any failing required current release gate must still be investigated and
  resolved or explicitly dispositioned before acceptance. Inherited failures
  and unavailable fixtures are not passing results.

## XIP coordination

The dedicated release-readiness workstream already corrected the two stale
ROM layout expectations and reran the stock qualification on the same retained
artifacts in [PR #583](https://github.com/CPMArchives/BetterCPM/pull/583).
That PR merged as `04f0e610fdb0c53a325dabfbb560dee6d3b82f46`.
The [stock receipt](evidence/2026-11-03-protected-xip/rom-xip-qualification.json)
and [run record](evidence/2026-11-03-protected-xip/run.json) report exit 0,
all seven guard controls passing, protected CPX/RSX operations and workspace
checks. ROM SHA-256:
`cc6917780ce47ab34fbed7949abdf93a17d20eb182ab9fdcd15c8d16cd864168`.
The minimum recorded stack margin is 8 bytes, meeting the existing threshold.
This closes the stock XIP gate for those exact artifacts/configuration; it is
not acceptance of later or changed public packages. The original failed run
remains historical evidence. Package freeze remains on hold.

## Verification

Compared the documentation against exact-base src/system/layout.inc,
src/system/gateway.mac SYS_COLD/SYS_WARM, and the history-owner lifecycle.
Checked the patch for stale replaced examples, arithmetic and whitespace;
reviewed the exact #583 merge and its artifact-bound passing receipt.
This documentation-only change does not rerun guest tests or alter their
recorded outcomes. Bring this change back for maintainer review; do not merge
without approval.
