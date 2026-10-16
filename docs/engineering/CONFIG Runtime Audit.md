# CONFIG runtime support audit

## Scope and status — 2026-10-16

The original persistent-IOBYTE findings below are superseded by Build 011
[implementation and qualification](CONFIG%20Cold%20IOBYTE.md). Its disk-operand
patch and private-buffer relocation add no resident bytes. Printer/serial
findings remain open; no deferral has been approved.

This is a source/backend and existing-memory audit of the gated proposals in
CONFIG specification sections 13–15. It does not qualify new runtime code or
silently remove those proposals. No BIOS, BDOS, persistence format or utility
behavior changes are made by this audit.

## Measured existing boundaries

| Item | Evidence | Available space |
| --- | --- | --- |
| Model 4 BIOS | `build/bios/bios.bin`: 757 bytes, E991h through EC85h; listing ends at EC86h, exactly `LY_FILE` | 0 bytes in its assigned slot |
| CONFIG Build 007, two validation profiles | 14,716-byte COM; builder limit 3D00h bytes from load address 0100h | 900 bytes before 3E00h program/stack boundary |
| Unloaded TPA | `LY_TPA=D501h`, `LY_SYS=D5C4h` in `src/system/layout.inc` | Existing 53K target preserved |

These measurements are of the current artifacts, not estimates for the proposed
features. They do not establish that all other resident regions are full.
The CONFIG boundary is transient workspace ownership, separate from the TPA
contract. Moving its buffers/stack needs its own overlap and native-build checks.

## Backend findings

Model 4's `IO_CAPS` advertises 2002h: CRT console and CRT list. `BIOLIST`
can send output through the monitor for LST=CRT, but there is no physical LPT
implementation. Reader/punch leaves do not supply a configurable serial port.
No UART configuration implementation was found in the Model 4 platform or BIOS
sources. Hardware capabilities must not be inferred from the machine's name.

cpmsim's builder publishes 7337h. `chario.inc` supplies auxiliary input/output
at port 5 and printer status/output at ports 2/3. Neither the leaves nor the
public BetterCP/M configuration backend provides serial port enumeration,
baud, parity, stop-bit or handshake settings. Other machines' UART models in
the z80pack source tree are not evidence that this BetterCP/M backend supports
them. A CONFIG serial menu cannot honestly expose the proposed fields today.

## Persistent IOBYTE

Current cold stores load literal 95h: Model 4 in reclaimable stage one;
cpmsim in PL_INIT, shared by RAM/ROM cold initialization. Warm boot preserves
live changes. Editing an immediate would add zero instruction bytes at that
store, but is not a qualified persistence implementation:

- Stage one is installed separately from the resident carrier. CONFIG's existing
  resident-profile save transaction does not automatically update it.
- cpmsim's initializer is part of immutable platform code. Patching it needs a
  defined editable/fingerprint domain and consistent boot-template ownership.
- A protected configuration record requires a versioned storage contract,
  validated cold read, fallback and RAM/ROM qualification. BCST v1 cannot be
  repurposed without changing its header/checksum contract.
- Reading a default only when a startup command is enabled or not suppressed
  would fail the independent cold-default requirement.

Recommendation: audit a dedicated cold-default field and transaction before
adding syntax. Preserve STAT's live assignment role. Exact added code cost is
still unmeasured; do not advertise this as a free CONFIG-only change.

## Printer transformations

The required consumer is the list/printer path, not ordinary console output.
A console monitor RSX alone is not a printer hook: it also sees console output
and does not necessarily see cpmsim's physical printer leaf.

For a deliberately bounded 8-bit page/column implementation, three mode bits
can occupy one byte, with page length and tab width in two more bytes. Previous
CR, current page line and column require at least three further state bytes:
**six bytes of configuration/state before code**, under that explicit bounded
assumption. This is not a measured complete implementation cost. The spec has
not frozen numeric ranges, line counting (CR versus LF), wrap behavior, or FF
at an existing page boundary; those affect implementation and tests.

A prototype must measure each transformation and their shared dispatcher,
place it on the proper list path, preserve ordinary console/MONRAW behavior,
and include persisted settings, cold reset and failure/ready behavior. Model 4
also needs a real printer backend before physical-printer claims are possible.
With zero free Model 4 BIOS-slot bytes, this cannot be appended without space
recovery or an explicitly designed separate extension. No such change is
qualified here.

## Serial settings

There are currently zero enumerated configurable serial ports in the CONFIG
backend contract. Supporting the proposal requires a backend capability/query
and validated update API, real per-platform drivers, persistence, and measured
flow-control logic. XON/XOFF additionally requires an input-consumption policy
that does not steal application data. An eight-port ceiling is not eight
implemented ports. Exact runtime cost cannot be measured from absent drivers.

Recommendation: retain this as gated scope until a real backend is selected;
do not expose nonfunctional controls or assume host auxiliary files are UARTs.

## Next qualification gates

1. Complete CONFIG's existing drive-workbench CLI and pending-default design,
   measuring the remaining transient space before adding controls.
2. Select the persistent IOBYTE storage/boot transaction and measure a prototype.
3. Freeze printer counting/range rules and qualify a separately measured list
   transformation prototype if retained for 1.0.
4. Select actual serial hardware/backend support before implementing serial UI.

The last three remain proposals requiring decisions and implementation evidence;
this audit does not declare CONFIG complete or approve their deferral.

## Printer/serial RSX follow-up — 2026-10-16

The [peripheral RSX audit](CONFIG%20Peripheral%20RSX%20Audit.md) records measured
BDOS-filter coverage, lifecycle and capability limits, hardware-only serial
setup, memory accounting and historical Montezuma Micro evidence. It approves
neither implementation nor deferral. Build 011 IOBYTE behavior is unchanged.

## Scheduling decision — 2026-10-16

The maintainer has now deferred the printer RSX feature and CONFIG integration
to post-1.0. Earlier statements that no deferral was approved describe the audit
or prototype stage and are superseded for printer work. Preserve this evidence
for the [post-1.0 work item](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#printer-rsx-implementation-follow-up--2026-10-16).
The separate serial proposal remains undecided.

## Serial scheduling follow-through — 2026-10-16

The maintainer has also moved serial support and CONFIG serial configuration
to post-1.0. This supersedes the earlier open serial decision. See the
[backend audit](CONFIG%20Serial%20Backend%20Audit.md) and
[roadmap](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#serial-support-follow-up--2026-10-16).
