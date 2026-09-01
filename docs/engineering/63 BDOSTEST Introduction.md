# Engineering Specification 63: BDOSTEST Introduction

## Milestone

BetterCP/M's generated conformance disk now includes `BDOSTEST.COM` after the
complete `ENTRYTST` pass. A reusable Model 4 command runner derives hexadecimal
keyboard masks from the physical matrix, boots a selected DMK, types one
command, and captures the bounded 80 by 24 display.

`BDOSTEST /VER` reports version `1.0.0-dev14` and returns normally to the CCP.
The first complete `/SAFE` run reports 35 passes, 21 failures, zero errors, and
zero observations.

## Baseline classification

Eighteen failures require a configured B: drive and the controlled
`BDSA.TMP`/`BDSB.TMP` fixtures. BetterCP/M currently exposes only A:, so these
form the next multi-drive platform milestone rather than eighteen independent
BDOS defects.

The remaining three cases, 0042, 0525, and 0529, share one portable defect:
selectors above the CP/M 2.2 Function 40 ceiling returned `FFh`. BetterCP/M now
returns the conventional zero result with the normal A/L and B/H aliases.

## Verification

The unit boundary invokes selector 41 and requires zero in A, L, B, and H.
Native CP/M and cross builds must remain byte-identical. Physical reruns of the
three affected BDOSTEST selectors provide external verification:

- 0042 passes: Function 41 returned zero;
- 0525 passes: Function 40 is valid and Function 41 unsupported;
- 0529 passes: an unsupported call returned zero.

Each selector reports one pass, zero failures, zero errors, and zero
observations. The remaining baseline work is the configured B: drive and its
controlled fixtures.
