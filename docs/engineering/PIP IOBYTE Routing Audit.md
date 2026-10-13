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
| Model 4, compact dispatch plus monitor hooks | 636 | 756 | 120 | 638 |
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
120 bytes: a provisional two-byte margin. The combined routing/monitor prototype now assembles to 756 bytes, confirming
the 120-byte total. Its dispatch is qualified as described below; production
repacking and provider lifecycle integration remain pending. Table-based
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

## Combined prototype qualification, 14 October 2026

The audit builder now emits `trs80m4/combined`, composing compact IOBYTE routing
with the previously specified multiplex monitor hooks. CRT console paths and
CRT list output reach monitor dispatch; the raw backend entry bypasses both
IOBYTE and the provider, preventing recursive dispatch. Cold initialization
selects the baseline backend. This does not implement RSX publication/rebinding.

The dispatch campaign executes 1,792 cases each for the compact router, combined
baseline and combined active test provider: **5,376 cases** total. It also checks
raw output/status/input while a provider is active. Endpoints remain stubbed;
real keyboard/video behavior and provider relocation are not covered.

The current 3,452-byte BDOS and 942-byte disk saving candidates pass the existing
isolated behavioral campaigns: public BIOS/BDOS contracts, grouped extents (480
cases), error recovery (24 combinations), retries (112 cases), differential
geometry (8,400 cases), and transfer length setup. Observed private BDOS stack
high-water is 28 bytes within its retained 40-byte allocation. These tests do
not establish WD controller timing or a final packed image.

`tools/test_native_memory_candidates.py` stages private cpmsim disks to compare
the candidate BDOS, disk service and combined Model 4 BIOS against native
ZSM4/LINK output. Audit sources and binaries remain separate from production.

Native ZSM4/LINK qualification passed for all three isolated candidates:

| Candidate | Bytes | Native/cross result |
| --- | ---: | --- |
| Combined BDOS savings | 3,452 | Identical |
| Combined disk-service savings | 942 | Identical |
| Model 4 compact routing plus monitor hooks | 756 | Identical |

The private native-build harness sends a harmless initial carriage return to
wake the emulator terminal before waiting for its prompt, and preserves a final
CR/LF before the source-file Ctrl-Z terminator. Native output is compared only
against the isolated audit images; it does not replace production artifacts.

These results qualify the source transformations and combined dispatch well
enough to proceed to production repacking. They do not close the remaining BAT
status policy, monitor-provider lifecycle, packed boot/real-media qualification,
or PIP physical-alias availability decisions.
