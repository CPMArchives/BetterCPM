# Combined TCAP integration and qualification

Status: engineering candidate qualified, 8 November 2026. TCAP 2.0 is implemented
in one unloadable personality/renderer module on cpmsim, Model 4 and Model II.
**Later on 8 November, the maintainer assigned TCAP 2.0 to BetterCP/M 1.1**
as part of its frozen feature set. This report remains evidence for the
engineering candidate, not acceptance of the final 1.1 distribution bytes.
Utility migrations, further personalities and HELP delivery remain deferred.
This report qualifies the compact replacement, not the retired transaction
engine or the intervening 1.x template implementation.

## Full display-path cost

These totals include personality, renderer, immutable facts, callable descriptors,
cache footer, allocation rounding, the complete application helper and its data,
shared BIOS display state, and disclosed 32-byte call-site and 32-byte stack
allowances. Only general RSX machinery is excluded.

| Platform | ADM3A | VT52 | ANSI |
| --- | ---: | ---: | ---: |
| cpmsim | 1,247 bytes | 1,247 bytes | 1,759 bytes |
| Model 4 | 994 bytes | 994 bytes | 1,762 bytes |
| Model II | 994 bytes | 1,250 bytes | 1,762 bytes |

ADM3A and VT52 meet the 1,280-byte ceiling. ANSI meets the separately accepted
1,792-byte ceiling. Its resident allocation is 1,536 bytes; its caller helper is
159 bytes (113 code, 46 data). Adding 64 bytes of call/stack allowances and three
native BIOS cursor bytes gives 1,762. cpmsim has no shared cursor bytes and totals
1,759. No rendering engine is hidden in an uncounted BIOS area or bank.

The first loaded RSX also requires 1,024 bytes of shared RSX machinery. Therefore
loading ANSI alone consumes 2,560 bytes of TPA before accounting for application
code: 1,536 display plus 1,024 generic machinery. The caller helper lives within
the application's remaining TPA. Complete unload returns the entire loaded
allocation. **Additional permanent display reservation: zero bytes.**

## Qualification

Each platform passed source cold boot; legacy application output; portable TCAP
clear, position and strong/fallback rendering; ordinary warm returns; movement
with a second RSX; repeated unload/reload; real SYSGEN installation; installed
cold boot; and the same installed-disk lifecycle. Native screenshots verify
reverse TCAP TEXT for ADM3A and ANSI, and plain fallback for VT52. All nine
canonical builds reproduce the exact tested carrier bytes.

The ANSI CPU comparison passes **64,942 checks** at two relocation addresses on
both native and host renderers. It covers the existing recognized ASCII command
set, supported native attributes, full host rendition/indexed/RGB groups,
malformed groups, bounded sequences, cancellation, margins, reusable saves,
Function-178 cursor presentation, and direct portable operations. Maximum
observed external stack use is **22 bytes**, within the charged 32-byte allowance.
Model II separately passes exact admission, public/foreign/platform refusal,
video-bank restoration, protected caller stacks, interrupt preservation and its
included guarded 20-byte private stack.

A separate packaged-startup campaign passed on all three platforms. It boots
without a prequeued submit fixture, then uses ordinary command input. The tests
verify complete COM files on disk, check every loaded padding byte, and clear
that padding before warm return so later loads cannot pass on stale bytes.
The original full-size COM is loaded again after complete unload.

| Platform | Unloaded maximum COM | With ADM3A | With VT52 | With ANSI | Final unloaded maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| cpmsim | 57,344 | 55,296 | 55,296 | 54,784 | 57,344 |
| Model 4 | 54,272 | 52,480 | 52,480 | 51,712 | 54,272 |
| Model II | 57,344 | 55,552 | 55,296 | 54,784 | 57,344 |

All entries are bytes, not rounded free-KiB display values. The final unloaded
boundary equals the original boundary on each platform. Tests use the actual
cpmsim and trs80gp executables identified in their receipts; this is emulator
qualification, not a claim of physical-hardware testing.

## Package and boundaries

The generated engineering bundle contains bootable images, the matching
SYSTEM.SYS and RSX workers, ADM3A/VT52/ANSI modules, a qualified DEMO consumer,
startup dependencies, accounting manifests and qualification receipts. From a
booted image, use `RSX LOAD ANSI`, `DEMO 1`, press `1` at READY, and
`RSX UNLOAD ANSI`. Select ADM3A or VT52 in the same way. No separate screen-backend
load is required. The recorded package was an engineering candidate. Its
qualification predates the separate 1.1 release assignment and must be checked
again against the final distribution media.

The public interface is the [TCAP 2.0 direct-operation contract](TCAP-Direct-ABI.md).
It is intentionally incompatible with the unreleased template ABI and does not
advertise TCAP 1.x. A personality still defines the legacy protocol; its renderer
performs the platform effects. Existing SCRN/SCX clients and broader screen APIs
retain their separate path. TYPE, TED and HELP have not been migrated.

These profiles use a fixed **80x24, seven-bit terminal protocol**. Arbitrary host
geometry, terminal-size negotiation and the historical eight-bit raw-BIOS bypass
are outside this candidate. The [coverage description](TCAP-Integrated-Display-Redesign.md#protocol-coverage-and-boundaries)
records the retained commands, native limitations and host attribute behavior.
No whole-SCX feature parity or universal terminal conformance is claimed.

The [evidence index](evidence/tcap-direct-integration/README.md) contains raw
receipts, exact module/image hashes, source closure and reproduction checks.
The [inline-footer contract](RSX-Inline-Cache-Footer.md) records why the allocation
reduction is real and why unmodified providers retain ownership of their padding.
