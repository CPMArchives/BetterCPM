# Engineering Specification 98: Calculated Command Environment

Date: 2026-09-02

## Purpose

This increment resolves the temporary CCP-space problem without removing its
current resident commands. It removes the arbitrary five-page build limit,
separates the CCP from the stage-one resident image, establishes the first
movable CP/M compatibility gateway, and makes WBOOT reconstruct an ordered
CPX set before loading the CCP.

## Current no-RSX layout

The fixed BetterCP/M system gateway remains at `C000h`; the fixed BDOS core
entry remains at `C100h`; and the Extension Control Block remains at `C080h`.
With no installed RSXs, the reloader materializes a three-byte `JP C100h`
compatibility gateway at `BFFDh..BFFFh`. Page zero contains `JP BFFDh`, so
`0006h..0007h` advertise the true exclusive transient ceiling.

The CCP builder rounds the actual linked size upward to a 256-byte allocation.
It no longer rejects growth beyond the former `0500h` slot. The current 1,116
bytes still round to `0500h`, but are calculated below the dynamic gateway:

```text
BFFDh - 0500h = BAFDh
```

The non-page-aligned result is intentional: the gateway itself is exactly
three protected bytes. The relocatable command module permits any calculated
base that fits above page zero.

## Cold and warm reconstruction

The CCP is no longer embedded in the stage-one resident image. Both BIOS BOOT
and WBOOT enter the fixed Model 4 command-environment reloader at `E900h`.
The resident image now begins at `C000h`; stage one loads only the fixed core.

The reloader:

1. begins at the current dynamic-gateway boundary in `ECB_TPATOP`;
2. clears the runtime CPX head;
3. reads the persistent ordered reconstruction table at `C094h`;
4. loads each `BCX1` module downward, applies its relocation records, and
   links its four-byte CPX header into the active chain;
5. loads the `BCM1` CCP module below the completed CPX region;
6. publishes the calculated CCP base and allocation in the ECB;
7. advances the configuration generation; and
8. enters portable WBOOT, which rebuilds page zero and transfers to the CCP.

The current saved and active CPX profile is empty. A focused test supplies a
synthetic one-module profile and verifies that its CPX is restored, relocated,
and linked before the CCP. This exercises the non-empty path without making a
temporary demonstration command part of the production system.

## Persistent CPX table and carrier slots

`C094h` contains the active CPX count and `C096h` begins eight eight-byte
records. Byte zero of each current record selects the first raw module slot;
the remaining bytes are reserved for module identity, policy, and integrity
fields. The loader accepts up to eight ordered entries.

The two MM system tracks provide ten 512-byte command-module slots between
the fixed resident image and the filesystem. Slots zero through three hold
the current CCP module. CPX modules begin at slot four. Bounds checks prevent
module reads from reaching the filesystem; CONFIG must later validate source
overlap and populate the reserved table fields transactionally.

## Compatibility and verification

- The existing CCP retains its resident commands, including `DIR`.
- The focused CCP parser, resident-command, and CPX-dispatch tests pass.
- Empty and one-CPX reconstruction profiles pass in the Z80 execution test.
- All 39 BDOS calls, 17 BIOS vectors, directory behavior, `DIR`, command-tail
  loading, and `HELLO.COM` pass after the layout change.
- The generated DMK cold-boots through disk-backed command reconstruction.
- CCP, gateway, BIOS, boot stages, and the 511-byte reloader are byte-identical
  between native CP/M ZSM4/LINK and cross builds.

## Next boundary

The next command-memory increment should define the production CPX module
metadata fields and build the first real `BASIC.CPX`. Until that module is
verified, resident commands remain in the CCP.
