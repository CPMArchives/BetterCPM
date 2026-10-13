# Resident-to-transient handoff memory audit

Audit date: 2026-10-13. Baseline: main `62e147d`, after PR 245.
This is a prerequisite assessment, not implementation or lifecycle qualification.
Production source and memory layout are unchanged.

## Fresh baseline

| Component | Emitted bytes | Allocation/limit | Remaining |
| --- | ---: | ---: | ---: |
| CCP | 5,437 | 5,632 | 195 payload bytes |
| RCP payload | 6,785 | 6,912 | 127 payload bytes |
| RCP relocation header | 744 words plus 48-byte prefix | 1,536 | 0 relocation words |
| CCP relocation header | 488 words plus 16-byte prefix | 1,024 | 16 relocation words |
| Protected gateway | 248 | 248 | 0 appended bytes |
| Unified BDOS | 3,555 | 3,555 allocated region | 0 |
| Model 4 BIOS | 636 | 638 | 2 |
| Extension services | 424 | 425 | 1 |
| Disk/CPX control overlay | 1,018 | 1,024 | 6 |
| Command reloader | 931 | 932 | 1 |

The older 5,376-byte CCP figure is obsolete. Current CCP and RCP allocations
consume 12,544 bytes of reconstructible command memory; they are reclaimed for
transient execution. Neither allocation is the permanent TPA boundary.
Unloaded transient capacity remains D501h - 0100h = 54,273 bytes: 53 KiB plus
one byte. The protected resident span is D5C4h through EF7Fh (6,588 bytes).
Optional RSXs lower the live transient ceiling by their existing allocations.

## Isolated assembled probes

`tools/audit_handoff_memory.py` assembles candidates under `build/handoff-audit`.
It does not publish candidates as system artifacts.

- A separate protected request byte at `LY_SYS+00B7h`, cleared at command
  dispatch and tested after a handled CPX return, adds 10 CCP bytes. The result
  is 5,447 bytes, still allocated 5,632, with unchanged 488 relocations. Normal
  loader entry bypasses another resident search and preserves command text.
  This is only the dispatch footprint, excluding richer missing-command output.
- A canonical eight-byte `RCP     ` name comparison and policy reset in the
  successful removal path grows the control overlay to 1,051 bytes. One branch
  also needs promotion from JR to JP. This straightforward candidate exceeds
  the 1 KiB limit by 27 bytes and cannot be shipped unchanged.
- RCP's existing 744 relocation words exactly exhaust its current builder
  header. Added relocated addresses require compaction or a larger carrier
  header even if the executable still fits the 127-byte payload remainder.
  The complete controls/diagnostics have not yet been assembled; do not present
  the dispatch-only measurement as the size of finished handoff.

## Protected state and lifecycle

The CPX profile occupies D65Ah through D679h. Seven zero-filled bytes precede
SINIBODY at D681h. Policy at D67Ah and a request byte at D67Bh therefore preserve
all field addresses, gateway length, four-record profile capacity, and TPA.
The policy remains RCP-owned suppression bits with zero meaning enabled.
The request is separate, cleared per command, and not persisted to CONFIG.

Cold boot installs the resident image containing zero-filled state. WBOOT
reconstructs CCP/CPXs using the retained protected profile; it must not reset
policy. RCP initialization and shutdown must not clear it: shutdown also occurs
for transient launch. Reset belongs only to committed canonical RCP removal;
absent removal, failed requests, duplicate loads, other-package removal and
reordering preserve it. RSX reconfiguration must likewise preserve the fixed
protected byte. These are source-supported placement/lifetime expectations;
execution tests remain necessary before declaring them qualified.

For 1.0, associate policy with the canonical profile stem `RCP     `. Alternate
filenames or multiple RCP instances need an explicit contract; do not silently
claim alias support. Clearing on committed removal makes subsequent load start
with defaults without initialization-time resets that would break WBOOT.

## Required bounded implementation work

1. Keep existing carry-based CPX handled/declined ABI. Use the distinct request
   byte to signal handoff, and clear it before each invocation. Preserve caller
   DU and the original tail before loading the transient. Existing explicit
   colon/period invocation remains independent of suppression policy.
2. Add per-command controls before operand parsing, beginning with agreed
   `/HANDOFF=ON` and `/HANDOFF=OFF`. Reject malformed controls without state
   changes. Trigger fallback only before resident mutation: never retry an
   already partially completed destructive operation as a transient command.
3. Recover at least 27 bytes in the control overlay for the measured simple
   removal candidate, or use a smaller equivalent committed-removal hook.
   No available permanent region should be enlarged to solve this.
4. Measure the complete RCP candidate. Prefer reducing relocated references;
   if that is insufficient, increase the accepted maximum carrier header to
   2,048 bytes and qualify the larger header. This changes a builder/test limit,
   not the BCPX descriptor format. The reloader already streams declared,
   record-aligned headers and bounds relocation words against their length;
   it does not require the entire header to occupy the 1 KiB buffer. Larger
   header support still needs carrier validation and both-platform execution.
5. Measure final CCP diagnostics and relocation count: 16 additional words fit
   its current header. If payload growth exceeds 195 bytes, round command
   allocation up explicitly; this reduces command-mode free space, not unloaded
   TPA. Apply the same distinction to possible RCP allocation growth.

## Assessment

Handoff does not intrinsically require BDOS/BIOS growth, a smaller unloaded
TPA, or a changed CPX dispatch descriptor. Protected state and the CCP dispatch
fit. It is not a drop-in addition to every existing size limit: the control
reset candidate overruns its overlay, and RCP has no relocation-header headroom.
Proceed with a bounded overlay-compaction/carrier-capacity implementation, then
measure the whole result before calling the memory audit closed for production.
No production allocation or carrier-limit change is approved merely by this
probe. Lifecycle, suppression independence, present/missing transients, SUBMIT,
command-tail preservation and adjacent protected-byte guards remain acceptance
checks for implementation.

Baseline reproduced with build_rcp_cpx.py, build_ccp.py, build_bdos.py,
build_system.py and build_ccpreload.py. The legacy report_memory_layout.py
reports an overlap because it mixes low transient loader stack addresses into
its protected-only ordering; its failed output was not used as memory evidence.
