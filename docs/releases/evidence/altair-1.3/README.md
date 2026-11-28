# Altair 1.3 release candidate evidence

All focused engineering and package gates pass. Publication is separate.
The frozen source commit is `cb561f759f81e215a0fe57256398c648dc0a23fc`;
its Git tree is `00ba2b312234d8dd670561091b97533c61bd47d0`.
The evidence/documentation commit following it does not change product inputs.

`summary.json` records seven native/platform gates, package checks, source reuse,
exact media hashes and both archive hashes. `receipts-and-transcripts.tar.gz`
contains the actual result files, console transcripts, build logs and the
package-check script. `artifact-ledger.json.gz` expands to the full downloadable
`ALTAIR-RELEASE.json`, including every archive member and media file hash.
`SHA256SUMS-Altair-1.3.txt` covers the additive release files;
`EVIDENCE-SHA256SUMS.txt` covers the retained evidence files.

The test campaign ran against source commit
`c1193311` (full identity in `summary.json`), whose Git tree is identical to the
frozen GitHub commit. Two original clean builds, a fresh frozen-source build and
a rebuild from the exported Source ZIP reproduce all four disk images.
Repeated packaging reproduces both ZIPs, the ledger and checksums byte-for-byte.
The package launcher builds its own emulator offline, preserves working media,
selects Utilities mounts, and leaves immutable masters unchanged.

The 269 independent automatic assertions are not a claim of 627 newly executed
cards. Shared 1.3 core evidence is reused only within the byte/source comparison
boundary. BIOS/controller/media, all 256 IOBYTE routes, cold configuration,
installation, full-disk management, error DMA behavior, loader guards, 45 utility
queries, screen personalities, overlays and native tools have direct evidence.
The claim is limited to Z80/64 KiB/88-2SIO/Tarbell under the pinned serial-only
emulator; physical hardware is unqualified.

## Reproduction

Read [Altair installation](../../../platform/ALTAIR-INSTALLATION.md). From the
frozen source root, use fresh output directories:

```sh
python3 tools/prepare_altair_emulator.py --output build/altair-emulator
python3 tools/build_altair.py --release --work build/altair-release
python3 tools/qualify_altair_release.py \
  --build-root build/altair-release/profiles/altair-fullram/altair \
  --simulator build/altair-emulator/altairsim/altairsim \
  --suite /path/to/rc564-conformance-suite --output build/altair-acceptance
python3 tools/package_altair.py \
  --build-root build/altair-release/profiles/altair-fullram/altair \
  --acceptance build/altair-acceptance --output build/altair-packages
```

The suite must contain pinned revision
`a9a878fcd2e36698c7e856654a85847a004fdd20`. The source offer includes the
pinned emulator/assembler sources. Package reconstruction was tested using the
same assembler executable as recorded; a different host/toolchain may produce
a different private binding and must build a coherent new set.

## Additive publication

After merge/release approval, upload the four files in
`metadata/release-assets-altair-1.3.json` to the existing v1.3 release. Verify
`SHA256SUMS-Altair-1.3.txt` first. Do not replace any of the eight existing 1.3
archives or their original source/documentation/checksum assets. The two new ZIPs
must be available together, preserving their matching source and notices.
