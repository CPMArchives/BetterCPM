# Engineering Specification 57: Resident DIR

## Milestone

The BetterCP/M CCP now provides a resident `DIR` command. On the generated
physical system disk it lists `HELLO.COM`, returns to the prompt, and leaves the
transient loader fully operational.

## Architectural boundary

`DIR` uses the public CP/M BDOS interface rather than private directory-service
entry points. It constructs an all-wildcard FCB, selects DMA address `0080h`,
and iterates BDOS Search First and Search Next (Functions 17 and 18). The result
slot selects one of the four conventional 32-byte entries returned in the DMA
record.

This makes the resident command a useful integration test of the same API seen
by transient software. It also avoids coupling the CCP to BetterCP/M's internal
directory implementation.

Only canonical first extents are displayed: entries whose `EX` or `S2` values
identify later extents are skipped. Attribute bits are masked while printing,
space padding is suppressed, and the conventional dot is inserted only when an
extension is present. An empty result prints `NO FILE`.

## Resident placement

The preceding CCP left only 139 bytes free, which was insufficient for a useful
resident command. Patch 2026-09-01 therefore moved directory services from
`D800h` to `D700h` and the CCP from `EA40h` to `E940h`. This consumes existing
gaps without moving the BIOS at `EF00h`, reducing the TPA, or changing the
page-zero BDOS ABI. The CCP occupies 818 of its 960 available bytes.

## Verification

All 39 defined CP/M 2.2 BDOS functions and the existing BIOS and directory
regressions continue to pass. Native CP/M ZSM4 builds remain byte-identical to
the cross builds. The physical `trs80gp` test now types `DIR`, requires
`HELLO.COM`, then types `HELLO`, requires its message, and verifies return to the
`A>` prompt.

The initial implementation scans the complete directory through BDOS and real
disk I/O. This is intentionally correct before it is optimized; the automated
test allows the physical scan to complete before entering the next command.

## Next increment

Implemented by [Engineering Specification 58](58%20Transient%20Command%20Tail.md).
