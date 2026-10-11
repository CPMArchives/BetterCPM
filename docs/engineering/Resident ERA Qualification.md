# Resident ERA shared-selection qualification

RCP Build 005 implements the resident boundary in [ERA Specification](ERA%20Specification.md).
The full ERA.COM workflow remains a separate task.

## Implementation

- Full shared DU/filespec/attribute selection; parse and supported-drive checks
  finish before deletion.
- Fresh lexical rescans between exact-file erases avoid invalidating BDOS search
  state. All physical extents are checked independently for RO/SYS protection.
- RO and SYS files are always skipped, including explicit protected predicates.
- Bare ERA is harmless; all-wildcard selection retains one ALL (Y/N)? prompt.
- Caller DU is restored; `/VER` reports Resident, RCP Build 005.
- Minimal failures report Erase failed and continue. No transient overrides,
  destructive erase, paging, recovery menu or rich accounting is added.

The shared caller-DU capture and domain check also serve existing resident
commands. Transient expansion retains its previous source path. No BDOS, CPX
format, descriptor or protected-state changes are required. Payload: 6,862 bytes;
allocation: 6,912 bytes; relocation entries: 744 (the existing header limit).

## Evidence

- `tools/test_rcp_shared_selector.py`: production payload relocated at 4000H,
  8101H and A000H; full selector acceptance, malformed-file rejection, captured
  DU/input preservation and all sixteen drive-domain cases.
- `tools/test_resident_era.py`, cpmsim: no ERA.COM or DIR.COM; exact and compound
  selection, multi-extent deletion in users 0 and 2, unconditional RO/SYS skips,
  predicates, invalid operands/drives/options without mutation, bare ERA,
  `/VER`, warm reconstruction, and all-files N/Y protection behavior.
- The same harness, Model 4: SUBMIT executes resident ERA on disposable physical
  DMK media. Final directory entries independently confirm both user copies of
  the multi-extent source and the selected ordinary file are gone. RO/SYS flags,
  protected contents and the safety file remain intact. The executed carrier
  bytes are reconstructed from the final disk and compared with the build.
  Captures confirm the resident version and protected-file listing.
- `tools/test_rcp_selector_lifecycle.py`, cpmsim: unload/reload, WBOOT, resident
  selection and compound ERA deletion with DIR.COM absent.
- Native ZSM4/LINK assembly reproduces all 6,862 host-assembled payload bytes.

Local evidence directories:
`/private/tmp/era-shared-final`, `/private/tmp/era-cpmsim-proof`,
`/private/tmp/era-model4-offline`, `/private/tmp/era-lifecycle-z80`.
The Model 4 harness can recheck completed captures and media using
`--verify-existing`; this does not rerun commands or modify the disk.
