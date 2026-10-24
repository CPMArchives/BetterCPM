# cpmsim build integration: maintained streaming command stages

24 October 2026. Third integration checkpoint; ready for maintainer review.
The maintainer requested push and continuation after the
[profile-input checkpoint](CPMSIM-BUILD-PROFILES.md). Its commit `55aef33` was
already on GitHub and was verified before this work began.

## Implementation

The streaming command loader now has maintained assembly sources:
`src/system/command-stage1.mac` and `command-stage2.mac`.
`tools/build_checked_command_loader.py` assembles them directly through the
selected generated profile inputs. It imports no assessment modules, applies
no textual instruction/section patches and modifies no source files.
Historical P9/CR9/CR10 labels remain for symbol-based observers and fixtures.

Stage 1 obtains its expected stage-2 checksum as a generated assembler constant.
The builder emits two private carriers with the same checked layout as the
prototype: 1,024 bytes for stage 1, and 2,048 for stage 2. The payloads remain
54 and 1,301 bytes respectively. Stage 2 occupies raw records 84–99; its
stack/header/record-buffer boundaries remain `0D00h`, `1000h` and `1600h`, with
the prospective payload floor at `1680h`. There is no additional memory charge.

`checked_build_contract.py` supplies a shared private identity for forthcoming
ordinary component builders. It verifies the prepared profile, exact source
closure, generated layout/flags and assembler hash before computing the ID.
That contract includes all source, tools, metadata and retained third-party
inputs, profile/format epochs and scratch/command-loader choices. Documentation
revision labels do not change an otherwise identical private contract.

The ordinary stage-builder CLI accepts its ID only from this verified contract.
Its lower-level assembly function also supports reference-ID fixtures so the
migration can be compared byte for byte with the earlier qualified artifacts.
Those fixtures are test products. No existing prototype private ID is reused
as the identity of a newly prepared build.

| Profile | New component-build ID | Stage 1 payload | Stage 2 payload |
| --- | --- | ---: | ---: |
| `cpmsim-fullram` | `3e37cb0a3b7a6cf74f1eadedfcbbf4f5` | 54 | 1,301 |
| `cpmsim-legacy-checked` | `2d43ab5ac7a837ac82cbe7ad6e7708cb` | 54 | 1,301 |

The generated profile flags now also define the checked resident CRC,
identity-compare, identity-data and rollback-pointer addresses. Implementing
those resident services through the ordinary build remains subsequent work.
Their definitions alone do not make a prepared workspace a runnable checked OS.

## Verification

All checks passed:

- **63 emitted-code cases per profile:** 21 stage-1 admission cases and 42
  streaming CCP/CPX admission cases, for 126 cases across both layouts.
- **11 profile/contract tests**, including modified source, metadata, unexpected
  input files, assembler mismatch, distinct profile identities and stable IDs
  across documentation-only revision labels.
- **13 existing distribution tests.**
- Each profile independently reproduced all four stage binaries/carriers.
  Source integrity and prepared-cache reuse still passed after compilation.

The component harness executes actual emitted Z80 instructions with controlled
resident I/O, CRC and identity-comparison services. It tests successful private
CCP/private CPX/public CPX relocation and entry publication, foreign IDs,
corrupt code/tails/checksums, invalid format/class/relocation/lifecycle/header
fields, truncated reads, I/O errors, ignored record padding, exact workspace
floor admission and refusal one byte below it. Failed loads preserve the
allocation boundary, and guards above that boundary remain intact. A public
CCP carrier is explicitly rejected. These are component tests; their service
stubs do not establish native BDOS/BIOS stack bounds.

Under each layout's earlier reference ID, all four generated artifacts—stage-1
binary/carrier and stage-2 binary/carrier—are byte-identical to the qualified
reconciled prototype. Under the new IDs, stage 2's executable bytes still match;
private IDs and the corresponding stage-1 expected checksum change as intended.
This connects the maintained sources to the accepted implementation without
claiming a newly integrated live OS image.

The default cpmsim distribution also rebuilt and boot-qualified successfully.
Its 30-file, 368,640-byte image remains byte-identical to the previous checkpoint,
SHA-256 `d806fa1911fa18623f9d7495d561cae57d6623bb66fbe68e85f3b355a866ee96`.
Filesystem, file-integrity and CONFIG fingerprint checks passed. This increment
did not repeat live Model 4 qualification; the prior host-launch limitation
remains recorded in the profile-input checkpoint.

The [machine-readable evidence](CPMSIM-COMMAND-LOADER-INTEGRATION.json) preserves
the 1,088-file input closure, contracts, artifact hashes, individual component
case results, reference equality, repeat checks and default distribution result.
The implementation was tested on parent `55aef33` plus those exact recorded
working-tree input bytes. The checkpoint commit preserves those bytes.

## Reproduction and remaining work

Prepare a fresh workspace as described in the profile-input checkpoint. From
its `WORK/profiles/PROFILE/z80pack/` directory:

```sh
export BETTERCPM_BUILD_CONTEXT="$PWD/build/profile/context.json"
python3 tools/build_checked_command_loader.py
python3 tools/test_checked_command_loader.py --reference /path/to/reconciled-reference-profile --output "$PWD/build/z80pack/command-loader/qualification.json"
```

The test command requires the matching earlier full-RAM or legacy checked
reference profile, including its stage products and `assessment-profile.json`.
Its `reference-id-stages` output directory must be fresh. The component builder
requires a fresh output directory; `--output` can select another one for repeat
comparison. No command carrier or distribution image is created by this builder.
HELLO fixtures remain excluded from distribution.

The next bounded increment should migrate the checked resident services and
RSX reconstruction path into maintained ordinary sources/builders. Direct
command/RSX carrier generation, checked package/install/export, private utility
gates and full distribution publication/acceptance still require integration.
The historical assessment route remains a reference until that migration is
qualified. This checkpoint neither changes the accepted core 1.0 (`3b2d2d7`)
nor reopens the completed engineering assessment. Its measured two-byte BDOS
stack margin remains an existing qualification limit.
