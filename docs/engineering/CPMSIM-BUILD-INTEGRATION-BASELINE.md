# cpmsim normal-build integration: reconciled baseline

23 October 2026. First integration checkpoint; ready for maintainer review.
Normal-build integration is in progress. The engineering assessment remains
closed, and this is not another numbered assessment part.

## Reconciliation result

The maintainer authorized normal-build integration after approving the completed
prototype. The starting revisions are:

| Role | Revision |
| --- | --- |
| Accepted core 1.0 | `3b2d2d7f4fe0472438465165f11fb550d79c8662` |
| Approved prototype branch | `81e181218bffe0aef3f05d66f17e88c82bd19579` |
| Current main, pinned and rechecked | `4c37c7f68ca856eb3f17643ecdc8f43fb95289e6` |
| Reconciled integration baseline | `a1204c36b6ec4787c12b11141c4a7baff555631f` |

Main already contains the prototype implementation and completion evidence
through `9703b84`. Only the subsequent approval record was missing. The new
`integration/cpmsim-builds` branch joins current main and the approved prototype
with a two-parent merge, applying that documentation change without conflicts.
Current main's compression utilities, utility-version work, Utilities Disk
builder changes and NOAH specification are preserved. This checkpoint changes
no implementation source and does not alter the accepted core 1.0 baseline.

Compared with the approved prototype, the private build input closure grows
from 1,040 to 1,073 files: 33 additions, eight modifications and no removals.
Those changes belong to the compression/utility work. Since the compatibility
contract conservatively hashes all those inputs, the private IDs change even
though the checked OS implementation does not. Old private products must not
be mixed with these newly built products.

## Verification of the combined baseline

Fresh builds used the existing guarded prototype builder. These are reference
products for the upcoming migration; the normal distribution builder does not
yet offer the proposed profile switches.

| Profile | New private ID | Unloaded maximum COM | With ANSISCRN + ADM3A |
| --- | --- | ---: | ---: |
| `cpmsim-fullram` | `c49c6144b0676fc856054be08e4773ba` | 57,344 bytes / 56 KiB | 54,272 bytes / 53 KiB |
| `cpmsim-legacy-checked` | `6bf1ad1aeac7e36ac0249050f70da12c` | 54,272 bytes / 53 KiB | 51,200 bytes / 50 KiB |

Both are RAM cpmsim profiles; the legacy comparison is not a Model 4 image.
The full-RAM gain remains 3,072 bytes. All checks below passed:

- Source closure, private bindings and manifest audit; 30 distribution files
  per profile, excluding HELLO.RSX, HELLO.CPX and STATEFUL.RSX.
- A separate full-RAM build reproduced all 35 audited artifacts exactly.
- Eleven live loader/boundary cases per profile, including maximum-size COM,
  rejection of the next 128-byte record, four warm-return routes, malformed
  command carriers and bad boot-loader components.
- Per profile: 57 utility-entry gate cases, seven CONFIG entry/preflight cases,
  three native-packager refusals, and a live cross-profile utility campaign.
- Per profile: ordinary-simulator smoke/configuration/export checks and two
  lifecycle cases, including five early refusals with preserved state.
- Per profile: four observed disk-error cases covering Ignore and Abort with
  ADM3A reverse video and ANSI reverse video in a scrolling region. BDOS stack
  use reached 36 and 38 bytes respectively within its 40-byte allocation.

For each layout, BDOS (3,454 bytes), the gateway (248), streaming stage 2
(1,301), resolver (738) and repaired ANSISCRN payload (1,365) are byte-identical
to the corresponding approved build. Bound carriers and complete images do
change with their new private IDs. Clean image hashes remained unchanged by
the test campaigns, which operate on copies.

This is targeted reconciliation verification, not a rerun of the entire
prototype acceptance campaign or qualification of the compression utilities.
The earlier measured two-byte BDOS stack margin remains a limit to track;
these cases do not prove every possible callback or application path safe.
Machine-readable results, artifact hashes, source changes and the staged-file
inventory are in [the baseline evidence](CPMSIM-BUILD-INTEGRATION-BASELINE.json).

## Normal-build migration contract

The intended ordinary entry points are:

```sh
python3 tools/build_distribution.py --target z80pack --profile cpmsim-fullram
python3 tools/build_distribution.py --target z80pack --profile cpmsim-legacy-checked
```

These are planned commands, not currently implemented options. Existing
invocations retain their present behavior during integration. Checked profiles
must reject unsupported target combinations, including `trs80gp` and `all`,
instead of falling back to a different layout or building an unqualified ROM
product. Changing release defaults requires a later explicit adoption decision.

The current prototype modifies 29 existing staged input files. The exact list
is preserved in the evidence. Normal integration must replace those mutations
with explicit build choices and generated inputs:

| Area | Required migration |
| --- | --- |
| Profile and layout | One validated profile description supplies platform, RAM mode, layout, capacities and format epochs to Python helpers and assembler inputs. Parent-process imports and child builders must select the same profile. |
| Loader and reconstruction | Promote checked entry, reader, compatibility/CRC checks, compact reconstruction and streaming command loading into maintained source choices; preserve existing bounds and failure behavior. |
| Carriers and packages | Generate private bindings and selected carrier/package formats directly in ordinary builders. Preserve public/private distinctions, checked export/install behavior and cross-profile rejection. |
| Utilities | Retain CONFIG, SYSGEN and STAT private-entry gates, public operations, dynamic CLS dispatch and explicit native-packager refusals. Replace assessment-specific version labels with ordinary version metadata. |
| Distribution and cache | Key build state, generated inputs, outputs and publication paths by profile. Preserve manifest selection, fixture exclusions, hash-verified cache reuse and qualification before publication. |

Isolated source copies may remain useful. Builders must not rewrite either the
repository's source or its staged source copies to select a profile. Generated
layout/constants and assembly output belong in build directories. Existing
deliberate code-generation helpers can remain where their inputs and profile
choices are explicit; simply renaming an assessment patcher is insufficient.

## Remaining bounded increments

1. **Profile plumbing and layout selection.** Add the validated profile model,
   generated layout/constants and propagation through shared build helpers.
   Prove selected addresses, unsupported-combination rejection, distinct cache
   identities and unchanged existing default behavior. Pause for review.
2. **Checked implementation and artifact generation.** Move the checked
   loader, reconstruction, binding, package and utility choices into ordinary
   sources/builders. Compare with this reconciled reference; explain any binary
   difference and repeat the affected functional/stack checks. Pause for review.
3. **Distribution qualification and adoption review.** Complete the ordinary
   entry points and profile-specific publication. Repeat both-profile acceptance,
   cache/repeat checks, package install/export and fixture-exclusion checks;
   verify existing Model 4/default builds remain usable. Document supported
   invocations and retire the prototype patch route from the production path.

If an increment proves too large, split it before execution to preserve the
maintainer's requested credit-review pauses. Model 4 upper-RAM recovery, new ROM
or native-packager support, future feature defaults and architectural redesign
remain separate work. No switch to Astra is indicated for the next profile
plumbing increment; flag a difficult architectural decision if one emerges.

## Reproducing this checkpoint

Check out `a1204c36b6ec4787c12b11141c4a7baff555631f` and use the pinned environment
in [the prototype reproduction record](CPMSIM-PROTOTYPE-REPRODUCTION.md).
Use fresh directories for full-RAM, legacy-checked and repeated full-RAM builds.
Run its three build commands and `audit_part11_builds.py`, then run
`qualify_part11_live.py` and `qualify_part12_utilities.py --live` in both layout
directions. Run `qualify_cpmsim_completion.py` for each profile with the ordinary
simulator, `--untraced --campaign smoke`, then `--untraced --campaign lifecycle`.
Use the pinned observer with `--campaign faults` and
`--match 'ADM3A-reverse|ANSI-region-reverse'`. Run simulator campaigns sequentially because
their auxiliary FIFOs are shared. Expected IDs are those in this record, rather
than the older prototype IDs. The evidence records exact executed commands.
