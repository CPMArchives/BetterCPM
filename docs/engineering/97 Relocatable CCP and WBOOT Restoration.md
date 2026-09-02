# Engineering Specification 97: Relocatable CCP and WBOOT Restoration

Date: 2026-09-02

## Result

BetterCP/M now produces a relocatable command module and restores it from the
TRS-80 Model 4 system tracks during WBOOT. The no-extension configuration may
therefore expose the former CCP allocation to transient programs and publish
`C000h` as its TPA ceiling.

## Command-module format version 1

`build/ccp/ccp.rlm` consists of a 512-byte header/relocation sector followed
by the unpadded CCP payload. The header begins:

| Offset | Size | Meaning |
|---:|---:|---|
| `00h` | 4 | signature `BCM1` |
| `04h` | 1 | format version, 1 |
| `05h` | 1 | header-sector count, 1 |
| `06h` | 2 | link base |
| `08h` | 2 | payload size |
| `0Ah` | 2 | page-rounded allocation size |
| `0Ch` | 2 | entry offset |
| `0Eh` | 2 | relocation count |
| `10h` | 2 each | little-endian relocation offsets |

The current 1,116-byte CCP has 87 relocation records and a `0500h` allocation.
The complete module is 1,628 bytes and occupies four 512-byte physical sectors.

The build derives relocations by assembling the same source at `BB00h` and
`BC01h`, identifying address words whose difference equals the origin delta,
and proving that applying the generated records reproduces the entire
alternate image byte for byte. The canonical payload remains independently
assembled under native CP/M and must match the cross build exactly.

## System-track placement

Stage zero and stage one occupy physical indices 0 and 1. The 28-sector
resident image occupies indices 2 through 29. The command module occupies
indices 30 through 33, corresponding to cylinder 1, side 1, sectors 1, 3, 5,
and 7 in the MM interleave. The CP/M filesystem still begins at index 40.

## WBOOT path

The public BIOS WBOOT vector transfers to a fixed 294-byte Model 4 command
reloader at `E900h`. A BetterCP/M-private physical-read vector immediately
after the public BIOS jump table reads the system disk without exposing
controller details to the portable gateway.

The reloader:

1. reads and validates the module header;
2. checks the declared allocation and payload bounds;
3. reads the payload into the descriptor-selected CCP base;
4. rereads the relocation directory;
5. applies the difference between the selected base and link base; and
6. transfers to the portable WBOOT gateway, which reconstructs public state
   and enters the CCP through `ECB_CCPBASE`.

Failure enters a closed stop loop rather than executing a partial command
image. A later recovery increment should report the failure and try a known
recovery image.

## TPA reclamation

The initial descriptor still reports `BB00h` as the active CCP base and
`0500h` as its allocation, but now reports `C000h` as the exclusive transient
ceiling. Thus the reloadable CCP may be overwritten. This is safe only because
the current configuration has no CPXs. A configuration with CPXs must retain
a protected lower ceiling until its WBOOT image includes and reconstructs the
complete CPX chain.

## Verification

- Focused reloader execution restores the canonical CCP at `BB00h` after the
  destination has been overwritten.
- The same module is restored at `B900h`, and all relocation records produce
  the independently assembled alternate image.
- Native ZSM4/LINK and cross builds produce byte-identical CCP payloads,
  BIOS, boot stages, diagnostics, and the 294-byte reloader.
- All BIOS, directory, BDOS, CCP, and resident-system regressions pass.
- The generated DMK boots under `trs80gp`.
- A physical `WARM` command performs disk-backed WBOOT; the reconstructed CCP
  then executes `VER` and reports `BetterCP/M 0.1`.

## Next extension step

The module format and reconstruction transaction must next encompass ordered
CPX modules. RSX reconstruction remains separate because RSXs persist above
the command environment during ordinary WBOOT.
