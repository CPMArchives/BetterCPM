# CONFIG serial backend follow-up — 2026-10-16

## Status

Completes the backend inventory for CONFIG specification section 15 after the
printer prototype was moved to post-1.0. The maintainer has now moved serial support and CONFIG serial configuration
to post-1.0. This report implements no driver.

## Platform findings

| Platform | Available transport | Current BetterCP/M support | Missing for CONFIG serial controls |
| --- | --- | --- | --- |
| Model 4 / trs80gp | Emulated Model 4 UART; emulator can connect to TCP/IP or a host serial device | No configured UART reader/punch backend; current capability mask 2002h supplies CRT console/list | Validated UART programming, supported settings table, driver/routing, readiness and handshake behavior, configuration-state contract |
| cpmsim | Auxiliary input/output files or pipes through ports 4/5 | Auxiliary reader/punch byte transport | No guest UART baud/framing/control-line interface on this endpoint; cannot honestly expose those controls |

This distinction matters: an emulator having serial support does not mean the
operating system has implemented a serial backend. Conversely, missing
BetterCP/M support is not evidence that trs80gp lacks the hardware emulation.

## Primary local evidence

- `src/bios/bios.mac`: Model 4 capability mask and reader/punch leaves.
- `src/platform/trs80m4/hardware.inc`: no implemented UART configuration layer.
- `src/platform/z80pack/chario.inc`: auxiliary byte routing.
- Local z80pack `cpmsim/srcsim/simio.c`: auxiliary ports 4/5 and file/pipe paths;
  these endpoints have no guest baud/parity/stop-bit registers.
- Installed trs80gp help, `Serial_(RS-232)_Ports.html`, under its application
  `Contents/Resources/help/`: documents TCP/IP connection/listen, host serial
  device connections on macOS/Linux, and propagation of emulated UART settings
  to a host serial device. For TCP/IP the framing settings do not change the
  network protocol, but emulated transmit/receive speed follows port setup.
- Retained reconstructed MM 2.32 BIOS: TR1602 routines use E8h modem/reset,
  E9h baud generator, EAh UART control/status and EBh data. This is a reference,
  not a qualified BetterCP/M backend or a complete modern settings table.

## Work breakdown

A transient can write hardware baud/framing registers and exit without adding
resident setup code. That observation does not establish OS serial usability.
To expose serial controls usefully, separate these tasks:

1. Establish the supported Model 4 UART register encoding and exact rates;
   reject unsupported values before hardware writes. Do not infer support for
   38400/57600/115200 from the generic vocabulary in the CONFIG proposal.
2. Supply reader/punch and any selected console routing, readiness and supported
   hardware/software flow-control behavior. Preserve input bytes: the MM
   reference's seven-bit input mask must not silently define an eight-bit mode.
3. Publish actual supported endpoints and settings to CONFIG/PIP consistently.
   Reuse the peripheral lifecycle discipline if an optional RSX owns routes.
4. Define live versus saved state, startup replay, reset/reconstruction behavior
   and handling of settings that cannot be read back reliably from hardware.
5. Qualify TCP/IP and, where available, host serial connections separately.
   Register-write fixtures alone do not qualify a real serial link or handshakes.

XON/XOFF is a driver policy with an input-consumption/state contract; it cannot
be implemented solely by setting UART baud/framing bits. CTS/DSR support must
also be tested through actual readiness/wait paths. Do not expose unsupported
controls or assume two emulator platforms have identical capabilities.

## Scheduling alternatives

For 1.0, implementing Model 4 serial support is new backend work, rather than a
small CONFIG menu change. It requires the bounded memory/lifecycle review above.
Moving it to post-1.0 is a separate maintainer decision; printer deferral does not
implicitly defer serial. Until that decision and implementation, preserve the
existing auxiliary transport and omit nonfunctional serial menu entries.

## Scheduling decision

The maintainer selected post-1.0 implementation. This supersedes the pending
scheduling alternatives above. Preserve this inventory for the
[serial work item](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#serial-support-follow-up--2026-10-16).
Existing auxiliary transport is unchanged.
