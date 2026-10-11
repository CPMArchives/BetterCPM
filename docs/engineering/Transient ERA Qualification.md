# Ordinary transient ERA qualification

Qualified 2026-10-11. ERA.COM 1.0 Build 001 is 5,244 bytes, SHA-256
`0a89f3b9f6171c8b9cbf22430040157089711b5a7d574126754ef15aa6e02e8c`.
Native ZSM4/LINK and cross-assembled binaries are byte-identical.

## Implemented increment

Shared bounded filespecs, DU sets and attribute predicates; complete target
collection before mutation; `/VER`, `/Y`, `/Q`, `/C`, `/R`; preflight manifest
and paging; exact and per-file confirmations; matching-branch protected-file
admission; recovery R/S/A/?; allocated-space and outcome accounting; caller-DU
restoration. Destructive `/D`, `/QQ`, `/N` and `/DRV` remain unimplemented and
are rejected before any deletion. This is not completion of the entire ERA
specification.

The shared parser sources are linked privately into ERA.COM. It does not depend
on RCP being loaded. Admission uses the same attribute atom decoder and adds
branch-specific protection masks; no second attribute lexical grammar is used.
All extents are merged before selection. Live attributes are checked again
before deletion, and only exact concrete filespecs are passed to BDOS delete.
RO is cleared only after authorization. Failure attempts to restore RO before
recovery; a failed restoration reports an explicit diagnostic. No BDOS or
resident allocation changes are required.

## Evidence

`tools/test_transient_era.py`:

- Eighteen private cpmsim sessions on disposable disks. Physical directory
  state and surviving file contents are checked independently of ERA output.
- Broad protection, same-branch SYS+RO admission, separate-branch rejection,
  negated aliases, `/Y` RO skipping, `/R` authorization, one RO prompt with
  `/C`, exact-file confirmation, `/Q` interaction, and per-file Y/N decisions.
- Invalid filespecs, unsupported options, invalid predicate and unsupported
  drive in a compound selector leave the target set unchanged.
- Multi-DU selection with repeated locations, multi-extent erase, and actual
  allocated-space accounting (33,024 bytes occupy 34K on this filesystem).
- Production-code tests for thirteen admission truth masks, nine unsigned
  DWORD decimal values (including 0, internal zeros and 4,294,967,295), retry,
  skip, abort, Ctrl-C, help without state changes, and unattended failure.
- Injected failed RO deletion checks temporary clearing followed by restoration;
  failed restoration checks the diagnostic and failed-file accounting.
- Target-record overflow leaves storage untouched. Paging resumes on Space or
  Enter; Ctrl-C cancels without a recursive paging prompt.

`tools/test_model4_transient_era.py`:

- Private trs80gp instance and disposable Model 4 DMK. SUBMIT exercises explicit
  transient execution, `/VER`, mixed-drive rejection before mutation, multi-
  extent ordinary erase, unattended RO preservation, separate-branch rejection,
  SYS/RO authorization and negated aliases.
- Finish markers prove command completion. Physical DMK directory examination
  confirms the intended files were deleted and the rejection fixture survived.

`tools/build_native_era.py`: 5,244 byte-identical native/cross bytes.
`tools/test_utility_versions.py`: 124 identity, dispatch and usage checks pass.

The failure-injection and capacity tests execute the production Z80 code with a
controlled BDOS boundary. Real disk tests complement them; raw destructive-write
failure handling is outside this increment and requires separate qualification.

## Reproduce

From the repository root, using a disposable z80pack image directory:

```sh
python3 tools/build_era.py
python3 tools/test_transient_era.py --image-dir IMAGE_DIRECTORY --report NEW_REPORT_DIRECTORY
python3 tools/test_model4_transient_era.py --report NEW_MODEL4_REPORT_DIRECTORY
python3 tools/build_native_era.py
python3 tools/test_utility_versions.py
```

Reports must use fresh directories. Native build tool/image paths can be supplied
through the builder's documented options. Model 4 reports retain launch
arguments, screen captures, transcript and the resulting disk image.
