## BetterCP/M 1.0: Make the z80pack/cpmsim Qualification Environment Reproducible

BetterCP/M 1.0 currently uses `z80pack/cpmsim` as one of its two required qualification platforms, but this is **not stock cpmsim**. BetterCP/M development has added emulator-side functionality, including the disk-geometry extensions required by the BetterCP/M z80pack platform and the ROM-qualification instrumentation already represented by `tools/cpmsim-rom-qualification.patch`.

This must be made a formal part of the BetterCP/M 1.0 release process.

**Status:** Accepted 1.0 release requirement; implementation pending.

### Goal

Make it possible for another developer, starting from an identified upstream z80pack revision and the BetterCP/M repository, to reconstruct the **exact cpmsim environment used to qualify BetterCP/M 1.0**.

Reproducibility means pinned source, an identified ordered patch series, declared
build inputs/options, and repeatable qualification behavior. It does not require
identical executable bytes across different hosts or compiler versions. Record
and qualify each resulting executable by its own hash; a reconstructed binary
does not inherit another binary's qualification merely because its source matches.

Do not redesign the z80pack target or cpmsim integration. Preserve current working behavior. This task is about provenance, packaging, reproducibility, documentation, and release qualification.

### Existing Relevant Material

Inspect the current repository before making changes. Relevant material already includes at least:

- `src/platform/z80pack/README.md`
- `src/platform/z80pack/`
- `tools/cpmsim-rom-qualification.patch`
- `tools/test_cpmsim_rom_guard.py`
- `tools/test_z80pack_rom_xip.py`
- `tools/test_z80pack_rom_boot.py`
- `tools/build_z80pack_image.py`
- `tools/build_z80pack_boot.py`
- `docs/engineering/CPMSIM-ROM-QUALIFICATION-ASSESSMENT.md`
- the BetterCP/M 1.0 roadmap, implementation contracts, release-readiness material, and backlog

The current z80pack README states that variable-format media require the BetterCP/M cpmsim geometry interface from the `bettercpm-disk-geometry` branch of the companion z80pack repository. A branch name alone is not sufficient provenance for a reproducible 1.0 qualification environment.

Historical engineering material also records z80pack revisions used at various stages. Do **not** assume one of those is automatically the correct final base revision. Determine the actual provenance of the current BetterCP/M cpmsim modifications.

### Required Work

#### 1. Identify the exact z80pack provenance

Determine:

- the upstream z80pack repository used by BetterCP/M;
- the exact upstream commit from which the BetterCP/M cpmsim changes derive;
- the current BetterCP/M-specific emulator changes required for ordinary z80pack operation;
- the disk-geometry changes required by the BetterCP/M platform;
- the ROM-qualification changes;
- any other cpmsim changes on which current BetterCP/M tests depend.

Distinguish clearly between:

- ordinary BetterCP/M runtime requirements;
- BetterCP/M qualification-only instrumentation;
- changes that belong entirely inside BetterCP/M rather than z80pack.

Do not silently depend on the maintainer's local z80pack checkout.

#### 2. Create a reproducible patch set

Represent the required z80pack/cpmsim modifications as a clean patch series against one exact upstream revision.

Prefer a structure similar to:

```text
third_party/z80pack/
    README.md
    UPSTREAM.txt
    patches/
        0001-...patch
        0002-...patch
        ...
```

If another repository location better matches existing BetterCP/M organization, use it, but keep the result obvious and self-contained.

Where practical, use a normal Git patch series rather than one undifferentiated diff. Separate logically distinct changes—for example disk-geometry support and ROM-qualification instrumentation—unless the actual history or dependencies make another division more accurate.

The existing `tools/cpmsim-rom-qualification.patch` may be incorporated, replaced, or retained as appropriate, but there must be **one clearly documented authoritative process** for constructing the qualification emulator.

#### 3. Record the upstream base precisely

Add machine-readable or plainly documented provenance containing at least:

- upstream repository URL;
- exact upstream commit SHA;
- any upstream release/tag corresponding to that SHA, if applicable;
- BetterCP/M patch-set identity;
- expected disk-geometry interface version;
- qualification options such as `ROM_QUALIFY=YES`;
- any build prerequisites that materially affect reproducibility.

The builder must extract committed files at the exact pinned SHA into a private
source tree, using the supplied local Git repository as an object source. Its
current branch and working-tree contents need not match that SHA and must not
be copied into the build. Fail clearly if the pinned commit is unavailable or
patch application fails. Confirm the pinned commit's upstream provenance before
freezing the release.

Do not treat "latest z80pack" as an acceptable base.

#### 4. Provide an automated reconstruction/build path

Add a script or equivalent reproducible procedure that can:

1. verify that the exact pinned upstream commit is available;
2. extract that commit into a private source tree;
3. apply the BetterCP/M patch series;
4. build cpmsim and required helper programs, including `cpmrecv` and `cpmsend`;
5. run basic environment validation;
6. produce an environment manifest.

Prefer using an existing local upstream checkout rather than requiring network access at test time, unless existing BetterCP/M tooling already has a different established policy.

The script should not modify the user's upstream source tree in place.

Provide explicit ordinary-runtime and ROM-qualification build profiles. Record
which patches and options each profile uses. Account for stack-measurement
instrumentation as well as ROM protection in the qualification profile.

A name such as the following is reasonable, but use repository conventions:

```text
tools/build_qualified_cpmsim.py
```

#### 5. Emit qualification provenance

The reconstructed environment should produce or permit generation of a manifest containing enough information to identify it later, including where practical:

```text
upstream z80pack repository
upstream commit SHA
BetterCP/M source revision
BetterCP/M cpmsim patch-set identity/hash
host operating system and architecture
compiler/build-tool identification and effective build flags
cpmsim executable SHA-256
cpmrecv and cpmsend source identity and executable SHA-256
disk-geometry interface version
ROM qualification support present/absent
qualification build options
```

The final BetterCP/M 1.0 evidence package should be able to record this information.

Do not make the cpmsim executable hash the sole identity: source provenance and
patch identity are required. Record the ordered patch filenames and hashes, plus
a combined patch-set identity. Final qualification uses a committed BetterCP/M
revision and records the actual executables, launch configuration, environment
options, and test media used.

#### 6. Test reconstruction, not merely patch existence

Add an automated test that proves the documented process works from the pinned upstream source.

At minimum verify:

- patches apply cleanly;
- cpmsim builds;
- BetterCP/M's required disk-geometry interface is present;
- the normal BetterCP/M z80pack boot path works;
- existing disk/interchange tests remain valid as applicable;
- the ROM qualification build can be produced;
- the existing ROM guard primitive tests pass;
- the protected-XIP qualification path still works.

Run this qualification as bounded stages:

1. pinned-source extraction, patch application, and emulator/helper builds;
2. geometry-interface validation and ordinary BetterCP/M boot;
3. applicable disk/interchange tests;
4. ROM guard primitive tests;
5. protected-XIP integration qualification.

Retain stage logs, manifests, and failure artifacts. Stop at the first failed
stage and use a targeted probe before broadening the investigation. A failure
must not force successful earlier stages to be repeated unless their inputs
change or the failure casts doubt on their results.

Reuse the existing test infrastructure rather than duplicating it unnecessarily.

The objective is to prove that the **published reconstruction procedure recreates the actual environment**, not simply that a patch file exists.

#### 7. Update platform documentation

Revise `src/platform/z80pack/README.md` and other relevant platform documentation so that they no longer refer merely to a private branch such as `bettercpm-disk-geometry`.

They should point to the reproducible BetterCP/M patch/provenance mechanism and explain:

- that BetterCP/M's required cpmsim is based on a pinned z80pack revision;
- which changes are required for ordinary BetterCP/M z80pack operation;
- which additions are qualification-only;
- how to reconstruct the emulator;
- how to verify the result.

#### 8. Make this a BetterCP/M 1.0 release requirement

Update the authoritative 1.0 project material so that reproducibility of the modified cpmsim environment is explicitly release-gating.

At minimum inspect and update as appropriate:

- `docs/releases/1.0-ROADMAP.md`
- `docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md`
- `TODO.md`
- release/qualification documentation
- relevant platform and engineering documents

The contract should establish that a BetterCP/M 1.0 z80pack qualification is not complete merely because it passed on the maintainer's local cpmsim binary.

The release evidence must identify and permit reconstruction of the exact emulator environment used for qualification.

A suitable principle is:

> BetterCP/M 1.0 qualification on z80pack/cpmsim attaches to a reproducibly reconstructible emulator environment consisting of a pinned upstream z80pack revision, the recorded BetterCP/M patch set, documented build options, and the resulting qualification configuration.

Do not reopen already frozen BetterCP/M architecture to accomplish this. Treat it as release-environment provenance and qualification work.

#### 9. Review README wording

The top-level README currently describes the target as z80pack `cpmsim`. Update wording if necessary so it does not imply that stock upstream cpmsim alone supplies the qualified BetterCP/M environment.

Keep this concise. Detailed reconstruction belongs in the platform/build documentation.

#### 10. Licensing and redistribution

Check the applicable z80pack license before deciding exactly what to distribute.

Prefer:

- upstream source provenance;
- BetterCP/M-owned patches;
- build/reconstruction scripts;

unless redistribution of a complete modified source tree or binaries is clearly permitted and provides additional value.

Do not import or redistribute upstream material unnecessarily.

### Acceptance Criteria

This task is complete when all of the following are true:

- the exact upstream z80pack base is pinned;
- every required BetterCP/M cpmsim modification is accounted for;
- the modifications exist as a documented reproducible patch set;
- a clean reconstruction can be performed without depending on the maintainer's existing patched checkout;
- the reconstructed cpmsim passes the applicable BetterCP/M z80pack and ROM-qualification tests;
- the resulting environment has recorded provenance and hashes;
- BetterCP/M documentation accurately distinguishes upstream cpmsim from the BetterCP/M-qualified variant;
- the 1.0 release contracts explicitly require reconstruction/provenance of the cpmsim qualification environment;
- existing BetterCP/M behavior and the frozen 1.0 architecture are unchanged except where repository/build plumbing is necessary for this reproducibility work.

### Important Constraint

BetterCP/M 1.0 is close to completion. Avoid unrelated cleanup, architectural redesign, or opportunistic refactoring. Make the smallest coherent set of changes necessary to turn the currently private/custom cpmsim dependency into a **reproducible, inspectable, release-qualified development environment**.