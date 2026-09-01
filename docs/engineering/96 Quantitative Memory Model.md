# Engineering Specification 96: Quantitative Memory Model

Date: 2026-09-02

## Purpose

This increment replaces the protected four-kilobyte CCP/extension bring-up
region with the first quantitative BetterCP/M memory model. Active component
addresses are configuration results. Stable code consults a descriptor rather
than embedding the current CCP address.

## Fixed 64K resident map

The current fixed resident components remain:

| Address | Owner |
|---|---|
| `C000h..C0FFh` | system gateway and Extension Control Block |
| `C100h..D5FFh` | BDOS core, state, descriptors, and workspaces |
| `D600h..E8D5h` | directory and filesystem services |
| `ED00h..EEFFh` | Model 4 physical-sector buffer |
| `EF00h..F2E3h` | BIOS |
| `F300h..F37Fh` | BIOS directory buffer |

Hardware-mapped memory above this range remains platform-owned.

The movable region grows downward from `C000h` in the order RSXs, CPXs, and
CCP. Every allocation is rounded to a 256-byte page. The resulting CCP base is
also the exclusive transient-program ceiling until true WBOOT reload permits
the command image to be reclaimed temporarily.

## Extension Control Block version 1

The fixed descriptor begins at `C080h`:

| Offset | Address | Size | Meaning |
|---:|---:|---:|---|
| `00h` | `C080h` | 2 | signature `BM` |
| `02h` | `C082h` | 1 | descriptor version, currently 1 |
| `03h` | `C083h` | 1 | flags |
| `04h` | `C084h` | 2 | active RSX-chain head, or zero |
| `06h` | `C086h` | 2 | active CPX-chain head, or zero |
| `08h` | `C088h` | 2 | low address of the RSX region |
| `0Ah` | `C08Ah` | 2 | low address of the CPX region |
| `0Ch` | `C08Ch` | 2 | active CCP base |
| `0Eh` | `C08Eh` | 2 | page-rounded CCP size |
| `10h` | `C090h` | 2 | exclusive TPA ceiling |
| `12h` | `C092h` | 2 | configuration generation |

All words are little-endian. Version-aware code may use this descriptor;
other bytes through `C0FFh` remain reserved.

## Default calculation

The current CCP binary is 1,116 bytes. Rounding upward to five 256-byte pages
gives `0500h` bytes. With empty RSX and CPX chains:

```text
C000h - 0000h RSXs = C000h
C000h - 0000h CPXs = C000h
C000h - 0500h CCP  = BB00h
```

The active layout is therefore:

```text
BB00h..BFFFh  CCP allocation
0100h..BAFFh  TPA
```

Only 1,116 bytes of the CCP allocation contain the current image; the
remaining page padding is reserved to that image. A size change that crosses
a page boundary changes the calculated base.

## Stable consumers

The system WBOOT gateway reads `ECB_CCPBASE` and transfers control indirectly.
The CCP reads `ECB_CPXHEAD` to begin CPX dispatch. The transient loader reads
`ECB_TPATOP` and refuses a record whose next load address would reach or cross
the active ceiling.

These consumers no longer encode the former `B000h` bring-up limit or a direct
jump to the default CCP address.

## Boot carrier

Moving the no-extension image base from `B000h` to `BB00h` reduces the sparse
TRS-80 resident image to 14,308 bytes. Stage one loads 28 physical sectors,
all below the MM 790K filesystem offset. The carrier format is unchanged.

## Verification

- The descriptor contents and indirect WBOOT path are exercised by the
  resident-system test.
- The CPX test obtains its chain head through `C086h`.
- CCP and gateway native CP/M builds are byte-identical to cross builds.
- All 39 BDOS functions and the existing BIOS and directory regressions pass.
- The generated DMK boots under `trs80gp`, runs resident `DIR`, and loads
  `HELLO.COM` with its command tail.

## Deferred work

The active descriptor currently describes the no-extension layout assembled
into the system image. The following increments remain:

1. Define and emit relocatable CCP records.
2. Load and relocate the CCP at a calculated address.
3. Reconstruct CPXs and the CCP during WBOOT.
4. Define the RSX dispatcher and relocatable RSX format.
5. Add transactional configuration calculation, validation, and publication.
6. Permit temporary transient use of reloadable command memory when safe.
