# Part 8 reproduction

Use `assessment/part8-carrier-binding`. These are isolated assessment builds,
not release commands. Host prerequisites are those in
[Part7-Reproduction.md](Part7-Reproduction.md): Python 3, z80asm 2.1 at
`~/bin/z80asm`, cpmtools and the pinned Part 2 cpmsim. Builders retain some
original host-specific assembler defaults; adjust them on another host.

Choose fresh absolute output directories. From the repository root:

```sh
python3 tools/assessment_checked_profiles.py cpmsim-fullram --carrier-bindings --output /tmp/p8-full
python3 tools/assessment_checked_profiles.py cpmsim-legacy-checked --carrier-bindings --output /tmp/p8-legacy
```

The flag migrates the admitted RSXs and rebuilds their readers. CCP and CPX in
the resulting media remain in their existing formats. M4SCRN and FREHDCLK
remain old-format, unadmitted platform artifacts. Inspect
`assessment-profile.json` and `assessment-build-logs/rsx-migration.json`.

Run the assembled-code and candidate-format fixtures from the full-RAM stage:

```sh
cd /tmp/p8-full
python3 tools/qualify_part8_rsx.py /tmp/p8-legacy/build/rsx
python3 tools/qualify_part8_formats.py
python3 tools/qualify_part7_container.py /tmp/p8-legacy/build/system/R3PACK.RSX
python3 tools/qualify_part7_raw.py
```

Read `assessment-build-logs/part8-rsx-tests.json`, `container-tests.json` and
`raw-tests.json`, plus `assessment-command-candidates/results.json`.
Candidate CCP/CPX files and the deliberately oversized reloader assembly are
saved under `assessment-command-candidates/`; they are not installed.

Run live cpmsim tests sequentially because it uses shared auxiliary FIFOs.
The old-RSX input should be the preserved Part 7 build, or an isolated checked
build made without `--carrier-bindings`:

```sh
export BETTERCPM_ASSESSMENT_SIM=/path/to/pinned/cpmsim
python3 tools/qualify_part7_live.py
P8_FOREIGN_RSX=/tmp/p8-legacy/build/rsx P8_OLD_RSX=/path/to/part7/build/rsx python3 tools/qualify_part8_live.py
python3 tools/qualify_part8_checksum_gap.py
python3 tools/qualify_part7_edges.py
```

The checksum-gap script is expected to print `CONFIRMED OPEN ISSUE` and record
that the changed payload executed with a stale checksum. It reproduces a
defect; success is not evidence the defect is fixed. Each live campaign works
on private disk copies under `qualification/`, preserving the original
`assessment-media/system.raw`. Read `qualification/results.json` and the
per-case transcripts. The evidence bundle also contains the checked legacy
smoke-test transcript and result.

For a clean repeat, build the same full-RAM profile into another fresh tree.
Compare `compatibility_id`, `build/` files with extensions `.bin`, `.rsx`,
`.cpx`, `.com`, `.rlm` (case insensitive), and `assessment-media/system.raw`.
Part 8's 182-file comparison is recorded in `repeated-build.json`. Source
revision metadata describes the checkout at build time; the content hashes
in the contract identify the exact private inputs, including uncommitted
prototype changes later preserved by the Part 8 commit. Listings and their
timestamps are not binary-equivalence tests.

The wrapper stages transformations rather than modifying the release sources
in place. The generated sources in the evidence bundle show the actually
tested result. Native packaging, Model 4, ROM, installation/private-utility
validation and complete stack/workspace qualification remain outside Part 8.
