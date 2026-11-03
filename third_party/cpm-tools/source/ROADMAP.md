# CP/M Tools Roadmap

This document records possible future development for the suite. It is a
direction of travel, not a promise that every item will be implemented. The
current behavior and limitations of released development versions are
documented in `docs/TOOLS.DOC`; completed work is recorded in each utility's
`CHANGELOG.md`.

The suite will remain a collection of small, independently useful CP/M-native
programs. New functions should be added to an existing utility when they fit
its purpose, rather than creating overlapping tools.

## SYSINFO

Current release: `1.0.0-dev8`.

Near term:

- Exercise the existing reports on a wider variety of CP/M 2.2 systems and
  document legitimate variations.
- Stabilize the command interface and prepare the first non-development
  release.
- Keep broad system summaries in SYSINFO while moving genuinely deep analysis
  to a specialized utility only when there is enough useful scope.

Possible later work:

- Add newly justified structural checks discovered during compatibility
  testing.
- Share proven formatting, parsing, BIOS, and DPB routines with the other
  native tools where this does not make them harder to build independently.

## DISKINFO

Current release: `0.1.0-dev4`.

Near term:

- Add a compact `/MAP` report showing directory, active-data, recoverable
  deleted-data, overwritten-deleted-data, and free allocation blocks. The
  deleted categories must be labeled as directory evidence rather than a
  guarantee that old contents remain recoverable.
- Report more detail about the logical-to-physical sector translation table.
- Expand the explanation of extent geometry and allocation-number width.
- Test unusual but valid DPBs, including small disks and nonstandard directory
  reservations.

Possible later work:

- Provide a compact comparison of two drives' public disk geometry.
- Add other derived values when they are useful to operators and can be
  calculated reliably from documented CP/M structures.

## DPBCHK

Current release: `0.1.0-dev2`.

Near term:

- Check the exact relationship between AL0/AL1, DRM, and the directory blocks
  which must be reserved.
- Strengthen CKS validation while allowing documented fixed-disk practice.
- Add plausibility checks for SPT, OFF, and sector-translation structures.
- Distinguish a definite contradiction from an unusual but usable format.

Possible later work:

- Compare parameters across logged drives and highlight suspicious differences.
- Feed clearly defined DPB failures into FSCK and DISKEDIT without merging the
  three programs.

## FSCK

Current release: `0.1.0-dev1`.

Near term:

- Validate filename and filetype bytes, attributes, extent numbers, and record
  counts more completely.
- Reconstruct each file's extent sequence and report gaps, overlaps, and
  inconsistent allocation lists.
- Reconcile directory ownership with the BDOS allocation vector.
- Improve verbose reports so every finding identifies the raw directory entry,
  user area, filename, extent, and allocation block involved.

Possible later work:

- Detect orphaned or unexpectedly allocated blocks and other recoverable
  directory anomalies.
- Produce a machine-readable or redirected report if CP/M console conventions
  permit it cleanly.
- Consider repair functions only after the read-only checker is mature. Any
  repair mode must be explicit, conservative, documented, and preceded by a
  practical backup path.

## DISKEDIT

Current release: `0.1.0-dev2`.

Dev2 starts at track zero so system areas remain accessible. `S`, `D`, and `T`
jump to the first SYSTEM, DIRECTORY, and DATA sectors. DATA-only formats have
no SYSTEM region and report that fact without moving the current position.
DATA sectors show their allocation block and the owning user/file, FREE, or
CONFLICT, based on active directory entries.

Near term:

- Jump to a specified track and logical sector.
- Jump to an allocation block or raw directory entry.
- Decode a directory entry alongside its bytes.
- Follow a file's extents and allocation blocks.
- Search for hexadecimal or ASCII byte patterns.

Possible later work:

- Move directly between a directory entry and its data blocks.
- Compare sector contents and restore the in-memory copy of the current sector.
- Add a carefully controlled editing mode. Read-only operation must remain the
  default; writes must require explicit confirmation and a clear recovery
  procedure.

## COMINFO

Current release: `0.1.0-dev2`.

Dev2 reports logical CP/M file length and load range, direct CALL 0005H,
JMP 0000H and other page-zero address patterns, and heuristic Z80 prefix
bytes. It recognizes immediate MVI C BDOS function selection, symbolic CP/M
2.2 function names, per-function counts, and adjacent LXI D arguments. Verbose
output identifies the file offset of each finding.

Near term:

- Add conservative instruction decoding and control-flow traversal so code is
  distinguished from embedded data where possible.
- Recognize additional safe function-selection idioms without treating stale
  register loads as current calls.
- Report a useful minimum TPA requirement without confusing file length with
  runtime data, stack, or overlay requirements.

Possible later work:

- Recognize common BDOS-call idioms, direct BIOS calls, absolute-address and
  memory-layout assumptions, self-modifying code, and suspicious references
  outside the loaded image.
- Estimate 8080 compatibility without presenting heuristics as proof.

COMINFO is not intended to become a general disassembler.

## BDOSPROBE

Current release: `0.1.0-dev4` (`BDOSPRB.COM` under CP/M).

Dev1 provided the common result-capture harness and version probe. Dev2 adds
console status; login, current-disk and read-only vectors; and allocation-vector
and DPB addresses. It records A, BC, DE, HL, flags, and SP, while interpreting
only documented results. Dev3 adds function 32 strictly in query mode and
checks that repeated queries leave the user number unchanged. Dev4 obtains the
current drive, selects only that same drive, and compares the current drive,
login vector, and read-only vector before and after. Admission rules are in
`docs/BDOSPROBE-DESIGN.md`.

Near term:

- Compare dev4 behavior on additional CP/M-compatible systems used during
  BetterCP/M development. Both z80pack CPU modes have passed. On Montezuma
  Micro CP/M 2.2, dev3 `/USER` passed in user areas 0 and 3, and dev4 `/SELECT`
  passed from current drives A and B without changing the selected drive,
  login vector 0003H, or read-only vector 0000H.

Possible later work:

- Add guarded probes for reversible state after save/restore and failure-path
  behavior have been demonstrated.
- Supply reusable evidence for BetterCP/M development without making the tool
  dependent on BetterCP/M.
- Keep persistent writes, reset, and termination out of the ordinary probe.

## BDOSTRACE

Status: planned, advanced.

Possible work:

- Intercept the standard BDOS entry while preserving the traced program's
  registers, stack, memory, and observable behavior.
- Report function numbers, symbolic names, important register arguments, FCB
  addresses, DMA changes, file operations, and program termination.
- Add selective tracing and an output path which does not recursively disturb
  the calls being observed.

This tool should not be started until the interception and logging design can
be demonstrated safely on several CP/M implementations.

## BIOSINFO

Status: conditional candidate.

BIOSINFO should be created only if it can provide substantially more than
SYSINFO's BIOS report. Candidate work includes shared-target and stub detection,
deeper SELDSK/DPH/DPB inspection, SECTRAN behavior, LISTST implementation, and
comparison of character-device routines. Otherwise this work remains in
SYSINFO.

## MEMINFO

Status: conditional, lower-priority candidate.

MEMINFO should be created only if deeper memory analysis would be clearer than
extending SYSINFO. Candidate work includes a detailed page-zero map, TPA and
resident-system boundaries, default FCB and DMA areas, command-tail storage,
and detection of unusual low-memory modifications.

## Suite-wide work

- Preserve one universal `BUILD.SUB` and one Montezuma Micro 880K tools image.
- Keep every diagnostic tool read-only until writing is essential to its stated
  purpose and has an explicit safety design.
- Test native ZSM4 and Digital Research LINK builds under CP/M.
- Test on additional CP/M BIOSes and disk geometries as suitable images become
  available.
- Reuse proven support routines where practical while keeping each utility
  independently buildable.
- Study historical utilities for operator-interface and diagnostic ideas while
  retaining an independent implementation. DISKSTAT's allocation map, deleted
  block accounting, large-disk arithmetic fixes, and CP/M 3/MP/M structure
  handling are useful reference points; CP/M 3 and MP/M remain later
  portability work rather than current CP/M 2.2 scope.
