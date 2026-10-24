# Checked cpmsim prototype: reproduce the completion snapshot

Use implementation commit `8e0fcc48b57665ae9355ea643b930daf15407f6b`.
Subsequent documentation-only commits do not change the private input closure.
The acceptance bundle preserves that closure and the exact qualified products.
Do not substitute a development-stage image for a final `qualified-*` image.

## Environment and builds

This qualification used the existing macOS environment, Python 3.9, cpmtools,
z80asm 2.1 at `~/bin/z80asm`, and the pinned Part 2 ordinary cpmsim. The assembler
SHA-256 is `edc437faf8b685efe0d408aa18830d844eaf9393f6f1f030187ef720f75433fc`.
The ordinary simulator SHA-256 is
`b2d4384af06dbea8d32bc43eab539bf9e4857e74780577a249d0e8c5e22c955d`.
The independent CPU/screen tests also require pyte; the retained environment was
`/tmp/bcpm-dump-venv/bin/python`. The observer build additionally needs make, a C
compiler and macOS codesign. This is a reproduction recipe for that environment,
not a portable installer.

Run from the repository root. Output directories must be new. If necessary set
PYTHONPYCACHEPREFIX to a writable temporary directory before these commands.

```sh
python3 tools/assessment_checked_profiles.py cpmsim-fullram --carrier-bindings --streaming-commands --output /tmp/pc-full
python3 tools/assessment_checked_profiles.py cpmsim-legacy-checked --carrier-bindings --streaming-commands --output /tmp/pc-legacy
python3 tools/assessment_checked_profiles.py cpmsim-fullram --carrier-bindings --streaming-commands --output /tmp/pc-repeat
python3 tools/audit_part11_builds.py /tmp/pc-full /tmp/pc-legacy /tmp/pc-repeat --output /tmp/pc-build-audit.json
```

The 1,040-file closure covers src, tools, metadata and retained third-party
inputs, excluding Python caches. Freeze those bytes before building: test edits
also change private IDs. Expected IDs are `25532937c320b7975df520ec184031cb`
(full-RAM) and `f5851ceca322f726611592c1cafd3d74` (legacy checked).

## Observer and completion campaigns

The observer was built from z80pack revision
`b7a6fa36a2ee185a73727dc5b56ac1af40679e81`, with the exact 152 input-file hashes
recorded in `observer/provenance.json`. Those source bytes are in the bundle.
The observed binary SHA-256 is
`8327b10f9de3b5e95342a173bf6fa664a54e64d6211eca85c65f7db1e29849e1`.
Host compiler/build details may change this binary hash; the recorded artifact
identifies the executable used here.

```sh
python3 tools/build_cpmsim_stack_trace.py /path/to/z80pack-source --output /tmp/pc-observer
python3 tools/qualify_cpmsim_completion.py /tmp/pc-full --output /tmp/pc-traced-full --simulator /tmp/pc-observer/cpmsim/cpmsim
python3 tools/qualify_cpmsim_completion.py /tmp/pc-legacy --output /tmp/pc-traced-legacy --simulator /tmp/pc-observer/cpmsim/cpmsim
python3 tools/qualify_cpmsim_completion.py /tmp/pc-full --output /tmp/pc-ordinary-full --simulator /path/to/ordinary/cpmsim --untraced
python3 tools/qualify_cpmsim_completion.py /tmp/pc-legacy --output /tmp/pc-ordinary-legacy --simulator /path/to/ordinary/cpmsim --untraced
```

Run all cpmsim campaigns sequentially: auxiliary FIFO names are shared. The
first two rows of each traced campaign deliberately violate an observer rule
and must be detected; all 75 OS cases must finish without an observer violation.
Read each results JSON alongside its transcript and stack trace. The observer
is disabled in ordinary runs; compare the functional fields after excluding
stack and commit-counter instrumentation fields.

To isolate the repaired failure and its adjacent states, use
`--campaign faults --match 'ADM3A-|VT52-|ANSI-'`. The pre-repair witness in the
bundle uses commit `cf812ca1ba82e333a4daf1b052ddba5e2540d69e`, an explicitly
positioned/reverse ADM3A screen and the same self-restoring BIOS error leaf.
It is failure evidence, not a final distribution product.

## Existing acceptance campaigns and renderer comparison

```sh
python3 tools/qualify_part12_utilities.py /tmp/pc-full /tmp/pc-legacy --output /tmp/pc-utils-full --live
python3 tools/qualify_part12_utilities.py /tmp/pc-legacy /tmp/pc-full --output /tmp/pc-utils-legacy --live
python3 tools/qualify_part11_live.py /tmp/pc-full /tmp/pc-live-full
python3 tools/qualify_part11_live.py /tmp/pc-legacy /tmp/pc-live-legacy
python3 tools/qualify_part11_packages.py /tmp/pc-full /tmp/pc-legacy --output /tmp/pc-packages-full
python3 tools/qualify_part11_packages.py /tmp/pc-legacy /tmp/pc-full --output /tmp/pc-packages-legacy --live-only
python3 tools/qualify_cpmsim_renderer.py /tmp/pc-full --output /tmp/pc-renderer.json
python3 /tmp/pc-full/tools/test_screen_backends.py
```

Use a Python environment with pyte for the last two commands. The older Part
11 package helper retains its pinned Part 2 simulator path; either restore that
path from the bundled ordinary binary or change the local reproduction harness
path after freezing the build inputs. Such a harness edit does not reproduce
the published source closure if included in a subsequent product rebuild.
The Part 12 live helper accepts BETTERCPM_ASSESSMENT_SIM for a relocated simulator.

The final evidence has 35 identical repeat artifacts, 30 selected distribution
files per layout, unchanged clean images after testing, and no HELLO.RSX,
HELLO.CPX or STATEFUL.RSX on either clean image. The archive's SHA-256 ledger
covers every included file except the ledger itself. Test disk copies are
omitted where reproducible from the retained fixtures and commands.

## Try the qualified full-RAM image

Extract the report's acceptance bundle. Make a new writable working directory
with a `disks` subdirectory and copy `products/fullram/system.raw` to
`disks/drivea.dsk`. Keep the archive's original image unchanged. Launch the pinned
ordinary simulator with `cpmsim -z -d /absolute/path/to/disks`, using its adjacent
srctools in PATH as in the test-session helper. `STAT MEM` should report a maximum
COM of 57,344 bytes. Loading ANSISCRN and ADM3A reduces that to 54,272 bytes.

These are RAM cpmsim products. The legacy checked image is a comparison layout;
it is not a Model 4 or ROM image. The checked prototype uses the existing guarded
staging builder. Normal release-build integration is deliberately separate.
