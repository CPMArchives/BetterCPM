# TCAP feasibility campaign: measured results

Status: isolated experimental implementation evidence, 7 November 2026.
The user authorized this bounded campaign after the final design review. Utility
migrations and release assignment remain deferred. Source baseline is the main
merge through PR #654 (`de0dbd20`); exact experiment/source/assembler hashes and
case inventory are in the [machine-readable evidence](evidence/tcap-feasibility/report.json).

## Follow-up status

The [second campaign](TCAP-Placement-Results.md) resolves the rejected-carrier
and bridge-placement gates in a private packed reference build. The first
campaign evidence below remains unchanged as a historical measured checkpoint;
its blockers must not be mistaken for the latest private-build disposition.
Production admission and utility migration are still incomplete.

## Disposition

The ownership/restoration concept works in the tested CPU/model slice, but the
naïve integration is **not ready for production placement or carrier packaging**.
This is not a delivered TCAP facility or public ABI implementation. HELP stays
held; TYPE, TED and HELP source is unchanged. Legacy personalities, SCRN/SCX and
normal console behavior retain their existing production contracts.

The campaign implements an experimental ANSI-associated owner, one capture and
nested takeover/emphasis state, saturating 32-bit serials, nonrecursive rendering
repair, safe-stack recovery, route mismatch handling, and an active-session guard
before the real commit engine. It uses private XTCP 0.1 conventions, not the
proposed 32/64/96/16-byte public request interface.

## Behavioral evidence

Forty-two named cases pass on each of two backends at each of two owner origins
(9000h and A101h): **168 case executions**, not 168 independent requirements.
The existing full `test_rsxcommit.py` mover/scheduler/publication regression also
passes against privately staged copies of the actual assembled engines.

Coverage includes normal and takeover emphasis, prior rendition, incomplete
parser and nested-scope refusal, stale/wrong tokens, serial carry/exhaustion,
SCX save-slot cursor/rendition independence, real cooked text, ^P echo and LIST
byte capture, route mismatch, partial Begin/End failure with persistent ownership,
retryable recovery, fatal failed-route repair, and cooked ^C abandoning the real
BDOS private frame into an injected safe-stack warm entry.

The model checks default margins, visible personality state, cleared pending
wrap, normalized rendition and the resulting prompt-start position. The host
check uses independent pyte-rendered output; Model 4 checks hardware-facing video
RAM and cursor fields under CPU emulation. These are not native visual results.
The busy guard preserves transaction input/publication memory when active; idle
calls reach the unmodified commit engine and invalid commits do not publish.
It is a wrapper experiment, not proof of finalizer/precommit integration or races.

## Measured resource ledger

| Item | Result | Interpretation |
| --- | --- | --- |
| Baseline portable ANSI payload | 1,466 bytes | Assembled current source. |
| Experimental payload | 2,028 bytes | Owner adds 562 bytes of code/data; its trailing data region is 52 bytes including constant normal rendition. |
| Baseline personality allocation | 1,536 bytes | Existing carrier builder accounting, including its descriptor. |
| Projected experimental allocation | 2,048 bytes | Raw payload plus two 10-byte service descriptors exactly fills eight pages. **Not an allocated/loaded carrier:** packaging failed. |
| Projected allocation delta | 512 bytes | Excludes new fixed coordinator/allocator cost and unmeasured manager/cache integration; not a measured TPA loss. |
| Experimental relocation entries | 292 words | Existing 512-byte header has room for 232 entries from offset 48. Needs 120 more header bytes than allowed. |
| Out-of-line bridge | 93 bytes | Rendering recovery coordinator, routing/commit wrappers and one coordinator-state byte; linked at 4000h in the fixture only. No packed resident placement assigned. |
| Reference Model 4 BIOS | 757/757 bytes | Zero free bytes in its current packed region. |
| Reference unified BDOS | 3,451/3,454 bytes | Three free bytes in its current region. |

A two-byte payload change near the descriptor/page boundary changes projected
loaded allocation by a full page. The report must not equate code delta with
loaded cost. The fixed allocator, full request parser, registry compatibility,
reloader/CCP wiring and other personalities are not included in this slice.
No claim is made about current full-RAM cpmsim or protected-ROM layout capacity
from this reference Model 4 map.

| Executed path | Client stack peak | Safe warm-stack peak | BDOS private stack peak |
| --- | --- | --- | --- |
| Model 4 backend | 12 bytes | 8 bytes | 24 bytes of current 40-byte region |
| ANSI-host backend | 26 bytes | 16 bytes | 32 bytes of current 40-byte region |

Every SP assignment is checked against separate fixture stack bounds; leaving
the selected BDOS stack range fails the campaign. These are observed maxima for
these paths, not whole-system worst-case stack qualification. In particular,
the host slice leaves only eight bytes of current private-stack margin before
additional integration work. Abandoned-frame recovery uses the new safe fixture
stack, not the old private call frame.

## Design correction supported by execution

A separate private BDOS column-reset entry is unnecessary for the tested safe
coordinator path: after rendering repair, ordinary BDOS Function 2 CR/LF sets
`UB_COLUMN` to zero using the existing cooked contract. It preserves echo and
does not require the personality to write BDOS-private storage. The test seeds a
nonzero cooked column and verifies zero after recovery and after cooked ^C.

Use this existing contract as the first integration choice, provided the
coordinator has already left the abandoned BDOS frame and established a safe
stack. Do not call BDOS from a BIOS output callback. The route observer performs
rendering repair only, retains RecoveryRequired, and leaves full CR/LF recovery
to the safe coordinator. A failed route repair enters the explicit fixture fatal
HALT instead of forwarding unverified output.

SCX legacy operation 15 also demonstrates why clients cannot interpret every
successful legacy operation as A=0: Model 4 returns the accepted cursor argument.
The prototype checks its defined invalid result and updates personality visibility
alongside backend visibility. Typed SCX operations with defined zero success keep
their own result rules.

## Exact production blockers

1. **Carrier packaging:** the ordinary builder rejects the raw 292-entry image
   with `RSX relocation directory exceeds its header`. No experimental carrier
   is published. Investigate fewer absolute references or a separately costed
   sharing/placement arrangement while preserving personality/backend ownership.
   Do not widen the format silently. Raw two-origin rebasing is not real-manager
   relocation or public service lookup qualification.
2. **Fixed placement:** the 93-byte fixture bridge and persistent validity allocator
   have no assigned space; the reference BIOS has none and BDOS has three bytes.
   A coordinated layout/space-saving design must satisfy the memory policy. No
   resident code, stack boundary or unloaded TPA has been changed to hide this.
3. **System integration:** actual finalizer serialization, coordinator/version
   admission, boot-global identities, reloader/CCP return guards and safe error
   dispositions are not wired. Full candidate ABI, other personalities, live
   cpmsim, protected-ROM and native Model 4 qualification remain outstanding.

These blockers are results of this campaign, not reasons to label the concept
impossible. The bounded experiment is complete; production implementation is not.
The next campaign should address carrier reference pressure and fixed placement
before any utility migration, then apply the existing integration qualification
plan. No release or ABI freeze follows from this report.

## Reproduction and scope

Run the [private campaign](../../tools/prototypes/tcap/README.md). It rebuilds the
baseline BIOS for matching symbols and stages all experimental products under
`build/tcap-feasibility/`. It deletes stale reports before work and records PASS
separately from blocked production feasibility. Pinned pyte/wcwidth, assembler,
assembled image and source hashes are recorded. No distribution images or
manifests are changed.

The host fixture uses the shared BIOS router with a substituted host-output leaf,
not a complete cpmsim BIOS. Keyboard and warm-return boundaries are injected.
No claim of live RSX installation, native assembly parity, actual-manager owner
compaction, public Function 182 discovery or public TCAP conformance is made.
The historical split-core `tools/test_bdos.py` is not the unified-core regression;
its initial invocation could not run with this workspace's build prerequisites.
The campaign's real unified-BDOS console paths and the existing commit regression
are the relevant executed checks; a full unified filesystem/system regression is
outside this isolated slice.
