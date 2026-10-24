# Component registry import

Status: first implementation increment, 2026-10-24; not an executable migration.
Source baseline: main `3dcc71fda7c92e4ec779f3b80ddc1b40327d8db4`.

`metadata/component-registry.json` is the authoritative identity catalog.
It imports 36 utility identities without advancing their counters and records
the five subsystem and eight additional loadable-module identities with initial
revision 001. Initial tracking begins here; these numbers do not describe older
artifacts. MOVE and WARM remain pending with null version/revision fields.
The identity accessor rejects pending assignments. ZSM4 and LINK have no rows.

RCP's canonical catalog version remains 1.0 (015). The existing carrier 0.2
conflict is recorded and not silently fixed in this increment. Module builders
still embed their previous implementation values; moving them to the registry
and embedding revisions requires the subsequent executable migration. No
existing artifact is relabeled as revision 001 by this import.

## Authority and compatibility projections

Edit identities in the registry. The existing TSV files are retained unchanged
as generated compatibility views, not additional authorities:

```sh
python3 tools/component_registry.py --check
python3 tools/component_registry.py --write
```

`--check` refuses stale views; `--write` explicitly updates them. Neither command
increments a counter. The legacy `build` column preserves its spelling for
existing consumers but means the imported independent revision. The registry
contains each subsystem version/API value once, referenced by the legacy-row
projection; planned services and the old aggregate milestone row are retained
as legacy descriptive records, not assigned independent components.

`tools/utility_versions.py` and `tools/version_metadata.py` now read registry
projections. Existing banner formatting, manager includes, resident descriptor
and utility identities are preserved exactly. Automatic generation of the TSV
views is intentionally explicit rather than a side effect of importing a module.
The check command is available for future CI integration; this increment does
not claim that every existing build command already checks stale views.

## Ownership and remaining implementation

Each entry records source roots, builders and placement imported from the
reviewed audit. These are ownership hints; selected-input closures are still
pending. Do not feed these roots or the conservative audit graph directly into
revision enforcement. The next increment must resolve mixed resident sections,
function-selected shared source and generated linkage, then implement per-variant
input records and development fingerprints. There is no clean/dev classifier
or revision-baseline acceptance operation in this increment.

The registry gives newly tracked identities their initial counters, but does
not create new API revisions, invent a core release, alter the frozen core 1.0
manifest, or select a core for release package 1.0. Development core wording,
normal numeric revision formatting, module revision embedding and the checked
banner correction remain executable migration work.

Important checked-build limitation: the existing private compatibility stamp
hashes broad metadata and tool inputs. Adding this registry and its readers
therefore affects freshly prepared checked contracts. The output-equivalence
checks here establish ordinary generated identity text equivalence, not checked
carrier byte identity or qualification. No checked carriers, native binaries,
disk images or release manifests were rebuilt or published. Narrow and validate
that contract dependency closure before claiming independent checked tracking.

## Validation

Eight focused tests cover import completeness, source/builder paths, exact TSV
projections, pending assignment refusal, independent lookups, continuing counters,
four-digit revisions, malformed identities/paths, duplicate JSON keys and
projection membership. Before/after comparison against the pre-import readers
checks all ordinary utility banners, six codec query/help texts, DDT/BYE text,
subsystem descriptors and manager includes. The legacy TSVs, generated assembly
includes and frozen core manifest remain byte-identical.

```sh
python3 tools/test_component_registry.py
python3 tools/component_registry.py --check
```
