# PR 605 post-merge review against spec 209

Reviewed merge `d95b30bfa91cbc3cace53c861d8964375a7afe70` against spec 209,
including implementation changes, the final candidate receipts and archived
native captures. No product defect was found. The 1.0 package freeze remains
**HOLD**; acceptance does not authorize a release or package-freeze promotion.

One regression-test finding was fixed: `test_config_fdb_runtime.py` still sent
G to enter CONFIG's disk-format menu. The current menu uses D. The corrected
test passes against the final complete cpmsim System image. This is a test-only
change and does not change any qualified binary or candidate archive.

The [integration acceptance report](209-final-integration.md) maps all six
specification gates and installation/cold boot to evidence on both platforms.
Review verified the evidence checksum manifest, native archive, actual Model 4
restoration/cold-boot screen contents, both named-109th-entry/file-read results,
disk-full postconditions, editor final assertions and preservation receipts.
Incomplete exploratory trials remain excluded. Earlier runtime results apply
only under the exact code/data and media identity checks recorded there.

Post-merge checks reran the 40-case converter regression, 50-case session and
nine-case editor regressions, native reader/all 108 bindings, 15 distribution
tests, nine candidate-packaging tests, two build-sequence tests, deterministic
catalogue packaging and the six-archive package-lock checker. All pass.
Rebuilding FDB and its viewer from merged source gives the exact qualified
SHA-256 values:

| File | SHA-256 |
| --- | --- |
| FDB.COM | `471b29358597f0dafdfd43ae9fa3945ee36f410afdebc689ea06d5c0637b7da2` |
| FDBVIEW.OVL | `29cfbc272db57ee8eb8c8b2dcc423eb9dc4346704ddd4c26e75ef282a739752c` |

A fresh native cpmsim run on the final System image also passes import/save of
entry 109, named CONFIG binding, actual file read, and original-file/reserved
area preservation. The current-pair Model 4 repeat passes safe 50 KiB refusal,
53 KiB workbench/viewer operation, queued console restoration, actual file
read, cold boot and preservation of all 32 original files/reserved tracks.
Fresh raw captures, result receipts and regression logs are in
[the post-merge evidence directory](../reviews/2026-11-04-fdb-post-merge/).

The original six candidate archives and their offline Source reconstruction
remain the qualified artifacts; this review does not claim a new candidate
generation from the merge commit. Source, documentation and evidence-only
differences from the candidate input do not change the tested media.
