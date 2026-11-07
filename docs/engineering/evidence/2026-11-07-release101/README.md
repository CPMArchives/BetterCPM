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

[Unchanged Utilities identity evidence](unchanged-utilities.tar.gz) refreshes
CRCKSUM and PATCH selected-input baselines after proving their assigned
executables exactly match the actual frozen 1.0 downloads. Automatic builds
then reproduce those bytes without overrides; their revisions stay 011 and
003. This prevents development labels caused solely by conservative shared
input changes from changing otherwise unchanged release binaries.

## Media execution results

[Media qualification](media-qualification.json) and its
[capture archive](media-qualification.tar.gz) record passing focused checks on
both cpmsim and Model 4: resident commands and file operations, FDB menu and
exit/editor paths, lowercase DIR, expanded PIP selectors and collision safety,
and offline RSX/cache-error recovery/XSUB. cpmsim also passes the host terminal
and ANSI resize/recovery checks. The actual System host kit reconstructs the
exact runtime and guest tools offline. Independent Utilities inventory and
unchanged-body comparisons retain the prior detailed coverage of the other
Utilities executables. The PIP fixture submits its commands directly through
STARTUP, and native DIR input waits for disk-based warm boots before typing.

Execution receipts identify image hashes rather than asserting that later
source-only packaging/harness edits were already present. Final package
acceptance must verify those same image bytes, exact source provenance, all
six ZIPs and checksums before release-ready naming.
