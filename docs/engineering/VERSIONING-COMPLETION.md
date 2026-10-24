# Versioning implementation completion

All 51 registered components now have selected input maps: 38 utilities, five
subsystems and eight loadable modules. The authoritative registry supplies their
identities; `component_registry.py --check` checks both TSV projections and the
three generated subsystem version includes. ZSM4 and LINK retain upstream
identities and have no BetterCP/M revision. WARM's disk placement is unchanged.

The maps cover owned source, assembler includes, source generators, selected
registry fields, relevant embedded component identities and toolchain hashes.
Some shared closures are deliberately conservative: a shared edit can require
review even when it produces identical bytes. Own revision is outside its own
input fingerprint. Revision assignment still compares executable bytes using
the same revision and display state; an unchanged executable keeps its revision.
No counters advance merely because a build runs or an input map changes.

## Build and acceptance workflow

`component_inputs.py COMPONENT --assembler PATH` captures inputs. Target,
profile and cross/native mode are separate variant fields. Native capture also
requires `--build-mode native --toolchain linker=PATH`, with the actual ZSM4
binary as assembler. Checked profiles bind their validated build context.
The installed catalog covers 97 supported default cross variants. Other
variants remain development/unknown until explicitly accepted; the catalog is
an input comparison reference, not execution qualification.

For a builder without its own guarded report, use:

```sh
python3 tools/component_tracking.py utility:BYE \
  --assembler "$HOME/bin/z80asm" \
  --artifact build/z80pack-tools/BYE.COM \
  --output build/z80pack-tools/BYE-build-report.json \
  -- python3 tools/build_z80pack_bye.py
```

The wrapper captures before/after inputs, effective invocation, target/profile,
assembler/linker binaries, display selection, actual output checksum and Git
provenance. Native mode uses `--native --linker PATH` and the existing native
builder command after `--`. Native source media carry prepared identity and
input fingerprint data; CP/M does not need Git. Different invocation flags are
inputs and therefore require their own accepted reference. Missing provenance
stays null rather than inventing a commit.

`component_revision.py plan` and `accept` retain their artifact comparison
workflow. `accept --install-baseline metadata/component-baselines.json` can
install the verified final input record explicitly. No normal build changes
registry counters or accepts a new baseline automatically.

## Disk and package records

Distribution and Utilities reports include provisional external disk records
bound to final image checksums and actual included component artifacts. Existing
checksum-matched build records preserve cached identities and original source
provenance. Collection builds record produced artifacts; the source identity
checks around distribution builds guard the generation. Upstream tool versions
and redistribution companion checksums remain separate.

`release_metadata.py disk --report REPORT --image IMAGE --output RECORD`
creates an immutable external record. `--freeze` additionally requires a full
source commit and original component build provenance; it refuses to relabel
unrecorded legacy artifacts. `release_metadata.py package --version VERSION
--revision REVISION --disk RECORD --output PACKAGE` references exact frozen disk
records and final image checksums. Records cannot be overwritten with different
content and contain no self-checksum. Freezing records does not assert release
qualification. No core/package 1.0 selection or release disk is frozen here.

Checked compatibility identity now binds resident/loader inputs, configuration,
epochs and tools without changing when unrelated utilities, tests or utility
counters change. Carrier formats and callable APIs remain unchanged.

## Direct validation

The complete default component build succeeds. All 51 previously inventoried
artifacts are byte-identical to the PR #496 inventory, so this completion batch
requires no revision increments. The guarded BYE launcher and collection build
records were exercised. Component versioning checks and direct manifest tests
pass; no parser, filesystem behavior, emulator or compression campaigns were
rerun. All 97 installed default cross baselines match current inputs.

A full Utilities disk rebuild could not run in this reconstructed checkout:
`third_party/zsm4/provenance.json` is absent. Manifest checksum, cached provenance,
immutability and package-reference behavior are covered directly. Native
execution, checked-profile execution and release acceptance are not claimed by
this work. The versioning implementation is complete; those remain ordinary
build/release qualification activities.
