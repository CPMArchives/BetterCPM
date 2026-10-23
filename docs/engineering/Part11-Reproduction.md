# Part 11 reproduction

Use `assessment/part11-checked-packages`, with Python 3, cpmtools, z80asm 2.1 at
`~/bin/z80asm` and the pinned Part 2 cpmsim. Its SHA-256 remains
`b2d4384af06dbea8d32bc43eab539bf9e4857e74780577a249d0e8c5e22c955d`.
No Part 8 build artifacts are required: this part builds fresh profile trees.
Each output directory must be new.

```sh
python3 tools/assessment_checked_profiles.py cpmsim-fullram --carrier-bindings --streaming-commands --output /tmp/p11-full
python3 tools/assessment_checked_profiles.py cpmsim-legacy-checked --carrier-bindings --streaming-commands --output /tmp/p11-legacy
python3 tools/assessment_checked_profiles.py cpmsim-fullram --carrier-bindings --streaming-commands --output /tmp/p11-repeat
python3 tools/audit_part11_builds.py /tmp/p11-full /tmp/p11-legacy /tmp/p11-repeat --output /tmp/p11-audit.json
```

The input closure deliberately includes test tools and build metadata. Source
changes can therefore change private IDs. Read `assessment-profile.json` in
each stage. A different source revision or assembler may require newly matched
private products; do not substitute an earlier assessment's files.

Each stage emits its clean manifest-selected image, diskdefs, SYSTEM.SYS and
manifest under `assessment-media/`. `build/z80pack/checked-package.json` records
the normalized package check and critical destination files. The generated
`package-guard.inc`, final SYSGEN listing and command-loader listings explain
the executable gates. Stage1/stage2 and all command carriers are generated
inside the same build; no after-the-fact disk patch is part of this procedure.

Run cpmsim sessions sequentially because the emulator uses shared auxiliary
FIFO names. The test harness uses the pinned simulator at the assessment's
known `/tmp` path; adjust that path in the harness on another host, then rebuild
all profiles from the resulting source closure.

```sh
python3 tools/qualify_part11_live.py /tmp/p11-full /tmp/p11-live-full
python3 tools/qualify_part11_live.py /tmp/p11-legacy /tmp/p11-live-legacy
python3 tools/qualify_part11_packages.py /tmp/p11-full /tmp/p11-legacy --output /tmp/p11-packages-full
python3 tools/qualify_part11_packages.py /tmp/p11-legacy /tmp/p11-full --output /tmp/p11-packages-legacy --live-only
python3 tools/qualify_part10_stream.py /tmp/p11-full /tmp/p11-full/build/z80pack/command-loader
python3 tools/qualify_part9_bootstrap.py /tmp/p11-full /tmp/p11-full/build/z80pack/command-loader
```

The package harness also accepts `--fixtures-only`. In the preserved run the
full-RAM fixture and live outputs were kept in separate directories. Read all
results JSON and corresponding transcripts; a host-only package check is not
substituted for executing the assembled LOADFILE/P11CHECK/P11FILES paths.

Live command tests inject HELLO.CPX and STATEFUL only into disposable copies.
The package tests prepare matching destination RCP.CPX/R3PACK.RSX, preserve a
sentinel file, compare all filesystem bytes, and cold-boot the resulting target.
They use a non-writing saved startup command to avoid SUBMIT scratch-file
changes obscuring preservation checks. Bad destination-file cases deliberately
replace/remove those files before taking the unchanged-target baseline.

The clean images themselves exclude HELLO.RSX, HELLO.CPX and STATEFUL.RSX.
The evidence bundle contains their manifests, raw images, v2 packages, profile
contracts, source inputs/hashes, qualification fixtures and transcripts. Tests
run on copies; do not install assessment media as an approved release.

The installer preserves existing files; it does not deploy the entire new file
inventory. Prepare matching private components first. Native/ROM profiles,
SYSBUILD migration and installation-interruption recovery are not qualified
by these commands.
