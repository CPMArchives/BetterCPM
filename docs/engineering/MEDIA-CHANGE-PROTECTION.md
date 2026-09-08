# Media-change protection — 8 September 2026

The BDOS now checks directory-record checksums and marks a logged disk read-only when a checked record changes. This implements the traditional protection response; it does not automatically relog replacement media.

Each of the four logical drives owns a separate 32-byte CSV, accessed through its DPH. The existing format validator limits CKS to 32; CKS=0 disables checking. Initial login seeds checksums. Successful directory writes refresh their checksums. A clean directory cache is discarded between public BDOS calls, allowing replacement media to be observed even without selecting another drive. Dirty records retain their normal synchronous flush path, and that path rechecks read-only state before writing.

A checksum mismatch leaves the drive protected until explicit reset. The mechanism detects changes in the DPB's checked directory region; it is not a hardware disk-change sensor or a guarantee that every possible replacement differs in checksum.

## RAM allocation

TPA remains 54,273 bytes. The fixed history reservation is reduced from 512 to 256 bytes (246 bytes of command text after its header). The system gateway and BDOS move down into the released space; BIOS/table addresses also move within the protected image. The new BDOS is 3,486 bytes in a 3,550-byte allocation, leaving 64 bytes of headroom. All build-time overlap and image-size checks remain active.

The logical-drive table allocation is now 576 bytes: four 80-byte DPH/binding records, a shared 128-byte ALV, and four 32-byte CSVs. Another 24 bytes describe the four physical drives. The CSVs are runtime state, not saved configuration.

For the intended ROMable architecture, live mutable definitions/mappings and disk state should ultimately reside in the fixed persistent RAM segment. ROM should contain code and default definitions copied into live RAM at cold boot. Stable DPH pointers separate table location from BIOS code. This preferred reorganization is recorded in TODO; the present repair retains the existing BIOS table area.

## Validation

- Real emulator media replacement: original and replacement directories read successfully; replacement marked read-only.
- A subsequent Make produces Disk R/O and warm restart without resuming the write caller.
- Function 37 clears protection; the replacement disk then accepts a new file and Close.
- The same reset/recovery case passes without an intervening drive selection.
- All 17 focused BIOS vector checks pass, including distinct CSVs and shared ALV.
- CCP parsing/history tests pass. Full TPA overwrite, CPX reconstruction and loaded-RSX survival pass.
- The legacy mutation unit fixture owns DIRBUF directly, rather than modeling backing media. Its cache-invalidation hook is explicitly bypassed and CKS disabled for those narrow mutation tests; the unmodified real-image tests above qualify media handling. This is documented in the fixture itself.

Evidence is retained under `build/compatibility/media-20260908-064616` (write rejection), `media-20260908-064810` (reset), and `media-20260908-064956` (same-drive reset). The initial reset probe incorrectly reread its option from the overwritten command-tail/DMA area; the corrected probe saves the option before disk calls. That invalid trial is excluded.

The new image is `build/compatibility/BetterCPM-Media-Protection.dmk`, SHA-256 `964836cdb772b728b949d774cbc56f33ad45b3a77eee5d4013246839dfb570c0`. Earlier qualification images and their historical failure records remain unchanged. This supersedes the earlier 0143 failure, not the other outstanding recovery failures or the COM-loader size limitation.

Automatic relogging remains deferred. Its design should consult ZSDOS/ZDDOS and available ZRDOS sources and define treatment of open FCBs, dirty buffers, and an interrupted operation before adopting a replacement disk.

The real-image regression finished with 84 FILETEST rows, 72 DIRTEST rows, and
20 DISKTEST rows, with no failed rows. These totals include observations and
not-run classifications; they are not all counts of REQUIRED passes. The
first DISKTEST invocation lacked its scratch-drive response and is excluded;
the second invocation supplied D and completed. See the adjacent evidence
archive and manifest for the retained records.
