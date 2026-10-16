# CONFIG printer and serial RSX audit

## Status — 2026-10-16

Audit of CONFIG specification sections 14–15 following Build 011. No peripheral
implementation or deferral is approved by this report. The existing 53K unloaded
TPA contract remains in force; optional loaded RSXs may reduce TPA.

## Conclusion

CONFIG can provide the interface and save settings, with optional RSXs supplying
runtime behavior. However, existing BDOS interception alone does not cover every
standard printer path. Transparent coverage needs lifecycle-managed BIOS routing
hooks and accurate device capability reporting. No BDOS growth is inherently
required for that design, but zero BIOS growth cannot currently be promised.

Serial hardware setup is a narrower exception: CONFIG can program UART registers
and exit because the hardware retains them. That does not supply missing serial
I/O drivers, software handshake handling, or OS routing.

| Approach | Core changes | Coverage |
| --- | --- | --- |
| BDOS Function 5 printer RSX | None | Explicit BDOS list calls only |
| CONFIG programs identified UART registers | None for register setup | Hardware baud/framing/control-line setup only |
| Shared peripheral RSX with managed BIOS bindings | New bounded hooks and RSX lifecycle integration | Standard BIOS/BDOS paths, subject to backend support |

The third approach deserves a measured prototype before a 1.0 scope decision.
The Model 4 BIOS currently occupies all 757 bytes of its assigned slot, so even
small permanent hooks require space recovery. Keep the substantial optional
feature code and state outside permanent BIOS memory.

## Verified printer coverage

`tools/audit_peripheral_rsx.py` executes the built BDOS with a minimal Function 5
interceptor and instrumented BIOS leaves. It modifies no production image.

| Path | Bytes reaching BIOS LIST | Interceptor hits |
| --- | ---: | ---: |
| BDOS Function 5 | 1 | 1 |
| BDOS Function 2 with printer echo enabled | 1 | 0 |
| BDOS Function 9 with printer echo enabled | 1 | 0 |
| Direct BIOS LIST | 1 | 0 |

In `src/bdos/unified.mac`, `UB_LIST` calls `BIO_LIST`, while `UB_PUTNOW` performs
printer echo by jumping directly to `BIO_LIST`. Console-to-list IOBYTE routing
also occurs below BDOS interception. Direct hardware access is outside an OS
filter's coverage in either architecture.

The 21-byte dispatch probe receives a 256-byte module allocation. It contains no
transformations, settings API, or qualified relocation behavior; it is not a
production filter size estimate.

## Why existing monitor hooks are insufficient

MCON exposes console operations, not an independently identifiable printer
stream. Model 4 LST=CRT reaches `MH_OUT` alongside normal console output; there
is no origin tag to distinguish the two. cpmsim LST=LPT reaches `IO_PRINT`
without passing through MCON. A monitor provider therefore cannot substitute
for a general list filter.

An RSX must not simply overwrite BIOS vector operands. Existing STATEFUL repair
handles pointers inside allocations; the manager has specific MCON detach and
republish machinery, not arbitrary external-vector repair. A moved or unloaded
RSX would leave stale BIOS targets. COLD_ONLY does not solve explicit unload,
and ROM vectors may be immutable. Carrier init/shutdown fields do not establish
a supported general installation/removal callback contract in the current
production manager.

Reuse the monitor lifecycle pattern for any new peripheral bindings: detach
before movement/removal, repair addresses, publish valid targets, and retain a
raw backend path. Measure the complete hook and manager cost before claiming
that it fits. Providers intercepting BDOS must chain to the next layer rather
than recursively invoking their own service through page five.

## Backends and capability reporting

Model 4 `IO_CAPS=2002h` advertises CRT console and CRT list. `BIOLIST` uses the
monitor output path; punch returns without output and reader returns 1Ah.
There is no implemented configurable physical printer or UART backend.
Optional code can access Model 4 hardware directly, but still needs real drivers,
readiness handling, validated settings and integration with OS device routing.

cpmsim uses printer status/data ports 2/3 and auxiliary data port 5.
The local z80pack `cpmsim/srcsim/simio.c` implements these as `printer.txt` and
auxiliary input/output files or pipes. Printer output discards CR; auxiliary
status is not UART modem-handshake state. Guest baud/parity/stop-bit controls
have no corresponding UART registers on this backend. Do not advertise them as
functional serial settings. Test printer transformations at raw port-byte level
as well as through the host file, whose CR stripping changes observed output.

PIP queries the BIOS capability vector at BIOS+63 through
`src/utilities/common/pipphysical.inc`. A BDOS reader/punch RSX alone would not
update that query. New supported routes must be published and withdrawn safely
with the provider rather than leaving capability reporting inconsistent.

## State, persistence and memory

A STATEFUL provider can retain previous-character, column and page counters,
and its settings, across supported reconstruction. CONFIG can resolve a named
callable service afresh to inspect or change them. Saved settings could live in
a checked ordinary file and be replayed by the cold-start SUBMIT workflow;
that is a possible design, not an existing peripheral persistence contract.

Module allocation rounds up to 256 bytes, with ten bytes per named callable
service before rounding. The first active RSX also brings the existing 1K
manager reserve; subsequent providers do not each incur that reserve. There
are four active-module slots. Clock, monitor, printer and serial would consume
all four, so one combined peripheral provider is worth considering.

Printer line counting, ranges, page-boundary formfeed behavior and tab expansion
must still be frozen. Serial CTS/DSR waiting requires driver behavior;
XON/XOFF additionally needs state and an input-consumption policy that preserves
application data. Neither becomes implemented merely by saving a CONFIG field.

## How Montezuma Micro handled it

MM CP/M did provide printer and serial configuration. Both retained original
CONFIG 3.01 and 3.10 binaries expose LF suppression, simulated formfeed and page
length; serial menus expose baud, parity, word length, stop bits, DTR/RTS,
CTS/DSR waiting and inversion. They also offer saving configuration to disk.
The binaries and extraction provenance are under `third_party/montezuma/`.

The vendor's [System Programmer’s Guide](https://oldcomputers-ddns.org/public/pub/manuals/montezuma_system_programmers_guide_trs80m4.pdf)
contains BIOS printer transformation code and state, plus Model 4 serial port
register definitions. Its printed BIOS 2.99+ listing places printer state at
F124h–F127h and identifies serial reset/baud/control/data ports E8h–EBh.
MM's solution was configurable BIOS drivers, rather than optional BDOS filters.
Its [February 1987 advertisement](https://colorcomputerarchive.com/repo/Documents/Magazines/80%20Micro/1987/80%20Micro%20-%208702%20-%20February%201987.pdf)
also describes configurable RS-232 and printer LF/formfeed handling.

For implementation-scale evidence, Jeff Post's April 2005 reconstructed MM 2.32
BIOS disassembly was assembled in selected regions:

| Selected routines including local state | Bytes |
| --- | ---: |
| Printer status/output/initialization | 116 |
| Serial status/input/output/CTS/DSR/setup | 78 |

These are not complete BIOS, CONFIG, or BetterCP/M RSX sizes. They exclude our
proposed tab expansion, XON/XOFF, generic service interface and persistence.
The reconstruction is not original vendor source and warns about comment
accuracy. Its printer branch ordering differs from the later printed vendor
listing; do not adopt that as a normative suppression algorithm or assume all
MM revisions behaved identically. No support for tab expansion or XON/XOFF was
established by this evidence.

## Reproduction and next decision

Build BDOS using the repository's normal build, then run:

```
python3 tools/audit_peripheral_rsx.py
```

Optional `--mm-archive PATH` accepts the retained `mmcpm232.zip` reference.
The tool writes measurements under ignored `build/audit/peripheral-rsx/` and
mechanically shortens long reference labels for the host assembler. It does
not add vendor code to production sources.

Next, prototype a managed list binding and optional printer provider, measure
permanent and loaded cost, and qualify echo, direct BIOS calls, IOBYTE routing,
move/unload, and capability changes. Select actual serial hardware/backend
support separately. This is a bounded extension of the existing RSX pattern,
not grounds for declaring these proposals complete or automatically deferred.

## Printer prototype follow-through

The [measured prototype](Printer%20RSX%20Prototype.md) exercises the proposed
primitive and optional transformations. It measures 19 bytes for the basic
permanent hook/cold call and a 512-byte optional allocation; full manager
integration and BIOS space recovery remain unqualified.

## Scheduling decision — 2026-10-16

The maintainer has now deferred the printer RSX feature and CONFIG integration
to post-1.0. Earlier statements that no deferral was approved describe the audit
or prototype stage and are superseded for printer work. Preserve this evidence
for the [post-1.0 work item](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#printer-rsx-implementation-follow-up--2026-10-16).
The separate serial proposal remains undecided.
