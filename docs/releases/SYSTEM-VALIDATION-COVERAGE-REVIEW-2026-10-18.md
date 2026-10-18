# System validation coverage and device review — 2026-10-18

This review follows V036. It does not declare Step 7 or system acceptance complete.
The Utilities Disk and CP/M Tools disk remain outside this campaign.

## Evidence rules

The independent suite checkout was inspected at pinned revision
`a9a878fcd2e36698c7e856654a85847a004fdd20`. Its case-to-executable catalog
contains 627 cards. Catalog implementation-status fields are historical inventory,
not execution results. Likewise, initial `STOUT` statuses in program tables are
not evidence that a card remained unexecuted after `/SAFE` or an external check.
A manual/provider label describes the supplied runner, not necessarily a need
for a human operator.

The campaign ledger records that early temporary evidence disappeared before
V023. Those historical results remain recorded results, but their raw artifacts
must not be represented as currently retained or freshly reproduced. Final
acceptance requires a clean merged-source build and fresh applicable-suite runs,
with exact input identities and retained per-card output. A focused external
check does not silently change the independent suite's printed status to PASS.

## Remaining-work register

| Coverage | Current disposition | Required closure |
| --- | --- | --- |
| Native 0368–0369 and 0379–0384 | Closed for the selected V034 image by V038 | Eight external native outcomes passed: selected diagnostic, usable CCP, caller B0/53K, unchanged protected media and shipped files. This is not DRI key-acknowledgement equivalence or a final merged-source rerun. |
| BDOSTEST 0143 | Selected native witnesses pass in V040 | Real emulator media exchange detects the changed directory and protects it; Make is rejected without mutation. A separate Function 37 reset permits one empty-file creation. CKS-enabled fixtures only; final merged-source rerun remains required. |
| BDOSTEST 0420 | Selected native witness passes in V039 | One controlled Function 10 input line updates the DE buffer; DMA and surrounding guards remain unchanged. Retain final merged-source rerun. |
| BDOSTEST 0519 | Selected native witness passes in V039 | A/B/A selections expose BDOS DPB/ALV pointers matching the selected BIOS DPH, without fixed addresses or a uniqueness requirement. Retain final merged-source rerun. |
| Native ECOTEST 0569, 0575 | Selected native witnesses pass in V041 | Resident DIR/ERA/REN/SAVE/TYPE/USER semantics run despite namesake marker COMs; SAVE produces exactly the primed 256-byte page. Private evidence fixtures are retained; caller returns to A0/53K. |
| Native ECOTEST 0577, 0579 | Selected native witnesses pass in V042 | TYPE BIOS-output bytes are captured and compared for text, empty/control/EOF/multi-record fixtures; seven ordinary failures and allocation-full SAVE recover with disk/file audits. Final merged-source reruns remain required. |
| BIOSTEST/ERRTEST documentary cards | OPEN: per-card reconciliation | Map retained external evidence and fresh suite output to the candidate cards below. Do not count documentary listings as execution, or declare all candidates missing merely from their initial status. |
| Unavailable-drive card 0154 and interactive physical-error profiles | PROFILE REVIEW | Apply the documented BetterCP/M error/restart contract, including its immediate warm-start behavior. Do not claim the interactive DRI acknowledgement profile passed if no acknowledgement exists. Required recovery/data-safety checks remain required. |
| Live cpmsim printer and auxiliary reader/punch | OPEN: supported endpoint checks | Exercise the emulator's configured host endpoints and compare exact host bytes, EOF/readiness and routing. V030 controlled device tests do not establish live endpoint operation. |
| Model 4 unavailable printer/UART aliases | Capability rejection contract | Validate rejection before mutation; do not claim physical-device operation. Printer transformations and serial configuration are deferred features, not implemented 1.0 controls awaiting an operator. |
| Physical host terminal/keyboard observations | MANUAL PENDING where claimed | Record terminal type, loaded personality/backend, positioning, erase, reverse and keyboard observations. Software-terminal checks cover selected semantics, not every real terminal or keyboard. |
| Clock-setting providers | Capability/profile review | Preserve the real host clock. Qualify supported provider behavior with a controlled clock fixture; verify unsupported-setting refusal. Do not treat a controlled provider as a physical-clock result. |
| Outside-scope/non-guaranteed suite cards | Explicit classification | Keep observations and outside-scope cards separate from passes. In particular 0625/0627 are outside the generic suite claim; BetterCP/M's own Z80/platform commitments still require their separate checks. |
| Native batch input anomaly in V040 | OBSERVED; cause unassigned | Initial command was captured as A0*MEDIA rather than A0:MEDIA and never reached the probe. Repeat with slower, simpler entry passed; retain this observation for final native input regression and investigate if reproducible. It is neither a media-change verdict nor proof of a keyboard fix. |
| Final acceptance | OPEN | Rebuild from the final merged revision; rerun applicable conformance, application/monitor regressions and disk integrity checks; resolve or explain each applicable failure and preserve artifacts. |

No blanket manual exclusion is approved by this review. Any later exclusion must
name the card, target, contract, reason and replacement evidence or remaining gap.
V038 closes the selected native read-only terminal outcomes. The next bounded
work remains in BIOS/error evidence reconciliation, live device/profile
closure, the recorded input anomaly review and final merged-source acceptance.
V039–V042 supply selected native witnesses for the three BDOS documentary
cards and four ecology procedures; those are not a final clean-source rerun.
Live host devices and operator observations can then be closed with named profiles.

## Device basis

The production cpmsim character-routing table in
`src/platform/z80pack/chario.inc` routes printer output/status through ports 3/2
and auxiliary reader/punch through port 5. Reader port 4 is EOF, not readiness;
BAT status has its own documented handling. These endpoints cannot be dismissed
as unavailable merely because a controlled PIP test used a synthetic provider.
Native Model 4 capability declarations and implemented console paths must be
used instead of assuming the cpmsim endpoint set applies to that target.
The earlier PIP routing audit contains prototype-era limitations; current code
and the current engineering specification determine the release contract.

## Candidate documentary cards for reconciliation

These are the pinned source tables' initial REQUIRED/not-run rows, not a newly
computed outstanding count. `/SAFE` and external evidence may already cover
individual rows. The list makes the next reconciliation finite and reviewable.

| Program | Card | Requirement |
| --- | --- | --- |
| BIOSTEST | 0424 | Function 27 allocation-vector pointer |
| BIOSTEST | 0425 | Allocation-vector length and bit mapping |
| BIOSTEST | 0426 | Reserved directory allocation bits |
| BIOSTEST | 0427 | Live allocation state |
| BIOSTEST | 0431 | Function 31 DPB pointer and layout |
| BIOSTEST | 0432 | DPB configuration and sharing |
| BIOSTEST | 0433 | Documented DPB modification |
| BIOSTEST | 0439 | Function 4 Punch convention |
| BIOSTEST | 0443 | Function 8 IOBYTE set |
| BIOSTEST | 0445 | IOBYTE routing boundary |
| BIOSTEST | 0448 | Character-device DMA independence |
| BIOSTEST | 0449 | Stateful BIOS disk setup |
| BIOSTEST | 0450 | SELDSK result and deferral |
| BIOSTEST | 0451 | Public DPH layout |
| BIOSTEST | 0453 | Track mapping and OFF |
| BIOSTEST | 0454 | Sector translation chain |
| BIOSTEST | 0456 | BIOS DMA state |
| BIOSTEST | 0457 | BIOS logical-sector transfer |
| BIOSTEST | 0458 | BIOS WRITE type codes |
| BIOSTEST | 0461 | BIOS jump-vector structure |
| BIOSTEST | 0463 | BIOS-base discovery through WBOOT gateway |
| BIOSTEST | 0464 | BOOT control contract |
| BIOSTEST | 0465 | WBOOT control contract |
| BIOSTEST | 0466 | Warm-start gateway reconstruction |
| BIOSTEST | 0468 | BIOS console status contract |
| BIOSTEST | 0469 | BIOS console input contract |
| BIOSTEST | 0470 | BIOS character output contracts |
| BIOSTEST | 0471 | BIOS reader contract |
| BIOSTEST | 0473 | Direct BIOS call layering |
| BIOSTEST | 0622 | Self-modifying transient execution |
| ERRTEST | 0404 | Sequential read logical result |
| ERRTEST | 0406 | Random read logical codes |
| ERRTEST | 0407 | Random write logical codes |
| ERRTEST | 0408 | Make/Delete/Rename/Close logical codes |
| ERRTEST | 0582 | Logical failures return without physical-error intervention |
| ERRTEST | 0405 | Sequential write logical result |
| ERRTEST | 0516 | Directory-full and allocation-full are distinct |
| ERRTEST | 0390 | CBIOS physical read result |
| ERRTEST | 0391 | CBIOS physical write result |
| ERRTEST | 0392 | BIOS retry responsibility |
| ERRTEST | 0393 | Physical/logical error separation |
| ERRTEST | 0394 | Bad Sector presentation |
| ERRTEST | 0581 | Physical failure suspends the BDOS caller |
| ERRTEST | 0395 | Physical-error ignore choice |
| ERRTEST | 0396 | Physical-error abort choice |
| ERRTEST | 0397 | Abort restart details |
| ERRTEST | 0586 | Physical-error abort abandons the interrupted caller |
| ERRTEST | 0587 | Abort recovery establishes a usable command environment |
