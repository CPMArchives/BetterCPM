# 153 — Stage 6 Extension and Clock Source Audit

Date: 2026-09-25
Status: accepted Stage 6 evidence; no source-code change

## Result

The current implementation supports the frozen Stage-6 architecture without
another lifecycle, PDS or hardware abstraction. Architecture Specifications
20, 22 and 25 now define the final 176–183 production selectors, the native
TIME ABI, and the P2DOS-compatible 200/201 frontend contract. Source migration
and frontend implementation remain later implementation work.

## Current selector inventory

The fixed extension dispatcher currently recognizes provisional Functions
200, 202 and 204–208. Disk service dispatch uses 207, while FDF.RSX additionally
intercepts 209. HELLO.RSX and ECHO.RSX use proof Functions 201 and 203.

The coordinated migration is:

| Current | Final | Owner |
| ---: | ---: | --- |
| 200 | 176 | CPX profile control |
| 202 | 177 | RSX profile control/reconstruction |
| 204 | 178 | console/video cursor support |
| 205 | 179 | printer-echo control |
| 206 | 180 | protected subsystem version descriptor |
| 207 | 181 | disk configuration/utility I/O |
| 208 | 182 | callable resident-service registry |
| 209 | 183 | FDF service |

Proof selectors move from 201/203 to non-public 198/199. No obsolete production
alias is retained.

Two files require semantic rather than numeric substitution. TIME.COM uses 208
for service discovery and 202 for provider/profile information, becoming 182
and 177. FDF.RSX uses 209 for FDF service and 202 for unload/profile handling,
becoming 183 and 177.

The current unknown-high-function path returns zero. Final unhandled Functions
200/201 must instead return A=FFh and HL=00FFh. This is a required implementation
change and acceptance test, not existing behavior.

## Registry and PDS ownership

Function 182 retains the implemented 20-byte resident-service request, its
LOOKUP, ENUMERATE and DESCRIBE_REGISTRY operations, and status values 00h–0Dh.
Validated BRSX-v2 provider descriptors remain in provider allocations, while
gateway and reconstruction-control state belongs to the fixed extension
subsystem. The bounded 192-byte 1.0 PDS acquires no new owner or allocation.

Both required clock providers advertise callable TIME ABI 1.0 and omit SET
capability. TIME.COM consumes the callable service and has no hardware-specific
or P2DOS dependency. A writable provider or controlled fixture remains required
to qualify successful SET.

## P2DOS evidence and frozen results

Original P2DOS 2.3 source labels Functions 200 and 201 as successful with
A=00h. Its common exit path clears and returns HL=0000h, restores DE and the
function selector, and does not define a public flag result. The bundled DATE
caller does not inspect a return status.

BetterCP/M therefore preserves A=00h, HL=0000h success and DE, SP, IX and IY.
It defines A=FEh, HL=00FEh when P2DOS.RSX claims but cannot complete a request,
and A=FFh, HL=00FFh when no frontend handles the selector. FEh is a BetterCP/M
extension, not historical P2DOS behavior. Failed GET leaves the caller's five
bytes unchanged, and an installed frontend never chains a claimed failure.

Evidence source:

<https://dflund.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/bdos/p2dos23/p2dos1.mac.txt>

## Optional 104/105 frontends

The four-byte CP/M 3/DOS+ and five-byte Z80DOS conventions cannot safely be
autodetected. Before either optional frontend is admitted, implementation must
prove that both cannot be active simultaneously. A narrow conflict check or
configuration restriction is sufficient; no general dependency framework is
required. Both remain outside the default profile and are not release gates.

## Implementation acceptance

The later coordinated source change must classify every 200–209 occurrence,
update dispatchers, RSXs, utilities, tests, fixtures and builders, rebuild all
in-tree clients, and regenerate distribution images. Qualification must prove
the final selectors, absence of obsolete aliases, FFh fallback, P2DOS success
and claimed failure, unchanged GET buffer on failure, per-call TIME discovery,
provider movement and removal, frontend load/unload, and unchanged native
TIME.COM operation with both required providers.
