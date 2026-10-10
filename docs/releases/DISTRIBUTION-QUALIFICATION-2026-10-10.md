# Current System Disk Distribution Qualification — 2026-10-10

The manifest-selected builder passed on both supported targets. This qualifies
current distribution assembly and bootability, not final 1.0 conformance.

| Target | Image format | Installed files | Free filesystem space | Filesystem / file integrity / boot |
|---|---|---:|---:|---|
| z80pack/cpmsim | CCS 332K raw DSK | 32 | 202 KiB | PASS / PASS / PASS |
| trs80gp/Model 4 | Extended 80T DS SYSTEM DMK | 32 | 648 KiB | PASS / PASS / PASS |

Every installed file matched its current build artifact byte-for-byte, allowing
only CP/M record padding. Directory membership and user-zero placement matched
the machine-readable manifest exactly. cpmtools filesystem checks passed.
Both emulator runs reached the prompt, listed RCP, and reported BetterCP/M via
VER. cpmsim also loaded and listed ZPRTC. A separate private-copy Model 4 smoke
run loaded, listed, and unloaded FREHDCLK, confirming the shipped manager-helper
dependencies work. This does not retest clock sampling or require FreHD hardware
for every boot.

SHA-256 image identities:

- cpmsim: `6fc5cfe84cdc7b25c57d02d969c219d6d329aba7891d14ae3a4a855c2f013073`
- Model 4: `4db060935835a82480fa47c0257a665e13969d59d06d0780d3c74395cc24aff9`

Retained generation:
`/private/tmp/bettercpm-distribution-final-20261010/release-bcb6197d075d-8ab514c4dabb/`.
Each target's `report.json` retains actual source/input identities, manifest and
artifact hashes, tools/emulator hashes, included files, omissions, and results.
The source revision is supplemented by hashes of the uncommitted builder and
manifest inputs; the revision alone does not identify this work.

Model 4 manager smoke evidence:
`/private/tmp/bettercpm-distribution-clock-smoke/clock-manager.txt` and its
`trs80-text-*.bin` captures. A hash-verified cache replay under
`/private/tmp/bettercpm-distribution-cache-check-20261010/` produced a byte-identical
cpmsim disk and passed its boot checks again.

Five automated failure-gate tests passed: planned omissions are reported;
missing implemented artifacts fail; block/directory capacity limits fail;
stale-source or changed-artifact caches are rejected; and failed named-image
copy verification preserves the previous image. Publication creates
an immutable generation only after all requested targets pass, using a completed
staging directory rename. Earlier successful images and development disks are
not overwritten.

## Open issues and planned omissions

- PIP.COM: no integrated source/approved adopted artifact yet.
- WHEREIS.COM: selected for the System Disk; implementation pending.
- Full-screen editor: program selection pending.
- Existing core VER reports `BetterCP/M 0.3` on both targets. Correcting system
  version presentation is a separate task; no OS code changed here.
- Utilities Disk and CP/M Tools Disk assembly are deferred.
- On-disk documentation filenames/placement have not been selected.
- Final conformance and pinned cpmsim environment reconstruction remain release
  requirements. Current local emulator hashes are recorded; they do not fulfill
  that reconstruction requirement by themselves.

The existing clean-build order expects SYSBUILD metadata prerequisites before
utility assembly. The new distribution orchestrator explicitly builds boot,
stage-one, and RSX-selector artifacts first, inside the isolated snapshot. No
existing development builder was changed.
