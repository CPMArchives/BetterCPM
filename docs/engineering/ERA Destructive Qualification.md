# Destructive ERA qualification

Qualified 2026-10-11. ERA.COM 1.0 Build 002: 7,619 bytes, SHA-256
`4d5be2a34e50dcf6aacfb8b782e4acc09a435562bcfab66a99d02cc7ba7a3a91`.
Native ZSM4/LINK output matches the cross-build byte for byte.

## Component and failure checks

- `test_era_raw_adapter.py`: 51 production-code positioning/snapshot cases,
  including capacity, buffer wrap and read failure. Read-only cases invoke no
  write vector.
- `test_era_destructive_plan.py`: 19 ownership/map cases, including byte and word
  allocation pointers, multiple extents, cross-user sharing, all-shared and empty
  files, deleted entries, reserved/invalid blocks, duplicate target pointers,
  invalid geometry, record overflow and workspace exhaustion. Snapshots stay
  unchanged and the planner performs no disk I/O.
- `test_era_destructive_failures.py`: eight production transactions with injected
  BIOS data/scrub failures. Data Skip preserves metadata. Data Retry reuses the
  saved plan. Partial-scrub Retry completes already-scrubbed entries safely.
  Scrub Skip, Abort, Ctrl-C and unattended failure report incomplete erasure,
  preserve unrelated entries/shared data, and reset only the affected drive.
  Ordinary BDOS delete/attribute mutation is forbidden by the test boundary.

## Real disk qualification

`test_era_destructive_disk.py` runs eight cpmsim cases against disposable disks:

- All allocated blocks of a multi-extent file are checked for zero bytes.
- Every selected entry is independently checked for exact `E5 00 ... 00` scrub.
- An allocated block shared with a file in another user area remains unchanged;
  reporting and freed-space accounting distinguish the shared outcome.
- Explicit RO authorization, empty-file scrubbing and a truly RO drive are
  exercised. RO is set inside the same transient invocation because WBOOT
  clears runtime drive protection. The denied operation leaves the disk intact.
- Two files in one invocation verify disk-state reconciliation before the next
  file. A destructive N confirmation leaves the image untouched. An RO `/C`
  operation receives one destructive RO authorization prompt.

`test_model4_era_destructive.py` runs a private trs80gp instance with a disposable
DMK. Offline inspection verifies zeroed unshared blocks, exact directory scrub,
RO authorization, and unchanged data and metadata of the other-user owner of a
shared block. Completion is proved by the SUBMIT finish marker.

Ordinary regression: 18 cpmsim sessions and 13 admission-mask checks pass,
including ordinary confirmations, protection, failure recovery, paging and
capacity boundaries. All 124 utility identity/dispatch checks pass.

## Reproduce

```sh
python3 tools/build_era.py
python3 tools/test_era_raw_adapter.py
python3 tools/test_era_destructive_plan.py
python3 tools/test_era_destructive_failures.py
python3 tools/test_era_destructive_disk.py --image-dir IMAGE_DIRECTORY --report NEW_REPORT_DIRECTORY
python3 tools/test_model4_era_destructive.py --report NEW_MODEL4_REPORT_DIRECTORY
python3 tools/test_transient_era.py --image-dir IMAGE_DIRECTORY --report NEW_ORDINARY_REPORT_DIRECTORY
python3 tools/build_native_era.py
python3 tools/test_utility_versions.py
```

Use fresh report directories and provide local native build tool/image paths
through builder options as needed. Only disposable media is modified.

Destructive erase is not a claim of cryptographic secure erasure. Failed data
writes may leave partially zeroed data, and failed scrubs may leave partially
scrubbed metadata. Shared data is intentionally retained.

## Final ERA closeout

Build 002 also passes the ordinary Model 4 workflow: mixed-drive rejection
before mutation, multi-extent deletion, unattended RO preservation, same-branch
protection admission, `/R`, and negated aliases. The SUBMIT finish marker and
independent directory inspection confirm completion and preservation of KEEP.DAT.

Both manifest-selected distribution disks were rebuilt from source and passed
filesystem, file-integrity and boot qualification. Each includes the exact
7,619-byte ERA binary with the SHA-256 recorded above. The z80pack disk contains
19 files with 208K free; the Model 4 disk contains 18 files with 656K free.
The RSX helpers are packaged in their single container. PIP, WHEREIS and the
provisional full-screen editor remain planned distribution items.

ERA's agreed 1.0 resident and transient operation contracts are complete.
Automatic resident-to-transient handoff is separate command-environment work;
use `:ERA` to select transient behavior explicitly when necessary. `/QQ`, `/N`
and `/DRV` are not part of the agreed transient switch set.
