# Checked cpmsim distribution integration complete

Date: 24 October 2026. This closes the final planned normal-build integration
stage after [package/utility integration](CPMSIM-PACKAGE-UTILITY-INTEGRATION.md).
The source baseline is merged main `4bdc6c2`, including PRs #479 and #480.
Core 1.0 remains frozen at `3b2d2d7`.

## Result

The ordinary distribution command now builds complete checked cpmsim System
Disks for both `cpmsim-fullram` and `cpmsim-legacy-checked`, with matching
SYSTEM.SYS packages, private bindings and utility guards. The maintained
profile-aware component builders supply all software; no assessment source
patches or prebuilt assessment media are used. Both 30-file images pass
filesystem and file-integrity checks, CONFIG fingerprint/cold-IOBYTE checks,
simulator boot and the live acceptance campaigns below.

| Selected profile | Unloaded maximum COM | ANSISCRN + ADM3A | Compatibility ID |
|---|---:|---:|---|
| cpmsim-fullram | 57,344 bytes (56 KiB) | 54,272 bytes (53 KiB) | b5a00a8b62ef358ac39cd72dfbd17b17 |
| cpmsim-legacy-checked | 54,272 bytes (53 KiB) | 51,200 bytes (50 KiB) | fb153ae3933e28390db36b251b1da4c2 |

The full-RAM profile retains the complete 3 KiB gain. Neither resident allocation
nor the approved component behavior changes in this checkpoint. HELLO.RSX,
HELLO.CPX and STATEFUL.RSX are injected into disposable test copies only; none
is in either delivered System Disk. This integrates the existing System Disk
manifest; it does not declare the documentation or Utilities Disk finished.

## Build, cache and publication

Use an explicit profile and an isolated work cache:

```sh
python3 tools/build_distribution.py --target z80pack --profile cpmsim-fullram --work /path/to/work --output /path/to/distributions --simulator /path/to/cpmsim
python3 tools/build_distribution.py --target z80pack --profile cpmsim-legacy-checked --work /path/to/work --output /path/to/distributions --simulator /path/to/cpmsim
```

The checked subprocess selects its validated generated layout before importing
layout-dependent helpers. Its component driver builds the resident, carriers,
package, command utilities and catalogue; it composes the reserved tracks and
uses the ordinary manifest selection and filesystem builder. Selected targets
remain cpmsim RAM only. The legacy mixed-platform complete-system and ROM
entry points retain their scope guards; use the distribution command above.

A candidate is published only after its full qualification and a final source
identity check. Separate profile workspaces, generation names, image names and
named-image directories keep default, legacy checked and full-RAM products
apart. Each immutable generation contains its image, matching SYSTEM.SYS,
package contract, report and acceptance transcripts. Named copies live under
`build/z80pack/disks/library/PROFILE/`.

Repeat with `--reuse-work` only against the same source identity. Cache reuse
checks the exact input and generated-file inventories and every recorded hash.
Both profiles were rebuilt through this route, requalified, and reused their
identical immutable generations. Deliberately corrupting a cached stage carrier
was rejected by the real CLI in both profiles, preserving the published images.
Generic publication tests also reject damaged images/reports, and the new test
rejects a corrupt published SYSTEM.SYS rather than silently reusing it.

## Acceptance

Each layout passes 22 live simulator campaigns on isolated copies:

- Exact maximum-size patterned COM and the one-record oversized rejection;
  RET, JP 0, BDOS Function 0 and BIOS warm returns.
- Public CPX execution; stateful RSX movement, callable service preservation,
  failed loads and unload recovery; screen backend/personality loading.
- Payload, public-binding, old-format, truncation and late-CRC CPX rejection,
  with preserved state and a subsequent successful load.
- Corrupt raw command-stage code/identity and CCP halt before a prompt.
- Package and disk-source installation preserving the destination filesystem,
  followed by a cold boot of the installed target.
- Exact disk-to-package export; resealed incompatible/corrupt package refusal;
  missing/changed runtime-file refusal; declined installation preserving target.

Five additional live campaigns run in each cross-profile direction. Foreign
CONFIG, SYSGEN and STAT MEM are rejected, while public STAT operations and the
RSX/CPX/CLS paths work. Foreign packages, disk-source systems, RCP and RSX packs
are rejected with the destination unchanged. That is 54 distinct live campaigns
across the pair; repeat-build campaigns are not counted a second time.

The [checked export adapter](evidence/checked-export-adapter.py) runs the existing
export fault harness against each emitted checked SYSGEN binary. Only host
package/entry fixtures change; production instructions are not patched. Each
layout passes 24 export/file-publication fault cases and two entry-boundary
cases, including failed reads/writes, close/verification failure, rename failures,
partial namespace changes, backup cleanup and recovery-file preservation. This
is controlled machine-code evidence, alongside the successful live workflows.
It is not a guarantee of atomic installation or recovery after arbitrary power
loss/media failure.

All 27 profile/distribution unit tests pass. The old unit expectation that a
checked distribution must be refused was removed now that this operation is
supported; unsupported targets still fail before creating output. A development
probe caught indentation in the patterned-COM fixture's assembly; dedenting the
fixture fixed it. Source edits during development were rejected before
publication, as intended. Final evidence uses the frozen input hashes below.

The default cpmsim distribution rebuilt and boot-qualified with its 30-file,
368,640-byte image byte-identical to a separate merged-main baseline:
`75e0ae5e15972fc92579fe3924a28c9d32c7e23cc6431bd932b54ef0841a9c13`.
The common-builder Model 4 development image is also byte-identical. No new
Model 4 live-boot or complete Model 4 distribution qualification is claimed.

## Artifacts and limits

| Profile | System Disk SHA256 |
|---|---|
| Full RAM | 4ffb2fb1f6fc3ee96306748b5dde2c4d991454dc0bd3b2f70420b8b4c1e1b6e8 |
| Legacy checked | 0c09f06b81e41906efa511afc23c12fff84616646dea68aede058d96b07a7c3b |

[Machine-readable evidence](CPMSIM-DISTRIBUTION-INTEGRATION.json) records the
source closure, profile manifests, component/cache hashes, artifact reports,
per-campaign results, cross-profile and export-fault checks and default
comparison. Qualification used `4bdc6c2` plus the exact recorded working-tree
input bytes preserved by this checkpoint commit.

The first engineering assessment, bounded prototype and cpmsim normal-build
integration are complete within their approved scopes. This is a simulator RAM
qualification; Model 4 memory reclamation, ROM/XIP and native checked packaging
remain separate roadmap work. The previously observed two-byte BDOS stack
margin remains a limit; these campaigns do not establish an exhaustive whole-OS
stack or interrupt bound. No further cpmsim integration stage is being added.
