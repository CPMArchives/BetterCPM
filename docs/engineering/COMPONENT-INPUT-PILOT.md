# Selected component input records: BYE pilot

Status: experimental input-record infrastructure, 2026-10-24.
Baseline: main `155d20ea26b84e9dab8baabd2f1f06d1c9d297fc` (registry PR #489 merged).

`tools/component_inputs.py` captures a deterministic selected-input record and
compares it with an explicitly supplied reference. The first map covers BYE's
default z80pack cross-build path. Other components, native builds and checked
profiles are refused rather than treated as unchanged. This does not implement
project-wide dependency enforcement or change executable output.

## Input selection

`metadata/component-inputs.json` lists explicit source/preparation files and the
effective origin/assembler flags. BYE uses `build_ccp.assemble`, which invokes
layout expansion and imports utility version and RSX container helpers. Those
preparation helpers and the default layout are therefore captured alongside
BYE's assembly source and common query include. Whole helper files are hashed
conservatively: an unrelated function edit in a shared helper may flag a
dependent for review, even if its executable ultimately remains identical.
This is the accepted distinction between affected inputs and changed bytes.

The registry contributes only BYE's version/API fields, not other components'
rows. Its revision remains comparison context outside the fingerprint to avoid
hashing a revision into itself. The selected map configuration and file list
are captured by value; adding another component's plan does not affect BYE.
Assembler bytes receive SHA-256 identification; no BetterCP/M counter is
assigned to the assembler. Tool paths, current HEAD, timestamps, generated
reports and artifact checksums are excluded from the selected-input hash.

The same file contents produce the same record regardless of whether an edit
is committed. Changed selected inputs compare as `development`; a byte-identical
input record compares as `unchanged`. Missing references, invalid record hashes
and wrong component/variant/assigned-identity references compare as `unknown`.
A matching fingerprint is not a qualification claim. No production revision
baseline is accepted or installed automatically by this tool.

## Use and boundaries

```sh
python3 tools/component_inputs.py utility:BYE --assembler /path/to/z80asm
python3 tools/component_inputs.py utility:BYE --assembler /path/to/z80asm \
  --baseline /path/to/reference-record.json
```

The command prints an envelope containing `record` and `comparison`. A reference
file must contain the `record` object alone. Without a baseline the command
still emits a captured record but returns unknown (exit 2). Exit 0 means a valid
comparison was made, whether unchanged or development; consumers must inspect
the state. Unsupported/missing inputs return unknown with an explanation.
Capture itself neither compiles nor writes files.

The BYE map is a pilot reviewed against the current source preparation, not an
automatically discovered or qualified closure. The actual builder is not yet
wired to emit/verify these records; callers must name the actual assembler.
There is no artifact/build provenance binding, baseline-publication operation,
executable-equivalence comparison, automatic revision assignment or `-dev`
banner embedding yet. Do not publish a capture as a build receipt. Python and
host execution-environment provenance also belong in later build records.

Prepared checked contexts are explicitly rejected. The existing broad checked
contract still needs independent redesign and validation; this map must not be
used to narrow runtime compatibility checks by assumption. Mixed subsystem
ownership, native prepared identities and generated linkage remain subsequent
mapping work. No claim of full versioning completion is made by this pilot.

## Verification

Twelve focused tests cover deterministic repeats, unrelated source/test/registry
and map edits, relevant source/helper edits, assembler and configuration changes,
revision self-exclusion, absent/corrupt references, unsupported components and
variants, missing files, duplicate/escaping paths, symlink escapes and checked
environment refusal. The eight registry tests and legacy projection checks
also pass. Tests use a fake assembler file as hash input; no compiler or
emulator execution is claimed.

```sh
python3 tools/test_component_inputs.py
python3 tools/test_component_registry.py
python3 tools/component_registry.py --check
```
