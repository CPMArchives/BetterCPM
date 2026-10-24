# Compression utility numeric revision migration

This increment follows automatic development identities in PR #495. SQ, USQ,
CR, UNCR, LZH and UNLZH now use the shared numeric title format for /VER and
/HELP. Each advances from 1.0 (Build 004) to 1.0 (005), once for the changed
executable identification. Other component identities remain unchanged.

The six assembler drivers share a build-record decorator in `codec_version.py`.
It captures selected inputs and display state before/after assembly, binds the
actual output bytes, removes stale reports before rebuilds and restores its
display context even on failure. Each command writes NAME-build-report.json so
six commands can share an output directory without overwriting one another's
receipts. Concurrent builds of the same command still require isolated output
directories. Ordinary builds do not update revisions or input baselines.

Explicit per-command maps cover only that codec's copied source/includes, common
codec/file/query support, identity preparation and the actual assembler flags.
For example, changing sq.mac affects SQ; it does not affect USQ. Shared helper
edits still affect review of each consuming utility. Per-target default cross
baselines select numeric or -dev output automatically. All builders expose
--target and --identity-state consistently with BYE/DDT.

Reference legacy binaries are newly reconstructed from the previous source;
their source hashes and actual artifacts supply reference records. They are
not relabeled historical qualification receipts. Same-revision numeric
candidates differ in executable bytes, proposing 005; final rebuilt artifacts
pass assignment verification with matching candidate fingerprints. Records for
both z80pack and trs80gp target labels are retained in
`CODEC-REVISION-ASSIGNMENTS.json`. Automatic baseline rebuilds reproduce the
assigned bytes, and no additional increment is taken for the new digits.

## Verification

The existing 58 versioning tests and three codec build-record tests pass.
The complete full-Z80 query/parser campaign passes 356 cases across all six
tools, including four-digit numeric identity, exact /HELP and /VER behavior,
bounded command tails, console-only query paths, register/context preservation
and deterministic builds. Runtime suites pass:

| Utility | Cases | Additional coverage |
| --- | ---: | --- |
| SQ | 51 | 11 USQ round trips |
| USQ | 71 | Parser, record I/O, fault cleanup and overwrite protection |
| CR | 47 | 11 UNCR round trips |
| UNCR | 87 | 13 historical files |
| LZH | 47 | 11 UNLZH round trips |
| UNLZH | 122 | 47 historical files, unsafe-name refusal |

The first UNCR/UNLZH attempts stopped because the reconstructed worktree lacked
their default fixture paths. Reruns with the existing compatibility-suite corpus
and original CrLZH archives pass; no fixture data was changed. These are focused
CPU-harness component checks. Native ZSM4/LINK and paired physical-emulator disk
campaigns must be rerun before transferring earlier Build 004 qualification to
new binaries. Previous receipts remain intact and retain their original scope.

No disk image or release package is frozen by this work. Ordinary common-utility
and module migration, RCP/MOVE/WARM resolution, additional input maps, native
records, checked-contract refinement, core development reporting and immutable
disk manifests remain outstanding.
