# cpmsim build integration: explicit profile inputs

23 October 2026. Second integration checkpoint; ready for maintainer review.
This implements the profile/layout increment described in the
[reconciled baseline](CPMSIM-BUILD-INTEGRATION-BASELINE.md).

## Implemented behavior

The ordinary distribution tool now accepts `--profile cpmsim-fullram` and
`--profile cpmsim-legacy-checked`, with `--prepare-profile --work DIRECTORY` to
prepare an isolated workspace. A validated profile defines its target, RAM
ceiling, reserved bytes, resident-address adjustment, checked format epochs,
command-loader contract and reconstruction workspace capacity.

Preparation copies source unchanged and writes three generated inputs under
the workspace's `build/profile/`: `context.json`, `layout.inc` and `profile.inc`.
Resident addresses move by an explicitly classified set of symbols. Transient
addresses, counts and carrier capacities retain their specified values. A new
unclassified numeric layout symbol causes an error so its treatment must be
decided explicitly. Derived assembler expressions remain expressions.

`system_layout.py` verifies the selected context before exporting Python
addresses or expanding assembler includes. Both consumers use the same
generated layout. `BETTERCPM_BUILD_CONTEXT` selects the context before import;
subprocesses inherit it and verify it against their own source workspace.
A foreign workspace, stale canonical source, altered manifest or modified
generated include is rejected.

Prepared workspace paths are `WORK/profiles/PROFILE/z80pack/`. Existing default
builds retain `WORK/z80pack/` and `WORK/trs80gp/`. Preparation records the profile
in its input identity and hashes the complete staged source and generated input
inventory. `--reuse-work` verifies the file set and recorded bytes, rejecting
added, removed, changed or cross-profile inputs. Component outputs in `build/`
do not invalidate unchanged prepared inputs. The preparation stamp is separate
from a completed distribution build stamp.

## Supported commands

Run from the repository root, using a fresh work directory:

```sh
python3 tools/build_distribution.py --target z80pack --profile cpmsim-fullram --prepare-profile --work /tmp/bcpm-profiles
python3 tools/build_distribution.py --target z80pack --profile cpmsim-legacy-checked --prepare-profile --work /tmp/bcpm-profiles
```

The tool prints the workspace and context paths. Select the context before
starting layout-dependent builders. For example:

```sh
cd /tmp/bcpm-profiles/profiles/cpmsim-fullram/z80pack
export BETTERCPM_BUILD_CONTEXT="$PWD/build/profile/context.json"
python3 tools/build_z80pack_image.py --resident-only --ram-only --system-tracks-only
```

This assembles resident components through the ordinary builders and stops
before constructing a bootable disk. Use a separate shell, or unset
`BETTERCPM_BUILD_CONTEXT`, before running distribution selection again. Python's
`context_environment()` helper supplies the verified selection to subprocesses
without changing the parent's environment.

Preparing either checked profile for `all` or `trs80gp` is rejected before
creating output. Selected contexts also refuse the full-system, full-disk and
Model 4 boot entry points that have not been integrated for these profiles.
Existing default distribution commands continue to build normally.

Full checked disk generation is unavailable at this checkpoint. The checked
loader, reconstruction, carrier, package and utility choices still need
migration from the prototype patch route. Profile epoch constants declare
the intended contract; they do not mean those formats have already been
emitted by ordinary builders. Context manifests identify their present status
as layout preparation.

## Verification

All nine new profile tests and thirteen existing distribution tests passed.
They cover qualified addresses/capacities, Python/assembler/child-process
agreement, context and source drift, cache separation, added/modified inputs,
unsupported combinations, and refusal of unintegrated disk paths.

Both final prepared profiles compiled BDOS, platform BIOS, disk services,
extension services, configuration overlay, disk tables and gateway. For each
layout, BDOS (3,454 bytes), gateway (248) and shared file loader (145) match the
corresponding reconciled reference binaries exactly. The staged source closure
remained unchanged after compilation; verified cache reuse passed afterward.

| Prepared profile | RAM end | BDOS base | Maximum record-aligned COM capacity |
| --- | ---: | ---: | ---: |
| `cpmsim-fullram` | `10000h` | `E2BCh` | 57,344 bytes / 56 KiB |
| `cpmsim-legacy-checked` | `F400h` | `D6BCh` | 54,272 bytes / 53 KiB |

These selected capacities match the earlier live reference measurements. This
increment does not claim new live TPA measurements of checked distributions.

The ordinary default cpmsim distribution was built and boot-qualified before
and after the implementation, and again after incorporating current main.
All 368,640-byte images have SHA-256
`d806fa1911fa18623f9d7495d561cae57d6623bb66fbe68e85f3b355a866ee96`.
Filesystem, file integrity, CONFIG fingerprint and boot checks passed, with 30
selected files. Hash-verified default cache/publication reuse also passed.

The ordinary default Model 4 disk built and passed filesystem, file integrity,
CONFIG fingerprint/cold-patch and DMK structural checks. Its 1,020,496-byte
image is identical to both pre-change candidates, SHA-256
`fd2873d3c1ac3c428ef1ba1bc290d015167cf50961c49f0b348cef88b628d642`.
Live Model 4 boot qualification could not be repeated: the unchanged reference
failed through macOS LaunchServices with `kLSNoExecutableErr`, and the existing
direct-launch option aborted with SIGABRT. No launcher changes were made here.

During this increment, main advanced to
`22d27e863b0e810ff5a6f970432bcc29cb3acbf1`, merging the previous integration
checkpoint and the initial NOAH/LBR implementation. The old integration branch
was deleted remotely. Those 15 incoming files do not overlap this implementation.
They were incorporated by a clean fast-forward, preserving the local work.
Profile tests, prepared component builds and default image checks were repeated
on that combined baseline. The new branch is `integration/cpmsim-profile-inputs`.

The [machine-readable evidence](CPMSIM-BUILD-PROFILES.json) retains exact source
closure hashes, generated manifests, binary hashes, default distribution
results and host-launch failure records. Final builds used main `22d27e8` plus
the recorded implementation input bytes; this checkpoint commit preserves those
same bytes. No CP/M implementation source under `src/` changed in this increment.

## Next bounded increment

Promote checked loader, reconstruction and artifact-generation choices into
maintained ordinary sources/builders, using these profile inputs. Preserve
private binding, streaming bounds, rollback, utility gates and native-packager
refusals. Compare against the reconciled prototype reference and repeat
affected functional and stack checks before another review pause. Full
distribution acceptance and publication adoption follow that migration.
The two-byte observed BDOS stack margin remains a qualification limit.
The accepted core 1.0 baseline remains `3b2d2d7`.
