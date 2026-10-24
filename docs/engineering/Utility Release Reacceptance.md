# Utility query reacceptance and current Utilities inventory

## Scope — 2026-10-24

**PASS for current-inventory and shared-query-change reacceptance.**

This campaign reaccepts the maintainer-directed forgiving `/VER` change for the
currently shipped owned utilities and qualifies the **current ten-file Utilities
inventory**. The maintainer explicitly chose to keep the unresolved selections
open. Neither the complete Utilities release nor system-wide conformance is
closed by this record.

The inventory is DDT.COM, DUMP.COM, XSUB.COM, BATCHIO.RSX, SQ.COM, USQ.COM,
CR.COM, UNCR.COM, LZH.COM and UNLZH.COM. No new compression features, guest
instructions or utility build numbers were introduced by this campaign.
The [machine-readable record](Utility-Release-Reacceptance.json) binds the
candidate media, executable identities, test results and
[evidence bundle](Utility-Release-Reacceptance.tar.gz).

## Artifact binding

Fresh isolated System builds from committed inputs produced the following
reference media, cold-boot checked on both platforms:

| Reference | SHA-256 |
| --- | --- |
| cpmsim System | `75e0ae5e15972fc92579fe3924a28c9d32c7e23cc6431bd932b54ef0841a9c13` |
| Model 4 System | `40e7ddeccf2bc0720179045785ed56fd41658c0ab1d6b957e178fdf1e813f72f` |
| cpmsim Utilities | `7e527f29a75cbd69c7af0dbe138f5674ebc4ea0cdda7d0bb86c314d2866497a1` |
| Model 4 Utilities | `b809f43d60b54a7be1caaf6f75bd69db00e5917ed5ab06c8c716811c44428511` |

The published private System generation records source revision `dc2008b` and
complete input hashes. An earlier candidate from `2023d89` had identical image
bytes; its per-platform checks completed, but the distribution builder correctly
refused publication after host test sources changed. The clean committed-input
build closes that publication issue. Component runs against the identical
candidate bytes retain their exact media scope. The follow-up branch also carries
the previously pushed pinned-cpmsim work, which had not yet reached main.

The runtime is the [reconstructed cpmsim](CPMSIM%20Reconstruction%20Qualification.md)
with hash `3a41c74a8e70562fefc9d4e6c0e532259bb82b83518f7bfc259230699fe82c05`.
Model 4 runs use the recorded trs80gp binary and private copies of all media.
The DUMP terminal-screen oracle is pyte 0.8.2; its source identity is retained.

## Checks and disposition

- The initial focused campaign passed 82 suites. Four failed harness invocations
  were resolved and retained, rather than discarded: the old DIR filespec test
  used a removed resident entry, the wrong DIR listing and an obsolete wrapper
  offset; DIR media and TYPE abort tests require explicit arguments; CONFIG's
  native campaign required desktop launch access and a longer host deadline.
- The current DIR parser test checks seven malformed operands before BDOS I/O
  or command-FCB expansion and checks wrapper call targets. The relocated
  production RCP selector passes at three origins. Separate real-media DIR
  coverage passes 63 selector, extent-size, sorting, attribute and total cases.
- TYPE's resident/transient Ctrl-C output abort preserves the active DU and
  source disk. CONFIG's native startup-record campaign checks reading, editing,
  clearing, testing and saving pending records, with explicit data assertions.
- Shipped utility queries pass on both platforms: 28 commands per platform,
  including all applicable System utilities and all nine Utilities COM files.
  Exact `/VER` tokens ignore extra operands and each command returns to batch
  execution. The common 250-query and pre-private-stack tests also pass.
- The continuous two-session cpmsim workflow passes README/DIR/WHEREIS, ED,
  PIP/REN/STAT/COPY/ERA, SUBMIT, monitor personalities, repeated returns and
  cold-boot persistence, with file/filesystem/system-track audits. Focused
  suites also cover TIME, CONFIG, DUP, SYSGEN, CPX/RSX, DDT and DUMP. These are
  relevant query-change regressions; they do not relabel every earlier
  component's full release or hardware qualification.
- DDT from Utilities B: passes 26 cpmsim interactions and all 14 Model 4 stages:
  identity, load, disassembly/assembly, editing/cancellation, breakpoint,
  trace/untrace, restart and Ctrl-C return. Utilities and the debuggee remain
  unchanged. A 180-second host deadline expired during the final stages of the
  first native trial; the complete 600-second run passes.
- DUMP from Utilities B: passes both platform campaigns, with 80/40-column
  pages, navigation, Go To, forward/backward record-crossing Find, ESC/physical
  CLEAR cancellation and return. Independent cell checks and unchanged file
  allocations/attributes accompany filesystem checks.
- XSUB from Utilities B: passes ignored-operand `/VER`, installation of its
  protected provider, Function-10 batch input, continued command execution and
  queue cleanup on both platforms. The exact packaged BATCHIO.RSX is installed
  on private A0, its documented required location. Input fixtures, companion
  and the Utilities image remain unchanged. Native operation is driven by a
  private startup batch, avoiding host command-injection timing.
- All six compression binaries and both Utilities image byte streams are
  identical to their existing qualification receipts. The Model 4 System image
  is also identical to the full prior 27-round-trip receipt. Fresh cpmsim
  acceptance on the new System image passes 86 commands and 27 round trips.
  Historical/native-build records retain their original scope and identical
  executable identities.
- An independent FDF reader checks exact ten-file membership, user 0, file
  attributes, allocation bounds/cross-links, all executable bytes and final
  record padding. It handles the cpmsim EXM=1 allocation groups and the Model 4
  16-bit block maps. Both filesystems and Model 4 DMK/raw conversion pass.
  Five deliberate wrong-user/name/allocation/payload/duplicate mutations are
  rejected. Free allocation blocks are 99 on cpmsim and 332 on Model 4.

The initial legacy interactive Model 4 whole-System workflow did not complete
at its first keyboard gate and was stopped. A targeted repeat with a 250ms
matrix-key hold and 1s settling reached the next gate. Independent readback
then verified the native PIP/COPY/REN results, STAT's final R/W attribute,
unchanged source/other-user files, and clean filesystem. This qualifies that
first operational phase only; the remaining ED/lifecycle/reboot phases are not
claimed as passed here. The original failure and targeted passing probe remain
separate in the evidence. Complete System release-workflow/conformance
acceptance remains a separate release responsibility.

## Reproduction

Build an isolated System generation with `tools/build_distribution.py --target
all --simulator ... --output ... --work ...`; keep its source inputs unchanged
until publication. Build the current Utilities set with:

```sh
python3 tools/build_utilities_disk.py --build --artifacts ARTIFACT_ROOT --output NEW_UTILITIES
python3 tools/test_utilities_inventory.py --artifacts ARTIFACT_ROOT \
  --images NEW_UTILITIES --output inventory.json
python3 tools/test_utilities_inventory_guards.py --artifacts ARTIFACT_ROOT \
  --image NEW_UTILITIES/BetterCPM-Utilities-z80pack-332K.dsk
python3 tools/test_ddt_utilities_release.py --system SYSTEM_GENERATION \
  --artifacts ARTIFACT_ROOT --output NEW_DDT --simulator PINNED_CPMSIM
python3 tools/test_dump_view_live.py --baseline SYSTEM_GENERATION/z80pack \
  --utilities NEW_UTILITIES/BetterCPM-Utilities-z80pack-332K.dsk \
  --output NEW_DUMP_CPM --simulator PINNED_CPMSIM
python3 tools/test_dump_model4.py --image MODEL4_SYSTEM \
  --utilities NEW_UTILITIES/BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk \
  --output NEW_DUMP_M4
python3 tools/test_xsub_utilities_release.py --system SYSTEM_GENERATION \
  --images NEW_UTILITIES --artifacts ARTIFACT_ROOT --output NEW_XSUB \
  --simulator PINNED_CPMSIM
python3 tools/test_utility_query_media.py --system SYSTEM_GENERATION \
  --utilities NEW_UTILITIES --output NEW_QUERIES --simulator PINNED_CPMSIM
```

Use the matching artifact tree's test scripts for focused regressions. The
initial orchestration, commands, source snapshots, original failures and all
replacement receipts are retained in the bundle. `--build --artifacts` now
actually invokes builders in that artifact tree; previously it built in the
caller repository and could then fail to find those outputs in the requested
tree. DDT acceptance uses the tested artifact's identity rather than a fixed
constant, and all native raw-System operations pin PCW 800K geometry.

## Remaining release decisions

The current ten files are accepted as components on these exact candidate
images. Utilities reports remain **PROVISIONAL** for the overall release.
Still open: full-screen editor and disassembler selection, ZSM4/LINK release
packaging, on-disk documentation/native-build-material placement, final
inventory approval and full frozen-release evidence closure. NOAH's complete
archive interface is selected post-1.0 work; it is not an unselected 1.0 archive
candidate and its development foundation is excluded from these disks.

Any change to guest executable bytes, System/Utilities media or emulator inputs
requires relevant reacceptance. Earlier receipts keep their original identities;
this record supplies the explicit shared-query-change and current-inventory
bridge. It does not promote unrelated development helpers or NOAH to the
release inventory.
