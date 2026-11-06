# 1.0.1 release preparation — 2026-11-07

The source cut includes merged main through PR #640 and the approved PIP
selector enhancement. The Utilities supplement includes only CPCSYS, CPCDATA,
PCW and BW14: 108 standard plus four optional definitions gives 112 entries.
ATONSS, ATONDS, PT2SS and the 48-byte checksum expansion are deferred for 1.1
consideration. The distribution builder retains its existing 32-byte layout;
no extra mutable BIOS region is reserved.

## Component identities

[Identity assignment evidence](identity-assignments.tar.gz) contains the prior,
candidate and final byte records, standard revision proposals/acceptances and
automatic reproduction results. Own revisions advance once when executable
bytes change. BIOS identity covers its executable, configuration, tables and
bootstrap pieces, including changes already merged since 1.0. The BIOS counter
is not a claim that checksum capacity was expanded in this cut.

Both targets reproduce all 56 recorded primary artifacts and their complete
BIOS implementation sets without forcing assigned labels. Working-tree
preparation records identify actual input fingerprints against the base
commit; they do not misrepresent the base commit as the prepared source.

## Acceptance boundary

These are build and identity proofs, not final release acceptance. Fresh System
and Utilities images must be constructed from the clean committed source,
qualified on cpmsim and Model 4, and matched by image hashes in the final
release acceptance record. Earlier expanded-layout build results are superseded.
The final archive evidence records the fresh checks separately. Unchanged
utility implementations retain their prior detailed component coverage; newly
constructed media require independent inventories and paired-media checks.
Physical media and historical application/boot compatibility remain untested.
