# PIP physical-device and IOBYTE routing audit

## Status

Measured on 14 October 2026 against main after PR 272. These are isolated
assembly experiments. No production BIOS, BDOS, memory layout or PIP behavior
has changed. PIP physical aliases continue to report `DEVICE UNAVAILABLE`.

The missing behavior is shared BIOS routing, not just PIP parsing. The public
console output vector goes directly to the platform backend; console input
ignores IOBYTE; list/punch discard output; reader returns EOF. STAT can change
the byte but that does not establish actual device routing.

## Measurements

Run `python3 tools/audit_iobyte_routing.py`, then
`python3 tools/test_iobyte_routing_audit.py`. Outputs live under
`build/audit/iobyte`; neither tool publishes system images.

| Platform / experiment | Baseline BIOS | Prototype BIOS | Growth | Existing allocation |
| --- | ---: | ---: | ---: | ---: |
| Model 4, table dispatch | 636 | 787 | 151 | 638 |
| Model 4, CRT-only compact dispatch | 636 | 692 | 56 | 638 |
| cpmsim, table dispatch and host device ports | 372 | 537 | 165 | 638 |

The compact Model 4 candidate implements the supported CRT endpoint, BAT
output via the logical list assignment, and CRT list output. It does not add a
serial driver or pretend TTY/PTR/PTP/LPT/user devices exist. Unavailable input
returns EOF, unavailable output does nothing, unavailable status is not ready.
Those fallback behaviors model the current scaffold and are not yet a final
platform device policy. Console input retains seven-bit normalization.

The assembled compact router passes 1,792 checks over all 256 IOBYTE values:
console status/input/output, reader, punch, list and list status. Physical
endpoints are stubbed, so these checks establish dispatch, unchanged IOBYTE,
output-character preservation and input normalization, not hardware behavior.
The cpmsim prototype has been size-measured only.

Re-running `tools/audit_monitor_memory.py` against the current baseline gives
101 BDOS bytes and 18 disk bytes of candidate savings, unchanged from the
previous review. BDOS is now 3,553 bytes; the combined candidate is 3,452.
The earlier repack calculation allows 122 additional BIOS bytes, subject to
qualification. Compact routing (56) plus the monitor hook prototype (64) is
120 bytes: a provisional two-byte margin. These independently measured
prototypes have **not** yet been integrated or jointly qualified. Table-based
Model 4 routing would exceed that budget even before monitor hooks.

## Actual cpmsim endpoints

The local z80pack primary source, `cpmsim/srcsim/simio.c`, provides console
status/data on ports 0/1, printer status/data on 2/3, and auxiliary status/data
on 4/5. Stock `cpmsim/srccpm2/bios.asm` uses these data ports for console, list,
punch and reader but does not supply a complete IOBYTE router.

Printer output is host-file backed and strips CR. Auxiliary input expands LF
to CR/LF. Missing input files can stop the emulator rather than returning a
recoverable CP/M error. Port 4 is an auxiliary EOF indicator in the pipe build,
not a conventional character-ready bit. Therefore BAT console status must not
blindly use port 4 as a ready test. Those host behaviors also need explicit
qualification before PIP physical aliases are enabled.

## Implementation boundary and next checks

A small platform-specific BIOS router looks feasible without changing public
BIOS vectors or introducing a PIP-specific routing ABI. Both platforms retain
the standard IOBYTE bit assignments. Their supported physical endpoints may
legitimately differ; unsupported devices must be documented and must not be
silently redirected to an unrelated backend.

Before production adoption:

- Settle BAT input/status and unavailable-device behavior against the CP/M
  contract and actual host media behavior.
- Qualify the memory-saving candidates and repack while preserving unloaded
  53K TPA, public entry contracts and native/cross build parity.
- Integrate routing with the reserved monitor hooks and measure the combined
  image; do not spend the monitor budget on routing alone.
- Qualify cold IOBYTE 95h and warm preservation, all supported STAT assignments,
  logical-device PIP operations, and physical aliases on real emulator media.
- Enable only aliases backed by a qualified platform endpoint. Keep unavailable
  aliases rejected before destination mutation.

This audit closes the initial sizing question, not the 1.0 IOBYTE requirement
or PIP's final release qualification.
