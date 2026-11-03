# Changelog

## 0.1.0-dev2 — 2026-08-31

- Build an allocation-block ownership map from active directory entries.
- Show allocation block and owning user/file for DATA sectors.
- Distinguish unclaimed blocks as `FREE` and competing claims as `CONFLICT`.
- Associate blocks from every extent with the same displayed user and filename;
  flag any repeated allocation-list claim as a conflict.
- Compact the status line to `Trk`, `Log`, `Xlt`, `Reg`, `Blk`, and `Own`.

## 0.1.0-dev1 — 2026-08-31

- Add read-only 128-byte logical-sector display in hexadecimal and ASCII.
- Show track, logical sector, translated BIOS sector, and disk region.
- Add next, previous, directory, and quit navigation commands.
- Add direct SYSTEM and DATA region navigation; calculate the DATA boundary
  from the directory blocks reserved by AL0/AL1.
- Start at track zero and use SYSTEM consistently for reserved system tracks.
- Add optional drive selection and common help, information, and version
  commands.
