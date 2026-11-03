# Model 4 lowercase correction: final source review

Reviewed 2026-11-03 against source candidate
`0bd7f127ebca849fe613c7a36b3cd9c1c38314a8`. This is a source/contract review,
not a substitute for the separate native qualification receipts.

## Assessment

No new production defect was identified in the three changed BIOS/Model 4
assembly files. The correction fits the existing allocation and preserves the
reviewed public contracts. It is suitable for maintainer acceptance review
with the measured qualification scope and remaining limitations stated below.
The separately merged BDOS/UI changes are included in the candidate but are
not attributed to the keyboard work.

## Keyboard path

`M4_KEYFD` reads modifiers once for character translation. For matrix slots
0..31, Control is handled first by returning the physical index. The expression
`(E-1) < 26` restricts alphabetic case conversion to A..Z, excluding @ and the
unconnected positions. Either Shift bit returns uppercase; otherwise the state
byte contributes bit 5 only when lock is off. Caps Lock therefore forces
uppercase, including with Shift. Other modifier bits cannot change that rule.

For punctuation, XOR 10h is equivalent to the previous two arithmetic cases
over the reachable ranges: comma through slash gain 16; 1 through semicolon
lose 16. Shift-0 returns before that operation. Special controls return below
the punctuation range, and Shift-Left retains DEL. The Control punctuation
lookup returns directly, so Shift does not change Montezuma chords.

CAPS confirmation compares the momentary contact with state bit 3, delays,
and samples again. Matching endpoints toggle bit 3 on either edge, but toggle
the lowercase mask only on a press. With 0922h iterations, the delay loop is
60,783 nominal Z80 T states, approximately 14.99 ms at 4.05504 MHz, before
surrounding instructions and hardware waits. This is **two-sample confirmation**;
it does not prove the contact stayed continuously stable throughout the delay.
Ordinary-key timing remains the inherited implementation.

Every scanner return passes through `M4_ROWS`, which initializes D=0. That
invariant makes the compact special-key lookup and pending-byte clear valid.
`M4_IN` captures ASCII when the physical identity first changes, and compares
identity rather than subsequently translated ASCII. Releasing Shift, Control,
or CAPS while holding a letter therefore does not synthesize another character
or alter its already captured case. FFh is outside all 56 matrix positions,
so using it as the empty identity preserves the @ position. The queue remains
one character deep; the patch does not promise general n-key rollover.

Cold loading initializes the lowercase mask from the resident image. Warm
reconstruction leaves the resident state intact. `M4_INIT` serves screen
clearing as well as initial output setup and does not reset CAPS.

## Space-saving changes

| Change | Contract reasoning | Supporting check |
|---|---|---|
| Shared exact-zero return | CONST branches directly to XOR A/RET, bypassing LDIR; no transfer is performed | All IOBYTE routes and BIOS vectors |
| LISTST flags | Only IOBYTE list bits 40h produce FFh/NZ; 00h, 80h and C0h produce 00h/Z | Exhaustive routing/status test |
| Shared reader/punch RET | Punch lands on RET, after the reader's LD A,1Ah | Assembled vector execution |
| BIO_SLOT address/count | For q=0..7, RRCA/RR constructs 128*q; OR with an aligned buffer high byte selects the correct page | All eight slots; builder rejects non-1024-byte alignment |
| Single BC=128 setup | Both copy directions reach BIO_SLOT after successful physical preparation; no intervening instruction changes BC | Real READ/WRITE contract execution, all 80 records and failures |
| Two-sector fetch factoring | Each M4_ONE saves its table pointer; 16-bit INC DE preserves read flags; first failure returns before the second read | Arbitrary table triples and both error positions |
| Selector restoration | PUSH AF/POP BC restores the selector into B while retaining the fetch flags; IX is preserved | All selectors and success/error stack checks |
| Monitor helper relocation | MONCALL remains a JP whose target begins LD HL,(MP_MON); helpers remain outside cpmsim's textual console substitution | API 1.7 inspection, both-platform hooks and native cpmsim providers |

The assembler emits 757 bytes at E991h..EC85h, with no spare byte. Model 4
disk-state and monitor-binding anchors remain fixed. The cpmsim private disk
state and binding changed addresses; generated bindings, ownership metadata
and the ROM copy-source map now agree. The ROM inventory independently checks
every remaining operand after the two removed absolute jump operands.

## Provider and publication compatibility

ADM3A, VT52 and ANSI use the unchanged monitor/screen service contracts. M4SCRN
is explicitly a **build-matched hardware backend**, and contains absolute cursor
and column bindings. Its rebuilt carrier must accompany the new BIOS; an old
M4SCRN carrier is not qualified against the new private state addresses. The
new distribution includes the regenerated carrier. This does not imply that
old and new platform-specific media may be mixed freely.

Before publication, assign the changed BIOS and build-matched M4SCRN component
revisions under `specifications/COMPONENT-REVISION-TRACKING.md`. Their current
registry identities are BIOS 1.14 revision 001/API 1.7 and M4SCRN 1.7 revision
001. Candidate source/artifact hashes preserve provenance but do not replace
independent component revisions. No identity change is made during the active
native run, and the frozen earlier candidate remains separate.

## Retained edge case for separate review

A differential instruction-level check found that a rollover can leave B in
the pending byte after CONIN returns A, while a subsequent empty matrix makes
CONST report 00h. The same result occurs in the verified earlier BIOS and the
new BIOS. The test executes the real M4_IN and BIOCONST, replacing only M4_SCAN
with scripted scan returns; it is not a native timing result.

`evidence/2026-11-03-model4-requalification/retained-pending-status-review.json`
records both BIOS hashes and the observed values. This retained discrepancy
may delay visibility of queued input for a client that gates CONIN on CONST.
It is not evidence of a regression introduced here. Record it for a separate
post-1.0 investigation rather than expanding the lowercase correction.

## Limits and stopping point

Qualification demonstrates the listed combinations and traces, not every
physical keyboard, bounce waveform, host layout, emulator version or terminal.
Ordinary physical host CAPS quick taps remain unconfirmed following the earlier
two-press report; the captured single-press sequence passed. Real-hardware
timing is a separate evidence limit. The source review provides no basis for
another production keyboard change merely to accommodate the earlier report.

The native batch has completed and its individual receipts were reviewed:
269 passing assertions, zero failure/error summaries, and passing ADM3A, VT52
and ANSI provider/integrity checks. The new cpmsim image separately has 121
selected passing conformance assertions, three passing providers and the
ordinary/XSUB reconstruction checks described in the qualification report.

The remaining acceptance work is component identity/publication review and an
explicit disposition of the stated physical-host evidence limit. No additional
run of the completed batch is requested. Further operator tests should follow
only from a concrete failure or a material uncovered contract, not an open-ended
search for coverage.
