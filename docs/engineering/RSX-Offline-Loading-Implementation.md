# RSX source selection and offline residency

6 November 2026. Implements the maintainer-accepted
[proposal](RSX-Offline-Loading-Proposal.md). This is a v1.0.1 maintenance
candidate; no release package is replaced and no PR is merged by this work.

## Result and boundaries

`RSX LOAD B3:STATEFUL.RSX` loads from that exact drive/user. The original
carrier may then be deleted or its disk removed. Ordinary warm boots and
later RSX loads/unloads use retained RAM data, including when the removed
provider's own carrier is unavailable. No hidden RAM or bank switching is
introduced. Cold boot still starts with an empty active profile.

The System runtime remains a separate dependency: keep the matched
`R3PACK.RSX` and new `R3CACHE.RSX` in A0. These are internal support files,
not providers to install with `RSX LOAD`. Update the raw Function-177 entry
with its matching runtime; copying a new XSUB onto an old System is not a
complete update. BRSX carrier formats and supplied BATCHIO/SUBMIT source
remain unchanged.

The FDB exit report remains **open, unreproduced**. Clean Q returned to CCP
on cpmsim and the existing FDB session/editor suites passed. The maintainer
could not recall the original sequence. No FDB runtime correction or FDB
fix PR is claimed. Its documented menu-presentation issue is separate.

## Discovery and compatibility

- Explicit `D[0..31]:` selects one source. `B:NAME` retains the caller's user.
- Unqualified RSX LOAD searches the current DU, then A0. Fallback occurs only
  after open failure; an opened invalid carrier never causes another search.
- `B0:XSUB B0:` uses B0's companion without a staging copy. Bare XSUB searches
  current DU, then A0. The executable's own location is not a companion path.
  There is no implicit all-drive scan or new CCP invocation-location interface.
- QUERY/UNLOAD and duplicate detection retain name-based identity. Loading
  another source with an already installed stem is an idempotent no-op, not
  replacement. Explicit qualifiers on the UNLOAD command are rejected.
- Legacy 18-byte Function-177 version-2 clients retain A0 lookup and their
  original results. Version 3 uses 20 bytes: +18 zero-based drive, +19 user;
  LOAD +2 is 0 for exact or 1 for A0 fallback. ENUMERATE/QUERY return provenance
  at +18/+19. Existing version-2 self-retirement remains supported.
- The source stream restores caller drive/user/DMA on returning failures as
  well as success. CPX and system-runtime file discovery remain fixed A0.

## Retained representation

The persistent 41-byte name/service table and its protected-memory boundaries
are unchanged. A new optional 1 KiB reader lives immediately below the
existing 1 KiB manager; providers are planned below both. It is loaded from
A0 only when creating a profile from empty, and stays resident across WBOOT.

Each provider's charged allocation includes a compact, offset-based capsule:

1. The used BRSX header: 48 fixed bytes plus the static relocation directory.
2. Original payload and typed metadata, omitting unused 512-byte-header padding.
3. An eight-byte footer immediately below the callable descriptors: capsule
   offset, compact length, source drive/user and `RC` signature.

Keeping the original payload also for STATEFUL modules deliberately reuses
existing full-carrier checksum/metadata validation. It costs more RAM than
an additional normalized-facts format but avoids changing those validation
and monitor-compatibility contracts. STATELESS preparation still starts from
its pristine template; STATEFUL movement preserves the live allocation.

The stream reconstructs the original header window in scratch and reports
the complete charged allocation to the planner. The saved STATEFUL carrier
retains the provider's original allocation size. Production pointer repair
uses that original size from the already moved capsule, so fixed external
values numerically inside loader-owned capsule space are not relocated.
The mover still copies the full charged block, including its capsule.

Candidate snapshots pack their capsules before commit. Retained STATEFUL
capsules move with their providers; retained STATELESS snapshots repack theirs.
No original carrier file is reopened. All fallible preparation precedes the
existing disk-free commit/publication boundary. Last-provider unload restores
the original no-RSX TPA and releases both optional runtime allocations.

The larger STATELESS snapshot can overlap the old normalized-facts scratch
when compacted downward. Dispatch is therefore read from the prepared snapshot
request rather than from facts which that copy may already have overwritten.

## Measured cost

The no-RSX TPA is unchanged. The reader adds 1,024 shared bytes while any RSX
is installed. Per-provider charge is the original declared allocation plus
`round_up_to_256(compact_carrier_bytes + 28)`; 28 reserves the footer and the
maximum two callable descriptors. Existing provider-owned padding is retained.

| Supplied provider | Declared | Compact carrier | Extra charged | Total provider |
| --- | ---: | ---: | ---: | ---: |
| HELLO | 1,024 | 124 | 256 | 1,280 |
| STATEFUL | 256 | 248 | 512 | 768 |
| BATCHIO | 512 | 669 | 768 | 1,280 |

BATCHIO alone therefore consumes 3,328 bytes including both shared runtime
allocations, 1,792 more than the old arrangement. This is an explicit tradeoff
for source-media independence, not a claim of unchanged loaded-RSX TPA. The
maximum-size Function-10 fixture now accounts for that charge.

## Validation

[evidence](evidence/2026-11-06-rsx-offline/results.json) records the checks and
links the per-platform receipts. Both supported RAM platforms qualified the
same current R3PACK, R3CACHE, raw entry, RSX.COM and XSUB.COM hashes.

- Independent full Z80 core: explicit B3/C31, legacy A0, provenance queries,
  invalid locations, returning open/read failure rollback, exact DU/DMA,
  idempotence, offline removal, STATELESS template reset, overlapping STATEFUL
  relocation, fixed external pointer preservation and last-provider reclamation.
- Capsule execution: zero/one/128/232 relocation words, relative offsets,
  header page boundaries, source DU, EOF/reset and original ownership bounds.
- CLI execution: bounded source prefixes, default current DU, malformed
  sources, exact-source restriction and help/version precedence.
- Existing snapshot, mover and all-15-slot container reader checks pass.
  Registry projections and selected-input tests pass.
- cpmsim and trs80gp Model 4: load HELLO from B0 and STATEFUL from B3,
  initialize/mutate, erase both carriers, remove HELLO to relocate STATEFUL,
  verify state, unload STATEFUL, then run `B:XSUB B0:` from SUBMIT. Function 10
  consumes `BATCHFULL`; erase BATCHIO's source and reach `MARK: RSXOFFLINE`.
  Independent filesystem extraction verifies the three carriers are absent,
  no queue remains, and both filesystems pass fsck. Original images are unchanged.

Model 4 used bcpm's explicit `-m4 -frehd` A–D arrangement, with a writable
capture directory and the normal startup allowance. Earlier short blank
captures were inconclusive startup samples, not boot failures. A separate
Model 12 window was not part of qualification and was not terminated here.

Checked-profile helper binding/checksum emission and ROM relocation packaging
are updated to include the internal reader. Checked conditional branches fit
their execution slots. These checks do not claim new native acceptance of the
post-1.0 checked/full-RAM or guarded-ROM prototypes.

## Reproduction

Build the unchanged core symbols before assembling the reader:

```sh
python3 tools/build_bdos.py
python3 tools/build_rsxresolver.py
python3 tools/build_rsxloader.py
python3 tools/build_rsx_runtime_overlays.py
python3 tools/build_rsx_utilities.py
python3 tools/build_batch.py
python3 tools/build_hello_rsx.py
python3 tools/build_stateful_test_rsx.py
python3 tools/build_stattst.py
python3 tools/test_rsx_cache.py
python3 tools/test_rsx_offline.py
python3 tools/test_rsx_source_cli.py
```

`tools/qualify_rsx_offline.py` accepts original System/Utilities paths and a
fresh output directory. Model 4 additionally accepts companion/work paths,
which it copies privately. Run it once per target; it records hashes, audits
source removal and never writes the input media. Native snapshots require the
host's usual trs80gp launch context. Package/release identity assignment and
publication remain separate from these development-artifact receipts.
