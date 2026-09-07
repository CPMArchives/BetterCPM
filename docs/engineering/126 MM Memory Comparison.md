# Montezuma Micro / BetterCP/M resident memory comparison

Measured 2026-09-06 against the current uncommitted compact BetterCP/M build.
This is a size comparison, not a declaration of equal functionality or a
completed BIOS validation.

## Findings

MM's BIOS is larger than our current BIOS grouping. Our BDOS is already smaller
than MM's. The current TPA shortfall is primarily additional resident services
and the test-platform RAM ceiling, rather than an oversized standard BDOS.

## Reference and verification

Downloaded Jeff Post's April 2005 reconstructed MM CP/M 2.32 source archive:
https://oldcpusrus.xepb.org/mmcpm232.zip, linked by
https://oldcpusrus.xepb.org/bb.html.

Archive SHA-256:
`e6a76f496240c22b92090ec1721b28a345ac815f54eecdfd36a88579177f50db`.

The README identifies this as a reconstruction by disassembly, not original
vendor source. This corrects the earlier description of the local BIOS file
as simply MM source. The archive supplies the previously missing system.inc,
plus CCP, BDOS, BIOS, boot, and related utility sources.

The archive defaults to MEMORY=63 and an extended 80-track format. For size
measurement, a temporary copy sets MEMORY=64 and mechanically renames long
symbols to accommodate the host assembler's eight-character symbol limit.
No instructions or allocation directives were changed. All three components
assemble without errors: CCP 2,048; BDOS 3,584; BIOS 3,840 bytes. These match
the explicit allocations in system.inc.

Separately, booted a disposable copy of the MM BIOS 2.32 distribution disk in
trs80gp and captured RAM. Page zero points to WBOOT EA03h and BDOS DC06h,
confirming BIOS EA00h and BDOS DC00h for the running 64K system. CCP is D400h
according to the matching system.inc layout. The emulator enabled MM's RAM
drive; the figures here concern the main 64K address space, not RAM-disk storage.

The reconstructed binaries are not byte-identical to the running snapshot:
configuration and mutable state differ. The comparison establishes region
sizes and addresses, not binary equivalence to the distribution disk.

Reference archive, extracted source, reproduction script, and both RAM captures
are under /Users/nathanael/CPM/montezuma-micro. No MM implementation is copied
into BetterCP/M.

## Complete accounting above the transient boundary

All sizes are bytes; KiB means 1,024 bytes.

| Category | MM 64K system | BetterCP/M current |
| --- | ---: | ---: |
| BDOS, including its internal state/stack | 3,584 | 3,373 |
| BIOS code, disk configuration, drive tables and internal state | 3,840 | 2,718 |
| Directory buffer and maximum physical-sector buffer | 1,152 | 1,152 |
| Additional fixed resident support components | included in above or absent | 2,790 |
| Remaining reservation, stack, history and padding | 640 | 722 |
| Upper address space excluded by current platform layout | 0 | 3,072 |
| Total above the transient boundary | 9,216 | 13,827 |
| Transient space above 0100h | 56,064 (54.750 KiB) | 51,453 (50.247 KiB) |

The total difference is 4,611 bytes. MM's conservative transient boundary is
DC00h, the start of its BDOS region, excluding the six-byte prefix preceding
its DC06h entry. BetterCP/M's actual page-zero BDOS target is C9FDh, matching
its published gateway boundary.

MM's 640-byte remainder is FD80h..FFFFh after its directory buffer at F900h
and 1,024-byte disk buffer at F980h. It includes stack/headroom and possible
extension space; it is not asserted to be 640 bytes of unused RAM. MM sets
SP=0000h for some BIOS work and references an optional EXBIOS patch at FE80h.

BetterCP/M's 722 bytes are history 512, external system/CCP stack 128,
RSX reconstruction state 41, TPA gateway 3, and alignment gaps 38. Its BDOS,
extension, and gateway internal stacks are already counted in their binaries.

### BetterCP/M component breakdown

| BIOS grouping | Bytes |
| --- | ---: |
| BIOS compatibility entries, logical-record handling, console adapter | 574 |
| Shared physical disk engine | 1,117 |
| Configuration validation | 547 |
| Four logical-drive records and shared ALV/CSV workspace | 480 |
| Total | 2,718 |

This is 1,122 bytes smaller than MM's 3,840-byte BIOS region. It is not feature
parity: MM includes richer console/device handling, RAM-disk support, and disk
behaviors not all reproduced here. Shared allocation workspace still needs
full regression coverage.

| Additional fixed support | Bytes |
| --- | ---: |
| System gateway and descriptors | 248 |
| Extension services and their private stack | 488 |
| RSX loader | 875 |
| Filename stream reader | 216 |
| CPX control | 152 |
| Command-environment reloader | 811 |
| Total | 2,790 |

The current BetterCP/M CCP allocates 2,816 bytes and BASIC.CPX 2,560 bytes
below the fixed gateway. The runtime snapshot places them at B4FDh and BFFDh.
They are reconstructible, overwriteable command-environment allocations,
not additional deductions from the advertised maximum transient boundary.
MM likewise reloads its CCP on warm boot. These bytes must not be double-counted
as permanent TPA loss. Installed resident RSXs can lower BetterCP/M's boundary;
none were active in this measured default boot.

## Platform distinction

MM runs in its full-RAM map and temporarily switches maps for keyboard/display
access (see kbscan/kbscandone and conoutcrt in bios.asm). It therefore uses RAM
above F400h. Our corrected current test adapter/layout stops at F400h, excluding
3,072 bytes. This explains part of the observed difference; it is not permission
to restore the rejected mapping optimization to portable system code.

For arithmetic only, keeping the same current footprint in a fully addressable
64K target would add 3,072 bytes of TPA, giving 54,525 bytes (53.247 KiB).
That is not a tested configuration or a portable implementation result.

## Implications for further work

- BDOS already saves 211 bytes relative to MM. Restoring the historical 3,201-
  byte BDOS checkpoint would save another 172, not multiple KiB.
- The present test layout needs 2,819 additional bytes to reach 53 KiB TPA,
  or 3,843 to reach 54 KiB.
- Audit the 2,790-byte support layer for common loaders, repeated metadata
  processing, unnecessary permanent residency, and reusable working state.
  This is an investigation target, not 2,790 bytes proven removable.
- Preserve required services and test reconstruction, drive switching, and
  transient overwrite behavior while reducing the resident footprint.
- Keep platform RAM availability separate from common-system byte cost when
  judging portability and memory targets.

No BIOS or BDOS implementation was changed during this comparison.


Follow-up: [53 KiB consolidation and validation](127%2053K%20Memory%20Consolidation.md) records the completed September 7 layout.
