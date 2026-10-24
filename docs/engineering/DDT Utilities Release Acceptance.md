# DDT Utilities Disk release acceptance

22 October 2026. DDT 1.0 Build 001.

DDT is accepted as a component of the tested Utilities Disk images for cpmsim and Model 4/trs80gp. This verdict covers the packaged program executing from Utilities B: beside normal System A:, including Model 4's normal M4SCRN/ADM3A startup. The Utilities Disk as a whole remains provisional: other manifest selections and packaging work are still pending. No distribution membership or debugger behavior changed.

## Acceptance boundary

The payload remains the qualified 6528-byte adaptation, SHA-256 `4b72c62b846dc3aaff673bf6b2fa3569c8fdc9887ca7927b3bf6ce3c357b6e46`. The Utilities builder verifies its on-disk readback before execution. The 332K raw cpmsim image and 800K Model 4 data DMK contain the owned adaptation; neither substitutes the historical reference.

The independent historical build again matches all 4864 bytes, SHA-256 `d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf`, with zero differences. DDT source, shared-library bindings, historical source/tools and earlier evidence bundles are untouched.

## Disposable-media campaign

`tools/build_distribution.py` rebuilds isolated normal System candidates for both platforms, checks filesystem/file integrity and configuration fingerprints, and boot-tests private copies. Both System candidates pass. The test then creates separate disposable A:/B: pairs, adds a six-byte controlled debuggee only to private A:, and runs DDT from the actual packaged Utilities B:. Original System images and packaged Utilities images are never mounted.

| Platform | Release-placement checks |
| --- | --- |
| cpmsim | `/VER`, invalid `/VER`, loading A:'s debuggee through `B:DDT TINY.COM`, edited arithmetic, F/S/D cancellation, queued A/L, breakpoint/restored instruction, T1, register PC input, U1, G0, restart and Ctrl-C |
| Model 4 | Normal startup and listed M4SCRN/ADM3A, `B:DDT /VER`, debuggee from A:, L, physical DEL editing, CLEAR cancellation without commit, memory readback, breakpoint, T1, register PC input, U1, G0, restart and physical BREAK |

The Model 4 campaign records fourteen VRAM stages; cpmsim records twenty-six interactions. Both return to caller A0. The original debuggee is read back unchanged, Utilities B: is byte-identical after execution, source System images are unchanged, and independent cpmtools filesystem checks pass for private A: and B:. System A: may create/retire the normal startup SUBMIT queue; this does not require changing any retained source image.

Earlier Model 4 tests cover the wider direct-console editing/rendering campaign and A/L input; the existing debugger qualification covers additional commands and HEX loading. This campaign establishes release placement and normal monitor-provider compatibility rather than changing or replacing those baselines. Real hardware and other monitor combinations remain outside the tested scope.

## Harness and packaging corrections

The System builder's cpmsim banner oracle expected the old compact identity twice. The styled cold banner now puts the product name and release on separate lines. The corrected oracle requires exactly one unique cold-banner operator hint and one compact identity from the explicit VER command. The full rebuilt System boot campaign passes this check; a missing or repeated cold banner still fails.

The first Model 4 release-placement runs sent commands before startup or RSX LIST had returned to CCP. The final harness waits for the unique normal startup banner and allows provider-list and version warm-boot output to settle. All subsequent assertions inspect captured guest output; a missing version response or debugger result fails acceptance. DDT needed no patch.

The Utilities builder accepts `--ddt-acceptance REPORT`. It binds the component verdict to the DDT artifact hash and both exact packaged image hashes before publishing either image. A supplied mismatched proof fails. Without a proof, DDT's per-image report remains `PENDING_RELEASE_ACCEPTANCE`; whole-disk status remains `PROVISIONAL` in either case. An acceptance receipt from a different Utilities generation cannot silently qualify a new image.

## Reproduction

Use fresh output/work directories:

```sh
python3 tools/build_distribution.py --target all \
  --output /private/tmp/ddt-system-release --work /private/tmp/ddt-system-work
python3 tools/test_ddt_utilities_release.py \
  --system /private/tmp/ddt-system-release/release-GENERATION \
  --artifacts /private/tmp/ddt-system-work/z80pack \
  --output /private/tmp/ddt-utilities-campaign
python3 tools/build_utilities_disk.py \
  --artifacts /private/tmp/ddt-system-work/z80pack \
  --ddt-acceptance /private/tmp/ddt-utilities-campaign/report.json \
  --output /private/tmp/ddt-utilities-bound
```

Replace `release-GENERATION` with the directory printed by the System builder. The acceptance harness records source and packaged-image hashes, emulator output, fixtures and post-run checks. Rebuilding Utilities with the same artifacts must match those hashes to bind the verdict. Changes to any packaged component require acceptance evidence for the resulting new media.

`DDT-Utilities-evidence.json` and `DDT-Utilities-evidence.tar.gz` retain the tested image hashes, passing campaign, image-bound package reports, proof-rejection checks, System validation summaries and the unchanged historical rebuild result. The manifest and user manual link this component acceptance while retaining whole-disk provisional status.

The [current-artifact reacceptance](Utility%20Release%20Reacceptance.md) repeats
this campaign on the recorded current System/Utilities pairs and binds DDT
Build 002 to the unchanged Utilities image hashes. The current inventory passes;
full disk selection and frozen-release closure remain separate.
