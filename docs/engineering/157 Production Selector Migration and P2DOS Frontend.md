# Engineering Specification 157: Production Selector Migration and P2DOS Frontend

## Purpose and bounded increment

This increment implements item 1 of the post-Stage-8 implementation program.
It migrates every active BetterCP/M private selector in one coordinated change,
moves the proof services, establishes the inherited P2DOS fallback, and adds the
separate P2DOS clock frontend. It does not change the accepted extension
architecture, carrier dependency model, or native TIME ABI.

Completion requires current source, generated clients and focused tests to agree
on the final namespace; no obsolete production alias may remain. Full
release-candidate qualification with both clock providers remains part of the
later cross-platform qualification program.

## Final selector inventory

| Historical implementation | Production | Owner |
| ---: | ---: | --- |
| 200 | 176 | CPX profile control |
| 202 | 177 | RSX profile control and reconstruction |
| 204 | 178 | console/video cursor support |
| 205 | 179 | printer-echo control |
| 206 | 180 | protected subsystem version descriptor |
| 207 | 181 | disk configuration and utility I/O |
| 208 | 182 | callable resident-service registry |
| 209 | 183 | FDF service |

HELLO and ECHO proofs moved from 201/203 to non-public Functions 198/199.
Functions 200/201 are now exclusively the inherited P2DOS-compatible GET/SET
clock interface. The explicit core gateway recognizes 176-183 and 200/201; it
does not blanket-capture other high functions. No historical BetterCP/M private
selector is retained as an alias.

## Source audit and implementation

The coordinated audit covered fixed BDOS routing, extension dispatch, CCP and
CPX clients, RSX modules, utilities, BIOS and platform disk paths, conformance
fixtures, host builders, generated-image builders, runtime tests, programmer
guides, architecture specifications, release contracts and the backlog.
Semantic dual-use callers were handled by purpose: TIME.COM uses Function 182
for service discovery and Function 177 for provider/profile control; FDF.RSX
uses Function 183 for FDF service and Function 177 for profile removal.

The ordinary unhandled result for Functions 200/201 is A=FFh and HL=00FFh.
Other unassigned selectors continue through ordinary BDOS behavior. The compact
gateway and extension changes preserve the fixed resident layout: BDOS exactly
fills its region, the extension region retains one free byte, and the default
53 KiB TPA boundary does not move.

## P2DOS frontend

`P2DOS.RSX` is a BRSX-v2 module advertising numeric Functions 200 and 201. It
contains no clock driver. Each invocation resolves callable service `TIME`, ABI
1.0, through Function 182 and invokes the current provider; it retains no
provider pointer between calls.

GET stages the native request privately and copies the five-byte record to the
caller only after native success. SET stages the caller record before invoking
the provider. Success returns A=00h and HL=0000h. Resolver, provider,
unsupported-SET and other claimed failures return A=FEh and HL=00FEh without
chaining. DE, SP, IX and IY are preserved, and failed GET leaves the caller
buffer unchanged.

The module occupies 140 code bytes in a 256-byte resident allocation. Its
builder emits the ordinary BRSX-v2 carrier and the complete-system, TRS-80 and
z80pack image builders include `P2DOS.RSX`.

## Focused qualification evidence

The complete-system build preserves the D5C4h-EF7Fh resident span and reports
the 54,272-byte record-aligned COM ceiling. The z80pack image build also
completes with the new frontend.

Focused tests cover:

- all final production and proof carrier selectors;
- positive routing and negative ordinary selectors, including obsolete 202;
- absent 200/201 FFh/00FFh behavior and preserved registers;
- P2DOS GET and SET success, claimed failure, failed-GET atomicity, and
  per-invocation provider discovery;
- callable-service gateway, TIME artifacts, RSX loader safety, request-v2,
  FDF integration, packed TPA, profile management and platform boot artifacts.

The stale-selector audit finds old values only in deliberate historical
documentation, migration tables, unrelated numeric data, and the negative
selector test. Engineering Specifications 153 and 155 remain historical audit
records; this specification records their completed item-1 disposition.

## Remaining release work

This focused qualification completes implementation-program item 1. It does
not replace final release-candidate testing. TIME.COM SET handling, complete
provider replacement/unload/WBOOT qualification, and the exact two-platform
clock and P2DOS matrix remain under implementation-program item 6 and final RC
qualification.
