# Engineering Specification 192: FDB Runtime Transition Closure

## Result

CONFIG and DUP now use the compiled `DISK.FDB` catalogue throughout their
runtime paths. CONFIG conditionally omits the old text loader, parser, index,
and assembled built-in catalogue from its shared source. DUP loads the same
validated FDB and uses its normalized-binding lookup when naming the selected
format. The TRS-80 and z80pack release builders therefore install `DISK.FDB`
without the transitional `DISK.FDF` runtime file.

CONFIG's embedded SYSGEN temporarily borrows the catalogue workspace. Its exit
path now reloads `DISK.FDB`; it no longer overwrites the binary catalogue with
legacy text before returning to CONFIG. The standalone SYSGEN utility has no
catalogue dependency.

CONFIG is 8,716 bytes after dead-reader removal, 2,838 bytes smaller than the
preceding native-selection build and 6,900 bytes below its 15,616-byte
transient ceiling. DUP is 7,645 bytes. Resident memory and the 53 KiB TPA floor
are unchanged.

## Focused evidence

- The disk-utility build assembles CONFIG, DUP, and SYSGEN without errors.
- The native FDB reader continues to reject the bounded framing, CRC, object,
  extension, and semantic mutations and constructs all 107 admitted bindings
  byte-for-byte.
- A direct cpmsim session enters CONFIG's embedded SYSGEN path, declines the
  write, returns to the format menu, and displays the canonical FDB first page.
- In the same session, DUP enters FORMAT for B: and names its current
  `California Computer Systems` binding through the FDB before any write.
- The changed image boots normally under cpmsim. The Expect wrapper currently
  stalls before its `Booting...` match for both the new image and the previously
  passing fixture, so that host-harness condition is not classified as a
  BetterCP/M failure.
- The available trs80gp executable still aborts in macOS application
  registration before emulation, as recorded in Engineering Specification 191;
  no TRS-80 result can be inferred from that host failure.

The historical text catalogues remain preserved as source and conversion
evidence. They are no longer part of the BetterCP/M runtime release contract.
